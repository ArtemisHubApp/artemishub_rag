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

As variáveis de credenciais/modelo de geração não estavam configuradas na sessão original; não houve chamada real a provedor nessa fase. O contexto inclui URL real, URL primária, editor, versão e artigo, e o prompt alerta que publicação original não certifica vigência atual.

Citações inexistentes/malformadas e parágrafos sem referência são rejeitados, mas o verificador não comprova suporte semântico. Nenhuma chave foi exposta ou versionada.

### Demonstração real executada — 08/11/2026

Com `LLM_API_KEY` configurada (Gemini, via endpoint compatível com OpenAI), `uv run python -m src.demo` foi executado contra as 5 perguntas fixas do roteiro. Dois problemas de infraestrutura precisaram ser resolvidos antes de medir fidelidade, nenhum deles no prompt:

1. **Modelo indisponível:** `gemini-2.5-flash` (sugerido em `.env.example`) retorna 404 ("no longer available to new users"), confirmado em testes repetidos em 08 e 09/11/2026. O substituto sugerido pela própria API, `gemini-3.8-flash`, respondeu 503 ("high demand")/timeout em testes repetidos. `gemini-flash-lite-latest` respondeu 200 de forma consistente, mas é um **apelido** (`-latest`): o modelo por trás dele pode mudar sem aviso, o que quebra a reprodutibilidade da demonstração. Padrão final, fixo: `gemini-3.5-flash` (testado, 200 OK, ~12s por chamada); se ele der 503/timeout, a alternativa testada é `gemini-3.5-flash-lite` (~0,7s por chamada). `.env.example` e `docs/rag_usage.md` atualizados.
2. **Citação combinada rejeitada:** o modelo escreve `[FONTE 2, FONTE 3]` (duas fontes em um colchete só) em vez de `[FONTE 2] [FONTE 3]`. O validador em `validate_citations` (`src/query.py`) usa `re.findall(r"\[FONTE[^\]]*\]", answer)` e rejeita qualquer label que não seja `\[FONTE\s+\d+\]` — então o bloco combinado falha como "Malformed citation identifier". Isso não é um problema de fundamentação (as duas fontes citadas sustentavam a afirmação); é só um formato de citação que o validador não reconhecia. Correção aplicada: reforço no prompt do sistema (nunca combinar fontes em um colchete) **mais** uma função `normalize_citations()` que roda antes do validador e só separa listas inequívocas — `"[FONTE 2, FONTE 3]"` e `"[FONTE 2, 3]"` → `"[FONTE 2] [FONTE 3]"`. Qualquer outra variação (intervalo `"FONTE 2-3"`, texto livre, número sem a palavra "FONTE") continua caindo no validador original e sendo rejeitada; cada número normalizado ainda passa pela checagem de existir entre os trechos recuperados. `validate_citations` não foi afrouxado. Testes em `tests/test_query.py` cobrem: 2 e 3 fontes combinadas, a forma curta `"[FONTE 1, 2]"`, citação combinada com fonte inexistente (deve falhar) e intervalo (deve falhar).

Resultado com `gemini-flash-lite-latest` (execução intermediária, descartada por não ser reprodutível): 5 perguntas · 4 respondidas com citação · 1 abstenção · 0 falhas.

**Resultado final com `gemini-3.5-flash` (modelo fixo, 09/11/2026): 5 perguntas · 2 respondidas com citação · 3 abstenções · 0 falhas** (relatório completo em `reports/demo_rag.md`, não versionado; modelo registrado no cabeçalho do relatório confere com o `.env`).

### Fidelidade (faithfulness) — avaliação manual

**Avaliação manual, feita por inspeção direta, sobre apenas 5 perguntas fixas — não é uma amostra estatística, só uma checagem de sanidade qualitativa.** Para cada afirmação da resposta, o trecho citado foi lido e comparado literalmente. Tabela refeita sobre a saída do modelo final (`gemini-3.5-flash`).

