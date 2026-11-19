# Plano: pacote `artemis_rag` importável

Spec: [2026-11-19-pacote-importavel](../specs/2026-11-19-pacote-importavel.md) · Issue #23

1. **Renomear.** `git mv src artemis_rag`; trocar `src.` por `artemis_rag.` em imports, testes (strings de monkeypatch), scripts, `known-first-party` (`ruff.toml` e `pyproject.toml`). Rodar suíte: 104 verdes, como na base.
2. **Empacotar.** `[build-system]` hatchling, `packages = ["artemis_rag"]`, `[dependency-groups] dev`, `requires-python = ">=3.11,<3.14"`, matriz da CI com 3.13, `uv lock`.
3. **TDD do caminho do índice.** Teste: `ARTEMIS_RAG_INDEX_DIR` aponta para um índice de teste e `active_collection()` sem argumento o encontra; parâmetro explícito vence a variável. Depois, `index_dir()` em `index.py`, usado por `active_collection`, `build_index` e `evaluate`.
4. **TDD da `IndiceIndisponivel`.** Teste: diretório vazio levanta `IndiceIndisponivel` com a mensagem atual (agora `python -m artemis_rag.pipeline`) e continua sendo `ValueError`. Depois, a exceção.
5. **TDD da API.** Testes de `buscar` (índice pequeno com encoder local, ids `FONTE N`, campos, `indice` explícito, variável de ambiente), `validar_citacoes` e `gerar` (payload idêntico ao do `generate`, `None` sem LLM). Depois, `api.py` e `__init__.py`.
6. **3.13.** `uv run --python 3.13 pytest` e ruff.
7. **Docs.** README, `docs/rag_usage.md`, `docs/base_de_conhecimento.md`, notas do `config/sources.json`; seção "Usar como biblioteca".
8. **Integração.** Projeto uv vazio em diretório temporário, `uv add "artemishub-rag @ git+file://<worktree>"`, `python -c "from artemis_rag import buscar, Evidencia"`.
9. **PRs.** Rag (`Closes #23`, para `main`); orquestrador e docs para `src.query` → `artemis_rag.query`, com issue própria.
