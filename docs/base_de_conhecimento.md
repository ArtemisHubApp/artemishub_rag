# Base de conhecimento do RAG Artemis

A base hoje tem **5 fontes ativas** (33 seções, 221 chunks). A entrega do Segundo Desafio pede **no mínimo 20 documentos-fonte**, então este documento lista as fontes ativas, as **15 candidatas já cadastradas** em [`config/sources.json`](../config/sources.json) com `"enabled": false` e 1 opcional que ainda precisa de link oficial. Com as 15 candidatas, a base chega a 20 fontes.

Todas as candidatas vieram dos documentos de pesquisa do grupo (First Day, Pesquisa de empoderamento feminino, PDR de 30/10 e lista de Datasets).

## Critérios de curadoria

Uma fonte entra na base quando atende a todos os critérios abaixo:

1. **Origem identificável:** órgão público, organismo internacional ou instituição de pesquisa reconhecida. Relatórios de uma empresa só (por exemplo, o relatório de transparência de um empregador específico) não entram.
2. **Texto extraível:** PDF com camada de texto ou página HTML. O `src/ingest.py` recusa páginas vazias, que exigiriam OCR.
3. **Responde perguntas das personas:** direitos e igualdade salarial, negociação, desigualdade de gênero no trabalho ou oportunidades para mulheres em STEM.
4. **Documento, não base de dados:** microdados e tabelas (RAIS, CAGED, PNAD) servem ao modelo de estimativa salarial, não à busca por texto.

## Fontes ativas (5)

| id | Fonte | Órgão | Formato | Tema |
| --- | --- | --- | --- | --- |
| `lei_14611_2023` | Lei 14.611/2023 | Presidência (alternativa: Câmara) | HTML | igualdade salarial |
| `clt_art_461` | CLT, art. 461 | Presidência (alternativa: Câmara) | HTML | equiparação salarial |
| `decreto_11795_2023` | Decreto 11.795/2023 | Presidência (alternativa: Câmara) | HTML | igualdade salarial |
| `cartilha_igualdade_salarial` | Cartilha Tira-Dúvidas da Lei da Igualdade Salarial | Ministério das Mulheres e MTE | PDF | igualdade salarial |
| `estatisticas_genero_ibge` | Estatísticas de Gênero, 3ª edição | IBGE | PDF | estatísticas de gênero |

## Candidatas cadastradas e desabilitadas (15)

### Prioridade 1: oficiais e direto no tema (11)

