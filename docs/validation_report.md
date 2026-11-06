# Revisão pré-PR do RAG Artemis — 05/11/2026

## Resultado executado

Na branch `feat/rag-e2e-validation`, foram coletadas e indexadas **as cinco fontes previstas**, com **33 registros e 221 chunks**. A pipeline real concluiu com código 0 às 11:41 locais (14:41 UTC). Lei, CLT e decreto vieram de alternativas oficiais explícitas da Câmara; os dois PDFs mantiveram suas URLs originais. O índice parcial anterior de 93 chunks e os demais índices foram preservados.

Foram executados **54 testes com sucesso**, Ruff, `pip check` e `git diff --check`, sem erros. Não houve commit, push, merge ou mudança de branch. O README institucional foi preservado sem alterações.

A validação real do LLM e a revisão humana independente continuam pendentes. Métricas de recuperação não comprovam fidelidade da geração, vigência jurídica nem recuperação integral de um artigo.

O arquivo `docs/validation_report.md` não existia no checkout ao iniciar esta revisão. Este relatório foi criado a partir dos artefatos locais anteriores, dos testes e dos experimentos efetivamente executados. O estado inicial tinha 45 testes passando e índice parcial de 93 chunks.

## Ambiente

- macOS arm64, Python 3.14.6, ambiente `.venv`.
- Chroma 1.5.9, SentenceTransformers 5.7.0, PyTorch 2.15.0, NumPy 2.5.4, PyMuPDF 1.28.2, HTTPX 0.28.1.
- Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Revisão fixada: `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`.
- Horários locais: America/Sao_Paulo; relatórios de execução usam UTC.
- O download exigiu acesso de rede fora do sandbox. As execuções posteriores de embeddings/avaliação usaram os pesos em cache, com `HF_HUB_OFFLINE=1`.

## Investigação das fontes

As três URLs originais do Planalto foram testadas pelo cliente HTTP da pipeline e por uma sondagem independente. Em ambos, a conexão foi encerrada com `ReadError: [Errno 54] Connection reset by peer`, antes de uma resposta HTTP utilizável. Não foram observados redirecionamentos nessas tentativas. Isso não permite afirmar bloqueio deliberado, indisponibilidade geral ou causa exata de TLS/rede. Não houve alteração de identificação para contornar acesso, desativação de TLS ou tentativa de contornar bloqueios.

As alternativas abaixo foram encontradas em bases oficiais, baixadas e conferidas. São tentadas somente após falha da URL primária, com todas as tentativas registradas. O manifesto mantém as URLs do Planalto, justificativa e notas de equivalência.

