from src.lexical import BM25, reciprocal_rank_fusion, tokens


def test_bm25_unicode_and_distinctive_term():
    chunks = [
        {'chunk_id': 'a', 'text': 'Remuneração e transparência no eSocial.'},
        {'chunk_id': 'b', 'text': 'Carreira e computação CTEM.'},
    ]
    assert tokens('REMUNERAÇÃO') == ['remuneracao']
    assert BM25(chunks).ranked('eSocial')[0]['chunk_id'] == 'a'
    assert BM25(chunks).ranked('CTEM')[0]['chunk_id'] == 'b'
    assert BM25(chunks).ranked('termo_inexistente') == []
    assert BM25([]).ranked('eSocial') == []


def test_rrf_combines_evidence_and_has_stable_ties():
    a, b, c = [{'chunk_id': label} for label in ('a', 'b', 'c')]
    result = reciprocal_rank_fusion([[a, b], [c, b]])
    assert result[0]['chunk_id'] == 'b'
    assert result[1]['chunk_id'] == 'a'
    assert len({h['chunk_id'] for h in result}) == 3
