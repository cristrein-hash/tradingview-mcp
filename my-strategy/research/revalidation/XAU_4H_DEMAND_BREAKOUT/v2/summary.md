# XAU_4H_DEMAND_BREAKOUT — Revalidation v2 (summary)

Generated: 2026-05-28T02:36:24.983661+00:00  ·  commit: `698c708677`

## Decision (recommendation only — lab never writes catalog)
**result_status: `fail`**  ·  reconciliation_status: `LEGACY_NOT_REPRODUCIBLE`
- recommended: validation_status → `REJECTED`, deployment → `DISABLED/NOT_DEPLOYED`
- rationale: avg_R=-0.1923, PF=0.7368 — no edge.

## Technical validity (Stage 1)
- no_future_leak: True
- entry == next-bar open: True
- all stop_distance > 0: True
- **technically_valid: True**

## Phase 1 — Reconciliation
Legacy targets: {'win_rate': 0.838, 'n': 80, 'avg_R_close_only': 2.43, 'sum_R': 194.57, 'metric': 'close_only_H20'}
- canonical window_84: signals_total=58 | 2023-2026=15 | H20 win(from signal close)=66.67% (n=15) | H10 win=73.33%
- canonical window_40: signals_total=79 | 2023-2026=24 | H20 win(from signal close)=62.5% (n=24) | H10 win=66.67%
- v6 dump signals: 27
  - overlap: canonical_w40=79 | v6=27 | intersection=17 | only_canonical=62 | only_v6=10
  - v6 diag: {'files': 8, 'records_total': 4320, 'records_with_ohlcv': 4320, 'records_with_cob_boxes': 4315, 'records_in_zone': 625, 'records_nas_in_band': 674, 'records_dist14_in_band': 1603, 'records_with_forming_last': 3962, 'signal_records': 37, 'unique_signal_epochs': 27}

## Phase 2 — R-real (stop=demand_zone_low primary, 2R, gross)
- raw candidate bars (inside_demand_zone): 2536
- canonical signals w84: 58
- canonical signals w40: 79
- R-real trades (primary stop): 52  ·  right-censored: 0
- n: 52  ·  win%: 26.92  ·  avg_R: -0.1923  ·  median_R: -1.0
- sum_R: -10.0  ·  PF: 0.7368  ·  max losing streak: 11
- sum_R ex-top5: -20.0  ·  ex-top10: -30.0
- MFE_R mean: 1.8028  ·  MAE_R mean: -3.9604
- exit mix: {'target': 14, 'stop': 38, 'time_limit': 0}

## By regime (sum_R / n / win%)
- _total: sum_R -10.0 / n 52 / win% 26.92
- _ex_covid: sum_R -6.0 / n 48 / win% 29.17
- _covid_only: sum_R -4.0 / n 4 / win% 0.0
- covid: sum_R -4.0 / n 4 / win% 0.0
- gold_bull_recent: sum_R -4.0 / n 13 / win% 23.08
- inflation_bear_macro: sum_R -3.0 / n 12 / win% 25.0
- pre_covid: sum_R 1.0 / n 23 / win% 34.78

## By cost (net R)
- cost 0: sum_net_R -10.0 / avg -0.1923 / win% 26.92
- cost 0.2: sum_net_R -17.1859 / avg -0.3305 / win% 26.92
- cost 0.5: sum_net_R -27.9649 / avg -0.5378 / win% 26.92

## By target
- 1R: n 52 / win% 30.77 / sum_R -20.0 / mix {'target': 16, 'stop': 36, 'time_limit': 0}
- 2R: n 52 / win% 26.92 / sum_R -10.0 / mix {'target': 14, 'stop': 38, 'time_limit': 0}
- 3R: n 52 / win% 19.23 / sum_R -12.0 / mix {'target': 10, 'stop': 42, 'time_limit': 0}

## By stop variant
- demand_zone_low: n 52 / win% 26.92 / sum_R -10.0 / PF 0.7368
- structural_3_low: n 50 / win% 16.0 / sum_R -26.0 / PF 0.381
- atr_1_5: n 42 / win% 35.71 / sum_R -3.5278 / PF 0.8655

## Warnings
- LEGACY_NOT_REPRODUCIBLE: canonical close-only != legacy 83.8%; merit verdict capped at 'pass' (no VALIDATED).

_See report.json for full provenance + signal funnel + v6 dump diagnostics. trades.jsonl is gitignored (regenerable from config + canonical data + the recorded commit)._
