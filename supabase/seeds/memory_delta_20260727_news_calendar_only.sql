-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260727_news_calendar_only
-- ============================================================================
-- Ordem Cris 2026-07-27: alertas de news no Telegram = SO calendario economico de alto impacto;
-- headlines (guerra/geopolitica/mercado) = contexto no sistema, nunca alertam.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260727_news_calendar_only:memory_items:news-calendar-only')::uuid,
  'product', 'internal', 'decision',
  'News Telegram = SO calendario economico ALTO IMPACTO just-out (ordem Cris 2026-07-27); headlines nunca alertam — contexto E0 apenas',
  'Escalada de news reconfigurada em runtime/news_escalate.py: o UNICO caminho de alerta Telegram passa a ser o release just-out do ff_calendar (o news_gate ja filtra impact=HIGH US) — cabecalho "CALENDARIO ALTO IMPACTO" + vies XAU + advisory. Finnhub e InvestingLive SAIRAM da escalada (GDELT/geopolitico ja tinha saido 2026-07-19). Guerra, cessar-fogo, dolar, yields e todas as headlines continuam recolhidas pelos collectors e a alimentar o news_gate/E0 como CONTEXTO que o read do E2 pesa — mas NUNCA alertam no Telegram. Coerencia com a doutrina price-first: choque real move o preco -> price-shock daemon dispara (o alerta vem do preco, nao da noticia). Verificado: compile OK, dry-run OK, nenhum outro emissor de news existe, lane 4min continua armada (NEWS_ALERTS_AUTHORIZED=1 no plist com.cristrein.external-factors-news; StartInterval pega o codigo novo sozinho).',
  array['seed:memory_delta_20260727_news_calendar_only','news-telegram','calendario-alto-impacto','headlines-sem-alerta','price-first','news-escalate','user-approved'],
  'external_factors_v2/runtime/news_escalate.py · alert-bridge/news_gate.py (ff_event impact=HIGH) · plist com.cristrein.external-factors-news',
  'active'
)
on conflict (id) do nothing;
commit;
