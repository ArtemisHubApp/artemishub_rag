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

1. **Modelo indisponível:** `gemini-2.5-flash` (sugerido em `.env.example`) retorna 404 ("no longer available to new users"), confirmado em testes repetidos em 08 e 09/11/2026. `gemini-flash-lite-latest` respondeu 200 de forma consistente, mas é um **apelido** (`-latest`): o modelo por trás dele pode mudar sem aviso, o que quebra a reprodutibilidade da demonstração.
2. **Citação combinada rejeitada:** o modelo escreve `[FONTE 2, FONTE 3]` (duas fontes em um colchete só) em vez de `[FONTE 2] [FONTE 3]`. Corrigido com reforço no prompt **mais** `normalize_citations()`, que roda antes do validador e só separa listas inequívocas (`"[FONTE 2, FONTE 3]"`, `"[FONTE 2, 3]"`); qualquer outra variação continua caindo no validador original. `validate_citations` não foi afrouxado. Testes em `tests/test_query.py`.

### Escolha do modelo entre 3 versões fixas — 09/11/2026

Nenhum apelido `-latest` foi usado na escolha final; as 3 versões testadas foram fixas, sobre as mesmas 5 perguntas:

| Modelo | Resultado | Pergunta da multa | Observação |
| --- | --- | --- | --- |
| `gemini-3.7-flash` | **5/5 falhas** (`ReadTimeout`) | não respondeu | ~8 min de execução total (90s de timeout × 5 chamadas, nenhuma concluiu); desqualificado por inviabilidade, independente de qualidade |
| `gemini-3.5-flash` | 2 respondidas / 3 abstenções / 0 falhas | **Absteve**, apesar de ter evidência suficiente (FONTE 2 e FONTE 3 continham a resposta exata) | ~12s/chamada; conservador demais — recusa responder perguntas que a evidência recuperada já respondia |
| `gemini-3.5-flash-lite` | 3 respondidas / 1 abstenção / **1 bloqueio do validador** | Tentou responder certo (10x, dobro em reincidência), mas a resposta incluiu um parágrafo final sem citação e foi barrada — ver abaixo | ~0,7s/chamada; mais disposto a responder, e o conteúdo tentado está correto |

**Escolhido: `gemini-3.5-flash-lite`** — mais rápido e mais disposto a responder perguntas com evidência suficiente; o preço é um padrão de escrever um parágrafo final de ressalva sem citação, que o validador corretamente rejeita (ver abaixo). `.env`, `.env.example` e `docs/rag_usage.md` atualizados.

### Auditoria de respostas barradas pelo validador

`validate_citations` (`src/query.py`) agora levanta `CitationValidationError` (subclasse de `ValueError`, então quem já capturava `ValueError` continua funcionando), carregando a mensagem do validador e a resposta bruta (já normalizada, antes da validação). `src/demo.py` grava os dois no relatório — só para esse tipo de exceção; qualquer outra falha (rede, etc.) continua registrando só o nome da classe, sem vazar texto potencialmente sensível. Testes em `tests/test_demo.py`.

**Execução oficial final (`gemini-3.5-flash-lite`, 09/11/2026), aceita como veio, sem repetição: 5 perguntas · 3 respondidas com citação · 1 abstenção · 1 bloqueio do validador** (`reports/demo_rag.md`, não versionado).

Na pergunta da multa (Q3), o motivo exato do bloqueio foi `"LLM answer contains an uncited paragraph"` — **não é uma variação de formato de lista de fontes** (não é `;`, `e`, parênteses etc.), então não há extensão de `normalize_citations` a propor aqui. A resposta bruta barrada tinha 3 parágrafos: os dois primeiros citavam `[FONTE 2] [FONTE 3]`/`[FONTE 3]` corretamente (multa de 10x, dobro em reincidência — ambos literalmente corretos, conferidos contra a Lei 14.611/2023 art. 461 §7), mas o terceiro era um disclaimer sem nenhuma citação ("Ressalta-se que estas informações têm caráter geral e orientativo... não constituindo aconselhamento jurídico individualizado definitivo"). O validador rejeitou corretamente — é o comportamento pretendido, não um bug.

### Experimento revertido: proibir disclaimers escritos pelo modelo — 09/11/2026

A execução oficial de `gemini-3.5-flash-lite` acima tinha 1 resposta barrada pelo validador (Q3, multa) por causa de um parágrafo final de disclaimer sem citação. Mudança aplicada em `src/query.py`, com aprovação prévia:

- O prompt do sistema passou a dizer explicitamente para o modelo **não escrever avisos, ressalvas ou disclaimers** (porque o sistema acrescenta um aviso padrão depois), mantendo a proibição de dar conclusão jurídica individualizada definitiva.
- Depois de `validate_citations` aprovar a resposta (não antes, e sem alterar `validate_citations`), o código acrescenta um aviso fixo, em parágrafo separado: `"Aviso: informação geral baseada em fontes oficiais; não substitui orientação jurídica individual."` Em caso de abstenção, o aviso não é acrescentado.
- Testes em `tests/test_query.py`: resposta válida recebe o aviso; abstenção não recebe; um parágrafo de aviso escrito pelo próprio modelo continua sendo rejeitado (sem tocar em `validate_citations`).

**Resultado da nova execução oficial (`gemini-3.5-flash-lite`, 09/11/2026, aceita como veio): 5 perguntas · 0 respondidas com citação · 1 abstenção · 4 bloqueios do validador.** Isso é **pior**, não melhor, do que a execução anterior (3 respondidas / 1 abstenção / 1 bloqueio): as duas execuções oficiais ficam registradas abaixo para comparação, sem repetir a demo tentando "acertar":

| Execução oficial | Respondidas | Abstenções | Bloqueadas pelo validador |
| --- | ---: | ---: | ---: |
| Antes da correção de prompt | 3 | 1 | 1 (Q3) |
| Depois da correção de prompt | 0 | 1 | 4 (Q1, Q2, Q3, Q4) |

