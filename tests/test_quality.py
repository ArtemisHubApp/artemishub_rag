import copy

import pytest

from src.common import digest
from src.eda import analyze
from src.prepare import prepare
from src.quality import validate_chunks, validate_documents


def test_hash_and_duplicate_validation(document):
    with pytest.raises(ValueError, match="Duplicate"):
        validate_documents([document, document])
    document["content_hash"] = "incorrect"
    with pytest.raises(ValueError, match="content_hash"):
        validate_documents([document])


@pytest.mark.parametrize("mutation,match", [
    ({"document_id": "missing"}, "reference"), ({"source_url": "https://other.org"}, "reference"),
    ({"text": ""}, "size"), ({"text": "x" * 1201}, "size"),
    ({"content_sha256": "incorrect"}, "hash"), ({"chunk_index": -1}, "chunk_index"),
])
def test_invalid_chunks(document, mutation, match):
    chunks = prepare([document])
    chunks[0].update(mutation)
    with pytest.raises(ValueError, match=match):
        validate_chunks([document], chunks)


def test_chunk_integrity_and_eda(document):
    chunks = prepare([document], chunk_size=150, overlap=20)
    assert validate_chunks([document], chunks)["chunks"] == len(chunks)
    report = analyze([document], chunks, [{"status": "success"}, {"status": "failed"}])
    assert report["source_success_percent"] == 50
    assert report["metadata_coverage"]["content_hash"] == 1
    assert report["document_characters"]["mean"] == len(document["content"])
    assert not report["problem_documents"]
    with pytest.raises(ValueError, match="Duplicate chunk_id|chunk_index"):
        validate_chunks([document], chunks + [chunks[0]])
    other = copy.deepcopy(document)
    other["document_id"] = "other"
    with pytest.raises(ValueError, match="without chunks"):
        validate_chunks([document, other], chunks)
    document["content"] = ""
    document["content_hash"] = digest("")
    with pytest.raises(ValueError, match="Missing content|short"):
        validate_documents([document])
