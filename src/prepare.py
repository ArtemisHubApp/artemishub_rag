"""Build deterministic, overlapping character chunks with traceable metadata."""

from src.common import PROCESSED, digest, load_jsonl, write_jsonl


def split_text(text, chunk_size=1200, overlap=180):
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    text = text.strip()
    result = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(text.rfind(". ", start + chunk_size // 2, end), text.rfind("\n", start + chunk_size // 2, end))
            if boundary > start:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            result.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return result


def prepare(documents, chunk_size=600, overlap=100):
    rows = []
    seen = set()
    for doc in documents:
        for i, text in enumerate(split_text(doc["content"], chunk_size, overlap)):
            chunk_id = digest(f"{doc['document_id']}|{doc.get('page')}|{i}|{text}")[:24]
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            rows.append({
                "chunk_id": chunk_id, "document_id": doc["document_id"],
                "title": doc["title"], "organization": doc["organization"],
                "source_url": doc["source_url"], "topic": doc["topic"],
                "page": doc.get("page"), "text": text,
                "chunk_index": i,
                "metadata": {**doc.get("metadata", {}), "page": doc.get("page")},
                "content_sha256": digest(text)
            })
    return rows


def main():
    from src.quality import validate_chunks, validate_documents
    docs = load_jsonl(PROCESSED / "documents.jsonl")
    validate_documents(docs)
    chunks = prepare(docs)
    validate_chunks(docs, chunks)
    write_jsonl(PROCESSED / "chunks.jsonl", chunks)
    print(f"Wrote {len(chunks)} chunks")


if __name__ == "__main__":
    main()
