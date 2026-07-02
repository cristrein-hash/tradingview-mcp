# SUPABASE MEMORY — WAVE 2C SUB-BATCH 2 VALIDATION (2026-07-02)

**Resultado: PASS ✅ — 200 dos 229 cards migrados (87,3%); base = 210 memory_items.**
**Modo:** validação 100% read-only via MCP (`supabase_read_only_user`). Zero escrita pelo Claude.

## 1. Aplicação (M3 Wave 2C-b)

- `supabase/seeds/memory_cards_wave2c_b_seed.sql` (commit `c276ba5`, tag `seed:memory_cards_wave2c_b`) aplicado **manualmente pelo Cris** via SQL Editor (`20260702_memory_cards_wave2c_b_seed`), cópia via `pbcopy`.
- **Verificação pós-Run no SQL Editor executada pelo Cris (novo protocolo obrigatório): count = 50 ✔** — confirmada ANTES de pedir a M4. Protocolo funcionou como desenhado (lição do incidente 2C-1).

## 2. Counts esperados vs reais

| Métrica | Esperado | Real | |
|---|---|---|---|
| memory_items total | 210 | **210** | ✅ |
| tag wave2c_b | 50 | **50** | ✅ |
| tags wave2a / wave2b / wave2c (intactas) | 50/50/50 | **50/50/50** | ✅ |
| scope private / product | 152 / 58 | **152 / 58** | ✅ |
| status active | 122 | **122** | ✅ |
| archived / dormant / deprecated / superseded / paused | 53/22/11/1/1 | **53/22/11/1/1** | ✅ |

## 3. Amostras recuperadas

Filtro por tag wave2c_b (LIMIT 10): cluster L2/BPT na ordem do seed — findings archived (bearleg_refined, convergence_elimination, episode_reading_276, exit_lab, conv_le1_skip, lineB_rescue, **overfade_irreducible** ✔) e módulos dormant (DSPA, clean_sky, lineB_bull_absorb). Scope/status exatos.

## 4. Role / read-only / conteúdo

`transaction_read_only = on` · `current_user = supabase_read_only_user`. Só os testes autorizados; zero INSERT/UPDATE/DELETE/migration/schema/RLS pelo Claude. Zero RAW/candles/logs/backtests/journal/secrets (grep pré-apply 0 hits; rows = filename + description + tags + source_ref + status).

## 5. Safety report

**BLOCKER=0 · WARNING=1 · INFO=50** — WARNING único = Caminho B TRUE_RISK (preservado).

## 6. Próximos passos (decisões do Cris)

- **Batch final:** ~13 project operacionais/config ainda **ativos** (receiver_broker_prefix, telegram_silencer, tv_layouts, watchlist_focus, replay_historical_base, custom_ob_detector, monitor_targets_leak, pipeline_fase3, roadmap_post_xau_1h, smc_eur/xau_audit, tf_15m_long_liberated) — como batch próprio ou conjunto com a 2D (aprovado na Decisão 3 de 2026-07-02: não forçar como archived).
- **Wave 2D:** ~16 legacy/no-metadata, revisão card a card, `UNKNOWN_REVIEW` quando duvidoso. Reconciliação final da contagem (229 = migrados + finais + legacy) obrigatória no fechamento.
- **Depois:** checkpoint final da migração total → só então reavaliar abertura do XAU 15M.

Progresso: **200/229 cards (87,3%)** + 44 rows Wave 1. Restam **29**.
