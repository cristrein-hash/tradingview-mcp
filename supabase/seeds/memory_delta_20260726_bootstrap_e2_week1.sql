-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260726_bootstrap_e2_week1
-- ============================================================================
-- Retoma 2026-07-26 (pre-abertura): restage dos factos da sessao 2026-07-24/25 posteriores ao seed 341.
-- (1) Deep-cross ground-truth 61 sinais + 7 winners (perna-1H = #1 separador). (2) E2 semana-1 em validacao:
-- winner-leak esta nos GATES deterministicos, nao no read; decisao Cris = acionar E2 LIVE + frame-explicito.
-- (3) Licao plotting historico 15M + higiene da retoma (retry E2 commitado, daemons contunuos reiniciados).
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 3 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260726_bootstrap_e2_week1:memory_items:deep-cross-groundtruth')::uuid,
  'product', 'internal', 'project',
  'Deep-cross ground-truth 2026-07-24: 61 sinais + 7 master-trades x todas as features — perna-1H = #1 separador; RSI/DMI/NAS/count = dropar do gate',
  'Cruzamento profundo (docs/architecture/DEEP_CROSS_GROUNDTRUTH_20260724.md, commit 6602894): 61 sinais da semana + 7 master trades do Cris (todos winners) + 4 stops dele, reconstruidos do bar-store com TODAS as features (perna/fluxo/DMI/RSI/NAS/sessao/macro/external-factors). ACHADO CENTRAL: alinhamento com a PERNA 1H e o #1 separador (COM-perna 56% WR / MFE 15.3 vs CONTRA-perna 27% / MFE 8.6; nos 61 sozinhos 48% vs 23%) — confirma o motor leg-based novo. DROPAR do gate por zero separacao: RSI (41%=41%), DMI (fraco), NAS (invertido/ruido N8), convergencia-por-CONTAGEM (nao e escada: 3/5 < 1/5 — contar leituras alinhadas NAO ordena qualidade, reforca canon convergencia!=determinismo). Fluxo-bubbles alinhado = confirmador secundario (52% vs 35%). O q FORTE/FRACO antigo era quase inutil (42% vs 33%). O motor antigo SOBRE-SHORTOU (49 short / 19 long) contra pernas de alta. External factors = backdrop constante na semana (nao diferencia sinal a sinal). Scripts research/deep_cross_20260724.py + master_trades_cross_20260724.py (motor novo: 7/7 winners SINALIZA, 4/4 stops do Cris SKIP). CAVEAT: diagnostico in-sample N68, nao valida edge; arbitro = forward. NOTA Cris: a 1a versao agregada-deterministica deste relatorio foi REJEITADA ("mecanizar leitura") — indicadores sao contexto-dependentes; o cruzamento serve para informar o READ, nao para virar tabela de pontos.',
  array['seed:memory_delta_20260726_bootstrap_e2_week1','deep-cross','ground-truth','perna-1h-separador','master-trades','drop-rsi-dmi-nas-count','sobre-short','in-sample-diagnostico','nao-mecanizar-leitura'],
  'docs/architecture/DEEP_CROSS_GROUNDTRUTH_20260724.md · research/deep_cross_20260724.py · research/master_trades_cross_20260724.py · commit 6602894 · memoria project_price_shock_leg_based_signal',
  'active'
),
(
  md5('seed:memory_delta_20260726_bootstrap_e2_week1:memory_items:e2-week1-winner-leak')::uuid,
  'product', 'internal', 'decision',
  'E2 semana-1 em validacao (ate 2026-07-24): winner-leak = GATES deterministicos, nao o read — decisao Cris: acionar E2 LIVE + frame-explicito da perna no render_composite',
  'Balanco da 1a semana do E2 em validacao (e2_verdicts/e2_outcomes): 5 candidatos surfaced (0 TP, 3 SL, 2 OPEN) e 9 candidatos que TERIAM batido TP todos skipados — 5 pelos GATES deterministicos (session_vacuum x4 — ja conhecido-observacional — e chase x1), 3 pelo READ (recusou os LONGs de 20/07 como counter-trend), 1 read falhou (is_error transitorio, origem do fix retry). LEITURA: a fuga de winners esta nos VETOS DETERMINISTICOS, nao no juizo contextual — coerente com o canon convergencia-nao-determinismo. Os 9 winners skipados foram plotados no chart 1H (tab 15M XAUUSD) para revisao visual do Cris. DECISAO Cris (2026-07-24/25, verbatim "VAMOS ACIONAR O E2 SEM SHADOW EM LIVE ... SAO 2 AJUSTES DE PESO"): (a) implementar FRAME-EXPLICITO no render_composite (e2_quality.py) — a perna 1H sobe a FRAME rotulado no topo do briefing (perna BULL -> demandas=compra, supplies-15M=pullback, so OB 4H/1D reverte), as outras vozes lidas CONTRA esse frame, graduacao por CONVERGENCIA nao contagem; (b) acionar E2 em LIVE (emissao Telegram) para correr a semana como arbitro. AMBOS PENDENTES de implementacao na retoma de 2026-07-26. Regra viva: nunca afinar prompt/limiar ao dia visivel; arbitro = forward nao-visto.',
  array['seed:memory_delta_20260726_bootstrap_e2_week1','e2','winner-leak-gates','session-vacuum','frame-explicito','perna-como-frame','e2-go-live-decisao','pendente-implementacao','convergencia-nao-contagem'],
  'alert-bridge/e2_quality.py::render_composite · logs/e2_verdicts.jsonl · logs/e2_outcomes.jsonl · research/.e2_missed_winners.json · memoria project_camada2_e2_convergence_read',
  'active'
),
(
  md5('seed:memory_delta_20260726_bootstrap_e2_week1:memory_items:plotting-1h-e-higiene-retoma')::uuid,
  'product', 'internal', 'feedback',
  'Licao plotting: chart 15M so tem ~2 dias carregados — trades >2 dias plotam em 1H/4H; + higiene retoma 2026-07-26 (retry E2 commitado, daemons contunuos reiniciados)',
  'PLOTTING (2026-07-25): plotar trades antigos no chart 15M colapsou as caixas para largura-zero num ponto default — o 15M so mantem ~2 dias de barras em memoria e nao ancora tempos fora do range carregado. REGRA REUTILIZAVEL: trade com mais de ~2 dias -> plotar no 1H ou 4H (historico completo carregado); excecao declarada ao canon de TF de plotagem, motivo=historico. Fix research/replot_1h.py: set timeframe 60 + replot + READ-BACK das caixas (draw_get_properties) confirmando largura/tempos distintos — 9/9 OK. Licao-mae: dados-corretos != visual-correto; SEMPRE ler de volta o desenho e confirmar com o Cris (ele faz o visual). HIGIENE RETOMA 2026-07-26 (pre-abertura, mercado fechado): (1) retry 3x com backoff no run_read do E2 (buraco-1: claude is_error transitorio escrevia branco) COMMITADO b8899e0; (2) AUDITORIA apanhou daemons contunuos (e1-detector desde 18/07, E0/E2 desde 19/07, realtime-monitor desde 16/07) a correr codigo ANTERIOR aos commits de 19-24/07 (cf7a29d amd_setup, e6e1977 anti-thundering-herd, retry E2) -> kickstart -k dos 4 com mercado fechado; todos voltaram limpos (E0 heartbeat fresh, E2 banner com codigo novo, monitor hb OK). REGRA OPERACIONAL NOVA: apos commit que toca daemon CONTINUO (KeepAlive), reiniciar o daemon — processo Python nao recarrega o modulo; StartInterval (price-shock, Cp, L1/L2) pega sozinho no ciclo seguinte.',
  array['seed:memory_delta_20260726_bootstrap_e2_week1','plotting-canon','15m-2-dias-historico','plot-1h-para-antigos','read-back-desenho','retry-e2-commitado','daemon-restart-apos-commit','keepalive-vs-startinterval','higiene-retoma'],
  'research/replot_1h.py · alert-bridge/e2_quality.py::run_read · commit b8899e0 · skills/plotting-canon/SKILL.md',
  'active'
)
on conflict (id) do nothing;
commit;
