-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260731_e1_bos_continuation
-- ============================================================================
-- Gatilho E1 bos_continuation (2a quebra = confirmacao) LIVE. 1 row. Idempotente.
-- Aplicar via scripts/supabase/apply_memory_delta.py.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260731_e1_bos_continuation:memory_items:trigger')::uuid,
  'product', 'internal', 'project',
  'E1 bos_continuation (R8) LIVE 2026-07-31 — 2a quebra estrutural = CONFIRMACAO (1o CHoCH/BOS = manipulacao, 2o vale mais)',
  'PRINCIPIO Cris: o 1o CHoCH/BOS e muitas vezes MANIPULACAO (liquidity grab); a 2a quebra e a CONFIRMACAO real e vale MAIS que a 1a. LACUNA (logs): e1_detector.py R3 choch so dispara na borda choch.dn False->True (1a quebra); as continuacoes (2a perna) NAO geravam candidato -> reader nunca perguntado. Caso real 30-31/07: 1a quebra ~21:30 consumiu a borda; a continuacao das 01:15 (close 4096) nao gerou nada; so havia sweep_reclaim do topo (ja recusado). NAO foi conservadoria do reader = lacuna de GERACAO (E1). NOVO gatilho R8 bos_continuation (flag E1_BOS_CONTINUATION=1, ON no start script): perna estabelecida = pm.choch.dn/up (a 1a quebra ja aconteceu, e do R3) + leg.dir concorda + mag_atr>=1.0 (mata micro/range) + quebra FRESCA do last_low(SHORT)/last_high(LONG) via cruz pclose->close (auto-dedup, so arma na barra da quebra); SL ESTRUTURAL = nivel-quebrado (ll/lh)+-0.1ATR (reclaim=invalidacao); pos=None (dispara no extremo pos~0). DUAS CORRECOES guiadas por EVIDENCIA (replay, NAO fitting): (1) trend==DOWN era estrito demais (fractal m=3 raramente confirma DOWN em queda rapida: replay b378 trend=RANGE) -> trocado por pm.choch (o marcador presente nos dados); (2) sl15_high dava R largo demais (entrada num novo low longe do topo 15M -> R>2xATR -> levels() descartava) -> trocado por nivel-quebrado (tight). PROVAS: selftest PASS (2a-quebra dispara / 1a nao / OFF byte-identico). Replay 30-31/07: 1 bos_continuation na quebra real b378 entry 4067.89 SL 4072.29 alvo 4054.69 3R pass (vs 38 sweep_reclaim do topo, intactos). Aditivo, SHADOW (0 Telegram, E2 julga cada candidato = conservadoria do reader mantida, agora a confirmacao e OFERECIDA). Ficheiros e1_detector.py + e1_replay.py + start_e1_detector.sh; commit 3ffc999 (push); e1-detector kickstarted. Desenho via Plan (verificacao evidence-first). PENDENTE: forward (taxa/qualidade dos candidatos R8 no live).',
  array['seed:memory_delta_20260731_e1_bos_continuation','bos_continuation-R8','2a-quebra-confirmacao','1o-choch-bos-manipulacao','gate-pm-choch','SL-nivel-quebrado','correcao-evidence-first-nao-fitting','replay-recall-b378','shadow-E2-julga','flag-E1_BOS_CONTINUATION'],
  'alert-bridge/e1_detector.py · e1_replay.py · start_e1_detector.sh · project_e1_bos_continuation_trigger · commit 3ffc999',
  'active'
)
on conflict (id) do nothing;
commit;
