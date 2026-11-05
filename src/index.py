"""Incrementally synchronize chunks with Chroma, without deleting the index first."""
import chromadb
from sentence_transformers import SentenceTransformer

from src.common import PROCESSED, ROOT, embedding_model, load_jsonl

COLLECTION = "stem_career_docs"


def build_index():
    chunks = load_jsonl(PROCESSED / "chunks.jsonl")
    if not chunks:
        raise ValueError("No chunks found. Run pipeline first.")
    client = chromadb.PersistentClient(path=str(ROOT / ".chroma"))
    model_name = embedding_model()
    collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine", "embedding_model": model_name})
    current_model = (collection.metadata or {}).get("embedding_model")
    if current_model and current_model != model_name:
        raise ValueError(f"Index model is {current_model}, requested {model_name}; rebuild index explicitly")
    # For this small MVP, fetching IDs + hashes is acceptable; use paginated queries at scale.
    existing = collection.get(include=["metadatas"])
    known = {id_: meta.get("content_sha256") for id_, meta in zip(existing["ids"], existing["metadatas"])}
    incoming = {chunk["chunk_id"] for chunk in chunks}
    changed = [c for c in chunks if known.get(c["chunk_id"]) != c["content_sha256"]]
    stale = set(known) - incoming
    if changed:
        model = SentenceTransformer(model_name)
        for offset in range(0, len(changed), 64):
            batch = changed[offset:offset + 64]
            embeddings = model.encode([c["text"] for c in batch], normalize_embeddings=True).tolist()
            collection.upsert(
                ids=[c["chunk_id"] for c in batch], embeddings=embeddings,
                documents=[c["text"] for c in batch],
                metadatas=[{k: (str(v) if v is not None else "") for k, v in c.items() if k not in ("text", "chunk_id")} for c in batch],
            )
    # Delete stale entries only after successful additions.
    stale_ids = sorted(stale)
    for offset in range(0, len(stale_ids), 500):
        collection.delete(ids=stale_ids[offset:offset + 500])
    stats = {"indexed": collection.count(), "added_or_updated": len(changed), "removed": len(stale), "unchanged": len(chunks) - len(changed), "embedding_model": model_name}
    print(f"Index synchronized: {stats}")
    return stats


if __name__ == "__main__":
    build_index()
