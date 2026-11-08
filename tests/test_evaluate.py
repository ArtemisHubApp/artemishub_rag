import pytest

from src.evaluate import check_evidence, context_precision_at_5, evaluate, irrelevant_by_document, score_ranking


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


def test_html_null_page_matches_chroma_empty_page():
    class HtmlRetriever:
        def retrieve(self, question, top_k=5):
            return [{'chunk_id': 'html', 'metadata': {'document_id': 'law', 'page': ''}}]

    cases = [{'id': 'html', 'question': 'fixture', 'review_status': 'verified',
              'relevant_document_ids': ['law'], 'expected_evidence': [{'document_id': 'law', 'page': None}]}]
    report = evaluate(cases, HtmlRetriever())
    assert report['page_metrics']['page_recall_at_5'] == 1
    assert report['page_metrics']['page_hit_rate_at_5'] == 1


def test_context_precision_counts_chunk_by_chunk_with_repeats():
    retrieved = ["a", "a", "b", "other", "other"]
    assert context_precision_at_5(retrieved, ["a", "b"]) == 3 / 5
    assert irrelevant_by_document(retrieved, ["a", "b"]) == {"other": 2}


def test_context_precision_none_relevant():
    retrieved = ["x", "y", "z"]
    assert context_precision_at_5(retrieved, ["a"]) == 0.0
    assert irrelevant_by_document(retrieved, ["a"]) == {"x": 1, "y": 1, "z": 1}


def test_context_precision_fewer_than_five_chunks():
    assert context_precision_at_5(["a"], ["a"]) == 1.0
    assert context_precision_at_5([], ["a"]) == 0.0
    assert irrelevant_by_document([], ["a"]) == {}


def test_evaluate_reports_context_precision_and_intrusion():
    class FakeRetriever:
        def retrieve(self, question, top_k=5):
            return [{"metadata": {"document_id": "doc", "page": 1}, "chunk_id": "c1"},
                    {"metadata": {"document_id": "doc", "page": 1}, "chunk_id": "c2"},
                    {"metadata": {"document_id": "intruder", "page": 2}, "chunk_id": "c3"},
                    {"metadata": {"document_id": "intruder", "page": 2}, "chunk_id": "c4"},
                    {"metadata": {"document_id": "intruder", "page": 2}, "chunk_id": "c5"}]

    cases = [{"id": "a", "question": "fixture", "review_status": "verified", "relevant_document_ids": ["doc"],
              "expected_evidence": [{"document_id": "doc", "page": 1}]}]
    report = evaluate(cases, FakeRetriever())
    case = report["cases"][0]
    assert case["context_precision_at_5"] == 2 / 5
    assert case["page_context_precision_at_5"] == 2 / 5
    assert case["irrelevant_by_document"] == {"intruder": 3}
    assert report["context_precision_metrics"]["context_precision_at_5"] == 2 / 5
    assert report["context_precision_metrics"]["top_intruding_document"] == "intruder"
    assert report["context_precision_metrics"]["top_intruding_document_chunks"] == 3
    assert report["context_precision_metrics"]["mean_irrelevant_chunks_at_5"] == 3
