"""Gera as respostas da comparação LLM puro x LLM + CoT x RAG (issue rag #8).

Para cada pergunta, o mesmo modelo responde de três jeitos:
  - llm_puro: só a pergunta, sem documentos;
  - llm_cot:  a pergunta e a instrução de raciocinar passo a passo, sem documentos;
  - rag:      a pergunta e os 5 trechos recuperados, com o `generate` do src/query.py.

Cada resposta vira uma linha em reports/respostas_comparacao.jsonl. O arquivo é
escrito linha a linha: se a execução parar no meio, rodar de novo pula o que já
foi respondido.

Uso:
  python -m scripts.comparar_llm_rag --conjunto desenvolvimento --limite 3
  python -m scripts.comparar_llm_rag --conjunto holdout
"""
import argparse
import datetime as dt
import json
import os
import time
from pathlib import Path

import httpx

from src.common import ROOT, load_jsonl
from src.query import ABSTENTION, CitationValidationError, Retriever, generate

SAIDA_PADRAO = ROOT / "reports" / "respostas_comparacao.jsonl"
CONDICOES = ("llm_puro", "llm_cot", "rag")

# O mesmo início de prompt nas duas condições sem documentos, para que a única
# diferença entre elas seja o pedido de raciocínio. A frase de abstenção é a
# mesma do RAG, para que "não sei" seja contado do mesmo jeito nas três.
SISTEMA_BASE = (
    "Você orienta sobre informações gerais de carreira e igualdade salarial no Brasil. "
    "Responda em português brasileiro, de forma direta, usando o seu conhecimento geral. "
    "Você não recebe documentos: responda com o que sabe. "
    "Não invente números, leis, artigos ou referências. "
    f"Só se realmente não souber, responda exatamente: {ABSTENTION} "
    "(essa frase é apenas o código padrão para 'não sei')."
)
SISTEMA_COT = SISTEMA_BASE + (
    " Antes de responder, raciocine passo a passo. "
    "Depois, escreva uma linha começando com 'RESPOSTA FINAL:' seguida só da resposta."
)
MARCADOR_COT = "RESPOSTA FINAL:"


def carregar_perguntas(conjunto):
    """Devolve as perguntas do conjunto pedido, já com o campo `conjunto` preenchido."""
    perguntas = []
    if conjunto in ("holdout", "todos"):
        for q in load_jsonl(ROOT / "evaluation" / "questions_holdout.jsonl"):
            perguntas.append({**q, "conjunto": "holdout"})
    if conjunto in ("desenvolvimento", "todos"):
        for q in load_jsonl(ROOT / "evaluation" / "questions.jsonl"):
            if q.get("evaluation_group") == "development":
                perguntas.append({**q, "conjunto": "desenvolvimento"})
    return perguntas


def chamar_llm(sistema, usuario, tentativas=3):
    """Chama o endpoint compatível com Chat Completions configurado no .env."""
    chave, modelo = os.getenv("LLM_API_KEY"), os.getenv("LLM_MODEL")
    if not chave or not modelo:
        raise RuntimeError("Defina LLM_API_KEY e LLM_MODEL no .env.")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {"model": modelo, "temperature": 0, "messages": [
        {"role": "system", "content": sistema},
        {"role": "user", "content": usuario},
    ]}
    for tentativa in range(1, tentativas + 1):
        try:
            with httpx.Client(timeout=90) as client:
                resposta = client.post(f"{base_url}/chat/completions",
                                       headers={"Authorization": f"Bearer {chave}"}, json=payload)
                resposta.raise_for_status()
                return resposta.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            # 429 = limite de requisições: espera e tenta de novo. Outros erros sobem.
            if exc.response.status_code != 429 or tentativa == tentativas:
                raise
            time.sleep(10 * tentativa)


def separar_cot(texto):
    """Separa o raciocínio da resposta final. Sem o marcador, o texto todo é a resposta."""
    if MARCADOR_COT in texto:
        raciocinio, final = texto.rsplit(MARCADOR_COT, 1)
        return raciocinio.strip(), final.strip()
    return None, texto.strip()


def absteve(resposta):
    return bool(resposta) and resposta.strip().startswith(ABSTENTION)


