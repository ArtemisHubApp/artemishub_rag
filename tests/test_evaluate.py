import pytest

from src.evaluate import (
    check_evidence,
    context_precision_at_5,
    evaluate,
    filter_by_evaluation_group,
    irrelevant_by_document,
    score_ranking,
)


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


def test_gold_v1_ignores_additional_evidence_entirely(document):
    class OtherDocRetriever:
        def retrieve(self, question, top_k):
            return [{"metadata": {"document_id": "other", "page": None}, "chunk_id": "c1"}]

    case = {"id": "case", "question": "fixture", "review_status": "verified",
            "relevant_document_ids": [document["document_id"]],
            "expected_evidence": [{"document_id": document["document_id"], "page": None,
                                   "content_hash": document["content_hash"]}],
            "additional_evidence": [{"document_id": "other", "page": None, "content_hash": "wrong-hash"}]}
    # v1 (default): additional_evidence is neither used for scoring nor validated for staleness.
    checked = check_evidence([case], [document])
    assert checked[0]["review_status"] == "verified"
    report = evaluate(checked, OtherDocRetriever())
    assert report["evaluated_cases"] == 1
    assert report["metrics"]["recall_at_5"] == 0.0


def test_gold_v2_accepts_additional_evidence_as_relevant(document):
    other = {**document, "document_id": "other", "content_hash": "other-hash"}

    class OtherDocRetriever:
        def retrieve(self, question, top_k):
            return [{"metadata": {"document_id": "other", "page": None}, "chunk_id": "c1"}]

    case = {"id": "case", "question": "fixture", "review_status": "verified",
            "relevant_document_ids": [document["document_id"]],
            "expected_evidence": [{"document_id": document["document_id"], "page": None,
                                   "content_hash": document["content_hash"]}],
            "additional_evidence": [{"document_id": "other", "page": None, "content_hash": "other-hash"}]}
    checked = check_evidence([case], [document, other], gold="v2")
    assert checked[0]["review_status"] == "verified"
    report = evaluate(checked, OtherDocRetriever(), gold="v2")
    assert report["evaluated_cases"] == 1
    assert report["metrics"]["recall_at_5"] == 1.0


def test_gold_v2_never_worse_than_v1_when_original_doc_is_found(document):
    """additional_evidence must never inflate the denominator score_ranking sees: if the
    original relevant document is retrieved, v2 recall/MRR must equal v1's, never drop
    just because an unrelated additional document wasn't also retrieved."""
    class OriginalDocRetriever:
        def retrieve(self, question, top_k):
            return [{"metadata": {"document_id": document["document_id"], "page": None}, "chunk_id": "c1"}]

    case = {"id": "case", "question": "fixture", "review_status": "verified",
            "relevant_document_ids": [document["document_id"]],
            "expected_evidence": [{"document_id": document["document_id"], "page": None,
                                   "content_hash": document["content_hash"]}],
            "additional_evidence": [{"document_id": "other", "page": None, "content_hash": "other-hash"}]}
    report_v1 = evaluate([case], OriginalDocRetriever(), gold="v1")
    report_v2 = evaluate([case], OriginalDocRetriever(), gold="v2")
    assert report_v1["metrics"] == report_v2["metrics"]
    assert report_v1["page_metrics"] == report_v2["page_metrics"]


def test_gold_v2_marks_stale_on_additional_evidence_hash_mismatch(document):
    case = {"id": "case", "review_status": "verified", "relevant_document_ids": [document["document_id"]],
            "expected_evidence": [{"document_id": document["document_id"], "page": None,
                                   "content_hash": document["content_hash"]}],
            "additional_evidence": [{"document_id": "other", "page": None, "content_hash": "stale-hash"}]}
    other = {**document, "document_id": "other", "content_hash": "current-hash"}
    # v1 doesn't look at additional_evidence, so it stays verified.
    assert check_evidence([case], [document, other])[0]["review_status"] == "verified"
    # v2 validates it too, and the mismatch marks the whole case stale.
    assert check_evidence([case], [document, other], gold="v2")[0]["review_status"] == "stale_or_missing_evidence"


def test_filter_by_evaluation_group_keeps_matching_only():
    cases = [{"id": "a", "evaluation_group": "answerable"},
              {"id": "b", "evaluation_group": "development"},
              {"id": "c", "evaluation_group": "development"},
              {"id": "d"}]
    assert [c["id"] for c in filter_by_evaluation_group(cases, ["answerable"])] == ["a"]
    assert [c["id"] for c in filter_by_evaluation_group(cases, ["development"])] == ["b", "c"]
    assert [c["id"] for c in filter_by_evaluation_group(cases, ["answerable", "development"])] == ["a", "b", "c"]


def test_filter_by_evaluation_group_no_filter_keeps_everything():
    cases = [{"id": "a", "evaluation_group": "answerable"}, {"id": "b"}]
    assert filter_by_evaluation_group(cases, None) == cases
    assert filter_by_evaluation_group(cases, []) == cases


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
