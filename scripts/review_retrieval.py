"""Inspect unchanged dense rankings and compare page diversification offline."""
import argparse
import json

from src.common import ROOT, load_jsonl, write_json
from src.evaluate import check_evidence, evaluate
from src.query import Retriever


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    retriever = Retriever(allow_partial=args.allow_partial, strategy="dense")
    documents = load_jsonl(ROOT / '.chroma' / retriever.active['snapshot'] / 'documents.jsonl')
    cases = check_evidence(load_jsonl(ROOT / 'evaluation/questions.jsonl'), documents)
    rankings = {case['question']: retriever.retrieve(case['question'], top_k=min(93, retriever.collection.count()))
                for case in cases if case.get('review_status') == 'verified'}

    class RecordedRetriever:
        def __init__(self, diversify=False):
            self.diversify = diversify

        def retrieve(self, question, top_k=5):
            hits = rankings[question]
            if not self.diversify:
                return hits[:top_k]
            selected, pages = [], set()
            for hit in hits[:20]:
                key = (hit['metadata']['document_id'], hit['metadata'].get('page'))
                if key not in pages:
                    selected.append(hit)
                    pages.add(key)
                if len(selected) == top_k:
                    break
            return selected

    diagnostics = []
    for case in cases:
        if case['id'] not in ('q02', 'q03', 'q15'):
            continue
        relevant = {(e['document_id'], str(e.get('page'))) for e in case['expected_evidence']}
        hits = rankings[case['question']]
        row = {'id': case['id'], 'question': case['question'], 'expected_evidence': case['expected_evidence'],
               'ranking': [{'rank': i, **hit} for i, hit in enumerate(hits[:20], 1)],
               'first_expected_page_ranks': {f'{doc}:page={page}': next((i for i, h in enumerate(hits, 1)
                   if (h['metadata']['document_id'], str(h['metadata'].get('page'))) == (doc, page)), None)
                   for doc, page in relevant}}
        diagnostics.append(row)
    report = {'configuration': retriever.active, 'diagnostics': diagnostics,
              'dense': evaluate(cases, RecordedRetriever()),
              'diverse_pages': evaluate(cases, RecordedRetriever(diversify=True)),
              'timing_note': 'Recorded rankings: latency here measures replay, not retrieval.'}
    write_json(ROOT / 'reports/review/retrieval_diagnostics.json', report)
    print(json.dumps({k: {m: report[k][m] for m in ('metrics', 'page_metrics', 'failures')}
                      for k in ('dense', 'diverse_pages')}, indent=2, ensure_ascii=False))
    print(json.dumps([{'id': d['id'], 'ranks': d['first_expected_page_ranks']} for d in diagnostics]))


if __name__ == '__main__':
    main()
