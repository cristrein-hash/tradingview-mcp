# SUPABASE MEMORY — WAVE 2C SUB-BATCH 2 PRE-REVIEW (2026-07-02)

**Ficheiro:** `supabase/seeds/memory_cards_wave2c_b_seed.sql` · **Tag:** `seed:memory_cards_wave2c_b` · **Estado: CRIADO, NÃO APLICADO.**
**Gerador versionado:** `scripts/memory/generate_wave2c_b_seed.py`. **Ficheiros do sub-batch 1 intocados** (verificado via git status).
**Natureza:** archive/index de project históricos — research morto fica frio (archived/deprecated/superseded/dormant), nunca reativado como hot memory. Zero escrita Supabase nesta fase; MCP read-only.

## 1. Contabilidade de cards

- Total: 229 · migrados (2A+2B+2C-1): 150 · **restantes antes da 2C-b: 79**
- **Este sub-batch seleciona: 50** → restarão **29**: ~13 project operacionais/config com metadata + ~16 legacy/no-metadata (ver §3).

## 2. Cards escolhidos (50 — todos private, type project)

- **Cluster L2/BPT (14, prioridade 2 do escopo):** findings históricos → archived (bearleg_refined, convergence_elimination, episode_reading_276, exit_lab_regime_bound, conv_le1_skip, lineB_bottom_add_rescue, **overfade_irreducible** ✔ conforme sinalizado, rabbithole_audit, raw_backbone_rebuild, svp_acceptance_raw) · módulos definidos-mas-pausados → dormant (DSPA, feature_clean_sky pré-aprovada, lineB_bull_absorb pré-aprovada, telegram_bear_flags_FUTURE).
- **Cluster XAU 15M (10):** labs/estudos → archived (bb_nas_kickoff, bubbles_nas_clusters, engine_learnings, range_t2_t3, reversal_power, session_patterns, sl_exit_entry_lab) · linhas pausadas → dormant (bottom_power_engine, managed_agents_engine, transversal_monforte).
- **Linhagem 4H/1H (11):** `xau_4h_long_FINAL_l1_l2_approved` = **active** (capstone — registro final da suite aprovada, ainda vigente) · `reversal_v1_4g_rws_a6` = **superseded** (substituída pela A6-A7, que migrou na 2A como dormant) · dormant (breakout_d1a_maturation, reversal_capitulation, reversal_discretionary, reversal_v1_4j, zone_touch_smc, xau_1h_demand_reclaim v1.1 — camada pausada) · archived (backtest_v1, discr_v1_base_sweep frozen, l1_refinement_approved — absorvida no capstone).
- **Findings bubbles/CF/MTF (4) → archived:** bubble_gate_relaxed_by_tf, bubble_sell_regime_dependent, cf_vs_obs_v2, mtf_gate_audit.
- **Registros/bugs resolvidos/planos (11):** archived (alerts_dataset_full, autonomous_execution_plan, cdp_chart_lock, d2r_indicator_appendix, hard_blocks_refactor, indicator_signals_dedup_bug, pine_slot_duplicate_bug) · dormant (creative_strategy_engine, enrich_outcomes_v2, forward_outcome_layer_spec, hard_blocks_mechanical_subset).

## 3. Cards excluídos deste sub-batch (e motivo)

- **~13 project operacionais/config com metadata** — ainda ATIVOS (não são "histórico", não pertencem tematicamente a esta wave de archive): receiver_broker_prefix_normalization, telegram_silencer_observacao, tv_layouts_architecture, watchlist_focus_5_plus_usousd, replay_historical_base_multitf, custom_ob_detector_v10, monitor_targets_leak, pipeline_fase3, roadmap_post_xau_1h_v1, smc_eur_audit_v3, smc_xau_audit_v3, tf_15m_long_liberated (+ eventual card não listado, reconciliação final no próximo batch). **Proposta: batch final conjunto com a 2D** (ou mini-batch 2C-c separado — decisão do Cris na abertura da 2D).
- **~16 legacy/no-metadata** → **Wave 2D** (revisão card a card; gerador aborta neles por design).

## 4. Distribuição do seed

- **Rows:** 50, só `memory_items` · **Scope:** 50 private/private (0 product — tudo research/estratégia).
- **Status:** 1 active · 31 archived · 17 dormant · 1 superseded · 0 deprecated (os refutados claros já migraram na 2C-1).
- **Type:** 50 project.

## 5. Exemplos

- `project_l2_bpt_overfade_irreducible_at_entry_2026_06_23` · **archived** — over-fade não resolvível na entrada; separadores refutados (finding preservado como evidência condicional).
- `project_xau_4h_long_FINAL_l1_l2_approved` · **active** — capstone: XAU 4H LONG finalizada (L1 EMA21 + L2/BPT aprovados).
- `project_xau_4h_reversal_v1_4g_rws_a6` · **superseded** — substituída pela V1.4g-RWS-A6-A7.
- `project_l2_bpt_lineB_bull_absorb_preapproved` · **dormant** — PRE_APPROVED_PENDING_VALIDATION.

## 6. Verificações executadas (pré-apply)

- Grep secrets → **0 hits** · Parse Postgres (sqlglot) → **OK** · 50/50 ids determinísticos + ON CONFLICT · rollback comentado por tag.
- Ficheiros do sub-batch 1 (`wave2c_seed.sql`, `generate_wave2c_seed.py`, review) **intocados** ✔.
- Safety report → **BLOCKER=0 · WARNING=1 (só Caminho B TRUE_RISK) · INFO=50**.
- **Nada aplicado. Zero conexão de escrita.**
- Header do seed inclui a **verificação pós-Run obrigatória** (Decisão Cris 2026-07-02): `SELECT count(*) FROM memory_items WHERE tags @> ARRAY['seed:memory_cards_wave2c_b'];` esperado **50** no próprio SQL Editor, antes de pedir M4.

## 7. Validação pós-apply (quando autorizada)

Esperado: memory_items total **210** (160 + 50) · tag wave2c_b = **50** · tags anteriores intactas (50/50/50) · scope: private 152 / product 58 · status: active 122 / archived 53 / deprecated 11 / dormant 22 / superseded 1 / paused 1.

## 8. Critério de aceitação (pré-apply)

- [x] Seed criado (50 rows) · [x] Gerador versionado · [x] Review criado · [x] Zero escrita Supabase · [x] Safety BLOCKER=0/WARNING=1 (Caminho B) · [x] Sub-batch 1 preservado · [x] Commit local, sem push sem autorização.
