# XAU 15M MARKUP-DEMAND — INVENTÁRIO DE ARTIFACTS (estado atual)
**2026-07-09.** Consolidação truth-saving pós-descoberta do event-selection lookahead. Commits: recovery `2a562e1` · SL/exit `9e5e34e` · trailing `f9dff65` · base repair `ed38c47`.

## Bloco 1 — N83 Recovery (VÁLIDO como proveniência)
| ficheiro | tipo | status |
|---|---|---|
| `XAU_15M_MARKUP_DEMAND_FILTER_N83_PREREG.md` | prereg | válido (status atualizado p/ BLOCKED_BASE) |
| `XAU_15M_MARKUP_DEMAND_FILTER_N83_{PREREG_DA,RECOVERY_DA}.md` | DA | válidos |
| `n83_source_recovery_verify.py` (+json) | script/output | válido (SOURCE_RECOVERED; predicado cego 96) |
| `../n96_fase1_fase2_maps.py` · `../results/n96_intra_bear_cut_{list,trades}` | source/output | válidos (proveniência do filtro) |
| `../../docs/architecture/XAU_15M_N96_INTRA_BEAR_CAPITULATION_FILTER_20260708.md` | doc canónico do filtro | válido (filtro); métricas da base = contaminadas |

## Bloco 2 — SL/Exit Review (CONDICIONAL-À-POPULAÇÃO; transferível)
| ficheiro | tipo | status |
|---|---|---|
| `xau_15m_n83_sl_exit_lib.py` | lib (byte-match) | válida (motor) |
| `xau_15m_n83_universe_for_sl_exit.py` (+json) | freeze | válido como reprodução do contaminado |
| `xau_15m_n83_{sl,exit}_audit.py` (+json, +REPORT.md) | audit | ⚠️ JSONs contêm certificação causal ERRADA (`i<j`); corrigida nos MD reports |
| `xau_15m_n83_sl_exit_baseline/sl_review/exit_review/combined/robustness` (+json/MD/DA) | review | condicionais; **SL V1 dominante + 3R robusto = TRANSFERÍVEIS** |
| `xau_15m_n83_exit_trailing.py` + `xau_15m_n83_rlad_robustness.py` (+json, REPORT) | trailing | RLAD = EXPLORATORY only; resto rejeitado |
| `xau_15m_n83_confirmation_leak_check.py` (+json) | leak check | **VÁLIDO — prova do lookahead (94/96)** |
| `XAU_15M_N83_SL_EXIT_FINAL_DA.md` · `..._STATUS_UPDATE.md` | DA/status | válidos (FAIL_LEAK + correções) |

## Bloco 3 — Base Repair Opção B (VÁLIDO, causal)
| ficheiro | tipo | status |
|---|---|---|
| `XAU_15M_MARKUP_DEMAND_BASE_REPAIR_OPTION_B_PREREG.md` | prereg | válido (§6 corrigido pós-DA) |
| `xau_15m_live_fireable_universe.py` (+json, +candidates.csv) | universo causal | **VÁLIDO** (N=166; DA reproduziu 166/166) |
| `xau_15m_live_fireable_source_guard.py` (+json) | guard | PASS |
| `xau_15m_live_fireable_n83_filter.py` (+json) | filtro na base causal | **VÁLIDO** (22L/0W; P 0,0016/0,0047) |
| `xau_15m_live_fireable_n83_robustness.py` (+json) | robustez | válido (marginalidade declarada) |
| `XAU_15M_MARKUP_DEMAND_BASE_REPAIR_{DA,STATUS_UPDATE}.md` | DA/status | válidos (PARTIAL) |
| `XAU_15M_MARKUP_DEMAND_BASE_REPAIR_OPTION_A_PREREG.md` | prereg A | PREREG_ONLY_NOT_TESTED |

## Classificação-resumo
- **INVALIDADO:** base N96/N83 original (+125R/62,7% = HISTORICAL_CONTAMINATED_RESULT).
- **VALIDADO/TRANSFERÍVEL:** Intra-Bear Capitulation Filter (risk-control causal) · SL V1 · exit 3R · universo live-fireable (motor).
- **EXPLORATORY:** RLAD · BULL bucket (lead estrutural).
- **PREREG-ONLY:** Opção A.

## Adenda (DA de consolidação)
| ficheiro | tipo | status |
|---|---|---|
| `../../docs/architecture/XAU_15M_MARKUP_DEMAND_FILTER_N83_GATE_MANIFEST.md` | gate manifest | válido (header corrigido → BLOCKED_BASE) |
| `_x15_extract_baseline.py` · `_x15_extract_repair.py` | helpers display | válidos (sem análise) |
| `../../docs/architecture/XAU_15M_N96_ENTRY_ENGINE_USER_APPROVAL_20260708.md` + `..._INTRA_BEAR_CAPITULATION_FILTER_20260708.md` | docs de aprovação antigos | ⚠️ banners de contaminação adicionados (métricas base = históricas contaminadas; filtro re-validado) |
