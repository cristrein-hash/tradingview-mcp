# SUPABASE IMPLEMENTATION PLAN (S1)

**Data:** 2026-07-02 · **Estado:** S1 = schema draft + boundary docs. **Sem conexão real, sem migração, sem runtime tocado.**
**Base:** `SUPABASE_MEMORY_DATA_ARCHITECTURE.md` (design aprovado). Artefactos: `supabase/schema.sql`, `supabase/README.md`, `.env.example`.

## 1. Objetivo
Transformar o design aprovado numa base técnica **mínima e versionada** (schema + docs), sem depender dela em produção. Resolver persistência/recuperação estruturada de contexto antes de abrir nova pesquisa (XAU 15M / SHORT geram muito estado).

## 2. Escopo S1 / S2
- **S1 (este bloco):** `schema.sql` draft (12 tabelas) + `supabase/README.md` + `.env.example` vars + este plano. Nada aplicado remotamente.
- **S2 (futuro, sob autorização):** setup local/manual (`supabase start` Docker), aplicar schema em local/dev, scripts de ingestão mínimos (memory_items/decisions/artifacts) lendo **pointers**, RLS em dev.

## 3. O que fica FORA (S1)
Conexão a Supabase real · migrations remotas · service role key · criar tabelas em produção · migrar MEMORY.md/RAW/candles/backtests/logs vivos · alterar daemon/EF v2/MCP/produção/Telegram/strategy runtime · backtest · XAU 15M · XAU SHORT.

## 4. Tabelas (ver `supabase/schema.sql`)
`memory_items` · `memory_embeddings` (opcional/pgvector) · `decisions` · `artifacts` · `agent_runs` · `safety_reports` · `external_factor_events` · `market_context_snapshots` · `trade_journal_events` · `episode_context_links` · `source_registry` · `retrieval_queries`.

## 5. Product / private boundary
- **Product memory** (`scope='product'`): docs/templates, safety_reports, agent_runs do engine, external_factor_events (schema normalizado), source_registry genérico.
- **Private alpha** (`scope='private'`): trade_journal_events, estratégias/decisões de edge, market_context_snapshots privados, RTSE/research links.
- `scope`+`visibility` em `memory_items`; RLS separa leitura (product ampla, private só service_role).

## 6. Security / RLS / secrets
- Secrets só em `.env` (gitignored): `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `SUPABASE_ENV`.
- **`SUPABASE_SERVICE_ROLE_KEY` nunca** em client/commits; separação anon vs service role.
- RLS por tabela (plano SQL comentado no fim do `schema.sql`), aplicado **em dev primeiro**.
- Backup/restore + retenção + audit log = definir em S2+.

## 7. Ingestão futura (S2+)
Scripts idempotentes que registam **pointers + checksums**, não conteúdo RAW: docs/decisões/checkpoints → `memory_items`/`decisions`/`artifacts`; safety report → `safety_reports`; EF snapshots → `external_factor_events`; rulers/RAW → `source_registry` (só ponteiro+checksum). **Nunca ingerir RAW massivo.**

## 8. Retrieval futuro (S2+)
`get_market_context(symbol,timeframe,bars)` → resumo estruturado pequeno + pointers (não candles); busca semântica via `memory_embeddings` (se pgvector); todo retorno cita `source_ref` + permite drill-down. Log em `retrieval_queries`. Limite de tokens por retorno.

## 9. Não-migração de RAW
RAW/source (`/Volumes/GUTS_ LACIE/TradingData`, rulers) **continua fonte de verdade no disco**. Supabase só guarda ponteiros+checksums (`source_registry`) e derivados com `source_ref`. Supabase **não valida backtest** sozinho.

## 10. Fases seguintes
S1 (feito: schema+docs) → S2 (local/manual + aplicar em dev) → S3 (ingest MVP memory_items/decisions/artifacts) → S4 (source_registry+agent_runs) → S5 (external_factor_events) → S6 (market_context_snapshots) → S7 (retrieval tools/MCP read-only) → S8 (integração Agentic OS).

## 11. Riscos
- Supabase virar de-facto validador → mitigado: só pointers/checksums, todo record liga a RAW; nenhum script de validação lê edge do Supabase.
- Leak de secrets → `.env` gitignored, service role fora do repo.
- Dependência externa no hot path → tudo degrada gracioso sem `SUPABASE_URL`.
- pgvector indisponível → embeddings opcionais/comentados; core aplica sem vector.

## 12. Rollback
S1 é aditivo/doc+SQL: rollback = `rm -rf supabase/` + apagar este doc + reverter `.env.example`. Nenhum runtime/produção afetado (nada aplicado remotamente).
