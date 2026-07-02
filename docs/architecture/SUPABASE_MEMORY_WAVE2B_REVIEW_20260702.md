# SUPABASE MEMORY — WAVE 2B PRE-REVIEW (2026-07-02)

**Ficheiro:** `supabase/seeds/memory_cards_wave2b_seed.sql` · **Tag:** `seed:memory_cards_wave2b` · **Estado: CRIADO, NÃO APLICADO.**
**Gerador versionado:** `scripts/memory/generate_wave2b_seed.py` (mesmo contrato da 2A; aborta se card sem description, sem metadata.type ou com padrão proibido).
**Zero escrita Supabase nesta fase. MCP read-only. Aplicação futura = manual Cris/SQL Editor (DEV), cópia via `pbcopy` do ficheiro.**

## 1. Contabilidade de cards

- Total de cards: 229 · já migrados (Wave 2A): 50 · **restantes antes da 2B: 179**
- **Wave 2B seleciona: 50** (43 feedback + 7 project) → restarão **129** para 2C/2D.

## 2. Cards escolhidos (50)

- **43 feedback restantes com `metadata.type`** — todo o corpus de método/disciplina ainda ativo: plataforma/execução (anticipate_platform_constraints, audit_full_list_mandatory, full_scan_after_pattern_fix, no_stderr_suppress_in_git, validate_before_manual_user_work, telegram_chat_ids_loop, tv_alert_caches_pine, pine_alert_no_chart_required), estatística/validação (bonferroni, convergent_contextual_vs_aggregate, estatistica_aplicada_realidade, multi_window_validation, outcome_proxy_lift_and_episode, recall_gate_before_backtest, sample_gate_for_rules, dont_conclude_from_broken_period, no_generalize_negative_findings, distance_quality_not_binary), processo (DA_calibrado_veto_vs_reporta, deep_source_reading, defense_in_depth_ordering, defenses_dimensioned_to_signal_origin, check_input_alive_before_code, memory_proactive_consultation, name_vs_definition_mismatch, root_cause_over_symptom, self_verification_protocol, event_driven_failures, raw_data_lookup_order), preferências/colaboração Cris (collaboration_signals, communication_style, em_validacao_term, manual_over_token, no_easy_paths, no_tables_in_chat, review_cadence, chart_cleanup_manual_cris), estratégia/asset (especificidade_ativo, ob_detectors_micro_vs_macro, python_path_for_new_strategies, strategy_validity_gate, validate_plot_id_mapping, xau_only_focus).
- **7 project ativos prioritários:** l2_bpt_consolidated_knowledge · l2_bpt_reader_layer2_library_and_dossier · l2_bpt_loser_cuts_consolidated · l2_bpt_trade_qualification_engine · xau_15m_fase1_state · macro_structural_reading_engine · indicator_signals_pipeline.

## 3. Cards excluídos da 2B (e motivo)

- **~16 legacy/no-metadata** (feedback_cadence, memory_methodology, partnership, session_persistence, statistical_patience, trades_in_chat; project_d2r_state, execution_context, external_factors, naming_proposal, operational_decisions, oracle_score, pending_work, xau_losing_patterns; reference_d2r_mechanics, reference_files) → **Wave 2D** (revisão card a card; gerador aborta neles por design).
- **Project históricos/refutados/sessão/superseded** (~96: caminho_a/b research trail, labs refutados, sessões consolidadas, bugs resolvidos, DEACTIVATED) → **Wave 2C** como archive/index com status próprio.
- **Reference restantes** (19: microstructure, SMC definitions, hardware, bridges, plotting canônico, etc.) → **Wave 2C**.

## 4. Distribuição do seed

- **Rows:** 50, só `memory_items` (1 card = 1 row).
- **Scope:** 29 product/internal (método/disciplina genéricos) · 21 private/private (preferências do Cris, estratégia/asset-specific, project L2/15M).
- **Status:** 50 active (nenhum superseded/dormant nesta wave — histórico vai na 2C com status próprio).
- **Type:** 43 feedback · 7 project.
- Body = frontmatter description (resumo curado); corpo integral só no card local via source_ref.

## 5. Exemplos

- `feedback_anticipate_platform_constraints` · product/internal/feedback/active — "antecipar limites da plataforma ANTES de agir em lote".
- `feedback_xau_only_focus` · private/private/feedback/active — foco operacional exclusivo XAU.
- `project_l2_bpt_consolidated_knowledge` · private/private/project/active — conhecimento consolidado L2/BPT (legpos = eixo causal validado).
- `project_indicator_signals_pipeline` · private/private/project/active — pipeline de coleta passiva.

## 6. ⚠️ Item sinalizado para revisão do Cris (migrado como active, sem alteração)

- `feedback_strategy_validity_gate` ("estratégia VÁLIDA se win% ≥ 70%") — **possível tensão** com canon posterior (engine = lucro/expectancy, não winrate; FundedNext WR 50–60%). Migrado fielmente como active por ser parâmetro definido pelo Cris; decisão de supersedê-lo é sua (se sim: status='superseded' num batch delta + atualizar card local).

## 7. Verificações executadas (pré-apply)

- Grep secrets (`SERVICE_ROLE|sbp_|eyJ|password|api_key`) → **0 hits**.
- Parse Postgres (sqlglot) → **OK** (begin + insert + commit).
- 50/50 ids determinísticos `md5('seed:memory_cards_wave2b:<filename>')::uuid` + ON CONFLICT.
- Safety report → **BLOCKER=0 · WARNING=1 (só Caminho B TRUE_RISK) · INFO=50** — critério atendido (gerador 2B não dispara o scanner; regra GUARDRAIL_CARD cobre filenames guardrail).
- **Nada aplicado. Zero conexão de escrita.**

## 8. Rollback

```sql
delete from memory_items where 'seed:memory_cards_wave2b' = any(tags);
```
(bloco comentado no fim do seed; ids recomputáveis para delete cirúrgico; independente das tags Wave 1/2A.)

## 9. Validação pós-apply (quando autorizada)

Counts esperados: memory_items total **110** (10 W1 + 50 W2A + 50 W2B) · tag wave2b = **50** · scope: private 55 / product 55 · status: active 105 / dormant 4 / paused 1. Sample por tag, read-only reconfirmado, safety report, doc de validação.

## 10. Critério de aceitação Wave 2B (pré-apply)

- [x] Seed criado (50 rows ≤ 50)
- [x] Gerador versionado
- [x] Review doc criado (este)
- [x] Zero escrita Supabase
- [x] Safety: BLOCKER=0, WARNING=1 (apenas Caminho B real)
- [x] Commit local (sem push — aguarda autorização)
