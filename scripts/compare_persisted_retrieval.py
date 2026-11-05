"""Reproduce the old-corpus comparison using real persisted Chroma indexes."""
import argparse
import json

from src.common import ROOT, load_jsonl, write_json
from src.evaluate import check_evidence, evaluate
from src.index import build_index
from src.prepare import prepare
from src.query import Retriever


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full-corpus', action='store_true')
    args = parser.parse_args()
    baseline = Retriever(allow_partial=not args.full_corpus, strategy='dense')
    original = load_jsonl(ROOT / '.chroma' / baseline.active['snapshot'] / 'documents.jsonl')
    cases = load_jsonl(ROOT / 'reports/review/questions_before.jsonl')
    cases = check_evidence(cases, original)
    if args.full_corpus:
        legacy_path = ROOT / '.chroma/experiments/full_1200'
        build_index(prepare(original, chunk_size=1200, overlap=180), original,
                    path=legacy_path, model=baseline.model)
        candidate = Retriever(model=baseline.model, strategy='pages')
        baseline = Retriever(path=legacy_path, model=baseline.model, strategy='dense')
    before = evaluate(cases, baseline)
    build = None
    if not args.full_corpus:
        experiment_path = ROOT / '.chroma/experiments/review_chunks_600'
        build = build_index(prepare(original, chunk_size=600, overlap=100), original,
                            path=experiment_path, model=baseline.model, partial=True)
        candidate = Retriever(path=experiment_path, allow_partial=True, model=baseline.model, strategy='pages')
    after = evaluate(cases, candidate)
    report = {'baseline': before, 'candidate': after, 'baseline_index': baseline.active,
              'candidate_index': candidate.active, 'build': build,
              'controls': 'Same corpus within each comparison, original gold labels and hashes, model/revision; Chroma-backed retrieval.',
              'limitations': '15 answered in-sample cases, no independent human review or held-out benchmark.'}
    write_json(ROOT / ('reports/review/full_persisted_before_after.json' if args.full_corpus else 'reports/review/persisted_before_after.json'), report)
    print(json.dumps({k: {m: report[k][m] for m in ('metrics', 'page_metrics', 'mean_latency_ms')}
                      for k in ('baseline', 'candidate')}, indent=2))


if __name__ == '__main__':
    main()
