"""In-sample test of fixed BM25/RRF before considering hybrid retrieval."""
import json
from collections import Counter

from src.common import ROOT, load_jsonl, write_json
from src.evaluate import check_evidence, evaluate
from src.lexical import BM25
from src.query import Retriever, diversify_pages


def main():
    dense = Retriever(strategy='dense')
    snapshot = ROOT / '.chroma' / dense.active['snapshot']
    chunks = load_jsonl(snapshot / 'chunks.jsonl')
    documents = load_jsonl(snapshot / 'documents.jsonl')
    original_cases = load_jsonl(ROOT / 'reports/review/questions_before.jsonl')
    lexical = BM25(chunks)

    class Hybrid:
        def retrieve(self, question, top_k=5):
            vector = dense.retrieve(question, top_k=20)
            lex = lexical.ranked(question)
            hits = {h['chunk_id']: h for h in vector}
            fused = Counter()
            for rank, hit in enumerate(vector, 1):
                fused[hit['chunk_id']] += 1 / (60 + rank)
            for rank, chunk in enumerate(lex, 1):
                fused[chunk['chunk_id']] += 1 / (60 + rank)
                hits.setdefault(chunk['chunk_id'], {'chunk_id': chunk['chunk_id'], 'text': chunk['text'], 'metadata': chunk})
            ranked = sorted(hits.values(), key=lambda h: (-fused[h['chunk_id']], h['chunk_id']))
            return diversify_pages(ranked, top_k)

    report = evaluate(check_evidence(original_cases, documents), Hybrid())
    report['configuration'] = {'method':'dense20 + BM25_20, equal RRF k=60, page diversity', 'index': dense.active}
    write_json(ROOT / 'reports/review/hybrid_experiment.json', report)
    print(json.dumps({k: report[k] for k in ('metrics','page_metrics','mean_latency_ms')}, indent=2))
    print([(r['id'],r['page_recall_at_5']) for r in report['failures']])


if __name__ == '__main__':
    main()
