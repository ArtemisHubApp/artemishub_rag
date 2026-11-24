import pytest

from artemis_rag.common import digest


@pytest.fixture
def document():
    text = "Igualdade salarial e transparência para mulheres em STEM. " * 5
    return {"document_id": "test", "title": "Fixture local, sem valor jurídico", "source": "Fixture",
            "organization": "Fixture", "topic": "test", "document_type": "html",
            "source_url": "https://example.org/test", "collected_at": "2026-11-05T00:00:00+00:00",
            "page": None, "content": text, "content_hash": digest(text),
            "content_sha256": digest(text), "metadata": {"page": None}}


@pytest.fixture(autouse=True)
def prompts_de_teste(monkeypatch):
    """Nenhum teste busca prompt na rede; o texto devolvido identifica o prompt pedido."""
    from artemis_rag import query
    from scripts import compare_llm_rag, judge_answers

    for modulo in (query, compare_llm_rag, judge_answers):
        monkeypatch.setattr(modulo, "obter_prompt", lambda nome, **variaveis: f"PROMPT {nome}")
    monkeypatch.setattr(query, "langfuse_configurado", lambda: True)
