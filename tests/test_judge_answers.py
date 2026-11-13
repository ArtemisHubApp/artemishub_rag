import json

import pytest

from scripts.judge_answers import JuizSemVeredito, compactar, julgar, ler_veredito, resumir

RESPONDIVEL = {"id": "h01", "expected_answer": "Multa de até 3% da folha."}
FORA = {"id": "h17", "expected_behavior": "abstain", "criterion": "A base não tem essa informação."}


def resposta(**campos):
    base = {"id": "h01", "conjunto": "holdout", "condicao": "rag", "pergunta": "Qual a multa?",
            "resposta": "Até 3% da folha [FONTE 1].", "absteve": False, "erro": None}
    return {**base, **campos}


def nao_chame(*_):
    raise AssertionError("o juiz não deveria ser chamado")


def test_ler_veredito_aceita_json_dentro_de_bloco_de_codigo():
    texto = '```json\n{"veredito": "parcial", "justificativa": "faltou o limite"}\n```'
    assert ler_veredito(texto) == ("PARCIAL", "faltou o limite")


def test_ler_veredito_recusa_texto_sem_json_ou_veredito_invalido():
    with pytest.raises(JuizSemVeredito):
        ler_veredito("Acho que está certa.")
    with pytest.raises(JuizSemVeredito):
        ler_veredito('{"veredito": "TALVEZ"}')


def test_abstencoes_sao_julgadas_sem_chamar_o_juiz():
    assert julgar(resposta(id="h17", absteve=True), FORA, juiz=nao_chame)["veredito"] == "ABSTENCAO_CORRETA"
    assert julgar(resposta(id="h17"), FORA, juiz=nao_chame)["nota"] == 0.0
    indevida = julgar(resposta(absteve=True), RESPONDIVEL, juiz=nao_chame)
    assert (indevida["veredito"], indevida["nota"]) == ("ABSTENCAO_INDEVIDA", 0.0)


def test_juiz_recebe_o_gabarito_e_a_nota_segue_o_veredito():
    recebido = {}

    def juiz(_sistema, usuario):
        recebido["texto"] = usuario
        return '{"veredito": "CORRETA", "justificativa": "ok"}'

    nota = julgar(resposta(), RESPONDIVEL, juiz=juiz)
    assert nota["nota"] == 1.0 and "3% da folha" in recebido["texto"]


def test_resumo_separa_respondiveis_e_fora_do_escopo():
    notas = [
        {"condicao": "rag", "respondivel": True, "nota": 1.0, "veredito": "CORRETA"},
        {"condicao": "rag", "respondivel": True, "nota": 0.0, "veredito": "ABSTENCAO_INDEVIDA"},
        {"condicao": "rag", "respondivel": False, "nota": 1.0, "veredito": "ABSTENCAO_CORRETA"},
        {"condicao": "rag", "respondivel": True, "nota": None, "veredito": "SEM_RESPOSTA"},
    ]
    assert resumir(notas)["rag"] == {"n_respondiveis": 2, "acuracia": 0.5, "abstencao_indevida": 0.5,
                                     "n_fora_do_escopo": 1, "abstencao_correta": 1.0}


def test_compactar_mantem_a_nota_mais_recente(tmp_path):
    saida = tmp_path / "notas.jsonl"
    saida.write_text(
        '{"id": "h01", "condicao": "rag", "veredito": "SEM_RESPOSTA"}\n'
        '{"id": "h01", "condicao": "rag", "veredito": "CORRETA"}\n', encoding="utf-8")
    compactar(saida)
    linhas = [json.loads(linha) for linha in saida.read_text(encoding="utf-8").splitlines()]
    assert [linha["veredito"] for linha in linhas] == ["CORRETA"]
