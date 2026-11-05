"""Publish immutable Chroma collections, reusing unchanged embeddings."""
import json
import os
import uuid
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from src.common import (
    PROCESSED,
    ROOT,
    digest,
    embedding_model,
    embedding_revision,
    load_jsonl,
    write_json,
    write_jsonl,
)

COLLECTION = "stem_career_docs"


@lru_cache(maxsize=2)
def load_model(name, revision=None):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name, revision=revision, trust_remote_code=False)


def chroma_client(path):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))


@contextmanager
def writer_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(f"Another index writer holds {path}; inspect before removing stale lock") from exc
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        path.unlink()


def active_collection(path=None, allow_partial=False):
    path = Path(path or ROOT / ".chroma")
    pointer = path / ("partial.json" if allow_partial and (path / "partial.json").exists() else "active.json")
    if not pointer.exists():
        if (path / "partial.json").exists():
            raise ValueError("Index is partial; inspect reports or explicitly use --allow-partial")
        raise ValueError("No published index. Run python -m src.pipeline first.")
    active = json.loads(pointer.read_text(encoding="utf-8"))
    if active.get("partial") and not allow_partial:
        raise ValueError("Index is partial; inspect reports or explicitly use --allow-partial")
    return chroma_client(path).get_collection(active["collection"], embedding_function=None), active


def chunk_metadata(chunk):
    return {key: (json.dumps(value, sort_keys=True, ensure_ascii=False) if isinstance(value, dict)
                  else str(value) if value is not None else "")
            for key, value in chunk.items() if key not in ("text", "chunk_id")}


def build_index(chunks=None, documents=None, path=None, model=None, model_name=None, partial=False):
    chunks = load_jsonl(PROCESSED / "chunks.jsonl") if chunks is None else chunks
    if not chunks:
        raise ValueError("No chunks found. Run pipeline first.")
    ids = [c["chunk_id"] for c in chunks]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate chunk_id")
    path = Path(path or ROOT / ".chroma")
    model_name = model_name or embedding_model()
    revision = embedding_revision(model_name)
    with writer_lock(path / "writer.lock"):
        client = chroma_client(path)
        # Diagnostic runs never overwrite the last complete index pointer.
        pointer = path / ("partial.json" if partial else "active.json")
        old = None
        if pointer.exists():
            active = json.loads(pointer.read_text(encoding="utf-8"))
            if active["embedding_model"] != model_name:
                raise ValueError("Index uses another embedding model; use a new index directory")
            if active.get("embedding_revision") != revision:
                raise ValueError("Index uses another embedding revision; use a new index directory")
            old = client.get_collection(active["collection"], embedding_function=None)
        existing = old.get(include=["metadatas"]) if old else {"ids": [], "metadatas": []}
        known = dict(zip(existing["ids"], existing["metadatas"], strict=True))
        incoming = set(ids)
        changed = [c for c in chunks if known.get(c["chunk_id"]) != chunk_metadata(c)]
        stale = set(known) - incoming
        stats = {"indexed": len(chunks), "added_or_updated": len(changed), "removed": len(stale),
                 "unchanged": len(chunks) - len(changed), "embedding_model": model_name,
                 "embedding_revision": revision}
        if old and not changed and not stale and active.get("partial", False) == partial:
            return {**stats, "collection": old.name, "embeddings_generated": 0, "published": True}
        name = f"{COLLECTION}_{uuid.uuid4().hex}"
        target = client.create_collection(name, embedding_function=None,
                                          metadata={"hnsw:space": "cosine", "embedding_model": model_name})
        snapshot = path / "snapshots" / name
        try:
            encoded = 0
            for offset in range(0, len(chunks), 64):
                batch = chunks[offset:offset + 64]
                reusable = [c["chunk_id"] for c in batch if c["chunk_id"] in known
                            and known[c["chunk_id"]].get("content_sha256") == c["content_sha256"]]
                cached = old.get(ids=reusable, include=["embeddings"]) if reusable else {"ids": [], "embeddings": []}
                vectors = dict(zip(cached["ids"], cached["embeddings"], strict=True))
                fresh = [c for c in batch if c["chunk_id"] not in vectors]
                if fresh:
                    encoder = model if model is not None else load_model(model_name, revision)
                    embeddings = encoder.encode([c["text"] for c in fresh], normalize_embeddings=True)
                    vectors.update(zip([c["chunk_id"] for c in fresh], embeddings, strict=True))
                    encoded += len(fresh)
                target.add(ids=[c["chunk_id"] for c in batch],
                           embeddings=[[float(value) for value in vectors[c["chunk_id"]]] for c in batch],
                           documents=[c["text"] for c in batch], metadatas=[chunk_metadata(c) for c in batch])
            if target.count() != len(chunks) or set(target.get(include=[])["ids"]) != incoming:
                raise RuntimeError("Staged index validation failed")
            # Snapshot files and pointer belong to the same generation as the collection.
            write_jsonl(snapshot / "chunks.jsonl", chunks)
            if documents is not None:
                write_jsonl(snapshot / "documents.jsonl", documents)
            write_json(pointer, {"collection": name, "embedding_model": model_name,
                                 "embedding_revision": revision,
                                 "partial": partial, "chunks": len(chunks),
                                 "dataset_sha256": digest(json.dumps(chunks, sort_keys=True, ensure_ascii=False)),
                                 "snapshot": str(snapshot.relative_to(path))})
        except Exception:
            client.delete_collection(name)
            raise
        return {**stats, "collection": name, "embeddings_generated": encoded, "published": True}


if __name__ == "__main__":
    # Standalone indexing must verify completeness against the configured manifest.
    from src.quality import validate_chunks, validate_documents
    documents = load_jsonl(PROCESSED / "documents.jsonl")
    chunks = load_jsonl(PROCESSED / "chunks.jsonl")
    validate_documents(documents)
    validate_chunks(documents, chunks)
    sources = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))
    if {s["id"] for s in sources if s.get("enabled", True)} != {d["document_id"] for d in documents}:
        raise SystemExit("Dataset is incomplete; run pipeline instead")
    print(json.dumps(build_index(chunks, documents), indent=2))
