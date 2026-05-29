# XAUUSD 4H BREAKOUT_CONTINUATION v1 — Revalidation Summary

- Generated: 2026-05-29T00:10:54.936206+00:00
- git: 5c34af217284
- Data: canonical 4H slim · 15187 bars · 2016-05-24 → 2026-05-22
- Method: replay_real_rt_canonical_slim
- Config: S_full_trend_htf
- Primary target: 4R · max_hold: 24 bars

## Aggregate

| Metric | Value |
|---|---:|
| signals | 261 |
| trades | 115 |
| win_rate | 0.3043 |
| avg_R | +0.2198 |
| total_R | +25.2778 |
| PF | 1.479 |
| BE moves | 57 |
| right-censored | 29 |

## Exit reasons

- `stop_be`: 25
- `stop`: 52
- `time_limit`: 29
- `target`: 9

## By regime

| regime | n | win_rate | avg_R | total_R |
|---|---:|---:|---:|---:|
| pre_covid | 22 | 0.3182 | +0.0951 | +2.0931 |
| bull_pre_covid | 14 | 0.3571 | +0.5329 | +7.4608 |
| covid_rally | 10 | 0.2000 | +0.3634 | +3.6343 |
| chop_post_covid | 8 | 0.1250 | -0.1250 | -1.0000 |
| chop_inflation_bear | 11 | 0.1818 | -0.4684 | -5.1522 |
| chop_macro | 10 | 0.3000 | +0.1822 | +1.8222 |
| bull_recent | 40 | 0.3750 | +0.4105 | +16.4196 |

## Legacy aggregate comparison (informational)

- legacy: n=234, pf=1.64, win=0.286, total_net_r=64.57
- canonical v1: n=115, pf=1.479, win=0.3043, total_R=+25.2778
- _note_: Aggregate-vs-aggregate informational comparison only — legacy lacks trade-level dump.