| Pergunta | Afirmação | Fonte citada | Sustentada? |
| --- | --- | --- | --- |
| 1. Onde faço uma denúncia? | — | — | **Absteve** (resposta anterior, com `gemini-flash-lite-latest`, respondia e citava FONTE 2/3 corretamente; `gemini-3.5-flash` é mais conservador aqui apesar da evidência estar disponível) |
| 2. Quais empresas publicam o relatório? | Empresas de direito privado com 100+ empregados publicam a cada semestre (duas vezes ao ano) o Relatório de Transparência Salarial | FONTE 1 (diretrizes, p. 4): "...deverão publicar a cada semestre relatórios..." **e** FONTE 4 (cartilha, p. 5): "...apresentar, duas vezes ao ano, o Relatório..." | **Sim**, nos dois (mesma periodicidade, duas fontes independentes) |
| 3. Multa por pagar menos a uma mulher | — | — | **Absteve**, apesar de FONTE 2 (OT SIT 11/2024, p. 1) e FONTE 3 (Lei 14.611, art. 461 §7) conterem a resposta exata ("10 vezes o valor do novo salário... elevada ao dobro em caso de reincidência"). **Esta é a pergunta que a revisão pediu atenção especial**: o modelo tinha evidência suficiente e não respondeu — abstenção excessivamente cautelosa, não um erro de fundamentação (não houve invenção; só não houve resposta) |
| 4. Quanto as mulheres ganham a menos | Pnad 2014: mulheres ganham 74,5% do salário dos homens | FONTE 2 (ONU Mulheres, p. 24): texto quase idêntico | **Sim** |
| 4. (cont.) | Total geral: R$ 3.864 (homens) vs R$ 3.042 (mulheres) | FONTE 1 (DIEESE, p. 13) | **Sim**, citação correta |
| 4. (cont.) | Ensino superior: R$ 8.357 (homens) vs R$ 5.409 (mulheres), ~35% a menos | FONTE 1 (DIEESE, p. 13, correto) **e** FONTE 3 (DIEESE, p. 12 — sobre percentis de renda, não tem esses números) | **Conteúdo correto, mas com uma citação extra incorreta (FONTE 3)** — o mesmo tipo de erro de atribuição de citação da execução anterior se repete, agora como citação redundante em vez de citação única errada (antes citava só FONTE 3 errado; agora cita FONTE 1 certo + FONTE 3 errado) |
| 4. (cont.) | Cargos de direção: R$ 10.492 (homens) vs R$ 7.546 (mulheres) | FONTE 1 (DIEESE, p. 13) | **Sim**, citação correta |
| 5. Previsão do tempo (fora do tema) | — | — | **Recusada corretamente**: nenhum dos 5 trechos recuperados trata de previsão do tempo; a resposta foi a frase de abstenção exata |

**Nota por resposta** (afirmações sustentadas / total): Q1 abstenção (0 afirmações, evidência disponível não usada), Q2 1/1, Q3 abstenção (0 afirmações, evidência disponível não usada — a pergunta da multa), Q4 3/4 com citação inteiramente correta (4/4 no conteúdo), Q5 abstenção correta. **Nenhuma afirmação foi encontrada sem qualquer sustentação no contexto recuperado em nenhuma das duas execuções** — mas o erro de atribuição de citação na Q4 **se repetiu** entre as duas versões do modelo (mesmo par de fontes confundido: DIEESE p. 12 vs p. 13), e `gemini-3.5-flash` ficou mais conservador, abstendo em 2 de 5 perguntas (incluindo a da multa) onde a evidência recuperada já respondia a pergunta. Troca de modelo resolveu o problema de reprodutibilidade (apelido `-latest`), mas trocou "resposta com uma citação mal atribuída" por "abstenção indevida" em parte dos casos — é um trade-off, não uma melhora estrita. Amostra pequena demais (5 perguntas) para generalizar qualquer uma das duas taxas de erro.

### Context Precision@5 — nova métrica de recuperação

