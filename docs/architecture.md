# Arquitetura do RAG Artemis

A arquitetura modular mantém a separação entre preparação offline e consulta online.

## Preparação e publicação

1. `config/sources.json` define fontes públicas, formatos e marcadores esperados.
2. `ingest.collect` coleta todas as fontes habilitadas e registra o resultado de cada uma. Downloads têm timeout, retry com backoff, limite de bytes e validação de redirecionamentos. Bloqueios e erros permanentes não são contornados.
3. A extração produz uma seção por página PDF ou documento HTML. `document_id` agrupa páginas da mesma fonte; página/artigo são os localizadores. A CLT recebe recorte específico do artigo 461.
4. `quality.validate_documents` confere campos, hashes e locadores. `prepare` produz chunks determinísticos; `quality.validate_chunks` verifica tamanho, referências e integridade.
5. `eda.analyze` gera perfil JSON do dataset e da cobertura das fontes.
6. `index.build_index` prepara uma nova coleção Chroma, copiando embeddings existentes e calculando somente os necessários. Novos registros e metadados são gravados nessa coleção, sem modificar a coleção ativa.
7. Após conferir contagem/IDs e escrever os snapshots, um rename atômico publica o ponteiro. A publicação completa usa `.chroma/active.json`; diagnósticos usam `.chroma/partial.json`. Uma execução parcial nunca troca o ponteiro completo. Coleções antigas são preservadas.
8. `data/processed/*.jsonl` são exports para inspeção. Consultas usam a coleção publicada; avaliação confere referências contra os documentos do snapshot dessa mesma versão.

O lock de escritor limita a publicação a um processo por diretório. Snapshots e coleções antigas exigem gestão manual de espaço; interrupção abrupta pode deixar lock ou staging órfão. A estratégia garante preservação lógica do índice anterior em falhas tratadas, sem prometer recuperação de falha física de disco.

## Recuperação e geração

`query.Retriever` fixa uma coleção publicada durante sua vida útil, carrega o mesmo modelo/revisão da indexação e recupera até cinco chunks por distância cosseno. O modelo é reutilizado dentro do processo. O limiar de distância é opcional e ainda precisa de calibração.

`query.generate` envia contexto JSON com IDs, URLs e páginas a um endpoint HTTPS compatível com Chat Completions. O prompt restringe o uso das fontes e trata os documentos como conteúdo não confiável. A validação rejeita IDs inexistentes/malformados e parágrafos sem citação, mas não verifica entailment semântico. Sem credenciais, a consulta mostra apenas evidências; sem hits, retorna abstenção sem chamar o LLM.

## Avaliação

`evaluate` calcula métricas por documento e por página esperada sobre os cinco chunks recuperados. Referências conferidas têm hashes de página; alterações as excluem até nova revisão. Casos sem resposta ficam separados e não entram no Recall. O corpus e o conjunto inicial são pequenos, sem validação humana independente; métricas altas por documento devem ser lidas junto às métricas por página.

Autenticação, currículos, vagas, RAIS/CAGED, agentes, busca híbrida e reranking permanecem fora deste MVP.
