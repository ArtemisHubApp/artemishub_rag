"""Controlled chunk-size experiment: same reviewed pages and model, no index mutation."""
import json

import numpy as np

from src.common import ROOT, load_jsonl, write_json
from src.evaluate import check_evidence, evaluate
from src.index import active_collection, load_model
from src.prepare import prepare


def main():
    _, active = active_collection(allow_partial=True)
    documents = load_jsonl(ROOT / '.chroma' / active['snapshot'] / 'documents.jsonl')
    cases = check_evidence(load_jsonl(ROOT / 'evaluation/questions.jsonl'), documents)
    model = load_model(active['embedding_model'], active['embedding_revision'])
    questions = [c['question'] for c in cases if c.get('review_status') == 'verified']
    question_vectors = model.encode(questions, normalize_embeddings=True)
    comparisons = {}
    for size, overlap in ((1200, 180), (600, 100)):
        chunks = prepare(documents, chunk_size=size, overlap=overlap)
        vectors = model.encode([c['text'] for c in chunks], normalize_embeddings=True)
        scores = np.asarray(question_vectors) @ np.asarray(vectors).T
        for diverse in (False, True):
            class ExperimentRetriever:
                def retrieve(self, question, top_k=5, scores=scores, diverse=diverse, chunks=chunks):
                    ranked = np.argsort(-scores[questions.index(question)], kind='stable')
                    selected, seen = [], set()
                    for index in ranked[:20] if diverse else ranked[:top_k]:
                        chunk = chunks[index]
                        page = (chunk['document_id'], chunk['page'])
                        if diverse and page in seen:
                            continue
                        seen.add(page)
                        selected.append({'chunk_id': chunk['chunk_id'], 'metadata': chunk, 'text': chunk['text']})
                        if len(selected) == top_k:
                            break
                    return selected
            report = evaluate(cases, ExperimentRetriever())
            comparisons[f'{size}_{"diverse" if diverse else "dense"}'] = {
                'chunk_size': size, 'overlap': overlap, 'chunks': len(chunks), 'page_metrics': report['page_metrics'],
                'metrics': report['metrics'], 'failures': [{'id':r['id'],'page_recall':r['page_recall_at_5']} for r in report['failures']]}
    output = {'index':active, 'comparisons':comparisons,
              'limitations':'In-sample experiment, same 15 answered cases; no held-out quality claim. Exhaustive cosine ranking.'}
    write_json(ROOT / 'reports/review/chunking_comparison.json', output)
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
