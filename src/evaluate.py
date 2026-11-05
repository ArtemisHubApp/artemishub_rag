"""Document hit@5. Initial evaluation; expand with passage labels later."""
from src.common import ROOT, load_jsonl
from src.query import retrieve


def main():
    cases = load_jsonl(ROOT / "evaluation" / "questions.jsonl")
    labeled = [c for c in cases if c.get("relevant_document_ids") and c.get("review_status") == "verified"]
    if not labeled:
        print("No labeled cases yet. Complete evaluation/questions.jsonl with reviewed IDs.")
        return
    hits = 0
    for case in labeled:
        result = retrieve(case["question"], top_k=5)
        retrieved = {r["metadata"]["document_id"] for r in result}
        ok = bool(retrieved.intersection(case["relevant_document_ids"]))
        hits += int(ok)
        print(f"{'HIT' if ok else 'MISS'}: {case['question']}")
    print(f"Document hit@5 = {hits}/{len(labeled)} = {hits/len(labeled):.1%}")
    print("NOTE: This is document hit@5, not passage-level Recall@5 or answer faithfulness.")


if __name__ == "__main__":
    main()
