"""Reproducible dataset profile, with no notebook or network dependency."""
import json
from collections import Counter
from statistics import mean, median

from src.common import PROCESSED, ROOT, load_jsonl, write_json
from src.quality import DOCUMENT_FIELDS


def distribution(values):
    return {"count": len(values), "min": min(values), "max": max(values),
            "mean": round(mean(values), 2), "median": median(values)} if values else {"count": 0}


def analyze(documents, chunks, outcomes=None):
    hashes = Counter(d.get("content_hash") for d in documents)
    successful = sum(o["status"] == "success" for o in outcomes or [])
    enabled = sum(o["status"] != "disabled" for o in outcomes or [])
    return {
        "documents": len(documents), "unique_sources": len({d["document_id"] for d in documents}),
        "documents_by_source": dict(Counter(d["document_id"] for d in documents)),
        "documents_by_type": dict(Counter(d.get("document_type", "unknown") for d in documents)),
        "document_characters": distribution([len(d.get("content", "")) for d in documents]),
        "chunks": len(chunks), "chunk_characters": distribution([len(c["text"]) for c in chunks]),
        "chunk_size_histogram": dict(Counter(f"{len(c['text']) // 200 * 200}-{len(c['text']) // 200 * 200 + 199}" for c in chunks)),
        "chunks_by_document": dict(Counter(f"{c['document_id']}:page={c.get('page')}" for c in chunks)),
        "problem_documents": [{"document_id": d.get("document_id"), "page": d.get("page")}
                              for d in documents if not d.get("content", "").strip()
                              or any(k not in d for k in DOCUMENT_FIELDS)],
        "duplicate_content_hashes": {h: count for h, count in hashes.items() if count > 1},
        "metadata_coverage": {key: (sum(key in d and d[key] is not None and d[key] != "" for d in documents) / len(documents)
                                   if documents else 0) for key in DOCUMENT_FIELDS},
        "source_success_percent": round(100 * successful / enabled, 2) if enabled else None,
        "source_outcomes": outcomes or [],
        "note": "Success percentage is per configured source; unavailable page counts are unknown.",
    }


def main():
    documents = load_jsonl(PROCESSED / "documents.jsonl")
    chunks = load_jsonl(PROCESSED / "chunks.jsonl")
    run_path = ROOT / "reports" / "latest_run.json"
    outcomes = json.loads(run_path.read_text(encoding="utf-8")).get("source_outcomes") if run_path.exists() else None
    report = analyze(documents, chunks, outcomes)
    write_json(ROOT / "reports" / "eda.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
