"""Dá nota de acerto às respostas da comparação LLM puro x LLM + CoT x RAG (issue rag #8).

Lê as respostas geradas por scripts/compare_llm_rag.py e, para cada uma:
- pergunta fora do escopo (expected_behavior = abstain): nota pela abstenção, sem chamar o juiz;
- pergunta respondível em que o sistema se absteve: nota 0 (abstenção indevida), sem chamar o juiz;
- demais: um LLM juiz compara a resposta com o gabarito (CORRETA = 1, PARCIAL = 0,5, INCORRETA = 0).

O gabarito é o expected_answer (holdout) ou, quando não existe, o criterion (perguntas de desenvolvimento).

Uso:
    python -m scripts.judge_answers --respostas reports/teste.jsonl --saida reports/notas_teste.jsonl
    python -m scripts.judge_answers   # padrão: reports/respostas_comparacao.jsonl -> reports/notas_acerto.jsonl

O modelo do juiz vem de JUDGE_MODEL (ou LLM_MODEL, se não houver). O ideal é um modelo diferente do avaliado.
"""
import argparse
import datetime as dt
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path

import httpx

from src.common import ROOT, load_jsonl

RESPOSTAS_PADRAO = ROOT / "reports" / "respostas_comparacao.jsonl"
SAIDA_PADRAO = ROOT / "reports" / "notas_acerto.jsonl"
ARQUIVOS_PERGUNTAS = (ROOT / "evaluation" / "questions.jsonl", ROOT / "evaluation" / "questions_holdout.jsonl")
NOTAS = {"CORRETA": 1.0, "PARCIAL": 0.5, "INCORRETA": 0.0}
FALHAS_TEMPORARIAS = ("HTTPStatusError", "ConnectError", "ReadTimeout", "RemoteProtocolError", "JuizSemVeredito")

SISTEMA_JUIZ = (
    "Você é um avaliador rigoroso. Compare a RESPOSTA de um sistema com o GABARITO de uma pergunta sobre "
    "igualdade salarial e carreira no Brasil. Ignore marcações de citação como [FONTE 1] e diferenças de "
    "estilo ou tamanho; julgue só o conteúdo.\n"
    "- CORRETA: traz o essencial do gabarito e não afirma nada que o contradiga.\n"
    "- PARCIAL: acerta parte do essencial, mas falta algo importante, ou acerta com um erro menor.\n"
    "- INCORRETA: erra o essencial, contradiz o gabarito ou inventa números, leis ou prazos.\n"
    'Responda só com JSON, sem texto fora dele: {"veredito": "CORRETA|PARCIAL|INCORRETA", '
    '"justificativa": "uma frase curta"}'
)


class JuizSemVeredito(ValueError):
    pass


def carregar_perguntas(arquivos=ARQUIVOS_PERGUNTAS):
    perguntas = {}
    for arquivo in arquivos:
        if arquivo.exists():
            for linha in load_jsonl(arquivo):
                perguntas[linha["id"]] = linha
    return perguntas


def gabarito(pergunta):
    return pergunta.get("expected_answer") or pergunta.get("criterion") or ""


