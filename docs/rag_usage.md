# Executar e revisar o RAG

A apresentação institucional permanece no README. A arquitetura está em [architecture.md](architecture.md); resultados e limites, em [validation_report.md](validation_report.md).

## Instalar e executar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m src.pipeline
python -m src.eda
python -m src.query "O que a cartilha informa sobre transparência salarial?"
python -m src.evaluate
```

A primeira execução baixa as fontes e o modelo. Após obter os pesos, `HF_HUB_OFFLINE=1` impede novas consultas ao Hub sem impedir os downloads das fontes. Configure o LLM opcional com `LLM_API_KEY`, `LLM_MODEL` e endpoint HTTPS compatível com Chat Completions. Sem credenciais, a consulta imprime evidências. A geração real ainda precisa de validação autorizada.

A pipeline usa chunks de 600 caracteres e sobreposição de 100. Para reproduzir os parâmetros anteriores: `python -m src.pipeline --chunk-size 1200 --overlap 180`. Isso publica uma nova coleção após validação, preservando a anterior. Não apague índices para comparar configurações.

A busca padrão é `hybrid`: vetorial + BM25, fusão RRF e diversidade por página/seção. As opções `--retrieval dense` e `--retrieval pages` estão disponíveis em `src.query` e `src.evaluate`. A avaliação aceita `--output caminho.json` para preservar comparações. Métricas de página/seção não validam completude de um artigo ou qualidade de resposta.

## Fontes e relatórios

`config/sources.json` mantém as URLs primárias. Cada alternativa explícita informa URL, editor, versão, seletor HTML, justificativa e limites de equivalência. `source_url` do dataset aponta à origem efetiva, enquanto `metadata.primary_url` preserva o Planalto. Falhas de todas as alternativas mantêm a fonte indisponível e bloqueiam publicação completa.

Códigos da pipeline: 0 sucesso de todas as fontes; 1 falha; 2 publicação parcial explicitamente permitida. `--skip-index` valida sem embeddings. O modo `--allow-partial` e as consultas com esse mesmo argumento usam o índice parcial separado; quando ele existe, essa opção prefere o parcial, mesmo havendo um completo. Para consultar as cinco fontes atuais, omita `--allow-partial`.

`reports/latest_run.json` contém tentativas, fonte efetiva e atualização do índice. `reports/eda.json` contém perfil e sinais de qualidade não destrutivos. `reports/retrieval_evaluation.json` separa casos respondíveis, sem resposta e excluídos. Referências com hash alterado são excluídas até revisão.

Os scripts em `scripts/` reproduzem os experimentos desta revisão usando snapshots locais e relatórios anteriores. Não fazem parte do caminho obrigatório da pipeline. Os corpora em `data/`, índices e relatórios de execução são ignorados pelo Git; o resumo publicado em `docs/validation_metrics.json` permite revisar os resultados sem esses arquivos.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check src tests scripts
python -m pip check
git diff --check
```

Não há revisão humana independente dos 20 casos nem validação real de geração. Não trate a publicação original de uma norma como confirmação automática de vigência.
