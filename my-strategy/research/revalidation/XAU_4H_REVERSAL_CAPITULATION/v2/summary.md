# XAU_4H_REVERSAL_CAPITULATION — Revalidation v2 (summary)

Generated: 2026-05-28T01:02:32.146081+00:00  ·  code_commit: `ce2abd6db6`

## Decision (recommendation only — lab never writes catalog)
**result_status: `fail`**
- recommended: validation_status → `REJECTED`, deployment → `DISABLED/NOT_DEPLOYED`
- rationale: avg_R=-0.3145, PF=0.4731 — no edge.

## Technical validity (Stage 1)
- no_future_leak: True (rsi leak count 0)
- entry == next-bar open: True
- all stop_distance > 0: True
- **technically_valid: True**

## Signal funnel
- raw NAS LONG events: 452
- primary full-condition signals: 74
- event-only signals: 57
- trades (primary, post no-overlap): 36  (right-censored: 0)
- mode that better approximates legacy n≈86: **primary** (primary 74 vs event-only 57)

## Aggregate (primary mode, 2R target, gross R)
- n: 36  ·  win%: 33.33  ·  avg_R: -0.3145  ·  median_R: -1.0
- sum_R: -11.322  ·  PF: 0.4731  ·  max losing streak: 7
- sum_R ex-top5: -18.8599  ·  ex-top10: -21.1354
- MFE_R mean: 0.7819  ·  MAE_R mean: -1.0416
- exit mix: {'target': 2, 'stop': 21, 'time_limit': 13}

## By regime (sum_R / n / win%)
- _total: sum_R -11.322 / n 36 / win% 33.33
- _ex_covid: sum_R -8.7513 / n 31 / win% 35.48
- _covid_only: sum_R -2.5707 / n 5 / win% 20.0
- covid: sum_R -2.5707 / n 5 / win% 20.0
- gold_bull_recent: sum_R 1.8895 / n 7 / win% 42.86
- inflation_bear_macro: sum_R -3.5554 / n 13 / win% 46.15
- pre_covid: sum_R -7.0854 / n 11 / win% 18.18

## By cost (net R)
- cost 0: sum_net_R -11.322 / avg -0.3145 / win% 33.33
- cost 0.2: sum_net_R -11.7505 / avg -0.3264 / win% 33.33
- cost 0.5: sum_net_R -12.3925 / avg -0.3442 / win% 33.33

## By target
- 1R: n 36 / win% 41.67 / sum_R -6.7537 / mix {'target': 10, 'stop': 18, 'time_limit': 8}
- 2R: n 36 / win% 33.33 / sum_R -11.322 / mix {'target': 2, 'stop': 21, 'time_limit': 13}
- 3R: n 36 / win% 33.33 / sum_R -10.6145 / mix {'target': 1, 'stop': 21, 'time_limit': 14}

_See report.json for full provenance + ATR validation. trades.jsonl is gitignored (regenerable from config.json + canonical data + the recorded commit)._
