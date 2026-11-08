# Base de conhecimento do RAG Artemis

A base tem **20 fontes ativas** (245 documentos, 1209 chunks), cumprindo o mínimo de 20 documentos-fonte do Segundo Desafio. `config/sources.json` também mantém **3 candidatas desabilitadas**, com o motivo registrado em cada entrada.

Todas as candidatas vieram dos documentos de pesquisa do grupo (First Day, Pesquisa de empoderamento feminino, PDR de 30/10 e lista de Datasets) ou de busca por substitutos oficiais quando uma candidata falhava.

## Critérios de curadoria

Uma fonte entra na base quando atende a todos os critérios abaixo:

1. **Origem identificável:** órgão público, organismo internacional ou instituição de pesquisa reconhecida. Relatórios de uma empresa só (por exemplo, o relatório de transparência de um empregador específico) não entram.
2. **Texto extraível:** PDF com camada de texto ou página HTML. O `src/ingest.py` recusa páginas vazias, que exigiriam OCR — salvo exceção auditada via `known_blank_pages` (ver abaixo).
3. **Responde perguntas das personas:** direitos e igualdade salarial, negociação, desigualdade de gênero no trabalho ou oportunidades para mulheres em STEM.
4. **Documento, não base de dados:** microdados e tabelas (RAIS, CAGED, PNAD) servem ao modelo de estimativa salarial, não à busca por texto.

## Fontes ativas (20)

| id | Fonte | Órgão | Formato | Tema |
| --- | --- | --- | --- | --- |
| `lei_14611_2023` | Lei 14.611/2023 | Presidência (alternativa: Câmara) | HTML | igualdade salarial |
| `clt_art_461` | CLT, art. 461 | Presidência (alternativa: Câmara) | HTML | equiparação salarial |
| `decreto_11795_2023` | Decreto 11.795/2023 | Presidência (alternativa: Câmara) | HTML | igualdade salarial |
| `cartilha_igualdade_salarial` | Cartilha Tira-Dúvidas da Lei da Igualdade Salarial | Ministério das Mulheres e MTE | PDF | igualdade salarial |
| `estatisticas_genero_ibge` | Estatísticas de Gênero, 3ª edição | IBGE | PDF | estatísticas de gênero |
| `ot_sit_11_2024` | Orientação Técnica SIT nº 11/2024 (multa) | MTE | PDF | fiscalização e multa por descumprimento |
| `guia_negociacao_coletiva` | Guia para Negociação Coletiva da Lei de Igualdade Salarial | Ministério das Mulheres e MTE | PDF | negociação salarial (persona Juliana) |
| `diretrizes_planos_acao` | Diretrizes para os Planos de Ação para Mitigação das Desigualdades Salariais | Ministério das Mulheres | PDF | plano de ação da empresa |
| `plano_nacional_igualdade` | Plano Nacional de Igualdade Salarial e Laboral (página oficial) | Ministério das Mulheres | HTML | eixos e ações do plano |
| `relatorio_transparencia_pagina` | Relatório de Transparência Salarial (página oficial) | Ministério das Mulheres | HTML | o que é o relatório e quem precisa publicar |
| `agencia_gov_6_relatorio` | 6º Relatório de Transparência Salarial | Agência Gov / MTE | HTML | prazos do ciclo atual (notícia datada) |
| `dieese_8_marco_2026` | Boletim Especial 8 de Março de 2026 | DIEESE | PDF | rendimento de mulheres e homens por escolaridade e cargo |
| `onu_mulheres_weps` | Princípios de Empoderamento das Mulheres | ONU Mulheres e Pacto Global | PDF | boas práticas de igualdade nas organizações |
| `fgv_ibre_desigualdade_genero` | Panorama atual da desigualdade de gênero no Brasil | FGV IBRE | HTML | análise da PNAD Contínua |
| `meninas_digitais` | Programa Meninas Digitais | SBC | HTML | oportunidades e redes para mulheres na computação |
| `portaria_mte_3714_2023` | Portaria MTE nº 3.714/2023 | MTE (DOU; URL principal oficial, alternativa no Datalegis/ANTT) | PDF | procedimentos do relatório de transparência e da fiscalização |
| `inep_resumo_tecnico_censo_superior_2024` | Resumo Técnico do Censo da Educação Superior 2024 | INEP | PDF | matrículas e concluintes por sexo e área (persona Mariana) |
| `lei_9029_1995` | Lei 9.029/1995 — proibição de atestados discriminatórios no emprego | Presidência (Câmara/legin) | HTML | discriminação no emprego |
| `lei_14457_2022` | Lei 14.457/2022 — Programa Emprega + Mulheres | Presidência (Câmara/legin) | HTML | mercado de trabalho |
| `gov_mulheres_dia_ciencia_fev2026` | Dia Internacional das Mulheres e Meninas na Ciência — Ministério das Mulheres, fevereiro/2026 | Ministério das Mulheres | HTML | oportunidades STEM |

### Correções aplicadas ao ativar candidatas