Mede, chunk a chunk sobre a lista bruta do top 5 (sem deduplicar documentos repetidos), a fração de trechos recuperados cujo documento (ou página) é realmente relevante para a pergunta — complementar ao Recall@5, que mede se o documento certo apareceu, não quanta "poluição" veio junto. Implementada em `context_precision_at_5`/`irrelevant_by_document` (`src/evaluate.py`), sem alterar `score_ranking` nem as métricas existentes; cobertura em `tests/test_evaluate.py`.

**Limitação:** a maioria das perguntas tem um único documento relevante, e o `diversify_pages` em `src/query.py` preenche deliberadamente o resto do top 5 com outros documentos para variedade — então uma precisão baixa não significa recuperação ruim, só reflete esse preenchimento. Por isso ela deve ser lida junto com `irrelevant_by_document`/`top_intruding_document`, que mostra qual documento mais ocupa espaço indevido.

### Comparação justa — as mesmas 16 perguntas originais, antes e depois

As 6 perguntas de desenvolvimento (`evaluation_group: "development"`) citam a fonte no próprio enunciado — mais fáceis por construção — e por isso saíram da comparação principal; `src/evaluate.py` ganhou um filtro `--evaluation-group` para reproduzir essa separação sem scripts ad hoc.

| Métrica (top 5) | 5 fontes, 16 originais | 20 fontes, mesmas 16 originais |
| --- | ---: | ---: |
| Casos avaliados / stale | 16 / 0 | 16 / 0 |
| Recall@5 documento | 100% | 93,75% |
| Hit rate@5 documento | 100% | 93,75% |
| MRR@5 documento | 0,9583 | 0,8177 |
| Recall@5 página | 100% | 87,5% |
| MRR@5 página | 0,8021 | 0,7083 |
| Context Precision@5 (documento) | 72,5% | 33,75% |
| Context Precision@5 (página) | 21,25% | 17,5% |
| Trechos não relevantes, média | 1,375 | 3,3125 |
| Documento que mais invade | `decreto_11795_2023` (11/16) | `guia_negociacao_coletiva` (17/16) |

### Linha separada — 6 perguntas de desenvolvimento (20 fontes)

| Métrica (top 5) | 20 fontes, 6 de desenvolvimento |
| --- | ---: |
| Casos avaliados / stale | 6 / 0 |
| Recall@5 / MRR@5 documento | 100% / 0,7778 |
| Recall@5 / MRR@5 página | 100% / 0,6944 |
| Context Precision@5 (documento / página) | 43,33% / 20% |
| Documento que mais invade | `cartilha_igualdade_salarial` (5/6) |

Recall/MRR altos aqui eram esperados — todas as 6 perguntas nomeiam a fonte na pergunta — e não devem ser somados ou lidos junto com a linha das 16 originais.

### Holdout (16 perguntas), antes e depois — nunca usado para ajustar nada

O snapshot do índice de 5 fontes (`stem_career_docs_0e0230700e1f48a3ad550ed6d090770c`) ainda existe fisicamente em `.chroma/snapshots/` (nunca é apagado ao publicar um novo índice), então foi possível medir a linha de base real, não só a atual.

| Métrica (top 5) | 5 fontes (antes) | 20 fontes (depois) |
| --- | ---: | ---: |
| Recall@5 documento | 96,88% | 87,5% |
| Hit rate@5 documento | 100% | 93,75% |
| MRR@5 documento | 0,8958 | 0,5302 |
| Recall@5 página | 93,75% | 78,13% |
| MRR@5 página | 0,7729 | 0,4469 |
| Context Precision@5 (documento) | 52,5% | 33,75% |
| Context Precision@5 (página) | 23,75% | 20% |
| Documento que mais invade | `cartilha_igualdade_salarial` (21/16) | `guia_negociacao_coletiva` (14/16) |

**A queda no holdout é maior do que no conjunto de desenvolvimento e um pouco maior do que nas mesmas 16 originais** — MRR@5 por página cai de 0,7729 para 0,4469 (queda de 42%), contra 0,8021→0,7083 (12%) nas 16 originais. O holdout nunca foi usado para ajustar nada nesta sessão; é só medido, e é o número mais pessimista — e o mais confiável — para avaliar a base de 20 fontes.