def trechos_para_salvar(hits):
    """Guarda o que o modelo recebeu, com o mesmo número usado nas citações [FONTE N]."""
    return [{"fonte": i, "chunk_id": h["chunk_id"], "document_id": h["metadata"].get("document_id"),
             "pagina": h["metadata"].get("page") or None, "texto": h["text"]}
            for i, h in enumerate(hits, 1)]


def responder(pergunta, condicao, retriever, llm=chamar_llm, gerar_rag=generate):
    """Responde uma pergunta numa condição e devolve a linha a salvar."""
    linha = {"id": pergunta["id"], "conjunto": pergunta["conjunto"], "condicao": condicao,
             "pergunta": pergunta["question"], "resposta": None, "raciocinio": None,
             "absteve": False, "trechos": [], "erro": None,
             "modelo": os.getenv("LLM_MODEL"), "data": dt.date.today().isoformat()}
    try:
        if condicao == "llm_puro":
            linha["resposta"] = llm(SISTEMA_BASE, pergunta["question"]).strip()
        elif condicao == "llm_cot":
            linha["raciocinio"], linha["resposta"] = separar_cot(llm(SISTEMA_COT, pergunta["question"]))
        elif condicao == "rag":
            hits = retriever.retrieve(pergunta["question"], 5)
            linha["trechos"] = trechos_para_salvar(hits)
            linha["resposta"] = gerar_rag(pergunta["question"], hits)
        else:
            raise ValueError(f"Condição desconhecida: {condicao}")
    except CitationValidationError as exc:
        # O validador barrou a resposta do RAG: guardamos o texto bruto para
        # ainda dar para corrigir e medir a fidelidade, e registramos o motivo.
        linha["resposta"] = exc.raw_answer
        linha["erro"] = f"citacao_invalida: {exc}"
    except Exception as exc:  # uma falha numa pergunta não para as outras
        linha["erro"] = f"{type(exc).__name__}: {exc}"
    linha["absteve"] = absteve(linha["resposta"])
    return linha


def ja_respondidas(saida):
    if not saida.exists():
        return set()
    # Respostas que falharam por problema de rede ou de limite são refeitas.
    falhas_temporarias = ("HTTPStatusError", "ConnectError", "ReadTimeout", "RemoteProtocolError")
    return {(r["id"], r["condicao"]) for r in load_jsonl(saida)
            if not (r.get("erro") or "").startswith(falhas_temporarias)}

def compactar(saida):
    """Deixa só a resposta mais recente de cada (id, condicao), apagando falhas já refeitas."""
    ultimas = {}
    for r in load_jsonl(saida):
        ultimas[(r["id"], r["condicao"])] = r
    with saida.open("w", encoding="utf-8") as arquivo:
        for r in ultimas.values():
            arquivo.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--conjunto", choices=("holdout", "desenvolvimento", "todos"), default="desenvolvimento")
    parser.add_argument("--condicoes", nargs="+", choices=CONDICOES, default=list(CONDICOES))
    parser.add_argument("--limite", type=int, help="Número máximo de perguntas (para testes)")
    parser.add_argument("--saida", default=str(SAIDA_PADRAO))
    args = parser.parse_args()

    perguntas = carregar_perguntas(args.conjunto)[:args.limite]
    saida = Path(args.saida) if os.path.isabs(args.saida) else ROOT / args.saida
    saida.parent.mkdir(parents=True, exist_ok=True)
    feitas = ja_respondidas(saida)
    retriever = Retriever() if "rag" in args.condicoes else None

    with open(saida, "a", encoding="utf-8") as arquivo:
        for pergunta in perguntas:
            for condicao in args.condicoes:
                if (pergunta["id"], condicao) in feitas:
                    continue
                linha = responder(pergunta, condicao, retriever)
                arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")
                arquivo.flush()
                status = "ERRO" if linha["erro"] else ("absteve" if linha["absteve"] else "ok")
                print(f"{pergunta['id']:>4} {condicao:<9} {status}")
    compactar(saida)
    print(f"Respostas em {saida}")
    

if __name__ == "__main__":
    main()
