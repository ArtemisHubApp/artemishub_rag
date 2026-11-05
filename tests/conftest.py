import pytest

from src.common import digest


@pytest.fixture
def document():
    text = "Igualdade salarial e transparência para mulheres em STEM. " * 5
    return {"document_id": "test", "title": "Fixture local, sem valor jurídico", "source": "Fixture",
            "organization": "Fixture", "topic": "test", "document_type": "html",
            "source_url": "https://example.org/test", "collected_at": "2026-11-05T00:00:00+00:00",
            "page": None, "content": text, "content_hash": digest(text),
            "content_sha256": digest(text), "metadata": {"page": None}}
