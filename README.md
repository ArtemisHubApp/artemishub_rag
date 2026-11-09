# 🌙 Artemis

### Inteligência Artificial para impulsionar mulheres em STEM 💜

[![CI Pipeline](https://github.com/ArtemisHubApp/artemishub_rag/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ArtemisHubApp/artemishub_rag/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![Status](https://img.shields.io/badge/status-MVP%20em%20desenvolvimento-purple)

O **Artemis** usa Inteligência Artificial para apoiar mulheres nas áreas de **Ciência, Tecnologia, Engenharia e Matemática (STEM)**, promovendo autonomia, valorização profissional e decisões de carreira mais seguras.

Este repositório contém o **RAG (Retrieval-Augmented Generation)** do Artemis: a base de conhecimento que responde perguntas sobre igualdade salarial e direitos trabalhistas a partir de **fontes oficiais**, sempre citando de onde veio cada informação.

## 📑 Sumário

- [Sobre o projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Como funciona](#-como-funciona)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Como executar](#-como-executar)
- [Testes e qualidade](#-testes-e-qualidade)
- [Resultados da avaliação](#-resultados-da-avaliação)
- [Documentação](#-documentação)
- [Equipe](#-equipe)
- [Como contribuir](#-como-contribuir)

## 💡 Sobre o projeto

Nossa proposta é transformar dados e tecnologia em ferramentas acessíveis que ajudem mulheres a reconhecer seu potencial, superar barreiras e conquistar novas oportunidades. A plataforma completa prevê:

- 💼 **Análise de perfil e currículo:** identificação de competências e pontos fortes.
- 💰 **Inteligência salarial:** referências de remuneração e informações sobre desigualdade salarial.
- 🎯 **Oportunidades personalizadas:** recomendações alinhadas ao perfil e aos objetivos profissionais.
- 📈 **Desenvolvimento de carreira:** identificação de habilidades a aprimorar.
- 💬 **Simulação de negociação salarial:** prática de conversas profissionais com auxílio de IA.
- 📚 **Orientação confiável:** acesso a informações fundamentadas sobre direitos e carreira.

> O Artemis está em desenvolvimento. Este repositório entrega a parte de **orientação confiável**; as demais funcionalidades serão implementadas e validadas progressivamente.

## ✨ Funcionalidades

O MVP atual:

- **Coleta fontes oficiais** listadas em [`config/sources.json`](config/sources.json): Lei 14.611/2023, CLT (art. 461), decreto regulamentador, dados do IBGE e cartilha de transparência salarial.
- **Valida e prepara os textos** em chunks de 600 caracteres com sobreposição de 100, guardando URL, página e hash de cada trecho.
- **Indexa** os trechos no ChromaDB com o modelo `paraphrase-multilingual-MiniLM-L12-v2`, sem apagar índices anteriores.
- **Busca híbrida:** combina busca vetorial e BM25 com fusão RRF.
- **Responde com citações**, usando um LLM compatível com a API de Chat Completions (opcional). Sem LLM configurado, mostra só os trechos encontrados.
- **Gera a demonstração** (`python -m src.demo`): perguntas, trechos recuperados, resposta e fontes citadas em `reports/demo_rag.md`.
- **Avalia a recuperação** com métricas de recall, hit rate e MRR em dois conjuntos de perguntas.

## ⚙️ Como funciona

```
fontes oficiais ──► ingest ──► quality ──► prepare (chunks) ──► index (ChromaDB)
                                                                     │
pergunta ──► query (vetorial + BM25 + RRF) ◄─────────────────────────┘
                 │
                 └──► LLM (opcional) ──► resposta com citações
```

Detalhes em [`docs/architecture.md`](docs/architecture.md).

## 🗂️ Estrutura do repositório

```
.
├── config/sources.json        # fontes oficiais e alternativas
├── src/
│   ├── pipeline.py            # executa coleta → preparo → índice
│   ├── ingest.py              # download e extração das fontes
│   ├── quality.py             # validação de documentos e chunks
│   ├── prepare.py             # divisão em chunks
│   ├── index.py               # publicação do índice no ChromaDB
│   ├── lexical.py             # BM25
│   ├── query.py               # busca híbrida e geração com citações
│   ├── evaluate.py            # métricas de recuperação
│   ├── eda.py                 # análise exploratória do dataset
│   ├── domain/                # entidades (arquitetura hexagonal)
│   ├── application/           # portas e casos de uso (orquestrador)
│   └── adapters/              # repositório em arquivo e vector store
├── evaluation/                # perguntas de avaliação (original e holdout)
├── scripts/                   # experimentos de chunking e busca
├── tests/                     # testes automatizados (pytest)
├── docs/                      # arquitetura, uso, relatório de validação, specs
├── agent/                     # skills de desenvolvimento orientado a spec (SDD)
├── .github/workflows/ci.yml   # CI: Ruff + pytest em Python 3.11 e 3.12
└── Dockerfile
```

## 🚀 Como executar

**Pré-requisitos:** Python 3.11 ou superior e [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ArtemisHubApp/artemishub_rag.git
cd artemishub_rag
uv sync --dev
cp .env.example .env
```

O `.env` só precisa ser preenchido para usar o LLM (`LLM_API_KEY`, `LLM_MODEL` e, se necessário, `LLM_BASE_URL`).

```bash
uv run python -m src.pipeline      # coleta, prepara e indexa as fontes
uv run python -m src.eda           # gera o perfil do dataset em reports/eda.json
uv run python -m src.query "O que a cartilha informa sobre transparência salarial?"
uv run python -m src.evaluate      # métricas de recuperação
uv run python -m src.demo          # demonstração com LLM em reports/demo_rag.md
```

A primeira execução baixa as fontes e o modelo de embeddings. Outras opções (`--skip-index`, `--allow-partial`, `--retrieval`, `--chunk-size`) estão em [`docs/rag_usage.md`](docs/rag_usage.md).

## 🧪 Testes e qualidade

```bash
uv run ruff check .
uv run pytest
```

O CI roda os dois comandos em todo push para a `main` e em todo pull request.

## 📊 Resultados da avaliação

Busca híbrida, chunks de 600/100, índice com 1209 chunks das 20 fontes ativas. **Comparação justa: as mesmas 16 perguntas originais, antes (5 fontes) e depois (20 fontes)** — as 6 perguntas novas (`evaluation_group: "development"`, todas citam a fonte no próprio enunciado, o que as torna mais fáceis) ficam numa linha separada, não misturadas na comparação principal:

| Métrica (top 5) | 5 fontes, 16 originais (antes) | 20 fontes, mesmas 16 originais (depois) | 20 fontes, 6 de desenvolvimento |
|---|---|---|---|
| Casos avaliados / stale | 16 / 0 | 16 / 0 | 6 / 0 |
| Recall@5 por documento | 100% | 93,75% | 100% |
| Hit rate@5 por documento | 100% | 93,75% | 100% |
| MRR@5 por documento | 0,9583 | 0,8177 | 0,7778 |
| Recall@5 por página | 100% | 87,5% | 100% |
| MRR@5 por página | 0,8021 | 0,7083 | 0,6944 |
| Context Precision@5 (documento) | 72,5% | 33,75% | 43,33% |
| Context Precision@5 (página) | 21,25% | 17,5% | 20% |

A ampliação para 20 fontes introduziu concorrência de documentos tematicamente próximos e baixou 2 das 16 perguntas originais (`q06`, `q15`); nenhuma delas tem chunks do INEP entre os 5 recuperados — o Resumo Técnico do INEP ocupa 36,7% do índice mas não causou essas regressões; quem mais "invade" o top 5 nas perguntas originais é o `guia_negociacao_coletiva` (17 chunks em 16 perguntas). Detalhes em [`docs/validation_report.md`](docs/validation_report.md).

**Qualidade do gabarito (`--gold v1|v2`, branch `feat/qualidade-base`):** uma revisão editorial encontrou evidência adicional válida para 9 das 43 perguntas (ex.: a `h04` pergunta o valor da multa; a Orientação Técnica SIT 11/2024 traz o valor exato, mas o gabarito original só registrava a CLT e a Lei 14.611). `--gold v2` passa a contar essa evidência sem inflar o denominador do Recall (`score_ranking` continua intocado), então v2 nunca fica pior que v1 na mesma pergunta — só pode igualar ou melhorar:

| Métrica (top 5), 16 originais | `main`, gabarito v1 | Esta branch, gabarito v2 (recomendado) |
|---|---|---|
| Recall@5 por documento | 93,75% | 93,75% |
| MRR@5 por documento | 0,8177 | 0,8229 |
| Recall@5 por página | 87,5% | **93,75%** |
| MRR@5 por página | 0,7083 | **0,7344** |

Quatro tentativas de melhorar a recuperação em si nesta branch (filtrar ruído no chunking, extrair tabelas, prefixar contexto no embedding, limitar chunks por documento) foram implementadas, testadas e medidas — e todas revertidas: cada uma piorou `page_recall_at_5` e/ou `page_mrr_at_5` nas 16 perguntas originais. Nenhuma dessa mudança de código está no diff final; a tabela completa com causa provável de cada regressão está em `docs/validation_report.md`.

**Holdout (16 perguntas, nunca usado para ajustar nada), antes e depois:**

| Métrica (top 5) | 5 fontes (antes) | 20 fontes, gabarito v1 | 20 fontes, gabarito v2 (recomendado) |
|---|---|---|---|
| Recall@5 por documento | 96,88% | 87,5% | 90,63% |
| MRR@5 por documento | 0,8958 | 0,5302 | 0,5615 |
| Recall@5 por página | 93,75% | 78,13% | 84,38% |
| MRR@5 por página | 0,7729 | 0,4469 | 0,5094 |

A queda no holdout é **maior** do que no conjunto de desenvolvimento (100%/0,69 por página) — esperado, já que as perguntas de desenvolvimento citam a fonte no enunciado. Do lado positivo: corrigir só o gabarito (v2, sem nenhuma mudança de busca ou chunking) já recupera parte real dessa queda no holdout (MRR por página +14%, de 0,4469 para 0,5094) — cerca de 28% da queda de MRR por página nas 16 originais era medição, não busca; os 72% restantes são recuperação real, e não foram recuperados por nenhuma das quatro tentativas desta branch.

Os conjuntos são pequenos, e o holdout serve só para medir versões finais, nunca para ajustar o sistema. A qualidade das respostas geradas pelo LLM foi checada manualmente em 5 perguntas fixas. O modelo de geração foi escolhido entre **3 versões fixas** (nunca um apelido `-latest`, que muda sem aviso): `gemini-3.7-flash` falhou nas 5 perguntas por timeout (~8 min, descartado), `gemini-3.5-flash` abstém em perguntas com evidência suficiente (incluindo a da multa), e **`gemini-3.5-flash-lite`** foi o escolhido (mais rápido e mais disposto a responder).

Uma tentativa de corrigir, via prompt, um parágrafo de disclaimer que o modelo escrevia sem citação (e que por isso era rejeitado pelo validador) **não funcionou**: pedir ao modelo para não escrever avisos não impediu que ele continuasse escrevendo — na execução oficial seguinte, as 4 respostas que antes eram exibidas passaram a ser bloqueadas pelo mesmo motivo. As duas execuções oficiais (antes e depois da tentativa) ficam registradas em `docs/validation_report.md`, sem repetir a demo tentando acertar. Nenhuma afirmação, em nenhuma execução testada, foi encontrada sem sustentação real no contexto recuperado; um erro de atribuição de citação entre duas páginas do mesmo documento (DIEESE p.12/p.13) se repetiu em todas elas — sinal de limitação na recuperação/prompt, não de um modelo específico. Detalhes em "Fidelidade" em `docs/validation_report.md`.

## 📚 Documentação

- [Arquitetura](docs/architecture.md)
- [Base de conhecimento: fontes ativas e candidatas](docs/base_de_conhecimento.md)
- [Uso detalhado do RAG](docs/rag_usage.md)
- [Relatório de validação](docs/validation_report.md)
- [Spec da orquestração](docs/superpowers/specs/2026-11-05-agent-orchestration.md) e [planos](docs/superpowers/plans/)

## 👩‍💻 Equipe

Desenvolvido pelo **Grupo 11**. Todas somos **AI Builders**, cada uma com uma frente principal de atuação:

<table>
  <tr>
    <td align="center" width="25%">
      <a href="https://github.com/AmandaElisa">
        <img src="https://github.com/AmandaElisa.png" width="90" alt="Amanda"/><br/>
        <b>Amanda</b>
      </a><br/>
      <sub>Fullstack</sub>
    </td>
    <td align="center" width="25%">
      <a href="https://github.com/anajbsouza">
        <img src="https://github.com/anajbsouza.png" width="90" alt="Ana Julia"/><br/>
        <b>Ana Julia</b>
      </a><br/>
      <sub>Ciência de Dados · Engenharia de Dados</sub>
    </td>
    <td align="center" width="25%">
      <a href="https://github.com/CamilaSilvaC">
        <img src="https://github.com/CamilaSilvaC.png" width="90" alt="Camila"/><br/>
        <b>Camila</b>
      </a><br/>
      <sub>Engenharia de Dados · DevOps</sub>
    </td>
    <td align="center" width="25%">
      <a href="https://github.com/eduardaoliveirazorg-jpg">
        <img src="https://github.com/eduardaoliveirazorg-jpg.png" width="90" alt="Eduarda"/><br/>
        <b>Eduarda</b>
      </a><br/>
      <sub>Ciência de Dados · Arquitetura de Software</sub>
    </td>
  </tr>
</table>

## 🤝 Como contribuir

1. Crie um branch a partir da `main` (`feat/...`, `fix/...`, `docs/...`).
2. Antes de abrir o PR, rode `uv run ruff check .` e `uv run pytest`.
3. Abra um pull request para a `main` e peça revisão de pelo menos uma pessoa do grupo.

Combinados do time: mudanças na `main` só por pull request, e nada de `git push --force` em branches compartilhados.

---

<p align="center">
  <i>Artemis — Mais conhecimento, confiança e oportunidades para mulheres em STEM.</i> 💜
</p>