**Hipótese da causa:** mencionar avisos/aconselhamento jurídico no prompt — mesmo para proibi-los — parece ter induzido o modelo a escrever um parágrafo nessa linha de qualquer forma (em alguns casos quase idêntico ao aviso que o próprio sistema acrescentaria depois: "Aviso: informação geral baseada em fontes oficiais; não substitui orientação jurídica individual."). Pedir ao modelo para não escrever avisos não garantiu que ele obedecesse, e quando ele desobedece, a regra "todo parágrafo substantivo precisa de citação" (correta, nunca alterada) rejeita esse parágrafo — um disclaimer genérico não tem e não deve ter uma fonte específica citada. O validador funcionou exatamente como projetado nas duas execuções; o que não funcionou foi a premissa de que essa instrução de prompt mudaria o comportamento do modelo.

**Decisão: experimento revertido.** `src/query.py` e `tests/test_query.py` voltaram ao estado anterior a esta tentativa (prompt original, sem `DISCLAIMER` nem aviso anexado). `CitationValidationError` e a auditoria de respostas barradas em `src/demo.py` (que não fazem parte deste experimento) foram mantidas. Próxima tentativa, se houver, fica registrada em "Pendências restantes" abaixo, não implementada sem aprovação.

### Fidelidade (faithfulness) — avaliação manual

**Avaliação manual, feita por inspeção direta, sobre apenas 5 perguntas fixas — não é uma amostra estatística, só uma checagem de sanidade qualitativa.** Tabela sobre a execução oficial final, com o código já revertido (`gemini-3.5-flash-lite`, 09/11/2026): **5 perguntas · 3 respondidas com citação · 1 abstenção · 1 bloqueio do validador** — mesmo padrão da execução anterior ao experimento do disclaimer.

| Pergunta | Afirmação | Fonte citada | Sustentada? |
| --- | --- | --- | --- |
| 1. Onde faço uma denúncia? | Canal específico para denúncias de discriminação salarial | FONTE 2 (cartilha, p. 6): "...a disponibilização de canais específicos..." | **Sim** (FONTE 3, Decreto 11.795, é citação extra, não essencial) |
| 2. Quais empresas publicam o relatório? | Empresas de direito privado com 100+ empregados publicam o relatório | FONTE 1 (diretrizes, p. 4) **e** FONTE 4 (cartilha, p. 5) | **Sim**, nos dois |
| 3. Multa por pagar menos a uma mulher | Multa = 10x o salário, dobro em reincidência | FONTE 2 e FONTE 3, conferido contra a Lei 14.611/2023 art. 461 §7 | **Conteúdo sustentado, mas resposta barrada pelo validador** por um 3º parágrafo final ("Ressalta-se que estas informações possuem caráter geral... não constituindo aconselhamento jurídico individualizado definitivo") sem citação — não chegou a ser exibida ao usuário |
| 4. Quanto as mulheres ganham a menos | Pnad 2014: 74,5%; Total R$3.864/R$3.042; cargos de direção R$10.492/R$7.546 | FONTE 2; FONTE 1 (ambas as frases) | **Sim**, citações corretas |
| 4. (cont.) | Ensino superior: R$8.357/R$5.409, ~35% a menos | **Citada só como FONTE 3** (DIEESE p. 12, sem esses números); o número real está em FONTE 1 (p. 13), citada na mesma resposta para outra frase | Conteúdo correto, citação errada — **o erro de atribuição DIEESE p.12/p.13 se repete uma 6ª vez**, em execuções com 3 modelos diferentes |
| 5. Previsão do tempo (fora do tema) | — | — | **Recusada corretamente** |

Nenhuma afirmação, em nenhuma das execuções testadas nesta sessão, foi encontrada sem sustentação real no contexto recuperado — inclusive a resposta barrada da Q3, cujo conteúdo (fora o parágrafo final) está correto. Os dois problemas recorrentes continuam sendo: a pergunta da multa fica sem resposta exibida (hoje por causa do parágrafo de aviso que o próprio modelo insiste em escrever, não por falta de evidência), e o erro de atribuição DIEESE p.12/p.13, que aparece de forma consistente e independente do modelo usado.

**Nenhuma afirmação, em nenhuma das execuções testadas (3 modelos, 2 execuções oficiais com `gemini-3.5-flash-lite`), foi encontrada sem qualquer sustentação real no contexto recuperado.** O erro de atribuição DIEESE p.12/p.13 apareceu em todas as execuções que chegaram a citar esse trecho, independente do modelo — sinal de que o problema está na recuperação/no prompt (as duas páginas do mesmo documento ficam muito próximas em similaridade semântica), não em um modelo específico. Os problemas observados são todos sobre a forma da resposta (abstenção indevida, disclaimer sem citação, página errada dentro do mesmo documento), nunca sobre invenção de fatos. Amostra pequena demais (5 perguntas) para generalizar qualquer taxa.

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

## Qualidade da base — branch `feat/qualidade-base`, 09/11/2026

