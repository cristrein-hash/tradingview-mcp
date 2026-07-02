-- ============================================================================
-- Trading System Agentic OS — Supabase memory schema (S1 DRAFT, 2026-07-02)
-- ============================================================================
-- DRAFT ONLY. Not applied to any remote project. Apply LOCAL/DEV first (see supabase/README.md).
-- Principles (see docs/architecture/SUPABASE_IMPLEMENTATION_PLAN.md):
--   * RAW/source stays the source of truth. Supabase INDEXES/DERIVES, never validates a backtest.
--   * Every derived row carries source_ref + timestamp/causal boundary + artifact_ref/checksum.
--   * No secrets, no broker credentials, no redistributable TradingView market data.
--   * scope/visibility separate PRODUCT memory from PRIVATE alpha memory.
-- ============================================================================

-- Extensions -----------------------------------------------------------------
create extension if not exists pgcrypto;   -- gen_random_uuid()
-- pgvector is OPTIONAL. Enable only if semantic search is used (memory_embeddings).
-- Supabase supports it, but keep guarded so the core schema applies without it.
-- create extension if not exists vector;

-- Enums (soft: kept as text + check to stay portable) -------------------------
-- scope:      'product' | 'private'
-- visibility: 'public' | 'internal' | 'private'
-- authority:  'source_of_truth' | 'derived' | 'index' | 'log'

