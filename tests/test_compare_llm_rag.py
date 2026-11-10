import json

from scripts.compare_llm_rag import ABSTENTION, absteve, compactar, responder, separar_cot
from src.query import CitationValidationError

PERGUNTA = {"id": "h04", "conjunto": "holdout", "question": "Qual a multa para a empresa?"}
HIT = {"chunk_id": "c1", "text": "multa de 10 vezes o novo salário",
       "metadata": {"document_id": "clt_art_461", "page": ""}}


class RetrieverFalso:
    def retrieve(self, question, top_k=5):
        return [HIT]


def test_separar_cot_divide_raciocinio_e_resposta():
    raciocinio, final = separar_cot("Passo 1...\nPasso 2...\nRESPOSTA FINAL: 10 vezes o salário.")
    assert raciocinio == "Passo 1...\nPasso 2..."
    assert final == "10 vezes o salário."


def test_separar_cot_sem_marcador_usa_texto_todo():
    assert separar_cot(" só a resposta ") == (None, "só a resposta")


def test_absteve_reconhece_a_frase_padrao():
    assert absteve(ABSTENTION)
    assert not absteve("A multa é de 10 vezes o salário.")
    assert not absteve(None)


def test_llm_puro_nao_recebe_trechos():
    linha = responder(PERGUNTA, "llm_puro", None, llm=lambda s, u: "Resposta.")
    assert linha["resposta"] == "Resposta." and linha["trechos"] == [] and linha["erro"] is None


def test_rag_guarda_trechos_numerados_como_as_citacoes():
    linha = responder(PERGUNTA, "rag", RetrieverFalso(), gerar_rag=lambda q, h: "10 vezes [FONTE 1]")
    assert linha["trechos"] == [{"fonte": 1, "chunk_id": "c1", "document_id": "clt_art_461",
                                 "pagina": None, "texto": "multa de 10 vezes o novo salário"}]
    assert linha["resposta"] == "10 vezes [FONTE 1]"


def test_rag_barrado_pelo_validador_guarda_texto_bruto_e_motivo():
    def gerar(q, h):
        raise CitationValidationError("LLM answer contains an uncited paragraph", "texto bruto")
    linha = responder(PERGUNTA, "rag", RetrieverFalso(), gerar_rag=gerar)
    assert linha["resposta"] == "texto bruto"
    assert linha["erro"].startswith("citacao_invalida")


def test_falha_de_chamada_nao_interrompe():
    def quebra(s, u):
        raise TimeoutError("demorou")
    linha = responder(PERGUNTA, "llm_cot", None, llm=quebra)
    assert linha["erro"] == "TimeoutError: demorou" and linha["resposta"] is None

def test_compactar_mantem_so_a_ultima_resposta(tmp_path):
    saida = tmp_path / "respostas.jsonl"
    saida.write_text(
        '{"id": "q1", "condicao": "rag", "erro": "HTTPStatusError: 503"}\n'
        '{"id": "q2", "condicao": "rag", "erro": null}\n'
        '{"id": "q1", "condicao": "rag", "erro": null}\n',
        encoding="utf-8",
    )
    compactar(saida)
    linhas = [json.loads(linha) for linha in saida.read_text(encoding="utf-8").splitlines()]
    assert [(r["id"], r["erro"]) for r in linhas] == [("q1", None), ("q2", None)]
