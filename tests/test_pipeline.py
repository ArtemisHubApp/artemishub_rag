import json

import httpx
import pytest

from src import ingest, pipeline
from src.common import load_jsonl
from src.common import validate_documents


def test_rejects_empty_documents():
    with pytest.raises(ValueError, match="No documents"):
        validate_documents([])


def test_rejects_missing_provenance(document):
    del document["source_url"]
    with pytest.raises(ValueError, match="source_url"):
        validate_documents([document])


def test_accepts_valid_document(document):
    assert validate_documents([document]) == {"documents": 1, "sources": 1}


@pytest.fixture
def local_pipeline(tmp_path, monkeypatch):
    source = {"id": "example", "title": "Example", "organization": "Org",
              "url": "https://example.org/document", "topic": "career", "kind": "html"}
    manifest = tmp_path / "sources.json"
    manifest.write_text(json.dumps([source]), encoding="utf-8")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(ingest, "RAW", tmp_path / "raw")
    real_client = httpx.Client

    def install_response(status, body):
        transport = httpx.MockTransport(
            lambda request: httpx.Response(status, text=body, headers={"content-type": "text/html"})
        )
        monkeypatch.setattr(ingest.httpx, "Client", lambda **kw: real_client(transport=transport, **kw))
        monkeypatch.setattr(ingest.time, "sleep", lambda _: None)

    return tmp_path, manifest, install_response


def test_pipeline_extracts_chunks_and_reports(local_pipeline):
    root, manifest, respond = local_pipeline
    respond(200, "<nav>IGNORE</nav><main>" + "Orientação de carreira. " * 100 + "</main>")
    stats = pipeline.run(manifest, skip_index=True)
    documents = load_jsonl(root / "processed" / "documents.jsonl")
    chunks = load_jsonl(root / "processed" / "chunks.jsonl")
    assert stats["sources"] == 1
    assert stats["chunks"] == len(chunks) > 0
    assert "IGNORE" not in documents[0]["content"]
    assert all(c["source_url"] == "https://example.org/document" for c in chunks)
    assert json.loads((root / "reports" / "latest_run.json").read_text())["chunks"] == len(chunks)


def test_failed_collection_preserves_published_dataset(local_pipeline):
    root, manifest, respond = local_pipeline
    processed = root / "processed"
    processed.mkdir()
    previous = processed / "documents.jsonl"
    previous.write_text("previous dataset", encoding="utf-8")
    respond(503, "Unavailable")
    with pytest.raises(RuntimeError, match="refusing partial publication"):
        pipeline.run(manifest, skip_index=True)
    assert previous.read_text() == "previous dataset"
    assert not (processed / "chunks.jsonl").exists()


def test_full_pipeline_with_real_chroma(local_pipeline, monkeypatch):
    import numpy as np

    from src import index
    from src.query import Retriever

    root, manifest, respond = local_pipeline
    respond(200, "<main>" + "Evidência sintética de integração local. " * 50 + "</main>")

    class Encoder:
        def encode(self, texts, normalize_embeddings=True):
            return np.tile(np.array([1.0, 0.0, 0.0], dtype=np.float32), (len(texts), 1))

    monkeypatch.setattr(index, "ROOT", root)
    monkeypatch.setattr(index, "load_model", lambda *args: Encoder())
    result = pipeline.run(manifest)
    assert result["status"] == "success" and result["index_published"]
    assert pipeline.run(manifest)["index"]["embeddings_generated"] == 0
    hits = Retriever(path=root / ".chroma", model=Encoder()).retrieve("fixture")
    assert hits and hits[0]["metadata"]["document_id"] == "example"


def test_wrong_document_markers_fail_closed(local_pipeline):
    root, manifest, respond = local_pipeline
    sources = json.loads(manifest.read_text())
    sources[0]["expected_text"] = ["Mandatory expected document header"]
    manifest.write_text(json.dumps(sources))
    respond(200, "<main>" + "Unrelated error page content. " * 50 + "</main>")
    with pytest.raises(RuntimeError, match="refusing partial"):
        pipeline.run(manifest, skip_index=True)
    report = json.loads((root / "reports" / "latest_run.json").read_text())
    assert report["source_outcomes"][0]["status"] == "failed"
    assert "marker missing" in report["source_outcomes"][0]["reason"]
    assert not (root / "processed" / "documents.jsonl").exists()


@pytest.mark.parametrize("status,expected", [("success", 0), ("partial", 2)])
def test_cli_exit_codes(monkeypatch, status, expected):
    monkeypatch.setattr("sys.argv", ["pipeline"])
    monkeypatch.setattr(pipeline, "run", lambda *args: {"status": status})
    with pytest.raises(SystemExit) as error:
        pipeline.main()
    assert error.value.code == expected