| Fonte | Representação utilizada | Resultado real |
| --- | --- | --- |
| Lei 14.611/2023 | [Câmara, publicação original](https://www2.camara.leg.br/legin/fed/lei/2023/lei-14611-3-julho-2023-794396-publicacaooriginal-168317-pl.html); DOU de 04/07/2023, seção 1, p. 1 | HTTP 200, sem redirecionamento; 5.498 caracteres extraídos |
| CLT, artigo 461 | [Câmara, texto atualizado](https://www2.camara.leg.br/legin/fed/declei/1940-1949/decreto-lei-5452-1-maio-1943-415500-normaatualizada-pe.html); somente artigo 461 | HTTP 200, sem redirecionamento; 2.940 caracteres; caput e parágrafos 1 a 7 presentes, artigo 462 excluído |
| Decreto 11.795/2023 | [Câmara, publicação original](https://www2.camara.leg.br/legin/fed/decret/2023/decreto-11795-23-novembro-2023-794987-publicacaooriginal-170182-pe.html); DOU de 23/11/2023, edição extra B, p. 6 | HTTP 200, sem redirecionamento; 5.984 caracteres |
| Cartilha Tira-Dúvidas | [Ministério das Mulheres/MTE](https://www.gov.br/mulheres/pt-br/central-de-conteudos/publicacoes/cartilha-tira-duvidas-lei-da-igualdade-salarial-e-de-criterios-remuneratorios-entre-mulheres-e-homens_defeso.pdf/@@display-file/file) | HTTP 200; 15 páginas, 14.395 caracteres |
| Estatísticas de Gênero | [IBGE, informativo](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102066_informativo.pdf) | HTTP 200; 15 páginas, 67.779 caracteres |

Também foi baixada a [publicação oficial do decreto no Senado](https://legis.senado.gov.br/norma/37855273/publicacao/37867096), HTTP 200, para inspeção de identidade e conteúdo. Ela não foi adicionada como uma sexta fonte nem usada para substituir silenciosamente o decreto.

**Diferenças e limites:** Câmara e Planalto são editores distintos. A lei e o decreto escolhidos são publicações originais; a CLT é uma consolidação atualizada com notas editoriais. Não foi possível demonstrar equivalência byte a byte com o Planalto, nem certificar todas as alterações jurídicas posteriores. Os textos oficiais indicam que não substituem a publicação no DOU. A documentação de versão não é uma certificação de vigência.

`source_url` aponta para a URL realmente utilizada, e `source`/`organization` identificam o editor da representação. `metadata` preserva `primary_url`, `final_url`, `publisher`, `version`, `alternative_used`, emissor e hash do download. A chave `url` do resultado de coleta continua identificando a URL primária; `selected_url` e `attempts` mostram a origem efetiva. Downloads bem-sucedidos são arquivados em `data/raw/versions/<fonte>/<sha256>.<tipo>`.

Na primeira tentativa com o seletor da Câmara, a validação recusou lei e decreto porque o extrator escolhia o título genérico “Legislação”. Foi corrigida a seleção do título imediatamente anterior ao corpo da norma, com teste de regressão. A versão que publicou o índice foi executada após essa correção. `.textoNorma` exclui navegação; a CLT usa recorte restrito do artigo 461.

## Qualidade dos dados

Os 33 registros representam **30 páginas PDF e 3 seções HTML**, agrupados em cinco fontes. Os hashes dos conteúdos dos PDFs e as evidências esperadas dos 15 casos originais não mudaram. Validações de campos, hashes e integridade dos 221 chunks foram executadas com sucesso.

| Indicador final | Valor |
| --- | --- |
| Fontes coletadas / habilitadas | 5 / 5 |
| Caracteres por registro: mínimo / média / máximo | 103 / 2.927,15 / 7.454 |
| Caracteres por chunk: mínimo / média / máximo | 103 / 520,98 / 600 |
| Registros com sinais de qualidade para inspeção | 26 |
| Chunks com possíveis palavras cortadas nas bordas | 124 |

As páginas 5 e 10 da cartilha foram renderizadas e inspecionadas visualmente. O texto extraído inclui blocos e fragmentos repetidos que não aparecem duplicados na renderização. A página 13 também contém repetição no texto extraído. O IBGE inclui números de gráficos/tabelas, cabeçalhos, ligaturas e um controle U+0008 na página 7.

**Não foi aplicado descarte automático desses conteúdos.** A EDA agora sinaliza linhas longas repetidas, controles, ligaturas, linhas numéricas e possíveis cortes de palavras. Esses sinais são avisos, não prova de erro semântico. A detecção de bordas usa a primeira ocorrência exata do chunk, o que limita sua precisão em textos repetidos. O chunking por caracteres e sobreposição ainda pode começar dentro de palavras; corrigir reconstrução de PDF e limites linguísticos exige validação editorial adicional, não apenas melhora de métricas.

O conteúdo original e versões anteriores permanecem preservados. Não houve limpeza agressiva de gráficos, tabelas ou trechos jurídicos. A auditoria de HTML confirmou ausência de “Veja também” e “Dados da Norma” nos registros legais finais.

## Recuperação: diagnóstico e comparação controlada

No índice inicial de duas fontes e 93 chunks, com gabaritos originais:

- `q02`: a primeira página 5 da cartilha aparecia na posição **13**.
- `q03`: a primeira página 5 aparecia na posição **23**.
- `q15`: cartilha/página 10 aparecia na posição **1**; IBGE/página 7, na **6**.

Apenas diversificar páginas ajudou `q15`, mas não `q02`/`q03`. Foi então comparado chunking 1200/180 com 600/100, preservando os mesmos documentos e hashes de evidência. No corpus completo, termos específicos como eSocial/CTEM motivaram um experimento BM25+vetores. Foram usados parâmetros fixos, sem modelos adicionais: BM25 k1=1,5/b=0,75; até 20 candidatos lexicais e 20 vetoriais; Reciprocal Rank Fusion com constante 60; prioridade de uma evidência por página/seção.

| Corpus e método — mesmos 15 casos originais | Recall@5 página | Hit Rate@5 página | MRR@5 página |
| --- | ---: | ---: | ---: |
| 2 fontes, 1200/180, vetorial original | 83,33% | 86,67% | 0,7389 |
| Mesmas 2 fontes, 600/100, diversidade por página | 96,67% | 100% | 0,7744 |
| 5 fontes, 1200/180, vetorial — controle do corpus ampliado | 70% | 73,33% | 0,6800 |
| Mesmas 5 fontes, 600/100, diversidade por página | 90% | 93,33% | 0,6911 |
| Mesmas 5 fontes, 600/100, híbrida com diversidade — adotada | **100%** | **100%** | **0,8333** |

Os controles usam Chroma persistente real e o mesmo modelo/revisão. A execução vetorial exaustiva inicial e os experimentos ficam em scripts reproduzíveis; os resultados de Chroma confirmaram a comparação. As mudanças não alteraram as perguntas nem as evidências dos 15 casos originais. A estratégia `hybrid` tornou-se padrão; `dense` e `pages` continuam selecionáveis.

Na estratégia final: `q02` recupera página 5 na posição 2; `q03`, na posição 1; `q15` recupera IBGE/página 7 na posição 2 e cartilha/página 10 na posição 4. O Recall por página dessas três perguntas é 1.

**Limite experimental:** resultados in-sample, sem conjunto independente. O tamanho pequeno, a predominância da cartilha e o uso do conjunto para decisões de implementação podem superestimar qualidade. Não há prova de generalização ou de qualidade da geração. Nos testes intermediários, algumas mudanças aumentaram Recall e reduziram MRR por documento; por isso os métodos e corpora são apresentados separadamente.

## Revisão dos 20 gabaritos

Todas as perguntas foram preservadas. A comparação automatizada também confirmou que as evidências dos 15 casos respondíveis anteriores permaneceram iguais.

| Casos | Classificação atual e conferência |
| --- | --- |
| q01 | Respondível; cartilha p. 4, definição |
| q02–q03 | Respondíveis; cartilha p. 5, empresas/periodicidade |
| q04–q05 | Respondíveis; cartilha p. 7, conteúdo/sistemas |
| q06 | Respondível; cartilha p. 8, eSocial |
| q07–q08 | Respondíveis; cartilha p. 9, informações/divulgação |
| q09 | Respondível; cartilha p. 11, empresas menores |
| q10 | Respondível; cartilha p. 12, plano de ação |
| q11 | Respondível; cartilha p. 13, participação |
| q12–q13 | Respondíveis; IBGE p. 7, CTEM/TIC |
| q14 | Respondível; IBGE p. 1, objetivo do estudo |
| q15 | Respondível; cartilha p. 10 + IBGE p. 7; sem inferência causal |
| q16 | Pendente de revisão comportamental; deve pedir esclarecimento |
| q17 | Artigo 461 coletado e referência registrada; pendente de revisão jurídica independente sobre o pedido de requisitos “vigentes”; excluído das métricas |
| q18 | Agora respondível em nível de localização da seção; lei coletada na Câmara, art. 5º e §§1º–4º; não é garantia de recuperação integral do artigo |
| q19–q20 | Sem resposta: salário individual futuro e senha pessoal; fora do denominador de Recall |

Total: **16 respondíveis, 2 sem resposta, 2 pendentes**. A evidência de q18 foi adicionada somente após coleta/inspeção; q17 não foi marcado validado apenas por existir texto. Todos os 20 casos têm `independent_human_review: pending`. Especialistas ainda precisam revisar gabaritos, aplicabilidade/atualidade jurídica e fidelidade das passagens, além de validar o protocolo de abstenção.

A revisão revelou um erro no avaliador: página HTML ausente era `null` no JSONL e string vazia no Chroma. Isso gerava falso erro de página para q18, embora o documento correto fosse recuperado. Foi normalizado o localizador e adicionado teste específico. Essa correção não alterou gabaritos; as métricas PDF anteriores não eram afetadas.

## Avaliação final executada

Sobre os 16 casos respondíveis, com índice completo e busca híbrida:

| Métrica | Resultado |
| --- | ---: |
| Recall@5 / Hit Rate@5 por documento | 100% / 100% |
| MRR@5 por documento | 0,9583 |
| Recall@5 / Hit Rate@5 por página ou seção HTML | 100% / 100% |
| MRR@5 por página ou seção HTML | 0,8021 |
| Latência média local de recuperação | 8,75 ms |

A latência inclui encoding, consulta e processamento lexical, sem inicialização do modelo/índice nem geração. Uma seção HTML representa um documento legal inteiro ou artigo recortado; localizar um chunk dessa seção **não prova que todos os parágrafos necessários foram recuperados**. Os dois casos sem resposta ainda retornam vizinhos; não foram contados como respostas corretas nem como falhas de Recall.

## Geração com LLM

As variáveis de credenciais/modelo de geração não estavam configuradas; não houve chamada real a provedor. Os testes simulados foram preservados. O contexto agora inclui URL real, URL primária, editor, versão e artigo, e o prompt alerta que publicação original não certifica vigência atual.

Citações inexistentes/malformadas e parágrafos sem referência são rejeitados, mas o verificador não comprova suporte semântico. Ainda falta executar, com credenciais autorizadas, um conjunto pequeno de perguntas documentais, fora do escopo e sem resposta, avaliando fidelidade/abstenção com revisão humana. Nenhuma chave foi exposta ou versionada.

## Persistência, testes e comandos

Índice completo: `stem_career_docs_ad59c5af59e8407da9e94f8af11f13bd`, 221 chunks. Uma reabertura e nova sincronização local confirmaram **221 inalterados, zero novos embeddings e zero remoções**. O índice parcial original de 93 chunks permanece em seu ponteiro separado; índices de experimentos não substituem o completo.

Comandos executados, com repetições após correções:

```bash
.venv/bin/python -m src.pipeline --skip-index
HF_HUB_OFFLINE=1 .venv/bin/python -m src.pipeline
.venv/bin/python -m src.eda
HF_HUB_OFFLINE=1 .venv/bin/python -m scripts.review_retrieval --allow-partial
HF_HUB_OFFLINE=1 .venv/bin/python -m scripts.compare_chunking
HF_HUB_OFFLINE=1 .venv/bin/python -m scripts.compare_persisted_retrieval
HF_HUB_OFFLINE=1 .venv/bin/python -m scripts.compare_persisted_retrieval --full-corpus
HF_HUB_OFFLINE=1 .venv/bin/python -m scripts.experiment_hybrid
HF_HUB_OFFLINE=1 .venv/bin/python -m src.evaluate
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests scripts
.venv/bin/python -m pip check
git diff --check
```

Resultado final: **54 testes aprovados; Ruff sem erros; nenhuma dependência quebrada; diff sem problemas de whitespace**. Permanecem seis avisos de depreciação de dependências, sem falhas. O CI remoto não foi executado nesta sessão.

Artefatos locais detalhados em `reports/official_source_probe.json`, `reports/latest_run.json`, `reports/eda.json`, `reports/retrieval_evaluation.json` e `reports/review/`. O resumo numérico versionável está em [validation_metrics.json](validation_metrics.json). Scripts de experimento exigem os snapshots/artefatos locais citados; esses dados não são distribuídos pelo Git.

## Pendências restantes

- Diagnosticar externamente a causa dos resets no Planalto; alternativas institucionais resolvem a coleta, não esse acesso.
- Revisão humana independente de todos os gabaritos, e revisão jurídica específica de q17/versões das normas.
- Corrigir reconstrução de PDFs e bordas de chunks somente com validação editorial e novas comparações; sinais atuais são preservados e reportados.
- Validar LLM real, completude de evidências, fidelidade, abstenção e resistência a injection. Métricas atuais não resolvem esses pontos.
- Construir conjunto independente e mais diversificado antes de generalizar a melhora de recuperação ou calibrar limiar de distância.
