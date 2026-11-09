"""Run a fixed set of questions end to end and save the evidence as Markdown.

Produces the demonstration required by the deliverable: the question, the
retrieved chunks with their sources, the generated answer and the citations
actually used. Credentials are read from the environment and never written.
"""
import argparse
import datetime as dt
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from src.common import ROOT
from src.query import ABSTENTION, CitationValidationError, generate, validate_citations

QUESTIONS = [
    "Onde faço uma denúncia de desigualdade salarial?",
    "Quais empresas precisam publicar o relatório de transparência salarial?",
    "Qual a multa se a empresa pagar menos para uma mulher na mesma função?",
    "Quanto as mulheres ganham em média em relação aos homens no Brasil?",
    "Qual a previsão do tempo para amanhã?",  # fora da base: espera-se abstenção
]


def run(questions, retriever, generator=generate, top_k=5):
    """Return one result per question; a failure in one question never stops the others."""
    results = []
    for question in questions:
        result = {"question": question, "hits": [], "answer": None, "cited": [], "error": None,
                  "citation_error_reason": None, "citation_error_raw_answer": None}
        try:
            result["hits"] = retriever.retrieve(question, top_k)
            answer = generator(question, result["hits"])
            result["answer"] = answer
            if answer and answer != ABSTENTION:
                result["cited"] = validate_citations(answer, result["hits"])
        except CitationValidationError as exc:
            result["error"] = type(exc).__name__
            result["citation_error_reason"] = str(exc)
            result["citation_error_raw_answer"] = exc.raw_answer
        except Exception as exc:  # noqa: BLE001 - recorded per question; details may hold secrets
            result["error"] = type(exc).__name__
        results.append(result)
    return results


def _one_line(text, limit=350):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def render_markdown(results, context):
    lines = ["# Demonstração do RAG Artemis", ""]
    lines += [f"- **Executado em:** {context.get('run_at', '')}",
              f"- **Modelo de geração:** {context.get('llm_model') or 'não configurado (só evidências)'}",
              f"- **Provedor:** {context.get('llm_host') or 'n/d'}",
              f"- **Estratégia de busca:** {context.get('retrieval', '')}",
              f"- **Coleção do índice:** {context.get('collection', 'n/d')}",
              f"- **Hash do dataset indexado:** {context.get('dataset_sha256', 'n/d')}", ""]
    answered = sum(bool(r["answer"]) and r["answer"] != ABSTENTION and not r["error"] for r in results)
    abstained = sum(r["answer"] == ABSTENTION for r in results)
    failed = sum(bool(r["error"]) for r in results)
    lines += [f"Perguntas: {len(results)} · respondidas com citação: {answered} · abstenções: {abstained} · falhas: {failed}", ""]
    for number, result in enumerate(results, 1):
        lines += [f"## {number}. {result['question']}", "", "### Trechos recuperados", ""]
        if not result["hits"]:
            lines += ["Nenhum trecho recuperado.", ""]
        for index, hit in enumerate(result["hits"], 1):
            meta = hit.get("metadata", {})
            page = meta.get("page") or "n/d"
            distance = hit.get("distance")
            distance_text = f" · distância {distance:.3f}" if isinstance(distance, (int, float)) else ""
            used = " · **citada na resposta**" if index in result["cited"] else ""
            lines += [f"**[FONTE {index}]** [{meta.get('title', 'sem título')}]({meta.get('source_url', '')})"
                      f" · página {page}{distance_text}{used}", "",
                      f"> {_one_line(hit.get('text'))}", ""]
        lines += ["### Resposta", ""]
        if result["citation_error_reason"] is not None:
            lines += [f"Falha na geração ({result['error']}): {result['citation_error_reason']}.", "",
                      "**Resposta barrada pelo validador — não exibida ao usuário:**", "",
                      f"> {_one_line(result['citation_error_raw_answer'], limit=2000)}", ""]
        elif result["error"]:
            lines += [f"Falha na geração ({result['error']}). Confira a configuração do LLM e rode de novo.", ""]
        elif result["answer"] is None:
            lines += ["LLM não configurado. Defina LLM_API_KEY e LLM_MODEL no .env.", ""]
        else:
            lines += [result["answer"].strip(), ""]
            if result["cited"]:
                lines += ["Fontes citadas: " + ", ".join(f"FONTE {n}" for n in result["cited"]), ""]
    lines += ["---", "",
              "A validação confere que cada parágrafo cita uma fonte recuperada; não verifica se o trecho sustenta a frase. "
              "Revise as respostas comparando com os trechos acima.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run demonstration questions and save evidence as Markdown")
    parser.add_argument("--questions", help="Text file with one question per line (default: built-in set)")
    parser.add_argument("--output", default=str(ROOT / "reports" / "demo_rag.md"))
    parser.add_argument("--retrieval", choices=("dense", "pages", "hybrid"), default="hybrid")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    questions = QUESTIONS
    if args.questions:
        questions = [line.strip() for line in Path(args.questions).read_text(encoding="utf-8").splitlines() if line.strip()]
    from src.query import Retriever
    retriever = Retriever(strategy=args.retrieval)
    results = run(questions, retriever, top_k=args.top_k)
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1") if os.getenv("LLM_API_KEY") else ""
    context = {"run_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
               "llm_model": os.getenv("LLM_MODEL") if os.getenv("LLM_API_KEY") else None,
               "llm_host": urlparse(base_url).hostname if base_url else None,
               "retrieval": args.retrieval, "collection": retriever.active.get("collection"),
               "dataset_sha256": retriever.active.get("dataset_sha256")}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(results, context), encoding="utf-8")
    print(f"Demonstração salva em {output}")
    raise SystemExit(1 if any(r["error"] for r in results) else 0)


if __name__ == "__main__":
    main()
