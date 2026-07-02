# SUPABASE MEMORY — WAVE 2C PRE-REVIEW (sub-batch 1, 2026-07-02)

**Ficheiro:** `supabase/seeds/memory_cards_wave2c_seed.sql` · **Tag:** `seed:memory_cards_wave2c` · **Estado: CRIADO, NÃO APLICADO.**
**Gerador versionado:** `scripts/memory/generate_wave2c_seed.py` (mesmo contrato 2A/2B; aborta sem description/metadata.type ou padrão proibido).
**Natureza da wave:** archive/index — histórico preservado como memória fria recuperável (rastreabilidade), **não** hot memory. Zero escrita Supabase nesta fase; MCP read-only.

## 1. Contabilidade de cards

- Total: 229 · migrados (2A+2B): 100 · **restantes antes da 2C: 129**
- Elegíveis 2C (com metadata): ~114 (17 reference + ~97 project históricos) · legacy/no-metadata: ~15–16 → 2D
- **Este sub-batch 1 seleciona: 50** (17 reference + 33 project) → restarão **79** (~64 project p/ 2C sub-batch 2 + ~15–16 legacy p/ 2D).

## 2. Cards escolhidos (50)

- **17 reference restantes (prioridade 1):** bubbles_auction_theory · cdp_wedged_diagnosis · cloudflared_tunnel · d2r_daily_logs · hardware · imac_bridge · L2_SMC_definitions_canonicas · long_position_overrides_ticks_bug · market_microstructure_explained_leonardo · market_microstructure_philosophy · mcp_ohlcv_time_range · SMC_Unified_Rebuild_v0_preregistro · svp_value_area_provenance · system_leigo_map · trade_plotting_canonical · xau_4h_backtest_resumo_leonardo · xau_4h_prints_archive.
- **11 project refutados/invalidados/retratados/DEACTIVATED → `deprecated`:** caminho_a_v3_A1_BALANCE (look-ahead) · caminho_a_v3_A1_PRIME_SUPERTREND (look-ahead) · caminho_a_v3_PR50n (refutado Wilson) · xau_15m_direction_short_mirror · xau_15m_macro_bottom · xau_15m_window_cleaning · xau_15m_entry_engine2 · l2_bpt_legbear_block (retratado circular) · l2_bpt_volume_1dbear (artefato tick-volume) · bubbles_nas_shadow (DEACTIVATED) · smc_btc_audit_v3 (fora do foco XAU).
- **6 snapshots de sessão/audits → `archived`:** checkpoint_2026_06_14 · session_2026_05_21 · session_2026_05_22_23 · sessao_autonoma_2026_06_06 · lookahead_audit_2026_06_06 · raw_revalidation_2026_06_03.
- **7 Caminho A trilha histórica:** 6 `archived` (roadmap pós-EUR, F4F5, padrões visuais 5 layers, pending_validations, A1' pré-registro, v3 pré-registro) + `pine_alerts_v1` = **`dormant`** (os 9 Pines mecânicos existem, pesquisa parada).
- **9 Caminho B trilha histórica → `archived`:** fraqueza_2020_2022 · hipoteses_30_grupos · raw_v1_strata_B_C · score_filter · v_stair_exit · v15_AB · v16_composite · v16_vstair_climax · volume_features. (Findings absorvidos; a estratégia Caminho B LONG em si já migrou na 2A como `dormant`.)

## 3. Cards excluídos deste sub-batch (e motivo)

- **~64 project históricos restantes** (labs L2/BPT concluídos, 15M labs/estudos, D2R/pipeline, incidentes resolvidos, SMC/EUR audits, roadmaps antigos etc.) → **2C sub-batch 2** (mesmo protocolo, próxima iteração).
- **~15–16 legacy/no-metadata** (feedback_cadence/partnership/etc., project_d2r_state/oracle_score/pending_work/etc., reference_d2r_mechanics/files) → **2D** (revisão card a card; gerador aborta neles por design).
- `project_l2_bpt_overfade_irreducible_at_entry` — deixado para o sub-batch 2 junto do cluster de findings L2 (evidência condicional, decidir status com o conjunto).

## 4. Distribuição do seed

- **Rows:** 50, só `memory_items` · **Scope:** 3 product/internal (cdp_wedged, mcp_ohlcv_time_range, long_position_ticks_bug — conhecimento genérico de tooling) · 47 private/private.
- **Status:** 16 active (reference lookup ainda válida) · 22 archived · 11 deprecated · 1 dormant. `reference_d2r_daily_logs` = archived (conceito D2R substituído pelo Forward Outcome Layer).
- **Type:** 17 reference · 33 project.

## 5. Exemplos

- `reference_L2_SMC_definitions_canonicas` · private/active — definições SMC canônicas L2 v2.
- `reference_mcp_ohlcv_time_range` · product/active — paging histórico via from_time/to_time.
- `project_caminho_a_v3_A1_BALANCE_OFICIAL` · private/**deprecated** — invalidada 2026-06-06 (look-ahead; artefato −110,6R).
- `project_caminho_b_volume_features` · private/**archived** — features de volume sobre 55 bottoms (trilha absorvida).

## 6. Verificações executadas (pré-apply)

- Grep secrets → **0 hits** · Parse Postgres (sqlglot) → **OK** · 50/50 ids determinísticos + ON CONFLICT · rollback comentado (`delete ... where 'seed:memory_cards_wave2c' = any(tags)`).
- Safety report → **BLOCKER=0 · WARNING=1 (só Caminho B TRUE_RISK) · INFO=50** — critério atendido.
- **Nada aplicado. Zero conexão de escrita.**

## 7. Validação pós-apply (quando autorizada)

Esperado: memory_items total **160** (10+50+50+50) · tag wave2c = **50** · wave2a/wave2b intactas (50/50) · scope: private 102 / product 58 · status: active 121 / archived 22 / deprecated 11 / dormant 5 / paused 1. Sample por tag, read-only, safety, doc de validação.

## 8. Critério de aceitação (pré-apply)

- [x] Seed criado (50 rows) · [x] Gerador versionado · [x] Review criado · [x] Zero escrita Supabase · [x] Safety BLOCKER=0/WARNING=1 (Caminho B) · [x] Commit local, sem push sem autorização.
