# Supabase — memory store (S1 draft, manual setup)

**Estado:** DRAFT (S1). `schema.sql` **não aplicado** a nenhum projeto remoto. **Sem conexão real, sem migração de dados.** Ver `docs/architecture/SUPABASE_IMPLEMENTATION_PLAN.md`.

## O que é
Store estruturado de **memória/índice** do Agentic OS (não fonte de verdade). RAW/source continua a autoridade; Supabase indexa/deriva e recupera *slices*. Nunca valida backtest sozinho.

## Ficheiros
- `schema.sql` — 12 tabelas (memory_items, decisions, artifacts, agent_runs, safety_reports, external_factor_events, market_context_snapshots, trade_journal_events, episode_context_links, source_registry, retrieval_queries; memory_embeddings opcional/pgvector).
- este README.

## Setup manual (quando autorizado — S2)
1. **Local primeiro** (recomendado): `supabase init` + `supabase start` (Docker) → aplicar `schema.sql` no Postgres local.
   ```bash
   psql "$SUPABASE_DB_URL" -f supabase/schema.sql
   ```
2. Definir vars em `.env` (NUNCA no repo — `.env` é gitignored):
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `SUPABASE_ENV=local|dev|prod`.
3. **pgvector (opcional):** só se usar busca semântica → descomentar `create extension vector;` + a tabela `memory_embeddings` + escolher dimensão do modelo.
4. **RLS:** aplicar em **dev primeiro** (bloco comentado no fim do `schema.sql`); product-memory leitura ampla, private-memory só `service_role`.

## Regras de segurança (obrigatórias)
- **Secrets nunca no repo.** Só `.env` (gitignored). `SUPABASE_SERVICE_ROLE_KEY` **nunca** em client-side/commits.
- Não guardar broker credentials, API keys, nem TradingView restricted market data para redistribuição.
- `scope`/`visibility` separam **product memory** de **private alpha**.
- Derivados carregam `source_ref` + timestamp/causal boundary + `artifact_ref`/checksum.

## O que NÃO fazer nesta fase (S1)
Conectar a Supabase real · rodar migrations remotas · usar service role key · migrar MEMORY.md/RAW/candles/backtests/logs vivos · tocar runtime/daemon/produção.

## Próximo (S2, só sob autorização)
Setup local/manual + aplicar schema em local/dev + scripts de ingestão mínimos (memory_items/decisions/artifacts) lendo pointers, nunca RAW massivo.
