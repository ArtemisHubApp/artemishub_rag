"""Calcula a Fidelidade (Faithfulness / Groundedness) das respostas do RAG (issue rag #8).

Avalia se as afirmações feitas pelo RAG estão estritamente fundamentadas nos trechos
de contexto recuperados (Top-5), seguindo a metodologia do RAGAS:
- Resposta com abstenção (absteve = True): fidelidade 1.0 (não gerou afirmações infundadas).
- Demais: um LLM avaliador quebra a resposta em afirmações atômicas e verifica se cada uma
  é diretamente sustentada pelos trechos de contexto fornecidos.
- Fidelidade = (afirmações suportadas) / (total de afirmações).

Uso:
    python -m scripts.evaluate_faithfulness --respostas reports/respostas_comparacao.jsonl \
        --saida reports/fidelidade_rag.jsonl
    python -m scripts.evaluate_faithfulness   # usa os caminhos padrão em reports/
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

from src.common import ROOT, load_jsonl, write_jsonl

RESPOSTAS_PADRAO = ROOT / "reports" / "respostas_comparacao.jsonl"
SAIDA_PADRAO = ROOT / "reports" / "fidelidade_rag.jsonl"
FALHAS_TEMPORARIAS = (
    "HTTPStatusError",
    "ConnectError",
    "ReadTimeout",
    "RemoteProtocolError",
    "AvaliadorSemVeredito",
    "JSONDecodeError",
)

SISTEMA_FIDELIDADE = (
    "Você é um avaliador rigoroso de fidelidade (faithfulness / groundedness) em sistemas RAG.\n"
    "Sua tarefa é verificar se as afirmações contidas na RESPOSTA DO SISTEMA são estritamente "
    "fundamentadas pelos TRECHOS DE CONTEXTO recuperados.\n\n"
    "Regras de avaliação:\n"
    "1. Extraia as afirmações factuais atômicas contidas na resposta. Ignore cumprimentos, avisos legais "
    "de caráter informativo geral (disclaimers) e marcações de citação como [FONTE N].\n"
    "2. Para cada afirmação, verifique se ela pode ser deduzida DIRETAMENTE dos trechos de contexto fornecidos:\n"
    "   - Se o contexto apoiar diretamente a afirmação: suportada = true\n"
    "   - Se o contexto NÃO mencionar a informação, for ambíguo ou contradizer a afirmação: suportada = false "
    "(mesmo que seja verdadeira no mundo real, só vale o que está no contexto).\n"
    "3. Calcule o score de fidelidade: (número de afirmações suportadas) / (total de afirmações). "
    "Se não houver afirmações factuais na resposta, o score é 1.0.\n\n"
    "Responda estritamente com um objeto JSON no seguinte formato, sem texto fora dele:\n"
    "{\n"
    '  "afirmacoes": [\n'
    '    {"afirmacao": "texto da afirmação atômica", "suportada": true, "justificativa": "citação curta"}\n'
    "  ],\n"
    '  "score": 1.0,\n'
    '  "resumo": "frase curta resumindo o resultado"\n'
    "}"
)


class AvaliadorSemVeredito(ValueError):
    pass


def formatar_contexto(trechos):
    """Formata os trechos recuperados para inspeção do avaliador."""
    if not trechos:
        return "Nenhum trecho recuperado."
    linhas = []
    for t in trechos:
        num = t.get("fonte") or "?"
        doc = t.get("document_id") or "desconhecido"
        pag = f" pág. {t.get('pagina')}" if t.get("pagina") else ""
        texto = (t.get("texto") or "").strip()
        linhas.append(f"[FONTE {num}] ({doc}{pag}):\n{texto}")
    return "\n\n".join(linhas)


def chamar_avaliador(sistema, usuario, tentativas=3):
    """Chama o modelo avaliador via endpoint compatível com Chat Completions."""
    modelo = os.getenv("JUDGE_MODEL") or os.getenv("LLM_MODEL")
    chave = os.getenv("LLM_API_KEY")
    if not modelo or not chave:
        raise RuntimeError("Defina LLM_API_KEY e LLM_MODEL (ou JUDGE_MODEL) no .env.")

    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    corpo = {
        "model": modelo,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
    }
    cabecalho = {"Authorization": f"Bearer {chave}"}

    for tentativa in range(1, tentativas + 1):
        try:
            with httpx.Client(timeout=90) as client:
                resposta = client.post(f"{base_url}/chat/completions", json=corpo, headers=cabecalho)
                if resposta.status_code == 429 and tentativa < tentativas:
                    time.sleep(10 * tentativa)
                    continue
                resposta.raise_for_status()
                return resposta.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", getattr(exc, "code", None))
            if status == 429 and tentativa < tentativas:
                time.sleep(10 * tentativa)
                continue
            if tentativa == tentativas:
                raise
            time.sleep(5 * tentativa)


def ler_veredito_fidelidade(texto):
    """Extrai o JSON de fidelidade gerado pelo LLM avaliador."""
    achado = re.search(r"\{.*\}", texto or "", re.DOTALL)
    if not achado:
        raise AvaliadorSemVeredito(f"Avaliador não devolveu JSON: {(texto or '')[:80]}")
    try:
        dados = json.loads(achado.group(0))
    except json.JSONDecodeError as exc:
        raise AvaliadorSemVeredito(f"JSON inválido do avaliador: {exc}") from exc

    score = dados.get("score")
    if score is None:
        raise AvaliadorSemVeredito("JSON não contém campo 'score'")
    try:
        score = float(score)
    except (ValueError, TypeError) as exc:
        raise AvaliadorSemVeredito(f"Score inválido: {score}") from exc

    score = max(0.0, min(1.0, score))
    afirmacoes = dados.get("afirmacoes", [])
    resumo = str(dados.get("resumo", "")).strip()
    return afirmacoes, score, resumo


def avaliar_fidelidade(linha_rag, avaliador=None):
    """Avalia a fidelidade de uma resposta do RAG."""
    registro = {
        "id": linha_rag["id"],
        "conjunto": linha_rag.get("conjunto"),
        "condicao": "rag",
        "pergunta": linha_rag.get("pergunta"),
        "absteve": linha_rag.get("absteve", False),
        "citacao_invalida": bool(linha_rag.get("erro")),
        "score_fidelidade": None,
        "total_afirmacoes": 0,
        "afirmacoes_suportadas": 0,
        "afirmacoes": [],
        "veredito": None,
        "resumo": None,
        "erro": None,
    }

    # Se a resposta se absteve: não há afirmação incorreta ou alucinação sobre a base
    if linha_rag.get("absteve"):
        registro.update({
            "score_fidelidade": 1.0,
            "total_afirmacoes": 0,
            "afirmacoes_suportadas": 0,
            "veredito": "ABSTENCAO",
            "resumo": "Sistema se absteve; nenhuma afirmação infundada produzida.",
        })
        return registro

    resposta = linha_rag.get("resposta") or ""
    contexto = formatar_contexto(linha_rag.get("trechos", []))
    usuario = (
        f"PERGUNTA: {linha_rag.get('pergunta')}\n\n"
        f"RESPOSTA DO SISTEMA:\n{resposta}\n\n"
        f"TRECHOS DE CONTEXTO RECUPERADOS:\n{contexto}"
    )

    funcao_chamada = avaliador or chamar_avaliador
    texto_saida = funcao_chamada(SISTEMA_FIDELIDADE, usuario)
    afirmacoes, score, resumo = ler_veredito_fidelidade(texto_saida)

    total = len(afirmacoes)
    suportadas = sum(1 for a in afirmacoes if a.get("suportada") is True)

    # Recalcula com precisão matemática se houver afirmações
    if total > 0:
        score = round(suportadas / total, 3)
    else:
        score = 1.0

    veredito = "TOTALMENTE_FIEL" if score == 1.0 else ("PARCIALMENTE_FIEL" if score > 0 else "INFIEL")

    registro.update({
        "score_fidelidade": score,
        "total_afirmacoes": total,
        "afirmacoes_suportadas": suportadas,
        "afirmacoes": afirmacoes,
        "veredito": veredito,
        "resumo": resumo,
    })
    return registro


def resumir(avaliacoes):
    """Gera resumo consolidado das métricas de fidelidade."""
    validas = [a for a in avaliacoes if a.get("score_fidelidade") is not None]
    if not validas:
        return {}

    ativas = [a for a in validas if not a.get("absteve")]
    abstencoes = [a for a in validas if a.get("absteve")]

    grupos = defaultdict(list)
    for a in validas:
        grupos[a.get("conjunto") or "desconhecido"].append(a)

    resumo_grupos = {}
    for cj, itens in sorted(grupos.items()):
        itens_ativos = [i for i in itens if not i.get("absteve")]
        resumo_grupos[cj] = {
            "total": len(itens),
            "respondidas": len(itens_ativos),
            "abstencoes": len(itens) - len(itens_ativos),
            "fidelidade_media_geral": round(sum(i["score_fidelidade"] for i in itens) / len(itens), 3),
            "fidelidade_media_ativas": (
                round(sum(i["score_fidelidade"] for i in itens_ativos) / len(itens_ativos), 3)
                if itens_ativos
                else None
            ),
        }

    return {
        "total_avaliadas": len(validas),
        "total_respondidas": len(ativas),
        "total_abstencoes": len(abstencoes),
        "fidelidade_media_geral": round(sum(a["score_fidelidade"] for a in validas) / len(validas), 3),
        "fidelidade_media_ativas": (
            round(sum(a["score_fidelidade"] for a in ativas) / len(ativas), 3) if ativas else None
        ),
        "respostas_100_fiel": sum(1 for a in ativas if a["score_fidelidade"] == 1.0),
        "respostas_parciais_ou_alucinadas": sum(1 for a in ativas if a["score_fidelidade"] < 1.0),
        "resumo_por_conjunto": resumo_grupos,
    }


def ja_avaliadas(saida):
    if not saida.exists():
        return set()
    return {
        a["id"]
        for a in load_jsonl(saida)
        if not (a.get("score_fidelidade") is None or str(a.get("erro") or "").startswith(FALHAS_TEMPORARIAS))
    }


def compactar(saida):
    """Mantém a avaliação mais recente de cada pergunta usando escrita atômica."""
    ultimas = {}
    for a in load_jsonl(saida):
        ultimas[a["id"]] = a
    write_jsonl(saida, ultimas.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--respostas", type=Path, default=RESPOSTAS_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--limite", type=int, help="Número máximo de avaliações (para testes)")
    args = parser.parse_args()

    respostas_path = args.respostas if args.respostas.is_absolute() else ROOT / args.respostas
    saida_path = args.saida if args.saida.is_absolute() else ROOT / args.saida
    saida_path.parent.mkdir(parents=True, exist_ok=True)

    todas = [linha for linha in load_jsonl(respostas_path) if linha.get("condicao") == "rag"]
    if args.limite:
        todas = todas[: args.limite]

    feitas = ja_avaliadas(saida_path)

    with saida_path.open("a", encoding="utf-8") as arquivo:
        for linha in todas:
            if linha["id"] in feitas:
                continue
            try:
                resultado = avaliar_fidelidade(linha)
            except Exception as exc:
                resultado = {
                    "id": linha["id"],
                    "conjunto": linha.get("conjunto"),
                    "condicao": "rag",
                    "absteve": linha.get("absteve", False),
                    "score_fidelidade": None,
                    "erro": f"{type(exc).__name__}: {exc}"[:300],
                }
            resultado.update(data=dt.date.today().isoformat())
            arquivo.write(json.dumps(resultado, ensure_ascii=False) + "\n")
            arquivo.flush()
            print(f"{resultado['id']:>4} RAG Fidelidade: {resultado.get('score_fidelidade')} "
                  f"({resultado.get('veredito') or 'ERRO'})")

    compactar(saida_path)
    resumo = resumir(load_jsonl(saida_path))
    print("\n=== RESUMO DE FIDELIDADE ===")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(f"\nAvaliações salvas em: {saida_path}")


if __name__ == "__main__":
    main()
