"""Document-level Recall@5, hit@5 and MRR; never score unlabeled cases."""
import argparse
import json
import time
from statistics import mean

from src.common import ROOT, load_jsonl, write_json
from src.query import Retriever


def score_ranking(retrieved, relevant):
    if not relevant:
        raise ValueError("Recall requires relevant documents")
    # Multiple chunks of one document count once, preserving the first rank.
    found = set(retrieved) & set(relevant)
    first = next((i for i, doc in enumerate(retrieved, 1) if doc in relevant), None)
    return {"recall_at_5": len(found) / len(set(relevant)), "hit_rate_at_5": float(bool(found)),
            "mrr_at_5": 1 / first if first else 0.0}


def check_evidence(cases, documents):
    """Exclude labels when their reviewed page is missing or changed."""
    hashes = {(d["document_id"], d.get("page")): d["content_hash"] for d in documents}
    checked = []
    for case in cases:
        row = dict(case)
        if row.get("review_status") == "verified" and row.get("expected_behavior") != "abstain":
            evidence = row.get("expected_evidence", [])
            if (not evidence or {e["document_id"] for e in evidence} != set(row.get("relevant_document_ids", []))
                or any(hashes.get((e["document_id"], e.get("page"))) != e["content_hash"] for e in evidence)):
                row["review_status"] = "stale_or_missing_evidence"
        checked.append(row)
    return checked


def page_locator(document_id, page):
    """Chroma stores absent HTML pages as empty strings; JSONL uses null."""
    return document_id, None if page in (None, "") else str(page)


def evaluate(cases, retriever):
    scored, unanswered, excluded = [], [], []
    for case in cases:
        if case.get("review_status") != "verified":
            excluded.append(case["id"])
            continue
        start = time.perf_counter()
        hits = retriever.retrieve(case["question"], top_k=5)
        elapsed = (time.perf_counter() - start) * 1000
        ranked = [h["metadata"]["document_id"] for h in hits]
        row = {"id": case["id"], "question": case["question"], "ranked_documents": ranked,
               "chunk_ids": [h["chunk_id"] for h in hits], "latency_ms": round(elapsed, 3)}
        relevant = case.get("relevant_document_ids", [])
        if case.get("expected_behavior") == "abstain":
            unanswered.append({**row, "returned_evidence": bool(hits)})
        elif relevant:
            evidence = case.get("expected_evidence", [])
            page_metrics = {}
            if evidence:
                pages = [page_locator(h["metadata"]["document_id"], h["metadata"].get("page")) for h in hits]
                expected = [page_locator(e["document_id"], e.get("page")) for e in evidence]
                page_metrics = {f"page_{key}": value for key, value in score_ranking(pages, expected).items()}
                row["ranked_pages"] = pages
            scored.append({**row, **score_ranking(ranked, relevant), **page_metrics})
        else:
            excluded.append(case["id"])
    metrics = {key: mean(row[key] for row in scored) for key in ("recall_at_5", "hit_rate_at_5", "mrr_at_5")} if scored else None
    page_scored = [row for row in scored if "page_recall_at_5" in row]
    page_metrics = {key: mean(row[key] for row in page_scored) for key in
                    ("page_recall_at_5", "page_hit_rate_at_5", "page_mrr_at_5")} if page_scored else None
    return {"scope": "document-level top-5 chunks; MRR truncated at 5", "metrics": metrics,
            "page_metrics": page_metrics,
            "evaluated_cases": len(scored), "excluded_cases": excluded, "cases": scored,
            "failures": [r for r in scored if r["recall_at_5"] < 1 or r.get("page_recall_at_5", 1) < 1],
            "unanswerable_cases": unanswered,
            "mean_latency_ms": mean(r["latency_ms"] for r in scored) if scored else None,
            "latency_scope": "query encoding + Chroma query, excludes model/index initialization",
            "unanswerable_note": "Returned evidence is not an answer; abstention requires separate generation review."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--retrieval", choices=("dense", "pages", "hybrid"), default="hybrid")
    parser.add_argument("--output", help="Report path; defaults to reports/retrieval_evaluation.json")
    parser.add_argument("--questions", default=str(ROOT / "evaluation" / "questions.jsonl"),
                        help="Arquivo JSONL de perguntas a avaliar")
    args = parser.parse_args()
    cases = load_jsonl(args.questions)
    retriever = Retriever(allow_partial=args.allow_partial, strategy=args.retrieval)
    snapshot = ROOT / ".chroma" / retriever.active["snapshot"]
    cases = check_evidence(cases, load_jsonl(snapshot / "documents.jsonl"))
    report = evaluate(cases, retriever)
    report["configuration"] = {"top_k": 5, "retrieval": args.retrieval,
                               "candidate_multiplier": 1 if args.retrieval == "dense" else 4,
                               "lexical": {"method": "BM25", "k1": 1.5, "b": 0.75, "rrf_constant": 60}
                               if args.retrieval == "hybrid" else None,
                               "embedding_model": retriever.model_name, "index": retriever.active}
    write_json(args.output or ROOT / "reports" / "retrieval_evaluation.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
