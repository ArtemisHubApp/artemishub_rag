import json

import pytest

from scripts.evaluate_faithfulness import (
    AvaliadorSemVeredito,
    avaliar_fidelidade,
    compactar,
    formatar_contexto,
    ler_veredito_fidelidade,
    resumir,
)


def test_formatar_contexto_monta_fontes():
    trechos = [
        {"fonte": 1, "document_id": "doc_a", "pagina": 2, "texto": "trecho 1"},
        {"fonte": 2, "document_id": "doc_b", "pagina": None, "texto": "trecho 2"},
    ]
    fmt = formatar_contexto(trechos)
    assert "[FONTE 1] (doc_a pág. 2):" in fmt
    assert "[FONTE 2] (doc_b):" in fmt
    assert "trecho 1" in fmt and "trecho 2" in fmt


def test_ler_veredito_fidelidade_valida_json():
    texto = (
        '{"afirmacoes": [{"afirmacao": "fato 1", "suportada": true, "justificativa": "ok"}], '
        '"score": 1.0, "resumo": "tudo fiel"}'
    )
    afirmacoes, score, resumo = ler_veredito_fidelidade(texto)
    assert len(afirmacoes) == 1
    assert score == 1.0
    assert resumo == "tudo fiel"


def test_ler_veredito_fidelidade_lanca_erro_em_json_invalido():
    with pytest.raises(AvaliadorSemVeredito):
        ler_veredito_fidelidade("Não é json")

    with pytest.raises(AvaliadorSemVeredito):
        ler_veredito_fidelidade('{"afirmacoes": []}')  # falta score


def test_avaliar_fidelidade_abstencao_recebe_score_1_sem_chamar_llm():
    linha = {
        "id": "h17",
        "conjunto": "holdout",
        "condicao": "rag",
        "pergunta": "Fora do escopo?",
        "resposta": "Não encontrei informações...",
        "absteve": True,
        "trechos": [],
    }

    def nao_chamar(*_):
        raise AssertionError("O avaliador não deveria ser chamado para abstenções!")

    resultado = avaliar_fidelidade(linha, avaliador=nao_chamar)
    assert resultado["score_fidelidade"] == 1.0
    assert resultado["veredito"] == "ABSTENCAO"


def test_avaliar_fidelidade_calcula_proporcao_corretamente():
    linha = {
        "id": "h01",
        "conjunto": "holdout",
        "condicao": "rag",
        "pergunta": "Qual a multa?",
        "resposta": "A multa é 10x e o prazo é 30 dias.",
        "absteve": False,
        "trechos": [{"fonte": 1, "document_id": "lei", "pagina": 1, "texto": "multa de 10x"}],
    }

    def avaliador_mock(_sistema, _usuario):
        return json.dumps({
            "afirmacoes": [
                {"afirmacao": "A multa é 10x", "suportada": True, "justificativa": "no texto"},
                {"afirmacao": "O prazo é 30 dias", "suportada": False, "justificativa": "não citado"},
            ],
            "score": 0.5,
            "resumo": "parcialmente fiel",
        })

    resultado = avaliar_fidelidade(linha, avaliador=avaliador_mock)
    assert resultado["score_fidelidade"] == 0.5
    assert resultado["total_afirmacoes"] == 2
    assert resultado["afirmacoes_suportadas"] == 1
    assert resultado["veredito"] == "PARCIALMENTE_FIEL"


def test_resumir_separa_conjuntos_e_abstencoes():
    avaliacoes = [
        {"conjunto": "v1", "absteve": False, "score_fidelidade": 1.0},
        {"conjunto": "v1", "absteve": False, "score_fidelidade": 0.5},
        {"conjunto": "v1", "absteve": True, "score_fidelidade": 1.0},
        {"conjunto": "v2", "absteve": False, "score_fidelidade": 0.8},
    ]
    resumo = resumir(avaliacoes)
    assert resumo["total_avaliadas"] == 4
    assert resumo["total_respondidas"] == 3
    assert resumo["total_abstencoes"] == 1
    assert resumo["resumo_por_conjunto"]["v1"]["respondidas"] == 2
    assert resumo["resumo_por_conjunto"]["v1"]["fidelidade_media_ativas"] == 0.75


def test_compactar_mantem_ultima_avaliacao(tmp_path):
    saida = tmp_path / "fidelidade.jsonl"
    saida.write_text(
        '{"id": "h01", "score_fidelidade": 0.5}\n'
        '{"id": "h01", "score_fidelidade": 1.0}\n',
        encoding="utf-8",
    )
    compactar(saida)
    linhas = [json.loads(linha) for linha in saida.read_text(encoding="utf-8").splitlines()]
    assert len(linhas) == 1
    assert linhas[0]["score_fidelidade"] == 1.0