-- 1. memory_items ------------------------------------------------------------
create table if not exists memory_items (
  id           uuid primary key default gen_random_uuid(),
  scope        text not null default 'private' check (scope in ('product','private')),
  visibility   text not null default 'private',
  category     text,                      -- user|feedback|project|reference|architecture|...
  title        text not null,
  body         text,
  tags         text[] default '{}',
  source_ref   text,                      -- pointer to file/commit/doc (NOT the raw content)
  status       text default 'active',     -- active|superseded|deprecated|archived
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists idx_memory_items_scope   on memory_items(scope);
create index if not exists idx_memory_items_category on memory_items(category);
create index if not exists idx_memory_items_tags     on memory_items using gin(tags);

-- 2. memory_embeddings (OPTIONAL — requires pgvector) ------------------------
-- Uncomment together with `create extension vector;` above. Dimension depends on model
-- (e.g. 1536 for text-embedding-3-small). Kept out of core apply by default.
-- create table if not exists memory_embeddings (
--   id             uuid primary key default gen_random_uuid(),
--   memory_item_id uuid not null references memory_items(id) on delete cascade,
--   embedding      vector(1536),
--   model          text not null,
--   created_at     timestamptz not null default now()
-- );
-- create index if not exists idx_memory_embeddings_item on memory_embeddings(memory_item_id);
-- -- ANN index (choose one after data exists):
-- -- create index on memory_embeddings using ivfflat (embedding vector_cosine_ops) with (lists=100);

-- 3. decisions ---------------------------------------------------------------
create table if not exists decisions (
  id            uuid primary key default gen_random_uuid(),
  decision_key  text unique,             -- stable slug e.g. 'l2_bpt_ok_final_2026_07_02'
  title         text not null,
  decision      text,                    -- the actual decision text
  status        text default 'approved', -- approved|rejected|deferred|superseded
  rationale     text,
  approved_by   text,                    -- 'Cris' | 'system' | ...
  decision_date date,
  source_ref    text,
  commit_sha    text,
  created_at    timestamptz not null default now()
);
create index if not exists idx_decisions_status on decisions(status);

-- 4. artifacts ---------------------------------------------------------------
create table if not exists artifacts (
  id            uuid primary key default gen_random_uuid(),
  artifact_type text not null,           -- report|manifest|csv|jsonl|commit|doc|plot
  path          text not null,           -- repo/disk pointer (NOT embedded content)
  title         text,
  description   text,
  checksum      text,                    -- sha256 when applicable
  commit_sha    text,
  source_ref    text,
  status        text default 'active',
  created_at    timestamptz not null default now()
);
create index if not exists idx_artifacts_type on artifacts(artifact_type);

-- 5. agent_runs --------------------------------------------------------------
create table if not exists agent_runs (
  id            uuid primary key default gen_random_uuid(),
  agent_name    text not null,
  task_type     text,
  prompt_ref    text,                    -- pointer, never full prompt with secrets
  output_ref    text,                    -- pointer to artifact/output
  status        text default 'completed',
  started_at    timestamptz,
  completed_at  timestamptz,
  commit_sha    text,
  notes         text
);
create index if not exists idx_agent_runs_name on agent_runs(agent_name);

-- 6. safety_reports ----------------------------------------------------------
create table if not exists safety_reports (
  id            uuid primary key default gen_random_uuid(),
  run_at        timestamptz not null default now(),
  blocker_count int not null default 0,
  warning_count int not null default 0,
  info_count    int not null default 0,
  report_path   text,
  commit_sha    text,
  status        text default 'report_only'
);
create index if not exists idx_safety_reports_run_at on safety_reports(run_at);

-- 7. external_factor_events --------------------------------------------------
create table if not exists external_factor_events (
  id           uuid primary key default gen_random_uuid(),
  event_time   timestamptz not null,
  source       text not null,            -- fred|forexfactory|fed_rss|cme|cftc|alpha_vantage|...
  event_type   text,                     -- CPI|NFP|FOMC|rate_decision|news|gold_flow|...
  asset_scope  text default 'XAUUSD',
  severity     text,                     -- low|medium|high
  title        text,
  summary      text,
  source_url   text,
  confidence   numeric,
  created_at   timestamptz not null default now()
);
create index if not exists idx_ef_events_time on external_factor_events(event_time);
create index if not exists idx_ef_events_asset on external_factor_events(asset_scope);

-- 8. market_context_snapshots (derived slices, NOT raw candles) --------------
create table if not exists market_context_snapshots (
  id           uuid primary key default gen_random_uuid(),
  symbol       text not null,
  timeframe    text not null,
  start_time   timestamptz,
  end_time     timestamptz,
  context_type text,                     -- regime|summary|levels|...
  summary      jsonb,                    -- small structured summary (NOT full OHLCV)
  source_ref   text not null,            -- pointer to RAW authority
  artifact_ref text,
  created_at   timestamptz not null default now()
);
create index if not exists idx_mcs_symbol_tf on market_context_snapshots(symbol, timeframe, start_time);

-- 9. trade_journal_events (PRIVATE; no broker secrets) -----------------------
create table if not exists trade_journal_events (
  id           uuid primary key default gen_random_uuid(),
  strategy_id  text,
  symbol       text,
  timeframe    text,
  event_time   timestamptz,
  event_type   text,                     -- entry|exit|note|skip|...
  status       text,
  payload_json jsonb,                    -- structured, NO credentials
  source_ref   text,
  created_at   timestamptz not null default now()
);
create index if not exists idx_tje_strategy_time on trade_journal_events(strategy_id, event_time);

-- 10. episode_context_links --------------------------------------------------
create table if not exists episode_context_links (
  id            uuid primary key default gen_random_uuid(),
  episode_id    text not null,
  symbol        text,
  timeframe     text,
  context_ref   text,                    -- external_factor_events id / snapshot id / doc
  artifact_ref  text,
  relation_type text,                    -- caused_by|context_for|evidence|...
  created_at    timestamptz not null default now()
);
create index if not exists idx_ecl_episode on episode_context_links(episode_id);

-- 11. source_registry (RAW/artifact authority pointers + checksums) ----------
create table if not exists source_registry (
  id              uuid primary key default gen_random_uuid(),
  source_type     text not null,          -- raw_replay|ruler|dataset|manifest
  path            text not null,
  symbol          text,
  timeframe       text,
  start_time      timestamptz,
  end_time        timestamptz,
  checksum        text,
  authority_level text default 'source_of_truth' check (authority_level in ('source_of_truth','derived','index','log')),
  created_at      timestamptz not null default now()
);
create index if not exists idx_source_registry_type on source_registry(source_type);

-- 12. retrieval_queries (log of context retrievals) --------------------------
create table if not exists retrieval_queries (
  id             uuid primary key default gen_random_uuid(),
  query_type     text,
  query_text     text,
  filters_json   jsonb,
  result_refs_json jsonb,
  token_estimate int,
  created_at     timestamptz not null default now()
);
create index if not exists idx_retrieval_queries_created on retrieval_queries(created_at);

-- ============================================================================
-- RLS PLAN (DO NOT apply to a shared/prod project without review) ------------
-- Enable RLS per table; product-memory readable broadly, private-memory locked to owner.
-- Applied only after dev validation + service-role/anon separation (see README).
-- Example (commented; apply in dev first):
-- alter table memory_items enable row level security;
-- create policy memory_items_read_product on memory_items for select using (scope = 'product');
-- create policy memory_items_all_private  on memory_items for all using (auth.role() = 'service_role');
-- (repeat per table; private tables => service_role only.)
-- ============================================================================
