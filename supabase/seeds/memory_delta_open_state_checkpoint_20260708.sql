-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_open_state_checkpoint_20260708
-- ============================================================================
-- Bloco: checkpoint de estado aberto 2026-07-08 (N96 approved, protocolo 15M active, L2/BPT trend-exit exploratory).
-- NAO APLICADO automaticamente. Aplicar so com autorizacao explicita do Cris via scripts/supabase/apply_memory_delta.py.
-- Zero RAW/candles/secrets/outputs massivos. Idempotente (on conflict do nothing).
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_open_state_checkpoint_20260708'];
-- Total: 5 rows. (UPDATE Cris 2026-07-08: L2/BPT trend-exit promovido a OFICIAL; swept-runner rebaixado.)
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
  'L2/BPT XAU 4H trend-exit / regime-flip = USER_APPROVED_OFFICIAL_NOT_PRODUCTION (Cris 2026-07-08)',
  'DECISAO CRIS 2026-07-08: estrategia XAU 4H LONG L2/BPT com novo exit trend-exit/regime-flip = OFICIAL APROVADA (USER_APPROVED_OFFICIAL_NOT_PRODUCTION = OFFICIAL_APPROVED_PENDING_PRODUCTION_AUTHORIZATION). O exit passa de let-run HZ120 (superseded) para: segurar enquanto o regime/tendencia persiste, sair na virada/invalidacao estrutural (hold ate regime virar BEAR, SL estrutural stop-first, cap horizonte). Causal barra-a-barra, DA confirmou NAO e look-ahead (FSM online byte-identico na era de trading). Numeros: SELECT-17 +105.3R (retDD 26x, streak3, DD-4.1) vs let-run120 +36.2R e hold500 +90.3R; FULL-245 ~+385.7R a +399.2R. #6 = winner mecanico +1.15R; o alvo +3R do #6 = leitura humana discricionaria (nao regra mecanica). CAVEATS ACEITOS pelo Cris: (1) ~78% do ganho nos 17 vem de HORIZONTE/exposicao (120->500), nao so inteligencia de regime (detector adiciona ~+15R sobre hold500, 2 topos in-sample); (2) full-base DD ~-72 / streak 22 = hostil a prop -> producao futura exige camada de execucao/risco (gestao DD, modelo de gap nos stops largos 2025). Operacional: NOT_PRODUCTION, NO_RUNTIME, NO_TELEGRAM, NO_AUTO_TRADING, NO_STRATEGY_RULES_WIRING, NO_MONITOR, NO_BROKER, PRODUCTION_PENDING_EXPLICIT_CRIS_AUTHORIZATION. Status canonico: L2_BPT_TREND_EXIT_OFFICIAL_APPROVAL_20260708.md (checkpoint tecnico/DA em L2_BPT_TREND_EXIT_EXPLORATORY_CHECKPOINT_20260708.md).',
  array['seed:memory_delta_open_state_checkpoint_20260708','l2-bpt-trend-exit','user-approved-official-not-production','production-pending-auth','regime-flip-causal','horizonte-vs-regime'],
  'docs/architecture/L2_BPT_TREND_EXIT_OFFICIAL_APPROVAL_20260708.md; docs/project_authority/04_STRATEGY_STATUS_MASTER.md sec 4.4; research/l2_bpt_trailing_exit_test.py',
  'active'
),
(
  md5('seed:memory_delta_open_state_checkpoint_20260708:memory_items:swept-runner-rebased')::uuid,
  'product', 'internal', 'project',
  'XAU 15M LONG swept-runner = RESEARCH_BASE_NOT_OFFICIAL (rebaixado Cris 2026-07-08; ex-OFICIAL_FN revogado)',
  'DECISAO CRIS 2026-07-08: o swept-runner NAO e mais estrategia oficial e NAO e OFICIAL_FN (carimbo anterior REVOGADO). Passa a servir de BASE de markup-demand + base para estudos futuros da 15M LONG + fonte de aprendizado/contexto. NAO pode ser descrito como OFICIAL_FN nem estrategia aprovada oficial. NAO pode ir a producao. NAO pode ser usado para Telegram/runtime/strategy_rules. Metricas historicas (N435 WR47.6% +291.5R / +233.6 SB, r/DD 16.4) ficam como REFERENCIA DE PESQUISA, nao como aprovacao. Status = RESEARCH_BASE_NOT_OFFICIAL. Status master 04 sec 4.5 atualizado.',
  array['seed:memory_delta_open_state_checkpoint_20260708','swept-runner','research-base-not-official','oficial-fn-revogado','not-production'],
  'docs/project_authority/04_STRATEGY_STATUS_MASTER.md sec 4.5; docs/architecture/OPEN_STATE_CHECKPOINT_20260708.md',
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
