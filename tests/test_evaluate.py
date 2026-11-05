import pytest

from src.evaluate import check_evidence, evaluate, score_ranking


def test_metrics_have_correct_denominators_and_ranks():
    metrics = score_ranking(["irrelevant", "a", "a", "other", "b"], ["a", "b", "c"])
    assert metrics == {"recall_at_5": 2 / 3, "hit_rate_at_5": 1.0, "mrr_at_5": 0.5}
    with pytest.raises(ValueError):
        score_ranking([], [])


def test_unanswerable_and_unverified_are_not_in_recall():
    class FakeRetriever:
        def retrieve(self, question, top_k):
            return [{"metadata": {"document_id": "doc"}, "chunk_id": "chunk"}]

    cases = [
        {"id": "a", "question": "fixture", "review_status": "verified", "relevant_document_ids": ["doc"]},
        {"id": "b", "question": "unknown", "review_status": "verified", "expected_behavior": "abstain"},
        {"id": "c", "question": "unreviewed", "review_status": "to_verify"},
    ]
    report = evaluate(cases, FakeRetriever())
    assert report["evaluated_cases"] == 1
    assert len(report["unanswerable_cases"]) == 1
    assert report["excluded_cases"] == ["c"]
    assert report["metrics"]["recall_at_5"] == 1


def test_changed_evidence_excludes_stale_labels(document):
    case = {"id": "case", "review_status": "verified", "relevant_document_ids": [document["document_id"]],
            "expected_evidence": [{"document_id": document["document_id"], "page": None,
                                   "content_hash": document["content_hash"]}]}
    assert check_evidence([case], [document])[0]["review_status"] == "verified"
    document["content_hash"] = "changed"
    assert check_evidence([case], [document])[0]["review_status"] == "stale_or_missing_evidence"
