from src.prepare import prepare, split_text


def test_chunks_overlap_and_cover_end():
    text = "abcde " * 100
    chunks = split_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert chunks[-1].endswith("abcde")


def test_prepare_keeps_provenance():
    docs = [{"document_id": "doc1", "title": "Title", "organization": "Org", "source_url": "https://example.org", "topic": "test", "page": 2, "content": "Texto de teste. " * 100}]
    chunks = prepare(docs)
    assert chunks and all(c["document_id"] == "doc1" and c["page"] == 2 for c in chunks)
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
