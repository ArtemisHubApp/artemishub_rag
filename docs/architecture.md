# Arquitetura MVP

## Decisão
RAG modular, com pipeline offline de ingestão/indexação e pipeline online de recuperação/geração.

## Fluxo
`config/sources.json` → `src.ingest` → `documents.jsonl` → `src.prepare` → `chunks.jsonl` → `src.index` (SentenceTransformers + Chroma) → `src.query` (Top-k + LLM opcional).

## Justificativa
Separar preparação, indexação e consulta facilita testes, rastreabilidade e substituição de componentes. A busca híbrida será considerada apenas após medir a recuperação vetorial.

## Fora do escopo do MVP
Consultas numéricas a RAIS/CAGED, catálogo de vagas, análise de currículos, autenticação e agentes.