- **TLS do INEP:** `download.inep.gov.br` falhava com `SSL: CERTIFICATE_VERIFY_FAILED` no bundle certifi padrão; `src/ingest.py` agora injeta o trust store do sistema (`truststore.inject_into_ssl()`) para validar o certificado corretamente — não é bypass de verificação, é usar outra fonte de CAs confiáveis.
- **`known_blank_pages` (novo mecanismo):** o PDF do INEP tem a página 108 (última) genuinamente vazia (0 caracteres, 0 imagens, confirmado manualmente). Um campo opcional por fonte permite declarar páginas sabidamente vazias; elas só são descartadas (não indexadas) se estiverem de fato vazias — se a página declarada tiver texto, ou outra página vier vazia sem estar declarada, a fonte continua falhando. Ver `tests/test_ingest.py`.
- **URL do `cartilha_plano_nacional` → `/@@display-file/file`:** mesmo padrão das outras publicações do gov.br; mas a fonte ficou desabilitada por outro motivo (ver abaixo).
- **`portaria_mte_3714_2023`:** URL principal trocada para o PDF oficial do DOU em gov.br/mulheres; o link do Datalegis/ANTT passou a alternativa.

### Achado de qualidade — PDF do INEP com codificação de fonte customizada

106 das 107 páginas de texto do INEP têm números e legendas de gráficos corrompidos (glyphs/caracteres de controle no lugar dos dígitos reais); o texto corrido (prosa) extrai limpo na maioria das páginas. Isso não impediu a ativação (os marcadores `expected_text` são textuais), mas é relevante para perguntas que dependam de números específicos do censo. Ver `docs/validation_metrics.json` → `expansion_20_sources_2026_11_08.limitations`.

## Candidatas desabilitadas (3)

| id | Fonte | Motivo |
| --- | --- | --- |
| `relatorio_final_gti` | Relatório Final do GTI de Igualdade Salarial | 404 — arquivo removido do gov.br |
| `ibge_educa_mulheres` | As mulheres do Brasil (IBGE Educa) | 403 Cloudflare; é resumo do mesmo PDF já ativo como `estatisticas_genero_ibge` — duplicata |
| `cartilha_plano_nacional` | Cartilha Rumo à Construção do Plano Nacional | páginas 1 e 9 sem texto extraível (imagem/capa); pipeline exige todas as páginas com texto e não há exceção declarada para este caso |

## Testado e descartado (não chegou a entrar em `config/sources.json`)

| URL | Motivo |
| --- | --- |
| `gov.br/trabalho-e-emprego/.../3o-relatorio-de-transparencia-salarial...` | 403 Forbidden mesmo com o User-Agent legítimo da app — WAF bloqueando o caminho |
| `gov.br/mcti/.../mcti-promove-diversidade-de-genero-na-ciencia...` | 403 Forbidden, mesmo motivo |
| `gov.br/secom/...` (2 notícias testadas) | 403 Forbidden |
| `gov.br/mulheres/.../emprego-feminino-avanca-e-politicas...` | 401, inconsistente com outras páginas do mesmo domínio |
| `senado.leg.br/noticias/materias/...` (2 notícias testadas) | retorna 200, mas o extrator genérico captura só um banner de notificação, não o corpo da matéria; precisaria de `html_selector` dedicado, não investigado |
| Planalto (`l14611.htm`, `del5452.htm`, `D11795.htm`) | reconfirmado em 08/11/2026 com 3 User-Agents honestos (padrão do curl incluso): reset de conexão em todos os casos, antes de qualquer resposta HTTP. Mantidas as alternativas da Câmara dos Deputados como fonte principal |

## Fora do RAG

| Fonte | Motivo | Onde usar |
| --- | --- | --- |
| RAIS, Novo CAGED, PNAD Contínua, microdados do Censo da Educação Superior (.zip) | tabelas, não texto | modelo de estimativa salarial |
| CBO, ESCO, O*NET | bases estruturadas de ocupações e competências | agente de competências |
| Kaggle e Hugging Face (Glassdoor, State of Data, currículos) | datasets de terceiros | experimentos de ML |
| Google Acadêmico, SciELO, Portal CAPES | portais de busca | revisão bibliográfica |
| Relatórios de empresas (Mahle, Deutsche Bank) | dados de um empregador só | exemplo de crítica à metodologia, não evidência geral |
| Artigos da HBR, NBER, Yale | em inglês e alguns com paywall | justificativa do problema |

## Como ativar uma nova candidata

1. Em `config/sources.json`, adicione a entrada com `"enabled": true` e confira se `expected_text` aparece no documento.
2. Rode `uv run python -m src.pipeline --skip-index`. Isso coleta e valida tudo sem gerar embeddings. Se uma fonte falhar (marcador ausente, página sem texto, link quebrado), a pipeline aponta qual foi em `reports/latest_run.json`.
3. Se a única falha for uma página sabidamente vazia (confirme com PyMuPDF: 0 caracteres e 0 imagens), declare-a em `known_blank_pages` em vez de descartar a fonte.
4. Rode `uv run python -m src.pipeline` para publicar o novo índice. O índice anterior continua preservado.
5. Acrescente perguntas sobre as fontes novas em `evaluation/questions.jsonl` (desenvolvimento) e rode `uv run python -m src.evaluate`. O holdout só deve ser usado para medir a versão final.
6. Confira em `reports/eda.json` se o documento novo passa a dominar o índice — hoje o INEP ocupa 36,7% dos 1209 chunks. O tratamento de tabelas para reequilibrar isso é tratado em uma branch separada (`feat/chunking-tabelas`), não nesta entrega.
7. Confira também a Context Precision@5 (`src/evaluate.py`, campo `context_precision_metrics`): mede quantos dos 5 trechos recuperados são de documentos realmente relevantes, não só o volume do índice. Na expansão para 20 fontes, quem mais "invade" o top 5 de perguntas que não são sobre ele é `guia_negociacao_coletiva` (vocabulário muito próximo do tema central), não o INEP — vale conferir de novo depois de ativar qualquer fonte nova.
