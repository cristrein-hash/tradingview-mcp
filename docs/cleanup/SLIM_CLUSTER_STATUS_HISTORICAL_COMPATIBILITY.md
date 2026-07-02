# SLIM CLUSTER — STATUS DE COMPATIBILIDADE HISTÓRICA (2026-07-02)

**Decisão (Cris 2026-07-02):** NÃO apagar este cluster enquanto o D1A / Breakout Continuation for `ACTIVE_CANDIDATE`. Distinção crítica:
- **SLIM como dado/proxy/validação → morto, proibido, deletável** (ver `SLIM_PIPELINE_DELETE_MANIFEST_20260702.md`: 4 scripts já removidos).
- **Código que usa RAW in-memory e só tem herança/nome/ramificação SLIM → NÃO apagar se sustenta candidato vivo.**

## STATUS aplicado a este cluster
`HISTORICAL_COMPATIBILITY` · `RAW_IN_MEMORY_ALLOWED` · `SLIM_MODE_FORBIDDEN` · `DO_NOT_USE_SLIM_FOR_VALIDATION`

## Ficheiros mantidos (4)
| Path | Papel | Porque fica |
|---|---|---|
| `scripts/extract_replay_features.py` | Canonical Feature Extraction Layer (schema v2). Tem 2 modos: (a) emite `slim_features/` = **PROIBIDO**; (b) interpretação **RAW in-memory** = **PERMITIDO** | Importado in-memory sobre RAW por `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/build_entry_anatomy.py` como "AUDITED canonical interpreter". Apagar quebra reprodutibilidade do candidato vivo. |
| `scripts/build_crosstf_dataset.py` | Join cross-timeframe (crosstf_v2) | `import` duro por `backtest_xau_4h_breakout_continuation_v1.py` (backtest do ACTIVE_CANDIDATE) e `backtest_xau_4h_demand_breakout_v2.py`. |
| `scripts/backtest_xau_4h_breakout_continuation_v1.py` | Backtest do ACTIVE_CANDIDATE `XAUUSD_4H_BREAKOUT_CONTINUATION` | Importa `build_crosstf_dataset`; sustenta candidato vivo. |
| `scripts/backtest_xau_4h_demand_breakout_v2.py` | Backtest (demand breakout) | Importa `build_crosstf_dataset`; parte do cluster. |

## Regras de uso (obrigatórias)
1. **Modo SLIM proibido:** não gerar/consumir `slim_features/` como input de qualquer nova validação/estratégia.
2. **Uso RAW in-memory permitido** apenas para reprodutibilidade/candidato vivo (interpretação aplicada a RAW, sem passar por ficheiros slim).
3. **Qualquer validação futura exige RAW mapping explícito** (source-field trace), nunca slim.
4. **Se o D1A/Breakout Continuation deixar de ser ACTIVE_CANDIDATE**, apagar o cluster completo (estes 4) num commit próprio com manifest.

## Referência
- Trava permanente: `feedback_never_use_slim_features` (memória do projeto).
- Manifest de remoção dos 4 slim já apagados: `docs/cleanup/SLIM_PIPELINE_DELETE_MANIFEST_20260702.md`.
- Status do candidato: `docs/project_authority/04_STRATEGY_STATUS_MASTER.md` (§3, `XAUUSD_4H_BREAKOUT_CONTINUATION = ACTIVE_CANDIDATE`).