0 `stale_or_missing_evidence` em todas as linhas de todas as tabelas acima. **Achado principal, consistente nas três comparações:** quem mais invade o top 5 de perguntas que não são sobre ele, na base de 20 fontes, é `guia_negociacao_coletiva`, não o INEP — apesar do INEP ocupar 36,7% do índice em volume de chunks, ele não domina a recuperação nas perguntas atuais. `guia_negociacao_coletiva` tem 38 páginas e vocabulário muito próximo do tema central da base (igualdade salarial/negociação coletiva), o que o torna um candidato frequente mesmo quando não é a fonte certa.

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

## Expansão para 20 fontes — 08/11/2026

A branch `feat/base-20-fontes` ampliou a base das 5 fontes originais (221 chunks) para **20 fontes ativas, 245 documentos, 1209 chunks**. 13 das 15 candidatas pré-existentes em `config/sources.json` foram ativadas; 2 foram descartadas (`ibge_educa_mulheres`, duplicata 403 do mesmo PDF já ativo como `estatisticas_genero_ibge`; `relatorio_final_gti`, 404) e 1 nova candidata (`cartilha_plano_nacional`) foi desabilitada por ter páginas 1 e 9 sem texto extraível. 3 fontes novas de reforço foram adicionadas: `lei_9029_1995` e `lei_14457_2022` (Câmara/legin) e `gov_mulheres_dia_ciencia_fev2026` (Ministério das Mulheres).

**Correção de TLS:** `download.inep.gov.br` falhava com `SSL: CERTIFICATE_VERIFY_FAILED` usando o bundle certifi padrão do Python, mas validava corretamente com o keychain do macOS. `src/ingest.py` agora chama `truststore.inject_into_ssl()` (dependência já transitiva de `httpx`/`httpcore2`, promovida a uso direto) para usar o trust store do sistema operacional em vez do bundle embutido. Não é um bypass de verificação — é trocar a fonte de certificados confiáveis.

**Mecanismo `known_blank_pages`:** o PDF do INEP tem a página 108 (última) genuinamente vazia — 0 caracteres, 0 imagens, confirmado manualmente. Como `src/ingest.py` recusava qualquer fonte com páginas vazias, foi adicionado um campo opcional `known_blank_pages` por fonte: a página declarada só é descartada (não indexada) se estiver *de fato* vazia; se a página declarada tiver texto, ou se outra página vier vazia sem estar declarada, a fonte continua falhando. As páginas descartadas aparecem em `reports/latest_run.json` (`dropped_blank_pages`). Cobertura de teste em `tests/test_ingest.py` (3 casos: página declarada vazia passa; página vazia não declarada falha; página declarada que não está mais vazia falha).

**Achado de qualidade não previsto — PDF do INEP com fontes sem mapeamento Unicode (ToUnicode):** parte do texto é desenhada com fontes Type0/Identity-H sem tabela ToUnicode. Nesses trechos, a extração devolve caracteres ilegíveis; o defeito é do arquivo, não do extrator (PyMuPDF, pypdf e pdfminer.six falham da mesma forma — confirmado em 09/11/2026 comparando os três sobre as mesmas páginas). O dano é localizado: afeta o cabeçalho repetido em todas as páginas ("RESUMO TÉCNICO DO CENSO... 2024") e sufixos de algumas legendas de gráfico. Nas páginas verificadas (4, 23 e 51), a prosa, os percentuais e as tabelas extraem corretamente (ex.: 51,2%, 29,3% e 43,0% na p. 23; tabela de idades na p. 51). Os gráficos são vetoriais (sem imagens). Verificação amostral, não exaustiva. Isso não bloqueou a ativação (os marcadores `expected_text` são textuais, não numéricos) — ver limitações em `validation_metrics.json`.

