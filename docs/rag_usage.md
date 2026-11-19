# Executar e revisar o RAG

A apresentação institucional permanece no README. A arquitetura está em [architecture.md](architecture.md); resultados e limites, em [validation_report.md](validation_report.md).

## Instalar e executar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m artemis_rag.pipeline
python -m artemis_rag.eda
python -m artemis_rag.query "O que a cartilha informa sobre transparência salarial?"
python -m artemis_rag.evaluate
```

A primeira execução baixa as fontes e o modelo. Após obter os pesos, `HF_HUB_OFFLINE=1` impede novas consultas ao Hub sem impedir os downloads das fontes. Configure o LLM opcional com `LLM_API_KEY`, `LLM_MODEL` e endpoint HTTPS compatível com Chat Completions. Sem credenciais, a consulta imprime evidências. A geração real ainda precisa de validação autorizada.

A pipeline usa chunks de 600 caracteres e sobreposição de 100. Para reproduzir os parâmetros anteriores: `python -m artemis_rag.pipeline --chunk-size 1200 --overlap 180`. Isso publica uma nova coleção após validação, preservando a anterior. Não apague índices para comparar configurações.

A busca padrão é `hybrid`: vetorial + BM25, fusão RRF e diversidade por página/seção. As opções `--retrieval dense` e `--retrieval pages` estão disponíveis em `artemis_rag.query` e `artemis_rag.evaluate`. A avaliação aceita `--output caminho.json` para preservar comparações. Métricas de página/seção não validam completude de um artigo ou qualidade de resposta.

## Usar como biblioteca

O `artemishub_agents` importa o RAG como pacote, sem passar pela CLI. Instale fixando um commit:

```bash
uv add "artemishub-rag @ git+https://github.com/ArtemisHubApp/artemishub_rag@<sha>"
```

A interface pública fica em `artemis_rag/api.py` e é reexportada em `artemis_rag`. Esses nomes são estáveis: mudar qualquer um deles quebra o agents.

| Nome | O que faz |
| --- | --- |
| `Evidencia` | Dataclass imutável: `id`, `titulo`, `url`, `pagina`, `artigo`, `texto`, `distancia`, mais a procedência opcional (`publicador`, `versao`, `url_primaria`, `alternativa_usada`). `id` é `"FONTE 1"`, `"FONTE 2"`... na ordem do ranking; `pagina` e `artigo` são `None` quando não se aplicam. |
| `buscar(pergunta, top_k=5, indice=None, parcial=False)` | Busca híbrida (a mesma da CLI), sem LLM. Devolve `list[Evidencia]`. |
| `validar_citacoes(resposta, evidencias)` | Números de FONTE citados, ordenados; `[]` para a abstenção. Levanta `CitationValidationError` para fonte inexistente, rótulo malformado ou parágrafo sem citação. Confere a referência, não se o trecho sustenta a frase. |
| `gerar(pergunta, evidencias)` | Resposta do LLM com citações já validadas. Devolve `ABSTENTION` sem evidências e `None` sem `LLM_API_KEY`/`LLM_MODEL`. Envia ao LLM o mesmo contexto que a CLI. |
| `IndiceIndisponivel` | Subclasse de `ValueError`: não há índice publicado, ou só um parcial e `parcial=False`. |
| `ABSTENTION`, `CitationValidationError` | Texto da abstenção e erro do validador. |

**Onde fica o índice.** O pacote instalado não traz o índice nem os dados (`.chroma/` e `data/` estão no `.gitignore`). A ordem de busca é: o parâmetro `indice`, senão a variável `ARTEMIS_RAG_INDEX_DIR`, senão o `.chroma` deste repo (o padrão da CLI). A variável vale também para a escrita: `ARTEMIS_RAG_INDEX_DIR=/caminho python -m artemis_rag.pipeline` publica ali. A consulta só lê o índice, nunca `data/`.

O modelo de embeddings da consulta precisa ser o do índice: não defina `EMBEDDING_MODEL` nem `EMBEDDING_REVISION` diferentes dos usados na publicação, senão `buscar` levanta `ValueError`. A primeira busca baixa o modelo do Hugging Face, se ele ainda não estiver no cache.

## Demonstração com LLM (Gemini)

O modelo de embeddings roda localmente e não precisa de chave. Só a geração usa uma API externa. Com uma chave gratuita do [Google AI Studio](https://aistudio.google.com/apikey), preencha o `.env`:

```
LLM_API_KEY=<sua chave>
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-3.5-flash-lite
```

`gemini-2.5-flash` está indisponível para novas chamadas (404: "no longer available to new users"), testado em 08/11/2026. Use uma versão fixa, nunca um apelido como `-latest`: um apelido muda de modelo sem aviso e quebra a reprodutibilidade da demonstração.

O modelo foi escolhido entre 3 versões fixas testadas sobre as mesmas 5 perguntas da demonstração (09/11/2026):

| Modelo | Resultado | Observação |
| --- | --- | --- |
| `gemini-3.7-flash` | 5/5 falhas (`ReadTimeout`) | ~8 min de execução, nenhuma chamada concluiu; descartado |
| `gemini-3.5-flash` | 2 respondidas / 3 abstenções / 0 falhas | ~12s/chamada; conservador, abstém mesmo com evidência suficiente |
| **`gemini-3.5-flash-lite` (escolhido)** | 3 respondidas / 1 abstenção / 1 bloqueio do validador | ~0,7s/chamada; mais rápido e mais disposto a responder |

Detalhes da comparação e da resposta barrada pelo validador em `docs/validation_report.md`.

Confira no AI Studio se o modelo continua disponível no plano gratuito. No plano gratuito, o Google pode usar prompts e respostas para melhorar seus produtos: envie só os trechos públicos da base, nunca dados de usuárias. Não versione o `.env` e apague a chave depois dos testes.

```bash
uv run python -m artemis_rag.pipeline   # se o índice ainda não existir
uv run python -m artemis_rag.demo       # gera reports/demo_rag.md
```

`artemis_rag.demo` roda 5 perguntas (a última fora da base, para observar a abstenção) e grava, para cada uma, os trechos recuperados com título, URL, página e distância, a resposta e as fontes citadas. Outras perguntas: `--questions arquivo.txt`, uma por linha. A saída nunca registra a chave. Uma pergunta com falha não interrompe as demais; o código de saída é 1 se alguma falhar.

A validação de citações confere que cada parágrafo cita uma fonte recuperada, não que o trecho sustente a frase. Revise cada resposta contra os trechos antes de usá-la como evidência.

## Fontes e relatórios

`config/sources.json` mantém as URLs primárias. Cada alternativa explícita informa URL, editor, versão, seletor HTML, justificativa e limites de equivalência. `source_url` do dataset aponta à origem efetiva, enquanto `metadata.primary_url` preserva o Planalto. Falhas de todas as alternativas mantêm a fonte indisponível e bloqueiam publicação completa.

Códigos da pipeline: 0 sucesso de todas as fontes; 1 falha; 2 publicação parcial explicitamente permitida. `--skip-index` valida sem embeddings. O modo `--allow-partial` e as consultas com esse mesmo argumento usam o índice parcial separado; quando ele existe, essa opção prefere o parcial, mesmo havendo um completo. Para consultar as cinco fontes atuais, omita `--allow-partial`.

`reports/latest_run.json` contém tentativas, fonte efetiva e atualização do índice. `reports/eda.json` contém perfil e sinais de qualidade não destrutivos. `reports/retrieval_evaluation.json` separa casos respondíveis, sem resposta e excluídos. Referências com hash alterado são excluídas até revisão.

Os scripts em `scripts/` reproduzem os experimentos desta revisão usando snapshots locais e relatórios anteriores. Não fazem parte do caminho obrigatório da pipeline. Os corpora em `data/`, índices e relatórios de execução são ignorados pelo Git; o resumo publicado em `docs/validation_metrics.json` permite revisar os resultados sem esses arquivos.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check artemis_rag tests scripts
python -m pip check
git diff --check
```

Não há revisão humana independente dos 20 casos nem validação real de geração. Não trate a publicação original de uma norma como confirmação automática de vigência.
