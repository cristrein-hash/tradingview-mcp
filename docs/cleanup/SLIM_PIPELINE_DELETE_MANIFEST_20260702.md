# SLIM PIPELINE — DELETE MANIFEST (2026-07-02)

**Decisão:** `DELETE_APPROVED` (Cris 2026-07-02) — remover scripts slim-pipeline de `scripts/` do código ativo.
**Motivo:** SLIM está permanentemente rejeitado como input/validação no Trading System (trava `feedback_never_use_slim_features`). Estes scripts produzem/consomem `slim_features/`.
**Commit base (antes da remoção):** `0bdbfd3` (origin/main sincronizado).
**Proibições respeitadas:** não tocar RAW/source, produção, `strategy_rules`, catalog, monitor, Telegram, runtime, RTSE, EF v2, governança, rulers RAW.

## Ficheiros REMOVIDOS (git rm) — 4 unambíguos
| Path | Papel slim | Porque é seguro remover |
|---|---|---|
| `scripts/backtest_xau_1h_auction_confluence_lab_v1.py` | consumidor slim (`SLIM_BASE .../slim_features`) | **zero referências vivas** (nenhum import/doc/produção) |
| `scripts/backtest_xau_intraday_bb_confluence_v1.py` | consumidor slim (`SLIM_BASE .../slim_features`) | **zero referências vivas** |
| `scripts/backtest_xau_4h_capitulation_v2.py` | consumidor slim (schema 2) | estratégia `XAU_4H_REVERSAL_CAPITULATION` = **REJECTED** (status master); só referência em `methodology.md` (doc histórico), nenhum import de código vivo |
| `scripts/run_signal_outcome_lab.py` | consumidor slim (`SLIM_ROOT .../slim_features`) | lab `SIGNAL_OUTCOME_LAB` = **"design only, not implemented"**; só referência = 1 entrada de permissão em `settings.local.json` (grep) + design docs; nenhum import de código vivo |

**Confirmação:** nenhum dos 4 é production/monitor/strategy_rules/catalog/Telegram/runtime/RAW/RTSE/EF v2/governança/ruler. Nenhum é importado por código vivo. Todos eram slim-pipeline (HISTORICAL_ONLY / DO_NOT_USE_FOR_VALIDATION).

## Ficheiros NÃO removidos (DEFERIDOS — aguardam decisão do Cris)
Regra #8 (ambiguidade → parar). Estão entrelaçados com um **ACTIVE_CANDIDATE** e/ou uso RAW-in-memory:

| Path | Porque NÃO foi removido |
|---|---|
| `scripts/extract_replay_features.py` | É o "Canonical Feature Extraction Layer (schema v2)". Além de emitir slim, é **importado in-memory sobre RAW** por `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/build_entry_anatomy.py` (`import extract_replay_features as cx # AUDITED canonical interpreter (applied to RAW in-memory)`). D1A/Breakout Continuation = **ACTIVE_CANDIDATE**. Apagar quebraria o pipeline RAW-first de um candidato vivo. |
| `scripts/build_crosstf_dataset.py` | **`import` duro** por `scripts/backtest_xau_4h_breakout_continuation_v1.py` (backtest do ACTIVE_CANDIDATE `XAUUSD_4H_BREAKOUT_CONTINUATION`) e `scripts/backtest_xau_4h_demand_breakout_v2.py`. Decisão de cluster: remover os três juntos OU manter. |

**Nota de cluster:** `backtest_xau_4h_breakout_continuation_v1.py` e `backtest_xau_4h_demand_breakout_v2.py` são eles próprios slim-pipeline (importam `build_crosstf_dataset`). Se o Cris decidir remover o cluster slim completo, estes 2 + os 2 deferidos saem juntos; se manter o ACTIVE_CANDIDATE, ficam todos.

## Verificação pós-remoção
Ver `git status --short` e `git diff --stat --cached` no commit "Delete obsolete SLIM pipeline scripts". Nenhum ficheiro vivo/produção tocado.
