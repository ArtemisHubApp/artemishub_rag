from src.demo import render_markdown, run
from src.query import ABSTENTION


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits

    def retrieve(self, question, top_k):
        return self.hits[:top_k]


HITS = [
    {"text": "Denúncias podem ser feitas ao MTE.", "distance": 0.21,
     "metadata": {"title": "Cartilha", "source_url": "https://example.org/cartilha", "page": "14"}},
    {"text": "Texto da lei.", "distance": 0.4,
     "metadata": {"title": "Lei", "source_url": "https://example.org/lei", "page": ""}},
]


def test_run_records_answer_citations_and_isolates_failures():
    def generator(question, hits):
        if "falha" in question:
            raise RuntimeError("Authorization: Bearer secret")
        return "Use os canais do MTE [FONTE 1]."

    results = run(["Onde denunciar?", "pergunta com falha"], FakeRetriever(HITS), generator)
    assert results[0]["cited"] == [1] and results[0]["error"] is None
    assert results[1]["error"] == "RuntimeError"
    assert "secret" not in render_markdown(results, {})


def test_render_marks_cited_source_abstention_and_missing_llm():
    results = run(["a", "b", "c"], FakeRetriever(HITS),
                  lambda q, h: {"a": "Resposta [FONTE 2]", "b": ABSTENTION, "c": None}[q])
    text = render_markdown(results, {"llm_model": "gemini-test", "retrieval": "hybrid"})
    assert "[FONTE 2]** [Lei](https://example.org/lei) · página n/d · distância 0.400 · **citada na resposta**" in text
    assert "abstenções: 1" in text
    assert "LLM não configurado" in text
    assert "gemini-test" in text


def test_invalid_citation_records_reason_and_raw_answer():
    results = run(["a"], FakeRetriever(HITS), lambda q, h: "Inventado [FONTE 9]")
    result = results[0]
    assert result["error"] == "CitationValidationError"
    assert result["citation_error_reason"] == "LLM cited a source that was not retrieved"
    assert result["citation_error_raw_answer"] == "Inventado [FONTE 9]"
    text = render_markdown(results, {})
    assert "LLM cited a source that was not retrieved" in text
    assert "Resposta barrada pelo validador — não exibida ao usuário" in text
    assert "Inventado [FONTE 9]" in text


def test_network_failure_still_hides_details():
    def generator(question, hits):
        raise RuntimeError("Authorization: Bearer secret")

    results = run(["a"], FakeRetriever(HITS), generator)
    result = results[0]
    assert result["error"] == "RuntimeError"
    assert result["citation_error_reason"] is None
    assert result["citation_error_raw_answer"] is None
    text = render_markdown(results, {})
    assert "secret" not in text
    assert "Falha na geração (RuntimeError)" in text
