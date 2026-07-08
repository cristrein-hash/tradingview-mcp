-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_open_state_checkpoint_20260708
-- ============================================================================
-- Bloco: checkpoint de estado aberto 2026-07-08 (N96 approved, protocolo 15M active, L2/BPT trend-exit exploratory).
-- NAO APLICADO automaticamente. Aplicar so com autorizacao explicita do Cris via scripts/supabase/apply_memory_delta.py.
-- Zero RAW/candles/secrets/outputs massivos. Idempotente (on conflict do nothing).
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_open_state_checkpoint_20260708'];
-- Total: 4 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_open_state_checkpoint_20260708:memory_items:n96-approved')::uuid,
  'product', 'internal', 'project',
  'XAU 15M N96 ENTRY ENGINE = USER_APPROVED_NOT_PRODUCTION (Cris 2026-07-08)',
  'XAU_15M_N96_ENTRY_ENGINE aprovado por Cris como USER_APPROVED_NOT_PRODUCTION (commit 059fd5d, status master 04 sec 4.6). Componentes: motor N96 (96 entradas, 52W/44L, 3R fixo, +112R) + filtro intra-BEAR capitulation (dentro do regime BEAR v5 hour-causal, SKIP se 1D_px_vs_ema>=0 = repique raso): corta 13 losers / 0 winners, impacto +4 a +13R por detector, DA=PROFITABLE_BUT_FRAGILE. RANGE/distribuicao, BULL-excess RSI-HTF (~80) e D-bear-deep = REVIEW-LAYERS apenas, NAO gates (nenhum gate adicional sobrevive multiplicidade honesta). Gestao humana preservada (nao auto-cortar): #24,#32,#64,#77. NAO producao/runtime/Telegram/broker/strategy_rules/monitor. Achado metodologico: eixo robusto = EXCESS de RSI-HTF; cruzamento global de indicadores = esteril; indicadores so discriminam apos leitura estrutural (regime+perna). Caveat: HTF primitives congelam 2026-05-24/06-09 (filtro nao dispara live ate extensao). Forward nas ops live do Cris = arbitro final.',
  array['seed:memory_delta_open_state_checkpoint_20260708','xau-15m-n96','user-approved-not-production','intra-bear-capitulation','review-layer-not-gate'],
  'docs/architecture/XAU_15M_N96_ENTRY_ENGINE_USER_APPROVAL_20260708.md; docs/project_authority/04_STRATEGY_STATUS_MASTER.md sec 4.6; commit 059fd5d',
  'active'
),
(
  md5('seed:memory_delta_open_state_checkpoint_20260708:memory_items:protocol-active')::uuid,
  'product', 'internal', 'reference',
  'XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = ACTIVE — no manifest/structural-bucket/claim-ledger = no lab',
  'Protocolo canonico executavel (nao memoria) obrigatorio para todo lab XAU 15M, especialmente antes do SHORT (commit b517312). Blockers fail-loud: scripts/safety/check_xau_15m_raw_lineage.py (bloqueia SLIM/resample/no-lineage/fonte-contaminada/HTF-stale-nao-declarado), check_xau_15m_structural_first.py (bloqueia indicator scan sem colunas macro_regime+leg_state+family), check_xau_15m_claims_ledger.py (bloqueia metrica sem script/input/output/source), run_xau_15m_lab_gate.py (runner -> XAU_15M_LAB_GATE_PASS). Templates: manifest gate + claims ledger. Docs: XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1.md + ROLLOUT. REGRA-MAE: sem macro_regime + leg_state + family_label, nenhum indicador vira evidencia. Labs pre-2026-07-08 grandfathered; todo lab 15M/SHORT novo tem de passar o gate. Testado (pass+fail). NAO producao.',
  array['seed:memory_delta_open_state_checkpoint_20260708','xau-15m-protocol','active','fail-loud-blocker','structural-first','claim-ledger'],
  'docs/project_authority/XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1.md; docs/architecture/XAU_15M_RESEARCH_EXECUTION_PROTOCOL_ROLLOUT_20260708.md; commit b517312',
  'active'
),
(
  md5('seed:memory_delta_open_state_checkpoint_20260708:memory_items:l2bpt-trend-exit')::uuid,
  'product', 'internal', 'project',
  'L2/BPT XAU 4H trend-exit / regime-flip = EXPLORATORY_NOT_APPROVED / NOT_FOR_DECISION (2026-07-08)',
  'Estudo exploratorio de gestao de exit por tendencia (Cris: em macro-regime BULL segurar na tendencia, nao cortar em horizonte fixo). Regua oficial L2/BPT PERMANECE SL_CONTEXT + let-run HZ120 (nao alterada). Regime-flip (segura ate regime virar BEAR, cap 500): SELECT-17 +105.3R (retDD 26x, streak3, DD-4.1) vs let-run120 +36.2R; FULL-245 ~+399R (online-causal +385.7R). CAUSALIDADE = PASS (DA reimplementou FSM online byte-identico na era de trading; regime-flip NAO e look-ahead; filtro >=15-bar significancia so na selecao de entrada, nao no exit). MAS ~78% do ganho nos 17 e HORIZONTE/exposicao (120->500 barras), replicavel por hold-500 burro (+90.3R); o detector de regime adiciona so ~+15R sobre hold500, sobre 2 topos macro IN-SAMPLE (detector calibrado as ground-truth boxes do Cris) -> N~2 eventos. #6 = winner mecanico +1.15R (CAP-driven), NAO +3R; os +3R do #6 = leitura discricionaria/target estrutural do Cris, ainda nao mecanizada. Full-base DD -57 a -72 / streak 22 = HOSTIL a prop; a tameness dos 17 vem da selecao de entrada, nao do exit. Teto-hindsight dos alvos desenhados = +87.6R (rejeitado por Cris como exagero; DA: 67% dos alvos em precos nunca vistos a entrada = hindsight). STATUS = EXPLORATORY_NOT_APPROVED; proximo = prereg formal (full-base, DD/streak control, gap-model, benchmark vs hold-500, DA) antes de qualquer adocao. NAO producao.',
  array['seed:memory_delta_open_state_checkpoint_20260708','l2-bpt-trend-exit','exploratory-not-approved','not-for-decision','regime-flip-causal','horizonte-vs-regime'],
  'docs/architecture/L2_BPT_TREND_EXIT_EXPLORATORY_CHECKPOINT_20260708.md; research/l2_bpt_trailing_exit_test.py',
  'active'
),
(
  md5('seed:memory_delta_open_state_checkpoint_20260708:memory_items:open-state')::uuid,
  'product', 'internal', 'project',
  'Open state checkpoint 2026-07-08: git sync (HEAD=origin=b517312), untracked chart/research scripts KEEP_COMMIT pendentes',
  'Checkpoint de estado aberto (doc OPEN_STATE_CHECKPOINT_20260708.md). Git: HEAD=origin/main=b517312, ZERO commits pendentes de push (tudo aprovado ja pushado: a32b25a/c05dbc1/737ff9b/059fd5d/b517312). Untracked classificados KEEP_COMMIT: scripts L2/BPT trend-exit (l2_bpt_*.py) + results pequenos (l2_bpt_17_trades.csv, l2_bpt_cris_targets.*) + scripts de chart N96 (make_n96_valid_plot_source.py, plot_n96_valid_canonical.py, remove_n96_cut_trades.py, n96_valid_trades.csv). l2_bpt_exit_forward_diagnostic.py = NEEDS_REVIEW (nao corrido, redundante). Decisoes abertas: formalizar ou nao trend-exit; #6 mecanico +1.15R vs discricionario +3R; extensao daily/HTF; abrir XAU 15M SHORT sob protocolo. Regra: nada novo iniciado; SHORT nao aberto; trend-exit nao aprovado; so salvar estado. Este delta = seed NAO aplicado (aguarda autorizacao Cris via apply_memory_delta.py).',
  array['seed:memory_delta_open_state_checkpoint_20260708','open-state-checkpoint','git-synced','untracked-keep-commit','decisoes-abertas'],
  'docs/architecture/OPEN_STATE_CHECKPOINT_20260708.md',
  'active'
)
on conflict (id) do nothing;
commit;
