-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260728_news_stabilize_retoma_forward
-- ============================================================================
-- Sessao 28/07 pre-FOMC: estabilizacao news/EF (301+FMP fallback+auditor auto) + forward retoma 0/4 vs reader 5/5.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 2 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260728_news_stabilize_retoma_forward:memory_items:news-stabilize')::uuid,
  'product', 'internal', 'decision',
  'Estabilizacao completa news/EF pre-FOMC (Cris 2026-07-28) — 301 InvestingLive + FMP fallback keyless Yahoo + auditor automatico + cap rotacao',
  'Cris reportou "news a cair constantemente" a 1 dia da sequencia FOMC. AUDITORIA COMPLETA (external factors + MCP): (1) InvestingLive HTTP 301 INTERMITENTE (redirect-loop /feed<->/feed/ que urllib reportava como erro; curl dava 200 = alcancavel; degradava graceful mantendo snapshot mas perdia breaking) -> FIX fetch robusto (3 tentativas + variante trailing-slash + seguir Location manual; commit c28d298). (2) FMP free "Limit Reach" (esgotado) -> Brent None + ouro None constantes -> FALLBACK KEYLESS Yahoo BZ=F (Brent) e GC=F (ouro), COM User-Agent Mozilla senao "Too Many Requests"; FMP fica primario, Yahoo entra so quando FMP falha; commits aae4298+ebd6742; testado Brent 87.24 ouro 4023.5. (3) Geopolitical (GDELT) recuperou no mesmo ciclo (flakiness transitoria, agora 50 arts/27 rel/11 TOP). (4) Finnhub 0 gold-relevant = LEGITIMO (filtra geral, key ok). (5) CALENDARIO FOMC = SOLIDO: fonte keyless ForexFactory/FairEconomy JSON (sem rate-limit), FOMC 29/07 ~19h Lisboa, countdown correto, escalada armada (calendario-only). (6) state_<ts> write-only acumulavam ~45/dia (nada os le de volta) -> limpei 154 manualmente + CAP DE ROTACAO 24h no monitor_external_factors.py (fail-soft; commit bc507b3). (7) AUDITOR AUTOMATICO research/news_collector_auditor.py (vigia persistente poll 120s): deteta falha por coletor (stale=parou de escrever OU conteudo degradado=preco None apos fallback tb falhar/calendario vazio) na TRANSICAO OK<->FALHA, avisa no chat -> auto-auditoria; commit a9853a1. CRITICO: o preco de ouro do TRADING vem do bar-store/GLD (nao FMP) = nunca esteve em risco; o price-shock apanha a reacao do FOMC. receiver /health 200, cloudflared up, watchdog 7/7 OK. Tudo pushed.',
  array['seed:memory_delta_20260728_news_stabilize_retoma_forward','news-estabilizacao','investinglive-301','fmp-limit','fallback-keyless-yahoo','auditor-automatico-coletores','cap-rotacao-state','calendario-fomc-keyless','pre-fomc','preco-trading-bar-store-nao-fmp'],
  'external_factors_v2/collectors/investinglive_news_collect.py · oil_collect.py · gold_collect.py · runtime/monitor_external_factors.py · research/news_collector_auditor.py · commits c28d298..a9853a1',
  'active'
),
(
  md5('seed:memory_delta_20260728_news_stabilize_retoma_forward:memory_items:retoma-forward-0-4')::uuid,
  'product', 'internal', 'project',
  'Forward retoma 0/4 vs reader 5/5 (28/07 pre-FOMC) — mecanico apanhou 4 facas na demanda, reader recusou todas; N pequeno + regime hostil, FOMC decide',
  'Continuacao do caso forward (BEAR/BEAR pre-FOMC, preco furou tudo 4090->4016 e coila 4018-4034). RETOMA v1 dry: N=4 · 0 WIN · 4 LOSS · streak -4 (entries 4085.64/4076.57/4047.99/4034.26; 5o OPEN entry 4026). O 4o PERDEU no PONTO FORTE = demanda 4H, perna 21xATR (o fundo mais profundo) -> mesmo a demanda HTF e faca em bear pre-FOMC sem o fluxo virar. READER E2 (via vigia demanda-com-reader, import render_composite+run_read do E2 - nunca paralelo): 5/5 RECUSOU todos os longs (conviccao-short 88->18->16->12->22, sempre "apanhar faca, sem reclaim, auction venda pura, vacuo pre-FOMC"; reconhece bounce potencial 4H pos 0.00 mas exige CHoCH-up 15M + auction comprador + climax para virar "legitimo"). Os 4 resolvidos deram-lhe razao. TESE CENTRAL a validar-se: leitura de convergencia contextual > gatilho mecanico isolado (feedback_contextual_convergence_not_determinism). CAVEAT DURO OBRIGATORIO: N=4 minusculo + janela BEAR pre-FOMC = PIOR regime para a classe retoma (que e range/recuperacao, nao bear profundo) -> 0/4 aqui NAO condena a camada; condenaria 0/20 no regime dela. Decisao com N>=20 (prereg), nunca com 4. FOMC 29/07 ~19h = catalisador (vira fluxo->reader aprova, ou estende bear). Prova de valor do reader: cada faca da retoma foi por ele recusada = a razao de o E2/reader existir. Bug do vigia demanda corrigido (re-arme a inundar toques ao oscilar no bordo -> ZTOP+12).',
  array['seed:memory_delta_20260728_news_stabilize_retoma_forward','retoma-0-de-4','reader-5-de-5-cetico','faca-na-demanda-4h','convergencia-bate-mecanico','N-pequeno-regime-hostil','fomc-decide','vigia-reamre-fix','caveat-nao-condena'],
  'my-strategy/strategies/xau_15m_long/ENTRY_ROUTER/.router_state/retoma_ledger.jsonl · research/watch_demanda_reader_20260728.py · memoria project_forward_case_20260727_retoma_vs_reader',
  'active'
)
on conflict (id) do nothing;
commit;
