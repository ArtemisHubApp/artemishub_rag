import json

import pytest

from src import pipeline
from src.common import load_jsonl


@pytest.fixture
def local_pipeline(tmp_path, monkeypatch):
    source = {"id": "example", "title": "Example", "organization": "Org",
              "url": "https://example.org/document", "topic": "career", "kind": "html"}
    manifest = tmp_path / "sources.json"
    manifest.write_text(json.dumps([source]), encoding="utf-8")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "PROCESSED", tmp_path / "processed")
    
    def respond(status, content):
        def mock_fetch(client, url, retries):
            class Response:
                def __init__(self, s, c):
                    self.status_code = s
                    self.text = c
                    self.content = c.encode("utf-8")
                    self.url = url
                    self.headers = {"content-type": "text/html"}
                def json(self): return {}
            return content.encode("utf-8"), Response(status, content), []
        
        monkeypatch.setattr("src.ingest.fetch", mock_fetch)
        
    return tmp_path, manifest, respond

def test_pipeline_basic_flow(local_pipeline, monkeypatch):
    root, manifest, respond = local_pipeline
    respond(200, "<nav>IGNORE</nav><main>" + "Orientação de carreira. " * 100 + "</main>")
    
    import src.index
    monkeypatch.setattr(src.index, "build_index", lambda *args, **kwargs: {"indexed": 1})
    
    stats = pipeline.run(manifest, skip_index=True)
    assert stats["status"] == "success"
    assert stats["documents"] == 1
    
    documents = load_jsonl(root / "processed" / "documents.jsonl")
    assert len(documents) == 1
    assert "IGNORE" not in documents[0]["content"]

def test_failed_collection_preserves_published_dataset(local_pipeline):
    root, manifest, respond = local_pipeline
    processed = root / "processed"
    processed.mkdir()
    previous = processed / "documents.jsonl"
    
    valid_doc = {
        "document_id": "old", 
        "source_url": "http://old.org", 
        "title": "Old", 
        "content": "old content", 
        "content_sha256": "abc", 
        "organization": "Org"
    }
    previous.write_text(json.dumps(valid_doc) + "\n", encoding="utf-8")
    
    respond(503, "Unavailable")
    
    with pytest.raises(RuntimeError, match="refusing partial"):
        pipeline.run(manifest)
    
    assert previous.exists()
    assert "old content" in previous.read_text()

def test_full_pipeline_with_real_chroma(local_pipeline, monkeypatch):
    root, manifest, respond = local_pipeline
    respond(200, "<main>" + "Evidência sintética de integração local. " * 50 + "</main>")

    import numpy as np

    import src.index
    class Encoder:
        def encode(self, texts, normalize_embeddings=True):
            return np.tile(np.array([1.0, 0.0, 0.0], dtype=np.float32), (len(texts), 1))
    
    monkeypatch.setattr(src.index, "ROOT", root)
    monkeypatch.setattr(src.index, "load_model", lambda *args: Encoder())
    
    result = pipeline.run(manifest)
    assert result["status"] == "success"
    assert result["documents"] == 1

def test_wrong_document_markers_fail_closed(local_pipeline):
    root, manifest, respond = local_pipeline
    sources = json.loads(manifest.read_text())
    sources[0]["expected_text"] = ["Mandatory expected document header"]
    manifest.write_text(json.dumps(sources))
    respond(200, "<main>" + "Unrelated error page content. " * 50 + "</main>")
    
    with pytest.raises(RuntimeError, match="refusing partial"):
        pipeline.run(manifest)
    
    report_path = root / "reports" / "latest_run.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["status"] == "failed"