def chamar_juiz(sistema, usuario, tentativas=3):
    modelo = os.environ.get("JUDGE_MODEL") or os.environ["LLM_MODEL"]
    url = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
    corpo = {"model": modelo, "temperature": 0,
             "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]}
    cabecalho = {"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"}
    for tentativa in range(1, tentativas + 1):
        resposta = httpx.post(url, json=corpo, headers=cabecalho, timeout=90)
        if resposta.status_code == 429 and tentativa < tentativas:
            time.sleep(10 * tentativa)
            continue
        resposta.raise_for_status()
        return resposta.json()["choices"][0]["message"]["content"]
    raise RuntimeError("limite de tentativas")


def ler_veredito(texto):
    """Extrai {veredito, justificativa} do texto do juiz, mesmo se vier dentro de ```json."""
    achado = re.search(r"\{.*\}", texto or "", re.DOTALL)
    if not achado:
        raise JuizSemVeredito(f"juiz não devolveu JSON: {(texto or '')[:80]}")
    dados = json.loads(achado.group(0))
    veredito = str(dados.get("veredito", "")).strip().upper()
    if veredito not in NOTAS:
        raise JuizSemVeredito(f"veredito inválido: {veredito}")
    return veredito, str(dados.get("justificativa", "")).strip()


def julgar(resposta, pergunta, juiz=None):
    """Devolve a linha de nota de uma resposta (sem campos de data/modelo)."""
    linha = {"id": resposta["id"], "conjunto": resposta.get("conjunto"), "condicao": resposta["condicao"],
             "respondivel": pergunta.get("expected_behavior") != "abstain"}
    if resposta.get("erro") and resposta.get("resposta") is None:
        return {**linha, "nota": None, "veredito": "SEM_RESPOSTA", "justificativa": resposta["erro"][:200]}
    if not linha["respondivel"]:
        if resposta.get("absteve"):
            return {**linha, "nota": 1.0, "veredito": "ABSTENCAO_CORRETA", "justificativa": "fora do escopo e se absteve"}
        return {**linha, "nota": 0.0, "veredito": "RESPONDEU_FORA_DO_ESCOPO", "justificativa": "deveria ter se abstido"}
    if resposta.get("absteve"):
        return {**linha, "nota": 0.0, "veredito": "ABSTENCAO_INDEVIDA", "justificativa": "a base tem a resposta"}
    usuario = (f"PERGUNTA: {resposta['pergunta']}\n\nGABARITO: {gabarito(pergunta)}\n\n"
               f"RESPOSTA DO SISTEMA: {resposta['resposta']}")
    veredito, justificativa = ler_veredito((juiz or chamar_juiz)(SISTEMA_JUIZ, usuario))
    return {**linha, "nota": NOTAS[veredito], "veredito": veredito, "justificativa": justificativa}


def resumir(notas):
    """Tabela por condição: acurácia nas respondíveis e abstenções."""
    grupos = defaultdict(list)
    for n in notas:
        if n["nota"] is not None:
            grupos[n["condicao"]].append(n)
    tabela = {}
    for condicao, linhas in sorted(grupos.items()):
        resp = [n for n in linhas if n["respondivel"]]
        fora = [n for n in linhas if not n["respondivel"]]
        tabela[condicao] = {
            "n_respondiveis": len(resp),
            "acuracia": round(sum(n["nota"] for n in resp) / len(resp), 3) if resp else None,
            "abstencao_indevida": round(sum(n["veredito"] == "ABSTENCAO_INDEVIDA" for n in resp) / len(resp), 3) if resp else None,
            "n_fora_do_escopo": len(fora),
            "abstencao_correta": round(sum(n["nota"] for n in fora) / len(fora), 3) if fora else None,
        }
    return tabela


def ja_julgadas(saida):
    if not saida.exists():
        return set()
    return {(n["id"], n["condicao"]) for n in load_jsonl(saida)
            if not (n["veredito"] == "SEM_RESPOSTA" or str(n.get("erro") or "").startswith(FALHAS_TEMPORARIAS))}


def compactar(saida):
    ultimas = {}
    for n in load_jsonl(saida):
        ultimas[(n["id"], n["condicao"])] = n
    with saida.open("w", encoding="utf-8") as arquivo:
        for n in ultimas.values():
            arquivo.write(json.dumps(n, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--respostas", type=Path, default=RESPOSTAS_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()
    respostas_arquivo, saida = ROOT / args.respostas, ROOT / args.saida
    modelo_juiz = os.environ.get("JUDGE_MODEL") or os.environ.get("LLM_MODEL")
    perguntas = carregar_perguntas()
    respostas = list(load_jsonl(respostas_arquivo))
    if any(r.get("modelo") == modelo_juiz for r in respostas):
        print(f"Aviso: o juiz ({modelo_juiz}) é o mesmo modelo avaliado. Defina JUDGE_MODEL no .env se puder.")
    feitas = ja_julgadas(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("a", encoding="utf-8") as arquivo:
        for resposta in respostas:
            chave = (resposta["id"], resposta["condicao"])
            if chave in feitas:
                continue
            pergunta = perguntas.get(resposta["id"])
            if pergunta is None:
                print(f"{resposta['id']:>4} {resposta['condicao']:<9} pergunta não encontrada, pulei")
                continue
            try:
                nota = julgar(resposta, pergunta)
            except Exception as exc:  # uma falha não interrompe a rodada; fica registrada para refazer
                nota = {"id": resposta["id"], "conjunto": resposta.get("conjunto"), "condicao": resposta["condicao"],
                        "respondivel": pergunta.get("expected_behavior") != "abstain", "nota": None,
                        "veredito": "SEM_RESPOSTA", "justificativa": "", "erro": f"{type(exc).__name__}: {exc}"[:300]}
            nota.update(juiz_modelo=modelo_juiz, data=dt.date.today().isoformat())
            arquivo.write(json.dumps(nota, ensure_ascii=False) + "\n")
            arquivo.flush()
            print(f"{nota['id']:>4} {nota['condicao']:<9} {nota['veredito']}")
    compactar(saida)
    print(json.dumps(resumir(list(load_jsonl(saida))), ensure_ascii=False, indent=2))
    print(f"Notas em {saida}")


if __name__ == "__main__":
    main()
