insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('l1_golive_producao_20260717')::uuid, 'private', 'private', 'project',
  'L1 EMA21 4H = LIVE EM PRODUCAO (go-live Cris 2026-07-17, Telegram ativo)',
  'Go-live executado 2026-07-17 ~11:17 UTC por autorizacao explicita do Cris (colocar live L1 e L2 ja aprovadas, Telegram ativo). 3 destravas do hard-lock 2026-07-09: plist com.cristrein.xau-l1-cycle carregado (6x/dia pos-fecho 4H Lisboa 03/07/11/15/19/23h05), flag send-telegram readicionada e L1_PRODUCTION_AUTHORIZED=1 via wrapper novo start_l1_cycle.sh. Ciclo launchd verificado end-to-end: telegram_real true, dedup persistente, fail-closed intacto. Warmup: regime D auto-curou (18 barras ate 2026-07-16, regime BEAR, logo no_candidate correto ate virar BULL); ledger NAS seedado, auto-cura no fecho 4H seguinte. Modo operacional final = TAB-PINNED: run_l1_cycle.py pin-tabs le a tab 1D pinada (refresh) e a tab 4H pinada (runtime) via TVMCP_TARGET_CHART_ID, zero troca de chart e zero pausa dos daemons; fallback fail-safe para o modo manage-chart antigo. Commit 5e0b9a3.',
  array['seed:memory_delta_l1_golive_tabpin_20260717','l1','producao','go-live','telegram'],
  'commit:5e0b9a3 · memory:project_l1_refinement_approved_2026_06_16.md', 'active'),
 (md5('tabpin_recurso_geral_e2_read_20260717')::uuid, 'private', 'private', 'architecture',
  'Tab-pinning = recurso geral de coexistencia MCP/CDP (Cris 2026-07-17) + Camada2 E2 read convergente ativo',
  'Decisao Cris: 5 tabs XAUUSD dedicadas (5M/15M/1H/4H/1D, indicadores habilitados); cada runtime le a tab do seu TF pinada via TVMCP_TARGET_CHART_ID. Helper partilhado my-strategy/core/tab_pin.py (descoberta, verificacao, cache; fail-closed se a tab nao existir). Provado na pratica: leituras de barras, pine_boxes (20 ob_zones), NAS e RSI na tab 4H pinada, barras diarias na 1D, com E0/E1/E2 ligados em paralelo sem conflito. Padrao obrigatorio para L2 e estrategias 15M. No mesmo dia: Camada2 E2 redesenhado para READ contextual unico de convergencia (Opus, claude -p), em validacao (0 Telegram), apos refutacao empirica do ensemble adversarial (reject-all matou winners e losers por igual); commit e7d5d01. L2/BPT trend-exit: runtime em construcao (port verbatim + paridades byte-exatas V1-V4 antes de Telegram).',
  array['seed:memory_delta_l1_golive_tabpin_20260717','tab-pinning','mcp','camada2','e2'],
  'commit:5e0b9a3 · commit:e7d5d01 · memory:project_camada2_e2_convergence_read.md', 'active')
on conflict (id) do nothing;