**Bloqueios confirmados, não contornados:**
- `gov.br/trabalho-e-emprego/.../noticias-e-conteudo/...` e `gov.br/mcti/...` retornam **403 Forbidden** mesmo com o User-Agent legítimo da aplicação (`AcademicRAGResearch/0.2`) — WAF bloqueando o caminho, não o UA.
- `gov.br/secom/...` também retorna 403 nos dois casos testados.
- Reteste do Planalto (3 URLs × 3 User-Agents honestos, incluindo o padrão do curl) confirma **reset de conexão em todos os casos** — handshake TLS completo, mas o servidor fecha a conexão após o `GET`, antes de responder. Não é um bloqueio por string de UA; mantemos as alternativas da Câmara dos Deputados.
- `senado.leg.br/noticias` retorna 200, mas o extrator genérico captura só um banner de notificação ("Quer receber notificações..."), não o corpo da matéria — descartado sem selector dedicado.

**Métricas (conjunto original de 16 respondíveis + 6 perguntas de desenvolvimento = 22 casos; ver `docs/validation_metrics.json` → `expansion_20_sources_2026_11_08`):**

| Métrica (top 5) | 5 fontes / 16 casos (baseline) | 20 fontes / 22 casos |
| --- | ---: | ---: |
| Recall@5 por documento | 100% | 95,45% |
| MRR@5 por documento | 0,9583 | 0,8068 |
| Recall@5 por página | 100% | 90,91% |
| MRR@5 por página | 0,8021 | 0,7045 |
| Holdout (16 casos) — Recall@5 / MRR@5 por página | não medido nesta fase | 78,13% / 0,4469 |

22/22 casos avaliados, **0 `stale_or_missing_evidence`** — nenhuma página/hash de evidência mudou com a expansão.

**Duas perguntas do conjunto original regrediram** (`q06`, `q15`), ambas com `page_recall@5 = 0`. Nenhuma tem chunk do INEP entre os 5 recuperados — a causa é concorrência de fontes novas tematicamente próximas (`portaria_mte_3714_2023`, `guia_negociacao_coletiva`, `plano_nacional_igualdade`), não o INEP. O INEP ocupa 36,7% do índice (444/1209 chunks) e a ONU Mulheres 19,6%; essa concentração é esperada em uma base com documentos de tamanhos muito desiguais e **fica registrada como limitação**, não corrigida nesta entrega — qualquer melhoria de chunking para tabelas/documentos grandes é tratada em uma branch separada (`feat/chunking-tabelas`), depois do PR desta entrega, sem alterar `content`/`content_hash` dos documentos já avaliados.

## Pendências restantes

- Diagnosticar externamente a causa dos resets no Planalto; alternativas institucionais resolvem a coleta, não esse acesso. Reconfirmado em 08/11/2026 com 3 User-Agents honestos (nenhum contornando bloqueio): reset de conexão em todos os casos.
- Revisão humana independente de todos os gabaritos, e revisão jurídica específica de q17/versões das normas.
- Corrigir reconstrução de PDFs e bordas de chunks somente com validação editorial e novas comparações; sinais atuais são preservados e reportados. Inclui a codificação de fonte customizada do PDF do INEP (números/legendas corrompidos) e o tratamento de tabelas (INEP/IBGE/ONU Mulheres), planejados para `feat/chunking-tabelas`.
- Validar LLM real, completude de evidências, fidelidade, abstenção e resistência a injection. Métricas atuais não resolvem esses pontos.
- Construir conjunto independente e mais diversificado antes de generalizar a melhora de recuperação ou calibrar limiar de distância.
- Reavaliar o desbalanceamento do índice (INEP 36,7%, ONU Mulheres 19,6%) após o tratamento de tabelas na branch `feat/chunking-tabelas`.
- Remover, na camada de chunking (`src/prepare.py`), o cabeçalho repetido ilegível do INEP ("RESUMO TÉCNICO DO CENSO... 2024"), sem alterar o `content` da página.
- Avaliar a Sinopse Estatística oficial do Censo da Educação Superior em planilha (zip de 397 MB, `download.inep.gov.br/informacoes_estatisticas/sinopses_estatisticas/sinopses_educacao_superior/sinopse_educacao_superior_2024.zip`) como fonte numericamente mais confiável para perguntas estatísticas sobre o censo.
