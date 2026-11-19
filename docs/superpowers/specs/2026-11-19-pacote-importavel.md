# Spec: pacote `artemis_rag` importável pelo artemishub_agents

Issue: #23 · Tamanho: S2 (muda o nome do pacote e cria interface pública consumida por outro repo) · Data: 2026-11-19

## Problema

1. O pacote se chama `src`, igual ao do `artemishub_agents`; instalar um dentro do outro colide.
2. Sem `[build-system]`, `uv add git+...` não instala o código.
3. O índice é achado só por `ROOT/.chroma`; instalado no site-packages, esse caminho não existe.
4. `requires-python = "<3.13"`, mas o agents testa no 3.12 e no 3.13.

## Decisão

- `src/` vira `artemis_rag/` (`git mv`). A CLI continua: `python -m artemis_rag.query|pipeline|demo|evaluate|eda`.
- `pyproject.toml`: hatchling com `packages = ["artemis_rag"]`; `[dependency-groups] dev`; `requires-python = ">=3.11,<3.14"` (dependências conferidas no 3.13). CI passa a testar 3.11, 3.12 e 3.13.
- Caminho do índice, nesta ordem: parâmetro explícito → `ARTEMIS_RAG_INDEX_DIR` → `.chroma` do repo (padrão da CLI). Vale para leitura (`active_collection`) e escrita (`build_index`), então a pipeline publica onde o agents lê. `evaluate` lê o snapshot do mesmo diretório.
- `data/` não é lido na consulta (o `Retriever` usa só o Chroma), então não ganha variável nova.
- API pública em `artemis_rag/api.py`, reexportada em `artemis_rag/__init__.py`:
  - `Evidencia` (frozen): `id, titulo, url, pagina, artigo, texto, distancia`, mais os campos opcionais de procedência que o `generate` já manda ao LLM (`publicador`, `versao`, `url_primaria`, `alternativa_usada`). Sem eles, `gerar` mudaria o contexto do LLM. `id` é `FONTE N` na ordem do ranking.
  - `buscar(pergunta, top_k=5, indice=None, parcial=False) -> list[Evidencia]`: `Retriever` híbrido atual, sem LLM.
  - `validar_citacoes(resposta, evidencias) -> list[int]`: `validate_citations` atual (levanta `CitationValidationError`).
  - `gerar(pergunta, evidencias) -> str | None`: `generate` atual; o contexto enviado ao LLM é idêntico ao da CLI.
  - `IndiceIndisponivel(ValueError)`: sem índice publicado (mensagem atual) ou índice parcial sem `parcial=True`. Herda de `ValueError` para não quebrar quem já captura esse tipo.

## Fora do escopo

Comportamento da busca, prompt, números de avaliação; scripts experimentais em `scripts/` (só os imports mudam); registros históricos (`docs/validation_report.md`, `docs/validation_metrics.json`, planos antigos) ficam como estão.

## Aceite

- `uv add "artemishub-rag @ git+..."` num projeto vazio e `from artemis_rag import buscar, Evidencia` funcionam.
- Testes novos (sem rede): `buscar` num índice pequeno, `ARTEMIS_RAG_INDEX_DIR`, `IndiceIndisponivel`, `gerar` com o mesmo payload do `generate`.
- Suíte atual verde no 3.11, 3.12 e 3.13; ruff limpo.

ADR: não cabe. É empacotamento dentro da stack já decidida, sem mudar arquitetura nem processo.
