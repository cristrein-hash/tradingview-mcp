-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260802_r10_live_r9_descritores
-- ============================================================================
-- R10 ligado live + R9 opcao C (descritores sem gate) + src visivel ao reader. 1 row. Idempotente.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260802_r10_live_r9_descritores:memory_items:update')::uuid,
  'product', 'internal', 'decision',
  'R10 top_fade LIGADO live + R9 opcao C: descritores de qualidade sem gate + reader ve o src de todas as regras (Cris 2026-08-02)',
  'DUAS decisoes do Cris no mesmo dia do go-live R9/R10: (1) R10 top_fade LIGADO EM LIVE (era estudo/off; Cris: "mercado esta em bear" -> fades de topo = shorts com-regime; e de qualquer forma shadow: 0 Telegram, cada candidato julgado pelo reader E2). E1_TOP_FADE=1 no start_e1_detector.sh; 4 flags E1 ativas (E1_STACKED_ZONES + E1_BOS_CONTINUATION + E1_OB_TOUCH + E1_TOP_FADE) = 9 gatilhos vivos. (2) Cris questionou a logica do R9 como "um tanto superficial" -> resposta honesta: gerador fino POR DESENHO (a profundidade vive no reader E2) MAS 3 buracos mecanicos reais vs a anatomia do trade dele; escolheu OPCAO C = medir sem gate. R9 agora anexa ao candidato: leg_into_zone_atr (magnitude da perna de CHEGADA a zona em ATR15 sobre 32 barras - despenca=combustivel de reversao vs deriva=setup fraco), touch_n (episodios de toque da zona em 24h; 1=zona virgem=mais forte), win_buy/win_sell (iniciativa das ultimas 4 barras do dossie; agressao contraria ABSORVIDA no bloco = acumulacao/distribuicao pela regra de polaridade context-dependente). Descritores no src E como campos do candidato (ledger/estudo); fail-soft (falta="?", nunca mata candidato). BONUS ESTRUTURAL: e2_quality render ganhou a linha "gatilho: <src>" no bloco CANDIDATO - o reader passa a ver o src de TODAS as regras R1-R10 (antes o src NUNCA chegava ao read). FILOSOFIA confirmada: gerador nao perde casos; a qualidade diferencia-se na CONVICCAO do read (monstro 11ATR toque#1 sell-absorvido vs drift 2ATR toque#4), nao em gates que matam candidatos que o reader aprovaria. Provas: selftests E1 16 casos + E2 selftest+anchors PASS; aceitacao --week 5/5 PASS (monstro continua a nascer). Daemons e1+e2 kickstarted. Commits 7714e8c (R10 live) + c504d40 (opcao C).',
  array['seed:memory_delta_20260802_r10_live_r9_descritores','R10-ligado-live-bear','R9-opcao-C-descritores-sem-gate','leg_into_zone_atr','touch_n-zona-virgem','win_buy_sell-absorcao','reader-ve-src-todas-regras','gerador-fino-reader-profundo','9-gatilhos-E1-vivos'],
  'alert-bridge/e1_detector.py (R9 _r9_desc) · e2_quality.py (render gatilho:src) · start_e1_detector.sh · commits 7714e8c+c504d40 · project_week_eval_20260802_r9_r10',
  'active'
)
on conflict (id) do nothing;
commit;
