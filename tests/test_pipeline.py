import json

import httpx
import pytest

from src import ingest, pipeline
from src.common import load_jsonl
from src.pipeline import validate_documents


def test_rejects_empty_documents():
    with pytest.raises(ValueError, match="No documents"):
        validate_documents([])


def test_rejects_missing_provenance():
    with pytest.raises(ValueError, match="source_url"):
        validate_documents([{"document_id": "x", "title": "t", "content": "a" * 120, "content_sha256": "x"}])


def test_accepts_valid_document():
    doc = {"document_id": "x", "source_url": "https://example.org", "title": "t", "content": "a" * 120, "content_sha256": "x"}
    assert validate_documents([doc]) == {"documents": 1, "sources": 1}


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
