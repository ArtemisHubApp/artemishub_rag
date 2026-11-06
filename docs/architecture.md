# Arquitetura do RAG Artemis

A arquitetura modular mantém a separação entre preparação offline e consulta online.

## Preparação e publicação

1. `config/sources.json` define fontes públicas, formatos e marcadores esperados.
2. `ingest.collect` coleta todas as fontes habilitadas e registra cada tentativa. Alternativas oficiais são explícitas no manifesto; URL primária, URL utilizada, editor e versão ficam nos metadados. Downloads têm timeout, retry com backoff, limite de bytes e validação de redirecionamentos. Bloqueios não são contornados. As representações baixadas são arquivadas por hash.
3. A extração produz uma seção por página PDF ou documento HTML. `document_id` agrupa páginas da mesma fonte; página/artigo são os localizadores. A CLT recebe recorte específico do artigo 461.
4. `quality.validate_documents` confere campos, hashes e locadores. `prepare` produz chunks determinísticos de até 600 caracteres, com sobreposição de 100; `quality.validate_chunks` verifica tamanho, referências e integridade. Os parâmetros anteriores (1200/180) continuam disponíveis no CLI para comparação.
5. `eda.analyze` gera perfil JSON do dataset e da cobertura das fontes, sinalizando repetições, ligaturas, controles, linhas numéricas e possíveis palavras cortadas. Os alertas não removem texto.
6. `index.build_index` prepara uma nova coleção Chroma, copiando embeddings existentes e calculando somente os necessários. Novos registros e metadados são gravados nessa coleção, sem modificar a coleção ativa.
7. Após conferir contagem/IDs e escrever os snapshots, um rename atômico publica o ponteiro. A publicação completa usa `.chroma/active.json`; diagnósticos usam `.chroma/partial.json`. Uma execução parcial nunca troca o ponteiro completo. Coleções antigas são preservadas.
8. `data/processed/*.jsonl` são exports para inspeção. Consultas usam a coleção publicada; avaliação confere referências contra os documentos do snapshot dessa mesma versão.

O lock de escritor limita a publicação a um processo por diretório. Snapshots e coleções antigas exigem gestão manual de espaço; interrupção abrupta pode deixar lock ou staging órfão. A estratégia garante preservação lógica do índice anterior em falhas tratadas, sem prometer recuperação de falha física de disco.

## Recuperação e geração

`query.Retriever` fixa uma coleção publicada durante sua vida útil e carrega o mesmo modelo/revisão da indexação. O padrão `hybrid` combina até 20 candidatos vetoriais e 20 BM25 para top-5, por Reciprocal Rank Fusion (constante 60), priorizando uma evidência por página/seção antes de repetir páginas. BM25 usa k1=1,5 e b=0,75, sem modelo adicional. Corpus lexical e modelo são reutilizados dentro do processo. As estratégias `dense` e `pages` preservam as comparações vetoriais. O limiar de distância é opcional, aplica-se também aos candidatos lexicais e ainda precisa de calibração. A escolha se baseia nas comparações registradas no relatório, sem garantia de generalização.

`query.generate` envia contexto JSON com IDs, URLs, páginas, artigo e proveniência/versão a um endpoint HTTPS compatível com Chat Completions. O prompt restringe o uso das fontes, diferencia versão de vigência e trata documentos como conteúdo não confiável. A validação rejeita IDs inexistentes/malformados e parágrafos sem citação, mas não verifica entailment semântico. Sem credenciais, a consulta mostra apenas evidências; sem hits, retorna abstenção sem chamar o LLM.

## Avaliação

`evaluate` calcula métricas por documento e por página/seção esperada sobre os cinco chunks recuperados. A ausência de página HTML é normalizada entre `null` no JSONL e string vazia no Chroma. Referências conferidas têm hashes; alterações as excluem até nova revisão. Casos sem resposta e pendentes ficam separados e não entram no Recall. O corpus e o conjunto inicial são pequenos, sem validação humana independente; métricas altas não comprovam recuperação integral de um artigo nem qualidade de geração. Consulte [validation_report.md](validation_report.md) e [rag_usage.md](rag_usage.md).

Autenticação, currículos, vagas, RAIS/CAGED, agentes e reranking por modelo adicional permanecem fora deste MVP.
