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


def context_precision_at_5(retrieved, relevant):
    """Chunk-by-chunk precision over the raw top-5 list: a document (or page) counted
    once per chunk, not deduplicated. Works for document_id lists and (document_id, page)
    tuple lists alike, since both are plain hashable values."""
    if not retrieved:
        return 0.0
    relevant_set = set(relevant)
    return sum(1 for item in retrieved if item in relevant_set) / len(retrieved)


def irrelevant_by_document(retrieved, relevant):
    """How many of the retrieved chunks, per document_id, are NOT among the relevant documents."""
    relevant_set = set(relevant)
    counts = {}
    for document_id in retrieved:
        if document_id not in relevant_set:
            counts[document_id] = counts.get(document_id, 0) + 1
    return counts


def filter_by_evaluation_group(cases, groups):
    """Keep only cases whose evaluation_group is in groups; groups=None/[] keeps everything."""
    if not groups:
        return cases
    return [c for c in cases if c.get("evaluation_group") in groups]


def check_evidence(cases, documents, gold="v1"):
    """Exclude labels when their reviewed page is missing or changed.

    gold="v1" checks only expected_evidence (original gabarito), exactly as before.
    gold="v2" additionally validates additional_evidence (the Etapa 0.5 gold-standard
    review): any hash mismatch in either list, for a verified case, marks it stale —
    the same rule applied to both lists, never silently dropping just one item."""
    hashes = {(d["document_id"], d.get("page")): d["content_hash"] for d in documents}
    checked = []
    for case in cases:
        row = dict(case)
        if row.get("review_status") == "verified" and row.get("expected_behavior") != "abstain":
            evidence = row.get("expected_evidence", [])
            stale = (not evidence or {e["document_id"] for e in evidence} != set(row.get("relevant_document_ids", []))
                      or any(hashes.get((e["document_id"], e.get("page"))) != e["content_hash"] for e in evidence))
            if gold == "v2" and not stale:
                additional = row.get("additional_evidence", [])
                stale = any(hashes.get((e["document_id"], e.get("page"))) != e["content_hash"] for e in additional)
            if stale:
                row["review_status"] = "stale_or_missing_evidence"
        checked.append(row)
    return checked


def page_locator(document_id, page):
    """Chroma stores absent HTML pages as empty strings; JSONL uses null."""
    return document_id, None if page in (None, "") else str(page)


def evaluate(cases, retriever, gold="v1"):
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
        additional = case.get("additional_evidence", []) if gold == "v2" else []
        relevant = case.get("relevant_document_ids", [])
        # v2 credit without inflating score_ranking's denominator: an alternative document
        # that fully answers the question is remapped to the first original relevant id/page
        # before scoring, so recall/MRR can only improve over v1, never require both to appear.
        # The (bigger) union set is used only for context precision, where there is no
        # denominator to inflate — it purely stops a correct alternative from looking like noise.
        additional_doc_ids = {e["document_id"] for e in additional}
        relevant_for_precision = list(dict.fromkeys([*relevant, *additional_doc_ids])) if additional else relevant
        ranked_for_scoring = [relevant[0] if d in additional_doc_ids else d for d in ranked] if additional and relevant else ranked
        if case.get("expected_behavior") == "abstain":
            unanswered.append({**row, "returned_evidence": bool(hits)})
        elif relevant:
            evidence = case.get("expected_evidence", [])
            page_metrics = {}
            context_precision_metrics = {"context_precision_at_5": context_precision_at_5(ranked, relevant_for_precision),
                                          "irrelevant_by_document": irrelevant_by_document(ranked, relevant_for_precision)}
            if evidence:
                pages = [page_locator(h["metadata"]["document_id"], h["metadata"].get("page")) for h in hits]
                expected = [page_locator(e["document_id"], e.get("page")) for e in evidence]
                additional_pages = {page_locator(e["document_id"], e.get("page")) for e in additional}
                expected_for_precision = list(dict.fromkeys([*expected, *additional_pages])) if additional else expected
                pages_for_scoring = [expected[0] if p in additional_pages else p for p in pages] if additional and expected else pages
                page_metrics = {f"page_{key}": value for key, value in score_ranking(pages_for_scoring, expected).items()}
                context_precision_metrics["page_context_precision_at_5"] = context_precision_at_5(pages, expected_for_precision)
                row["ranked_pages"] = pages
            scored.append({**row, **score_ranking(ranked_for_scoring, relevant), **page_metrics, **context_precision_metrics})
        else:
            excluded.append(case["id"])
    metrics = {key: mean(row[key] for row in scored) for key in ("recall_at_5", "hit_rate_at_5", "mrr_at_5")} if scored else None
    page_scored = [row for row in scored if "page_recall_at_5" in row]
    page_metrics = {key: mean(row[key] for row in page_scored) for key in
                    ("page_recall_at_5", "page_hit_rate_at_5", "page_mrr_at_5")} if page_scored else None
    context_precision_metrics = None
    if scored:
        intrusion_totals = {}
        for row in scored:
            for document_id, count in row["irrelevant_by_document"].items():
                intrusion_totals[document_id] = intrusion_totals.get(document_id, 0) + count
        top_intruder = max(intrusion_totals, key=intrusion_totals.get) if intrusion_totals else None
        context_precision_metrics = {
            "context_precision_at_5": mean(row["context_precision_at_5"] for row in scored),
            "mean_irrelevant_chunks_at_5": mean(sum(row["irrelevant_by_document"].values()) for row in scored),
            "top_intruding_document": top_intruder,
            "top_intruding_document_chunks": intrusion_totals.get(top_intruder) if top_intruder else None,
        }
        if page_scored:
            context_precision_metrics["page_context_precision_at_5"] = mean(
                row["page_context_precision_at_5"] for row in page_scored)
    return {"scope": "document-level top-5 chunks; MRR truncated at 5", "metrics": metrics,
            "page_metrics": page_metrics,
            "context_precision_metrics": context_precision_metrics,
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
    parser.add_argument("--evaluation-group", action="append", dest="evaluation_groups",
                        help="Restringe aos casos com este evaluation_group; repetível para incluir vários")
    parser.add_argument("--gold", choices=("v1", "v2"), default="v1",
                        help="v1 usa só expected_evidence (padrão); v2 também conta additional_evidence")
    args = parser.parse_args()
    cases = filter_by_evaluation_group(load_jsonl(args.questions), args.evaluation_groups)
    retriever = Retriever(allow_partial=args.allow_partial, strategy=args.retrieval)
    snapshot = ROOT / ".chroma" / retriever.active["snapshot"]
    cases = check_evidence(cases, load_jsonl(snapshot / "documents.jsonl"), gold=args.gold)
    report = evaluate(cases, retriever, gold=args.gold)
    report["gold"] = args.gold
    report["configuration"] = {"top_k": 5, "retrieval": args.retrieval,
                               "candidate_multiplier": 1 if args.retrieval == "dense" else 4,
                               "lexical": {"method": "BM25", "k1": 1.5, "b": 0.75, "rrf_constant": 60}
                               if args.retrieval == "hybrid" else None,
                               "embedding_model": retriever.model_name, "index": retriever.active}
    write_json(args.output or ROOT / "reports" / "retrieval_evaluation.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