| id | Fonte | Órgão | Formato | Para que serve |
| --- | --- | --- | --- | --- |
| `ot_sit_11_2024` | [Orientação Técnica SIT nº 11/2024](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/legislacao/SITn11de2024multacritriosremuneratrios.pdf) | MTE | PDF | como a fiscalização aplica a multa; cobre a lacuna de perguntas sobre punições |
| `guia_negociacao_coletiva` | [Guia para Negociação Coletiva da Lei de Igualdade Salarial](https://www.gov.br/mulheres/pt-br/central-de-conteudos/publicacoes/guia-para-negociacao-coletiva-da-lei-de-igualdade-salarial_defeso.pdf/@@display-file/file) | Ministério das Mulheres e MTE | PDF | negociação salarial (persona Juliana) |
| `diretrizes_planos_acao` | [Diretrizes para os Planos de Ação para Mitigação das Desigualdades Salariais](https://www.gov.br/mulheres/pt-br/central-de-conteudos/publicacoes/diretrizes-para-os-planos-de-acao-para-mitigacao-das-desigualdades-salariais_defeso.pdf/@@display-file/file) | Ministério das Mulheres | PDF | o que a empresa precisa fazer quando há desigualdade |
| `relatorio_final_gti` | [Relatório Final do GTI de Igualdade Salarial](https://www.gov.br/mulheres/pt-br/acesso-a-informacao/acoes-e-programas/plano-nacional-de-igualdade-salarial-e-laboral/copy_of_RelatrioFinalGTIIgualdadeSalarial1.pdf) | Ministério das Mulheres | PDF | diagnóstico e base do Plano Nacional |
| `cartilha_plano_nacional` | [Cartilha Rumo à Construção do Plano Nacional](https://www.gov.br/mulheres/pt-br/central-de-conteudos/publicacoes/cartilha-rumo-a-construcao-do-plano-nacional-de-igualdade-salarial-e-laboral-entre-mulheres-e-homens.pdf) | Ministério das Mulheres | PDF | política pública em linguagem acessível |
| `plano_nacional_igualdade` | [Plano Nacional de Igualdade Salarial e Laboral](https://www.gov.br/mulheres/pt-br/acesso-a-informacao/acoes-e-programas/plano-nacional-de-igualdade-salarial-e-laboral) | Ministério das Mulheres | HTML | eixos e ações do plano |
| `relatorio_transparencia_pagina` | [Relatório de Transparência Salarial](https://www.gov.br/mulheres/pt-br/acesso-a-informacao/acoes-e-programas/plano-nacional-de-igualdade-salarial-e-laboral/relatorio-de-transparencia-salarial) | Ministério das Mulheres | HTML | o que é o relatório e quem precisa publicar |
| `agencia_gov_6_relatorio` | [6º Relatório de Transparência Salarial](https://agenciagov.ebc.com.br/noticias/202608/empresas-com-100-ou-mais-empregados-devem-atualizar-informacoes-para-o-6o-relatorio-de-transparencia-salarial) | Agência Gov / MTE | HTML | prazos do ciclo atual (notícia datada) |
| `dieese_8_marco_2026` | [Boletim Especial 8 de Março de 2026](https://www.dieese.org.br/boletimespecial/2026/2026mulher.pdf) | DIEESE | PDF | rendimento de mulheres e homens por escolaridade e cargo (PNAD Contínua) |
| `portaria_mte_3714_2023` | [Portaria MTE nº 3.714/2023](https://anttlegis.antt.gov.br/action/ActionDatalegis.php?acao=detalharAto&tipo=POR&numeroAto=00003714&seqAto=000&valorAno=2023&orgao=MTE&nomeTitulo=codigos&cod_modulo=420&cod_menu=7145) | MTE (texto no Datalegis/ANTT; D.O.U. de 27/11/2023, seção 1) | HTML | procedimentos do relatório de transparência e da fiscalização |
| `onu_mulheres_weps` | [Princípios de Empoderamento das Mulheres](https://www.onumulheres.org.br/wp-content/uploads/2016/04/cartilha_ONU_Mulheres_Nov2017_digital.pdf) | ONU Mulheres e Pacto Global | PDF | boas práticas de igualdade nas organizações |

### Prioridade 2: contexto de carreira e STEM (4)

| id | Fonte | Órgão | Formato | Para que serve |
| --- | --- | --- | --- | --- |
| `ibge_educa_mulheres` | [As mulheres do Brasil](https://educa.ibge.gov.br/jovens/materias-especiais/22052-as-mulheres-do-brasil.html) | IBGE Educa | HTML | estatísticas em linguagem simples |
| `fgv_ibre_desigualdade_genero` | [Panorama atual da desigualdade de gênero no Brasil](https://blogdoibre.fgv.br/posts/panorama-atual-da-desigualdade-de-genero-no-brasil-uma-analise-partir-da-pnadc-e-da-smt) | FGV IBRE | HTML | análise da PNAD Contínua |
| `inep_resumo_tecnico_censo_superior_2024` | [Resumo Técnico do Censo da Educação Superior 2024](https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_superior/resumo_tecnico_do_censo_da_educacao_superior_2024.pdf) | INEP | PDF | matrículas e concluintes por sexo e área (persona Mariana); documento longo, conferir o peso no índice |
| `meninas_digitais` | [Programa Meninas Digitais](https://meninasdigitais.com.br/sobre-nos/) | SBC | HTML | oportunidades e redes para mulheres na computação (persona Mariana) |

## Opcional, pendente de link oficial (1)

| Fonte | Situação |
| --- | --- |
| UNESCO, *Cracking the Code: Girls' and Women's Education in STEM* (2017) | o link do grupo ([unesdoc](https://unesdoc.unesco.org/ark:/48223/pf0000253479)) é a página do catálogo; copiar dali a URL direta do PDF, sempre do domínio da UNESCO. Documento em inglês, mas o modelo de embeddings é multilíngue. Não é necessária para chegar a 20 fontes |

## Fora do RAG

| Fonte | Motivo | Onde usar |
| --- | --- | --- |
| RAIS, Novo CAGED, PNAD Contínua, microdados do Censo da Educação Superior (.zip) | tabelas, não texto | modelo de estimativa salarial |
| CBO, ESCO, O*NET | bases estruturadas de ocupações e competências | agente de competências |
| Kaggle e Hugging Face (Glassdoor, State of Data, currículos) | datasets de terceiros | experimentos de ML |
| Google Acadêmico, SciELO, Portal CAPES | portais de busca | revisão bibliográfica |
| Relatórios de empresas (Mahle, Deutsche Bank) | dados de um empregador só | exemplo de crítica à metodologia, não evidência geral |
| Artigos da HBR, NBER, Yale | em inglês e alguns com paywall | justificativa do problema |

## Como ativar uma candidata

1. Em `config/sources.json`, troque `"enabled": false` para `true` e confira se `expected_text` aparece no documento. Os marcadores das candidatas foram definidos pelo título e ainda não foram testados.
2. Rode `uv run python -m src.pipeline --skip-index`. Isso coleta e valida tudo sem gerar embeddings. Se uma fonte falhar (marcador ausente, página sem texto, link quebrado), a pipeline aponta qual foi em `reports/latest_run.json`.
3. Rode `uv run python -m src.pipeline` para publicar o novo índice. O índice anterior continua preservado.
4. Acrescente perguntas sobre as fontes novas em `evaluation/questions.jsonl` (desenvolvimento) e rode `uv run python -m src.evaluate`. O holdout só deve ser usado para medir a versão final.

Ativar fontes muda a proporção da base: hoje o IBGE gera 68% dos chunks. Vale conferir em `reports/eda.json` se algum documento novo passa a dominar o índice.