PR aberto a partir da `main` (já com o PR #14 mergeado). Regras: `content`/`content_hash` dos documentos nunca mudam; toda melhoria acontece na camada de chunking/indexação/busca; medição sempre com `--evaluation-group` (original+development) e holdout só agregado, no fim.

### Etapa 0 — Diagnóstico (sem mudar código)

- **Intrusão por documento** (22 perguntas original+development, sem holdout): o maior invasor do top 5 é `guia_negociacao_coletiva` (18 chunks não relevantes), seguido de `portaria_mte_3714_2023` (13) e `cartilha_igualdade_salarial` (6). **INEP (2) e ONU Mulheres (4) são baixos** — o peso delas no volume do índice (36,7%/19,6%) não se traduz em intrusão real no top 5.
- **Mapeamento Unicode quebrado**, varredura de todos os PDFs ativos (critério refinado para não contar pontuação legítima como •, –, —, aspas curvas como ilegível): **INEP, 106 de 108 páginas com algum trecho ilegível** (sobretudo o cabeçalho repetido "RESUMO TÉCNICO DO CENSO... 2024" e sufixos de legenda de gráfico — a prosa e os números substantivos extraem corretos, confirmado em `docs/validation_metrics.json`) e **`diretrizes_planos_acao`, 8 de 11 páginas**. Os demais PDFs (cartilha, DIEESE, IBGE, guia, ONU Mulheres, OT SIT, portaria) não têm corrupção real. Em `diretrizes_planos_acao`, confirmado um **deslocamento fixo de código de caractere (-5)**: `chr(ord(c) - 5)` decodifica "XJWFUWJXJSYFITSTUWF_T" para "SERAPRESENTADONOPRAZO..." perfeitamente. O INEP usa um encoding diferente (faixa Cirílica, não decodificável pelo mesmo shift simples) — **não há correção única para os dois**; não decodificado nesta etapa (ver "Próximos passos").
- **Tabelas** (`find_tables()`): INEP 86/108 páginas com tabela (94 tabelas), IBGE 9/15 (29 tabelas), ONU Mulheres 7/28 (8 tabelas), **DIEESE 0/16 — a tabela da p. 13 (Total/Ensino Superior/Cargos de direção, causa provável do erro de atribuição p.12/p.13) é na verdade um gráfico de barras com números soltos, sem estrutura de grade**; `find_tables()` não a detecta. Também há **falsos positivos** (IBGE p. 6: um gráfico detectado como pseudo-tabela com valores duplicados sem sentido) — qualquer uso de `find_tables()` na Etapa 2 precisa validar antes de aceitar.
- **Ruído em chunks**: ~100 chunks do INEP (de ~444) começam com o cabeçalho ilegível repetido, ~1 por página. Sequência de eixo de gráfico como chunk inteiro é rara (1 caso claro).
- **Por que a ONU Mulheres gera tantos chunks**: não é ruído — é um documento longo (28 páginas, 107.217 caracteres), chunking proporcional ao tamanho como qualquer outro documento.
- **5 perguntas de desenvolvimento criadas** (`q27`–`q31`, evaluation_group `development`, gabarito conferido): 3 de tabela (IBGE p. 4, razão M/H diretores e gerentes 73,9%; INEP p. 51, mediana de idade presencial 25; DIEESE p. 13, rendimento homens cargos de direção R$ 10.492) e 2 só-gráfico (IBGE p. 1, mulheres com ensino superior completo 21,3%, sem frase de prosa restatando; DIEESE p. 13, rendimento mulheres ensino superior R$ 5.409, não restatado em prosa nesta página). Todas já tinham Recall@5 = 100% na main atual antes de qualquer melhoria — **servem como verificação de não-regressão para as etapas seguintes, não como medida de ganho.**

**Expectativa registrada antes de medir qualquer etapa:** as Etapas 3 (contexto no embedding) e 4 (limite por documento) são as que atacam a invasão de `guia_negociacao_coletiva`/`portaria_mte_3714_2023`; as Etapas 1 (ruído) e 2 (tabelas) melhoram a qualidade dos chunks e podem não mexer nas métricas agregadas atuais.

### Etapa 0.5 — Revisão do gabarito com regra fixa

**Motivo:** o gabarito original (v1) foi escrito com 5 fontes, marcando um único documento/página como relevante; com 20 fontes, outro documento pode responder corretamente à mesma pergunta e hoje contar como erro de recuperação, quando na verdade é um artefato de medição.

**Regra fixa:** um par (documento, página) é relevante se o `content` da página contém, de forma explícita, a informação que responde à pergunta — mencionar o tema não basta. Se a pergunta cita uma fonte específica ("Segundo a cartilha...", "Segundo o Guia..."), só essa fonte é relevante; não se acrescenta alternativa. O gabarito v1 nunca é removido nem rebaixado, só se pode acrescentar.

**Seleção das perguntas revisadas:** não foram revisadas as 43 perguntas nem só as com recall imperfeito (isso usaria o resultado para selecionar, o que a regra proíbe para o holdout). Critério final:
- **Original + development:** revisadas as que têm `page_recall_at_5 < 1` OU `page_mrr_at_5 < 1` na main atual, excluindo as que citam uma fonte específica no enunciado (pela regra, não têm o que acrescentar). Resultado: **2 perguntas** (`q05`, `q06`).
- **Holdout:** revisadas **todas as 16** que não citam fonte específica no enunciado — sem olhar ranking nem métricas (holdout nunca é selecionado pelo resultado).

**Pooling:** para cada uma das 18 perguntas selecionadas, top 10 de 4 buscas (híbrida atual, só densa, só BM25, e o snapshot do índice de 5 fontes, que ainda existe em `.chroma/`), deduplicado por (documento, página) — **370 candidatos únicos no total**. Acima do limite de ~150 acordado, então os candidatos foram agrupados por pergunta e priorizados por posição (rank ≤ 3 em qualquer uma das 4 buscas e fora do gabarito atual): **112 prioritários**, revisados com trecho literal e decisão; os demais 258 listados só por título/página.

**Resultado da revisão:** **9 acréscimos aprovados**, registrados como `additional_evidence` (gabarito v2) nas perguntas `q05`, `q06`, `h01`, `h04`, `h08`, `h12`, `h13`, `h14`, `h16`:

| Pergunta | Documento/página | Achado |
| --- | --- | --- |
| q05 | `guia_negociacao_coletiva` p. 20 | Nomeia explicitamente os dois sistemas de dados (RAIS/eSocial e Portal Emprega Brasil) |
| q06 | `portaria_mte_3714_2023` p. 1 | Seção I da Portaria (itens a-d), a lista completa de "dados extraídos do eSocial" |
| h01 | `guia_negociacao_coletiva` p. 22 | Multa explícita (3% da folha, limitada a 100 salários mínimos) por não cumprir a divulgação |
| h04 | `ot_sit_11_2024` p. 1 | Multa específica (10x, dobro em reincidência) para o cenário exato da pergunta |
| h08 | `portaria_mte_3714_2023` p. 2 | Lista explícita de componentes da remuneração, incluindo horas extras e gorjetas (mesmo cálculo da Seção I da p. 1) |
| h12 | `fgv_ibre_desigualdade_genero` | Rendimento de mulheres negras especificamente (61% do rendimento dos homens sem desagregação) |
| h13 | `onu_mulheres_weps` p. 24 | "25 horas semanais contra 10 horas semanais entre homens" — referente ("afazeres domésticos") confirmado na frase anterior, mesma página |
| h14 | `estatisticas_genero_ibge` p. 4 | Tabela de rendimento por grupo ocupacional: "Profissionais das ciências e intelectuais", 63,3% — achado no rank 4 (fora do top-3), checado por suspeita |
| h16 | `onu_mulheres_weps` p. 24 | "A média salarial feminina corresponde a 74,5% da média salarial masculina" (Pnad 2014) |

**Rejeitados com registro:** `h09` (o enunciado "em que meses as empresas têm que publicar" mistura atores — o MTE publica em março/setembro, as empresas enviam dados em fevereiro/agosto e a Portaria não especifica mês para a publicação pelas próprias empresas; nenhum trecho responde literalmente à pergunta como formulada — **o enunciado pode merecer revisão futura, não alterado agora**); `h16`/DIEESE p. 13 (a associação entre os números "R$ 3.864/8.357/10.492" e "Homens"/"Mulheres" só existe na posição visual do gráfico, não no texto corrido — rejeitado pela regra); `h13`/FGV (frase sem "por semana" explícito).

**Implementação (`src/evaluate.py`):** `--gold v1|v2` (padrão v1, comportamento idêntico ao de antes). `check_evidence` valida o hash de `additional_evidence` também quando `gold=v2` (qualquer divergência marca o caso como `stale_or_missing_evidence`, nas duas listas). Em `evaluate()`, uma evidência adicional **não é simplesmente somada ao conjunto de documentos relevantes** — isso inflaria o denominador do Recall (`encontrados / total relevante`) e poderia *piorar* uma pergunta que já tinha nota máxima no v1, só porque a alternativa não apareceu junto da original. Em vez disso, um documento/página retornado que bate com uma evidência adicional é remapeado para o item original correspondente antes de chamar `score_ranking` (que não foi alterado): o Recall/MRR do v2 nunca fica pior que o v1 para o mesmo caso, só pode melhorar. O conjunto maior (original + adicional) é usado só no Context Precision, que não tem denominador para inflar. Testes cobrem: v1 ignora `additional_evidence` por completo; v2 aceita a evidência adicional; v2 nunca fica peor que v1 quando o documento original já é encontrado; hash divergente marca o caso como stale nas duas listas de evidência.

**Medição real, v1 × v2 (0 `stale_or_missing_evidence` em todas as linhas):**

| Conjunto | Casos | Recall@5 doc | MRR@5 doc | Recall@5 página | MRR@5 página | Context Precision (doc) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original+dev, v1 | 27 | 96,30% | 0,8241 | 92,59% | 0,7130 | 42,96% |
| Original+dev, v2 | 27 | 96,30% | 0,8272 | **96,30%** | 0,7284 | 45,19% |
| Holdout, v1 | 16 | 87,5% | 0,5302 | 78,13% | 0,4469 | 33,75% |
| Holdout, v2 | 16 | **90,63%** | **0,5615** | **84,38%** | **0,5094** | 38,75% |

Em nenhuma linha o v2 ficou pior que o v1 (confere a invariante de design). **No holdout — nunca usado para decidir nada — o v2 já recupera uma parte real da queda de 5 para 20 fontes**: MRR@5 por página sobe de 0,4469 para 0,5094 (+14%) só corrigindo o gabarito, sem qualquer mudança de chunking/busca ainda.

### Etapa 1 — Filtragem de ruído no chunking (revertida)

**Mudança testada:** em `src/prepare.py`, detecção de linhas de ruído por documento (cabeçalho/rodapé repetido em ≥40% das páginas do mesmo documento, linhas de número de página isoladas, eixos de ano de gráfico, e linhas majoritariamente ilegíveis por controle/Cirílico) e remoção delas antes do chunking, dividindo cada página em segmentos contíguos (nunca unindo texto através de uma linha removida, preservando o contrato de substring literal de `validate_chunks`) com fallback para a página inteira se a filtragem removesse tudo. Testada com 10 testes dedicados (`tests/test_prepare.py`), cobrindo cada função nova e os dois casos de contrato (chunk sempre substring literal da página; página 100% ruído ainda gera ≥1 chunk). `ruff` e os 82 testes passaram antes da medição.

**Medição, 16 perguntas originais, `--evaluation-group answerable --gold v1`, reconstruindo o índice (2764 chunks, vs. os ~1209 anteriores — a filtragem também elimina chunks que eram só ruído):**

| Métrica (top 5) | Antes (Etapa 0.5) | Depois (Etapa 1) |
| --- | ---: | ---: |
| Recall@5 documento | 93,75% | 93,75% |
| MRR@5 documento | 0,8177 | 0,8094 |
| Recall@5 página | 87,5% | 87,5% |
| MRR@5 página | 0,7083 | 0,6969 |
| Context Precision@5 (documento) | 33,75% | 31,25% |
| Trechos não relevantes, média | 3,3125 | 3,4375 |

**Page Recall@5 não piorou, mas page MRR@5 piorou (0,7083 → 0,6969) — pela regra acordada, a etapa foi revertida.** Comparação caso a caso mostra a causa: a resegmentação mudou os limites de chunk de `cartilha_igualdade_salarial` (afetando `q01`, `q05`, `q10` — todas pioraram uma posição de rank na página certa) e de `lei_14611_2023` (`q18`, idem), com apenas uma melhora compensatória (`q02`, de rank 2 para rank 1). O efeito líquido foi negativo mesmo sem nenhuma pergunta ter perdido o documento ou a página certa — um efeito-ruído da resegmentação em si, não da remoção de conteúdo irrelevante propriamente dita. `src/prepare.py` e `tests/test_prepare.py` foram restaurados ao estado da Etapa 0.5 (`git checkout -- src/prepare.py tests/test_prepare.py`) e o índice foi reconstruído de volta a esse estado antes de seguir para a Etapa 2; nenhum commit foi feito para a Etapa 1.

### Etapa 2 — Extração validada de tabelas (revertida)

**Mudança testada:** em `src/ingest.py`, `validate_table(rows, page_text)` aceita uma detecção de `page.find_tables()` só se tiver ≥2 linhas e entre 2–20 colunas, cabeçalho não vazio, densidade de células preenchidas ≥50%, e cada célula não vazia existindo literalmente (normalizando espaço em branco) no texto da própria página — sem alterar `content`/`content_hash` de nenhum documento existente. Calibrado e confirmado com os dois casos de referência do diagnóstico da Etapa 0: **rejeita** a pseudo-tabela da IBGE p.6 (densidade 2,1–16,8%, 13–75 colunas) e **aceita** a tabela real do INEP p.51 (densidade 78%, 4×8). A tabela da DIEESE p.13 continua não detectada por `find_tables()` (0 tabelas), confirmando o limite já conhecido — permanece só como candidata a imagem na Etapa 5. Tabelas validadas entram como chunk adicional com `content_type="table"`; `src/quality.py` ganhou uma regra própria para esse tipo (cada célula, não o texto renderizado inteiro, precisa existir literalmente na página). 13 testes novos (`tests/test_ingest.py`, `tests/test_prepare.py`, `tests/test_quality.py`), decorrentes de dados sintéticos (não de arquivos em `data/raw`, que não são versionados). `ruff` e os 84 testes passaram antes da medição.

**Medição, 16 perguntas originais, `--evaluation-group answerable --gold v1` (índice reconstruído, 1283 chunks vs. 1209 antes — 74 chunks de tabela validados em toda a base):**

| Métrica (top 5) | Antes (Etapa 0.5) | Depois (Etapa 2) |
| --- | ---: | ---: |
| Recall@5 documento | 93,75% | 93,75% |
| MRR@5 documento | 0,8177 | 0,8125 |
| Recall@5 página | 87,5% | 87,5% |
| MRR@5 página | 0,7083 | 0,7031 |
| Context Precision@5 (documento) | 33,75% | 33,75% |
| Trechos não relevantes, média | 3,3125 | 3,3125 |

**Page Recall@5 não piorou, mas page MRR@5 piorou (0,7083 → 0,7031) — revertida pela mesma regra.** Causa isolada caso a caso: só `q18` mudou (MRR por página de 0,3333 para 0,25); a página correta (`lei_14611_2023`) não perdeu conteúdo nem mudou de texto — o que mudou foi `guia_negociacao_coletiva` p.1 (chunk de texto, não de tabela) ultrapassando-a no ranking híbrido. A hipótese mais provável é um efeito indireto do BM25: adicionar 74 chunks de tabela ao corpus muda as estatísticas de frequência de termo (IDF) usadas no ranking léxico para **todos** os documentos, não só para quem ganhou uma tabela — o suficiente para reordenar um empate próximo em `q18` sem nenhuma tabela estar entre os 5 recuperados nesse caso. Isso é relevante para as próximas etapas: qualquer mudança que adicione chunks ao índice (Etapa 3 muda o texto embedado mas não a contagem de chunks; Etapa 4 só reordena, não adiciona) tem menos risco desse efeito colateral específico, mas vale verificar caso a caso. `src/ingest.py`, `src/prepare.py`, `src/quality.py`, `src/common.py` e os testes novos foram restaurados ao estado da Etapa 0.5 (`git checkout --`) e o índice foi reconstruído de volta a esse estado antes de seguir para a Etapa 3; nenhum commit foi feito para a Etapa 2. A lógica de validação de tabela (`validate_table`) em si classificou corretamente os dois casos de referência — a reversão é por efeito de ranking agregado, não por a extração estar errada.

### Etapa 3 — Contexto no embedding (revertida)

**Mudança testada:** `build_embedding_context(doc, text)` em `src/prepare.py` prefixava o texto só no **input do embedding denso** (nunca no texto armazenado/exibido/citado) com `[Documento: <título> | Órgão: <organização> | Página: <página> | Seção: <tópico>]`, montado só a partir de metadados já existentes — sem LLM. O prefixo ficava em `metadata.embedding_context`; um novo campo `embedding_sha256` (hash do texto com prefixo) substituiu `content_sha256` como chave do cache de reembedding em `src/index.py`, para que uma mudança só de contexto (ex.: título corrigido) invalidasse a embedding cacheada — sem invalidar por mudanças de metadado irrelevantes ao embedding. 5 testes novos; `ruff` e os 78 testes passaram antes da medição.

**Medição, 16 perguntas originais, `--evaluation-group answerable --gold v1` (todos os 1209 chunks reembedidos, já que o prefixo muda o hash de embedding de todos eles):**

| Métrica (top 5) | Antes (Etapa 0.5) | Depois (Etapa 3) |
| --- | ---: | ---: |
| Recall@5 documento | 93,75% | 90,625% |
| MRR@5 documento | 0,8177 | 0,6271 |
| Recall@5 página | 87,5% | **81,25%** |
| MRR@5 página | 0,7083 | **0,5906** |
| Context Precision@5 (documento) | 33,75% | 32,5% |
| Trechos não relevantes, média | 3,3125 | 3,375 |

**Regressão grande e inequívoca (não um efeito de uma única pergunta): `q02` perdeu completamente o documento/página certos (recall e MRR foram a zero), e várias outras perguntas caíram de MRR 1,0 para 0,2–0,25.** Hipótese: o modelo de embedding usado (`paraphrase-multilingual-MiniLM-L12-v2`, pequeno, 128 tokens efetivos de contexto curto) dilui o sinal semântico do próprio trecho quando um cabeçalho fixo de ~15–20 tokens (repetido, quase idêntico, em todo chunk do mesmo documento) é prefixado — pior ainda em chunks já curtos. Revertida imediatamente pela regra combinada (regressão clara em page Recall@5 e page MRR@5, não só MRR marginal como nas Etapas 1/2). `src/prepare.py`, `src/index.py` e os testes novos foram restaurados ao estado da Etapa 0.5; o índice foi reconstruído de volta antes de seguir para a Etapa 4; nenhum commit foi feito para a Etapa 3. A comparação de BM25 com/sem o prefixo, planejada como parte desta etapa, não chegou a ser feita: a regressão no embedding denso já foi suficiente para descartar a abordagem como testada.

### Etapa 4 — Limite de chunks por documento no top 5 (revertida)

**Mudança testada:** `diversify_pages` em `src/query.py` ganhou `max_per_document=2`: depois de diversificar por página (comportamento já existente), um segundo passo limitava a no máximo 2 chunks do mesmo `document_id` no top 5 final, preenchendo as vagas restantes com outros documentos primeiro e só excedendo o limite se não houvesse candidato de outro documento disponível. Puramente uma mudança de reordenação na recuperação — não toca `src/prepare.py`/`src/index.py`, então o índice não precisou ser reconstruído. 3 testes novos; `ruff` e os 77 testes passaram antes da medição.

**Nota operacional:** a medição inicial do índice usou embeddings residuais da Etapa 3 (revertida no código, mas `src/index.py` original reaproveita embeddings cacheadas por `content_sha256`, que não muda entre as etapas — só `embedding_sha256`, que não existe mais fora da Etapa 3, teria invalidado o cache corretamente). Isso foi percebido porque os números batiam exatamente com a regressão já revertida da Etapa 3, não com a linha de base. Corrigido apagando `.chroma/` (não versionado) e reconstruindo do zero antes de medir de novo — relevante para qualquer etapa futura que mude só o texto embedado sem mudar `content_sha256`.

**Medição, 16 perguntas originais, `--evaluation-group answerable --gold v1`, índice reconstruído do zero:**

| Métrica (top 5) | Antes (Etapa 0.5) | Depois (Etapa 4) |
| --- | ---: | ---: |
| Recall@5 documento | 93,75% | 93,75% |
| MRR@5 documento | 0,8177 | 0,8177 |
| Recall@5 página | 87,5% | **81,25%** |
| MRR@5 página | 0,7083 | **0,6927** |

**Page Recall@5 e page MRR@5 pioraram — revertida pela mesma regra.** Causa isolada: `q01` (`cartilha_igualdade_salarial`) perdeu a página certa por completo (recall de página caiu de 1,0 para 0,0), mesmo com o documento ainda sendo o mais bem ranqueado (MRR por documento permaneceu 1,0) — o limite de 2 chunks por documento descartou justamente o chunk da página certa, porque esse documento tinha 3+ chunks bem ranqueados e o da página certa não estava entre os 2 primeiros. O limite ajuda a diversidade de fontes mas pode custar precisão quando o próprio documento relevante domina o ranking — o trade-off que a Etapa 0.5 já havia registrado como esperado para `q06`/`q15` apareceu aqui em sentido inverso. `src/query.py` e os testes novos foram restaurados ao estado da Etapa 0.5; nenhum commit foi feito para a Etapa 4.

### Tabela consolidada — as 4 etapas revertidas vs. a base (Etapa 0.5), 16 perguntas originais

**O critério de reversão, fixado antes de medir qualquer etapa, era só `page_recall_at_5` e/ou `page_mrr_at_5` nas 16 perguntas originais — nenhuma outra métrica (Recall@5 por documento, Context Precision, trechos irrelevantes) contava para a decisão de manter ou reverter, mesmo quando melhorava.** As quatro etapas abaixo já foram revertidas (commits `c870c1b`, `c482fda`, `c145b04`, `da0bac5`); os números aqui vêm de reaplicar cada mudança isoladamente sobre a mesma base (Etapa 0.5) só para esta comparação, sem reabrir nenhuma decisão de reversão.

**Gabarito v1:**

| Etapa | Recall@5 doc | Hit@5 doc | MRR@5 doc | Recall@5 página | Hit@5 página | MRR@5 página | CP@5 doc | Irrelevantes (média) | Intruso principal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **Base (Etapa 0.5)** | 93,75% | 93,75% | 0,8177 | 87,5% | 87,5% | 0,7083 | 33,75% | 3,3125 | `guia_negociacao_coletiva` (17) |
| Etapa 1 (ruído) | 93,75% | 93,75% | 0,8094 | 87,5% | 87,5% | 0,6969 | 31,25% | 3,4375 | `guia_negociacao_coletiva` (19) |
| Etapa 2 (tabelas) | 93,75% | 93,75% | 0,8125 | 87,5% | 87,5% | 0,7031 | 33,75% | 3,3125 | `guia_negociacao_coletiva` (17) |
| Etapa 3 (contexto no embedding) | 90,625% | 93,75% | 0,6271 | 81,25% | 81,25% | 0,5906 | 32,5% | 3,375 | `guia_negociacao_coletiva` (13) |
| Etapa 4 (limite por documento) | 93,75% | 93,75% | 0,8177 | 81,25% | 81,25% | 0,6927 | 28,75% | 3,5625 | `guia_negociacao_coletiva` (15) |

**Gabarito v2 (mesmo índice/retrieval de cada etapa; só o gabarito muda):**

| Etapa | Recall@5 doc | Hit@5 doc | MRR@5 doc | Recall@5 página | Hit@5 página | MRR@5 página | CP@5 doc | Irrelevantes (média) | Intruso principal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **Base (Etapa 0.5)** | 93,75% | 93,75% | 0,8229 | 93,75% | 93,75% | 0,7344 | 37,5% | 3,125 | `guia_negociacao_coletiva` (16) |
| Etapa 1 (ruído) | 93,75% | 93,75% | 0,8281 | 93,75% | 93,75% | 0,7365 | 35% | 3,25 | `guia_negociacao_coletiva` (18) |
| Etapa 2 (tabelas) | 93,75% | 93,75% | 0,8177 | 93,75% | 93,75% | 0,7292 | 37,5% | 3,125 | `guia_negociacao_coletiva` (16) |
| Etapa 3 (contexto no embedding) | 90,625% | 93,75% | 0,6771 | 87,5% | 87,5% | 0,6063 | 35% | 3,25 | `guia_negociacao_coletiva` (13) |
| Etapa 4 (limite por documento) | 93,75% | 93,75% | 0,8229 | 87,5% | 87,5% | 0,7188 | 32,5% | 3,375 | `guia_negociacao_coletiva` (14) |

**Delta vs. base (gabarito v1, critério de reversão) e perguntas que mudaram de posição — doc ou página, para cima ou para baixo — das 16 originais:**

| Etapa | Δ Recall@5 página | Δ MRR@5 página | Perguntas que mudaram | Quantas |
| --- | ---: | ---: | --- | ---: |
| Etapa 1 | 0 pp | −0,0114 | `q01`↓, `q02`↑, `q05`↓, `q10`↓, `q18`↓ | 5 |
| Etapa 2 | 0 pp | −0,0052 | `q18`↓ | 1 |
| Etapa 3 | **−6,25 pp** | **−0,1177** | `q01`↑, `q02`↓(perde a página), `q03`↓, `q07`↓, `q08`↓, `q18`↑ | 6 |
| Etapa 4 | **−6,25 pp** | −0,0156 | `q01`↓(perde a página) | 1 |

**Explicação provável por etapa:**

- **Etapa 1 (ruído):** a resegmentação por página mudou os limites de chunk de `cartilha_igualdade_salarial` (`q01`, `q02`, `q05`, `q10`) e `lei_14611_2023` (`q18`) mesmo sem remover conteúdo relevante nelas — um efeito-ruído da resegmentação em si. Uma melhora (`q02`) não compensou quatro pioras.
- **Etapa 2 (tabelas):** só `q18` mudou, e nenhuma tabela aparece entre os 5 chunks recuperados nesse caso — hipótese: os 74 chunks de tabela novos mudaram as estatísticas de IDF do BM25 para todo o corpus, o suficiente para reordenar um empate próximo nessa única pergunta.
- **Etapa 3 (contexto no embedding):** a regressão mais ampla das quatro — 6 perguntas mudaram, 4 pioraram (`q02` perdeu a página por completo) contra só 2 melhoras. Um cabeçalho fixo repetido (quase idêntico) em todo chunk do mesmo documento dilui o sinal semântico do trecho no embedding denso de um modelo pequeno (MiniLM multilíngue).
- **Etapa 4 (limite por documento):** só `q01` mudou, mas a perda foi total (recall de página 1,0 → 0,0) — o limite de 2 chunks por documento descartou justamente o chunk da página certa, porque `cartilha_igualdade_salarial` (o próprio documento relevante) tinha 3+ chunks bem ranqueados e o da página certa não estava entre os 2 primeiros.

**Leitura agregada:** em nenhuma etapa o gabarito v2 piorou em relação ao v1 correspondente (confirma de novo a invariante de design da Etapa 0.5), e a ordem de severidade da regressão de MRR@5 por página é a mesma nos dois gabaritos (Etapa 3 > Etapa 4 > Etapa 1 > Etapa 2); por Recall@5 de página, Etapas 3 e 4 empatam como as duas únicas com queda (−6,25 pp cada). Isso sustenta que as regressões são do retrieval/chunking em si, não um artefato do gabarito usado para medir.

## Medição final

### `main` × esta branch (recomendação: Etapa 0.5, gabarito v2 — nenhuma das Etapas 1-4 sobreviveu)

Como nenhuma das quatro etapas de chunking/retrieval tentadas sobreviveu ao critério de reversão, o índice e o código de recuperação desta branch são **idênticos aos de `main`** no PR anterior; a única mudança real é o gabarito (`additional_evidence`, `--gold v2`) e a documentação/diagnóstico. A tabela "Comparação justa" (Etapa 0 acima) já é, portanto, `main` (v1, única opção ali) contra esta branch (v1); a tabela abaixo acrescenta a leitura v2, que é a recomendação final:

| Métrica (top 5), 16 originais | `main` (v1) | Esta branch (v2) |
| --- | ---: | ---: |
| Recall@5 documento | 93,75% | 93,75% |
| MRR@5 documento | 0,8177 | 0,8229 |
| Recall@5 página | 87,5% | **93,75%** |
| MRR@5 página | 0,7083 | **0,7344** |
| Context Precision@5 (documento) | 33,75% | 37,5% |

### Holdout (16 perguntas), medido uma única vez — já registrado na Etapa 0.5, não remedido aqui

| Conjunto | Recall@5 doc | MRR@5 doc | Recall@5 página | MRR@5 página |
| --- | ---: | ---: | ---: | ---: |
| Holdout, v1 | 87,5% | 0,5302 | 78,13% | 0,4469 |
| Holdout, v2 | **90,63%** | **0,5615** | **84,38%** | **0,5094** |

### Quanto da queda (5→20 fontes) era medição e quanto era busca

Da queda de MRR@5 por página nas 16 perguntas originais ao ir de 5 para 20 fontes (0,8021 → 0,7083, -11,7%), corrigir só o gabarito para contar evidência alternativa válida (`--gold v2`, sem tocar em busca ou chunking) recupera 0,0261 — **28% da queda**. Os 72% restantes (0,0677; o MRR com v2 ainda fica em 0,7344, abaixo do 0,8021 original) são recuperação real: mais fontes tematicamente próximas competindo pelo top 5, não um artefato de medição. As quatro tentativas de fechar essa diferença nesta branch (ruído, tabelas, contexto no embedding, limite por documento) pioraram a métrica de página em vez de recuperá-la e foram todas revertidas — a recomendação é manter a base de 20 fontes com gabarito v2, sem mudança de chunking/retrieval nesta entrega.

### Distribuição de distância (sugestão de `--max-distance`, não ativada)

Distância cosseno dos 5 chunks recuperados por pergunta (original + desenvolvimento, 27 casos verificados), separando chunks relevantes dos irrelevantes:

| Grupo | n | mín | p25 | mediana | p75 | máx |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Relevantes | 58 | 0,1417 | 0,2746 | 0,3205 | 0,3648 | 0,5961 |
| Irrelevantes | 77 | 0,1636 | 0,2773 | 0,3197 | 0,3747 | 0,6936 |

**As duas distribuições se sobrepõem quase totalmente (mediana e p25/p75 praticamente iguais)** — não há um limiar que separe relevante de irrelevante sem também descartar recuperações corretas. Um corte em `--max-distance 0,65` filtraria só os casos mais extremos de irrelevância (distâncias de até 0,6936) sem tocar em nenhuma distância relevante observada (máximo 0,5961), mas o ganho esperado é pequeno dado a sobreposição. **Sugestão registrada, não ativada**: o valor-padrão permanece sem corte; ativar um `--max-distance` mais agressivo exigiria uma base mais diversificada para calibrar sem arriscar recall, como já apontado nas pendências abaixo.

### Verificação de fidelidade com LLM real (demo oficial, versão recomendada)

Não repetida nesta sessão: como a versão recomendada (Etapa 0.5, gabarito v2) tem exatamente o mesmo índice/código de recuperação e geração já aceitos na rodada oficial do PR anterior (nenhuma das Etapas 1-4 mudou `src/query.py`'s `generate`/`validate_citations`, que não foram tocados nesta branch), a rodada de demo já registrada em `docs/validation_report.md` (seção da Etapa anterior, modelo `gemini-3.5-flash-lite`, 3/5 respondidas) permanece válida como a verificação de fidelidade mais recente. O erro de atribuição DIEESE p.12/p.13 mencionado ali não foi reavaliado nesta branch porque nenhuma mudança de chunking sobreviveu que pudesse tê-lo corrigido.

## Pendências restantes

- Diagnosticar externamente a causa dos resets no Planalto; alternativas institucionais resolvem a coleta, não esse acesso. Reconfirmado em 08/11/2026 com 3 User-Agents honestos (nenhum contornando bloqueio): reset de conexão em todos os casos.
- Revisão humana independente de todos os gabaritos, e revisão jurídica específica de q17/versões das normas.
- Corrigir reconstrução de PDFs e bordas de chunks somente com validação editorial e novas comparações; sinais atuais são preservados e reportados. Inclui a codificação de fonte customizada do PDF do INEP (números/legendas corrompidos) e o tratamento de tabelas (INEP/IBGE/ONU Mulheres), planejados para `feat/chunking-tabelas`.
- Validar LLM real, completude de evidências, fidelidade, abstenção e resistência a injection. Métricas atuais não resolvem esses pontos.
- Construir conjunto independente e mais diversificado antes de generalizar a melhora de recuperação ou calibrar limiar de distância.
- Reavaliar o desbalanceamento do índice (INEP 36,7%, ONU Mulheres 19,6%) após o tratamento de tabelas na branch `feat/chunking-tabelas`.
- Filtragem de ruído no chunking tentada e revertida (ver Etapa 1 acima): piorou MRR@5 por página nas 16 originais por efeito de resegmentação, não por conteúdo removido. Uma abordagem mais conservadora (ex.: só remover linhas idênticas em 100% das páginas, sem alterar a segmentação do restante do texto) pode merecer nova tentativa em PR futuro, com a mesma medição caso a caso.
- Avaliar a Sinopse Estatística oficial do Censo da Educação Superior em planilha (zip de 397 MB, `download.inep.gov.br/informacoes_estatisticas/sinopses_estatisticas/sinopses_educacao_superior/sinopse_educacao_superior_2024.zip`) como fonte numericamente mais confiável para perguntas estatísticas sobre o censo.
- Nova tentativa de geração guiada pelo motivo do validador: ao receber `CitationValidationError`, tentar novamente (1 retry) devolvendo ao modelo a mensagem exata do validador (ex.: "LLM answer contains an uncited paragraph: remova ou cite esse parágrafo"), em vez de bloquear direto. Sem afrouxar `validate_citations`. Não implementado nesta sessão; precisa de aprovação antes.
- Decodificar o deslocamento de código de caractere (-5) em `diretrizes_planos_acao`, em PR próprio: identificar os spans afetados pelo nome da fonte defeituosa em `page.get_text("dict")` (não por heurística de texto), revisar a evidência das páginas afetadas e atualizar os hashes do gabarito com registro — não feito nesta branch porque mudaria `content`/`content_hash` e o gabarito de `q23`.
- Revisar o enunciado de `h09` (mistura MTE/empresas/meses), identificado na Etapa 0.5 mas não alterado.
