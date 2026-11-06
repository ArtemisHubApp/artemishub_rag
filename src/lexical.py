"""Small deterministic BM25 index and reciprocal-rank fusion for the local MVP."""
import math
import re
import unicodedata
from collections import Counter

STOP = set('a ao aos as ate com como da das de do dos e em entre essa esse esta este ha na nas no nos o os ou para pela pelas pelo pelos por qual quais que se sem ser seu sua um uma uns umas sobre segundo'.split())


def tokens(text):
    normalized = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))
    return [t for t in re.findall(r'\w+', normalized) if len(t) > 1 and t not in STOP]


class BM25:
    def __init__(self, chunks):
        self.chunks = chunks
        self.counts = [Counter(tokens(c['text'])) for c in chunks]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.mean = sum(self.lengths) / max(len(chunks), 1)
        self.frequency = Counter(term for counter in self.counts for term in counter)

    def ranked(self, question, limit=20):
        query = set(tokens(question))
        scores = []
        for index, counter in enumerate(self.counts):
            score = 0
            for term in query:
                frequency = counter.get(term, 0)
                if not frequency:
                    continue
                count = self.frequency[term]
                idf = math.log(1 + (len(self.chunks) - count + 0.5) / (count + 0.5))
                score += idf * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * self.lengths[index] / self.mean))
            if score > 0:
                scores.append((score, index))
        scores.sort(key=lambda pair: (-pair[0], self.chunks[pair[1]]['chunk_id']))
        return [self.chunks[i] for _, i in scores[:limit]]


def reciprocal_rank_fusion(rankings, constant=60):
    scores, hits = Counter(), {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, 1):
            chunk_id = hit['chunk_id']
            scores[chunk_id] += 1 / (constant + rank)
            hits.setdefault(chunk_id, hit)
    return [{**hits[key], 'retrieval_score': scores[key]}
            for key in sorted(hits, key=lambda key: (-scores[key], key))]
