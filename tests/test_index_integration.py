"""Real persistent Chroma, deterministic local encoder; no model download."""
import json

import numpy as np
import pytest

from src.common import digest
from src.index import active_collection, build_index
from src.prepare import prepare
from src.query import Retriever


class LocalEncoder:
    def __init__(self, fail=False):
        self.encoded = 0
        self.fail = fail

    def encode(self, texts, normalize_embeddings=True):
        if self.fail:
            raise RuntimeError("Simulated embedding failure")
        self.encoded += len(texts)
        vectors = np.array([[text.lower().count("salarial") + 1, text.lower().count("carreira") + 1,
                             text.lower().count("transparência") + 1] for text in texts], dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def test_persistent_idempotent_incremental_index_and_retrieval(tmp_path, document):
    path = tmp_path / "index"
    encoder = LocalEncoder()
    chunks = prepare([document], chunk_size=150, overlap=20)
    first = build_index(chunks, [document], path=path, model=encoder, model_name="local-fixture")
    assert encoder.encoded == len(chunks)
    second = build_index(chunks, [document], path=path, model=encoder, model_name="local-fixture")
    assert first["collection"] == second["collection"]
    assert second["added_or_updated"] == 0 and encoder.encoded == len(chunks)
    retriever = Retriever(path=path, model=encoder, model_name="local-fixture")
    hits = retriever.retrieve("igualdade salarial")
    assert hits and hits[0]["metadata"]["source_url"] == document["source_url"]
    assert all(h["chunk_id"] in {c["chunk_id"] for c in chunks} for h in hits)
    document["content"] += " Nova informação sobre carreira."
    document["content_hash"] = document["content_sha256"] = digest(document["content"])
    updated = prepare([document], chunk_size=150, overlap=20)
    before = encoder.encoded
    third = build_index(updated, [document], path=path, model=encoder, model_name="local-fixture")
    fresh = {c["chunk_id"] for c in updated} - {c["chunk_id"] for c in chunks}
    assert encoder.encoded - before == len(fresh)
    assert third["removed"] == len({c["chunk_id"] for c in chunks} - {c["chunk_id"] for c in updated})
    active, _ = active_collection(path)
    assert set(active.get(include=[])["ids"]) == {c["chunk_id"] for c in updated}
    assert json.loads(active.get(include=["metadatas"])["metadatas"][0]["metadata"])["page"] is None


def test_failed_update_keeps_previous_snapshot(tmp_path, document):
    chunks = prepare([document])
    build_index(chunks, [document], path=tmp_path, model=LocalEncoder(), model_name="local-fixture")
    previous = (tmp_path / "active.json").read_bytes()
    document["content"] = "Changed content " * 30
    updated = prepare([document])
    with pytest.raises(RuntimeError, match="Simulated"):
        build_index(updated, [document], path=tmp_path, model=LocalEncoder(fail=True), model_name="local-fixture")
    assert (tmp_path / "active.json").read_bytes() == previous
    active, _ = active_collection(tmp_path)
    assert active.get(include=[])["ids"] == [c["chunk_id"] for c in chunks]
    assert not (tmp_path / "writer.lock").exists()
    with pytest.raises(ValueError, match="another embedding"):
        build_index(chunks, path=tmp_path, model=LocalEncoder(), model_name="other")


def test_partial_index_requires_opt_in(tmp_path, document):
    build_index(prepare([document]), [document], path=tmp_path, model=LocalEncoder(), model_name="local-fixture", partial=True)
    with pytest.raises(ValueError, match="partial"):
        active_collection(tmp_path)
    assert active_collection(tmp_path, allow_partial=True)[1]["partial"]


def test_partial_run_preserves_complete_pointer(tmp_path, document):
    chunks = prepare([document])
    full = build_index(chunks, [document], path=tmp_path, model=LocalEncoder(), model_name="local-fixture")
    pointer = (tmp_path / "active.json").read_bytes()
    build_index(chunks, [document], path=tmp_path, model=LocalEncoder(), model_name="local-fixture", partial=True)
    assert (tmp_path / "active.json").read_bytes() == pointer
    assert active_collection(tmp_path)[0].name == full["collection"]
    assert active_collection(tmp_path, allow_partial=True)[1]["partial"]


def test_failed_pointer_publication_preserves_complete_index(tmp_path, document, monkeypatch):
    from src import index

    chunks = prepare([document])
    build_index(chunks, [document], path=tmp_path, model=LocalEncoder(), model_name="local-fixture")
    pointer = (tmp_path / "active.json").read_bytes()
    document["content"] += " Updated text."
    updated = prepare([document])

    def fail_publication(*args, **kwargs):
        raise OSError("Simulated atomic publication failure")

    monkeypatch.setattr(index, "write_json", fail_publication)
    with pytest.raises(OSError, match="publication failure"):
        build_index(updated, [document], path=tmp_path, model=LocalEncoder(), model_name="local-fixture")
    assert (tmp_path / "active.json").read_bytes() == pointer
    assert set(active_collection(tmp_path)[0].get(include=[])["ids"]) == {c["chunk_id"] for c in chunks}


def test_metadata_only_change_reuses_embedding(tmp_path, document):
    encoder = LocalEncoder()
    build_index(prepare([document]), [document], path=tmp_path, model=encoder, model_name="local-fixture")
    before = encoder.encoded
    document["title"] = "Updated fixture title"
    result = build_index(prepare([document]), [document], path=tmp_path, model=encoder, model_name="local-fixture")
    assert result["added_or_updated"] == 1
    assert encoder.encoded == before and result["embeddings_generated"] == 0
    assert active_collection(tmp_path)[0].get(include=["metadatas"])["metadatas"][0]["title"] == document["title"]
