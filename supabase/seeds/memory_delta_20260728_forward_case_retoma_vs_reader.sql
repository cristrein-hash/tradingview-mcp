-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260728_forward_case_retoma_vs_reader
-- ============================================================================
-- Caso forward noite 27-28/07: retoma mecanica 0/3 LOSS vs reader E2 3 shorts certos + vigia-com-reader.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260728_forward_case_retoma_vs_reader:memory_items:forward-case')::uuid,
  'product', 'internal', 'project',
  'Caso forward 27-28/07 (noite pre-FOMC): retoma mecanica 0/3 LOSS vs reader E2 3 SHORTS certos (-44pts) — tese convergencia-contextual > gatilho-mecanico a validar-se ao vivo (N pequeno) + vigia-com-reader',
  'Primeiro caso forward do stack completo pos-go-live (E2 live + stacked-zones + retoma dry), noite 27->28/07, regime BEAR, FOMC ~45h, alivio Brent -9% (suporte-ao-ouro que NAO segurou). CONTRASTE (tese central AO VIVO, N pequeno nao conclui): RETOMA v1 dry mecanica = N=3 resolvidos 0 WIN 3 LOSS (entries 4085.64/4076.57/4047.99, cada reclaim comprou o repique e o mercado continuou a cair, preco 4077->4033 ~-44pts) = EXATAMENTE o vetor de invalidacao congelado no prereg ("se higher-lows em bear = facas, a camada morre") a manifestar-se. READER E2 contextual = recusou TODOS esses longs (conviccao-short 88->18->16->12 a colapsar mas sempre "apanhar faca, sem reclaim, continuacao de baixa") E surfou 3 SHORTS (20:05 conv42, 21:46 conv60, 00:47 conv50) = o lado que PAGOU; protegeu das 3 perdas do mecanico e apontou o lado certo. LICAO: reforca feedback_contextual_convergence_not_determinism (leitura do todo > gatilho mecanico isolado); HONESTIDADE: N minusculo, 1 noite, 1 regime = sinal direcional do desenho, nao prova de edge (arbitro = forward multi-semana). VIGIA-COM-READER (novo padrao, Cris 2026-07-28): pediu fundo 4050-4053 e "PERMITE O READER JULGAR, NAO MECANIZA OS ALARMES, deixa ele analisar reclaim legitimo" -> research/watch_demanda_reader_20260728.py: toque=heads-up geografico; RECLAIM REAL (fecho ACIMA da borda, gatilho apertado apos 4 leituras vazias abaixo da zona) chama O MESMO READER do E2 (import e2_quality.render_composite+run_read+surfaced, NUNCA reader paralelo) sobre o dossie vivo e devolve o JUIZO (reasoning/converges/conviction/tese/conflitos), nao um CONFIRMADO mecanico. PROVA DE VALOR: 4 velas verdes na zona durante a noite, o reader recusou as 4 (fluxo nunca virou) = alarme mecanico teria dado 4 falsos. Preco varreu ~15pts ABAIXO da zona prevista (fundo real 4034.69 vs 4050-4053) antes de qualquer virada = liquidez por baixo; a zona do Cris virou resistencia-a-reclamar. 3 vigias vivos: E2 (Telegram), retoma (dry), demanda-com-reader.',
  array['seed:memory_delta_20260728_forward_case_retoma_vs_reader','caso-forward','retoma-0-de-3','reader-3-shorts-certos','convergencia-bate-mecanico','vigia-com-reader','reader-julga-nao-mecaniza','fundo-varreu-abaixo','pre-fomc','N-pequeno-nao-conclui'],
  'my-strategy/strategies/xau_15m_long/ENTRY_ROUTER/.router_state/retoma_ledger.jsonl · alert-bridge/logs/e2_verdicts.jsonl · research/watch_demanda_reader_20260728.py · memoria project_forward_case_20260727_retoma_vs_reader',
  'active'
)
on conflict (id) do nothing;
commit;
