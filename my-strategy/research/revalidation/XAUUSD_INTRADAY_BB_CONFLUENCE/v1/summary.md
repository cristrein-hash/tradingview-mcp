# XAUUSD INTRADAY BB CONFLUENCE — Historical Lab v1 — Summary

- Strategy: `XAUUSD_INTRADAY_BB_CONFLUENCE`

- Config: `ZONE_REJECTION_v1`

- Generated: 2026-06-01T13:26:00.327568+00:00

- 15M window: 2024-05-24T23:59:59+00:00 → 2026-05-25T00:14:59+00:00

- Bars: 15M=47031  1H=11764  4H=15413  1D=3576

- Trades collected: **2168** (LONG=992, SHORT=1176)

- Discards: zone_missing=2119  risk_skip=12  atr_null=55


## Totals (primary outcome at 20 15M-bars)

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALL | 2168 | 0.417 | -0.001 | -1.46 | 0.999 | +1.09 | -1.01 |

## By direction

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| LONG | 992 | 0.456 | +0.074 | +73.51 | 1.158 | +1.11 | -1.04 |
| SHORT | 1176 | 0.384 | -0.064 | -74.97 | 0.879 | +1.08 | -0.99 |

## By zone_tf

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1H | 1514 | 0.406 | +0.003 | +3.99 | 1.005 | +1.20 | -1.13 |
| 4H | 654 | 0.443 | -0.008 | -5.44 | 0.979 | +0.83 | -0.75 |

## By zone_type

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| DEMAND | 992 | 0.456 | +0.074 | +73.51 | 1.158 | +1.11 | -1.04 |
| SUPPLY | 1176 | 0.384 | -0.064 | -74.97 | 0.879 | +1.08 | -0.99 |

## By regime_1d (entry year bucket)

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| bull_recent | 2168 | 0.417 | -0.001 | -1.46 | 0.999 | +1.09 | -1.01 |

## By bubble_context

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| absorption_base | 26 | 0.346 | -0.373 | -9.70 | 0.407 | +0.84 | -0.98 |
| continuation_support | 256 | 0.383 | -0.090 | -23.10 | 0.827 | +0.95 | -0.94 |
| none | 1705 | 0.420 | +0.011 | +18.18 | 1.021 | +1.09 | -1.02 |
| rejection_supply | 8 | 0.500 | +0.528 | +4.23 | 2.120 | +2.38 | -0.91 |
| unclear | 173 | 0.445 | +0.052 | +8.94 | 1.107 | +1.25 | -1.10 |

## By rsi_context

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| bear_divergence | 20 | 0.550 | +0.147 | +2.94 | 1.349 | +1.13 | -0.79 |
| bull_confirmation | 11 | 0.091 | -0.679 | -7.47 | 0.211 | +1.30 | -1.68 |
| exhaustion | 53 | 0.491 | +0.219 | +11.60 | 1.491 | +1.30 | -0.84 |
| neutral_no_trigger | 746 | 0.441 | +0.040 | +30.08 | 1.086 | +1.06 | -0.89 |
| overextended | 62 | 0.419 | -0.007 | -0.43 | 0.986 | +1.03 | -0.90 |
| unclear | 1276 | 0.400 | -0.030 | -38.18 | 0.942 | +1.10 | -1.10 |

## By location_quality (auction)

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| acceptable | 1853 | 0.424 | +0.008 | +14.75 | 1.016 | +1.07 | -0.99 |
| bad | 136 | 0.346 | -0.074 | -10.00 | 0.879 | +1.30 | -1.25 |
| good | 86 | 0.523 | +0.266 | +22.86 | 1.639 | +1.18 | -0.89 |
| unclear | 93 | 0.290 | -0.312 | -29.06 | 0.517 | +1.20 | -1.33 |

## By SMC recent BOS / CHoCH

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| BOS present | 1336 | 0.407 | -0.022 | -28.91 | 0.958 | +1.11 | -1.05 |
| BOS absent | 832 | 0.433 | +0.033 | +27.45 | 1.068 | +1.05 | -0.96 |
| CHoCH present | 1371 | 0.427 | +0.011 | +15.59 | 1.024 | +1.06 | -0.99 |
| CHoCH absent | 797 | 0.399 | -0.021 | -17.05 | 0.959 | +1.14 | -1.06 |

## By NAS labels in last 15 bars

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| NAS LONG present | 392 | 0.454 | +0.098 | +38.51 | 1.201 | +1.24 | -1.10 |
| NAS LONG absent | 1776 | 0.409 | -0.023 | -39.97 | 0.955 | +1.06 | -0.99 |
| NAS SHORT present | 436 | 0.388 | -0.096 | -41.86 | 0.816 | +1.03 | -1.00 |
| NAS SHORT absent | 1732 | 0.424 | +0.023 | +40.40 | 1.047 | +1.10 | -1.02 |

## By Bubble buy/sell recent

| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |
|---|---:|---:|---:|---:|---:|---:|---:|
| BUY bubble recent | 611 | 0.355 | -0.142 | -86.95 | 0.748 | +1.04 | -1.05 |
| no BUY bubble | 1557 | 0.441 | +0.055 | +85.50 | 1.116 | +1.11 | -1.00 |
| SELL bubble recent | 458 | 0.404 | -0.001 | -0.50 | 0.998 | +1.24 | -1.19 |
| no SELL bubble | 1710 | 0.420 | -0.001 | -0.95 | 0.999 | +1.05 | -0.97 |

## Exit reasons

- `hit_target_2`: 387
- `hit_stop`: 1000
- `timeout`: 781

## Notes

- Zones use Custom OB (canonical slim representation of BigBeluga-style zones).
- Parent 1H/4H bars looked up by `bisect_right(ts) - 1` (no lookahead).
- Primary outcome window = 20 15M-bars (5 hours). Secondary 40-bar window recorded per-trade in `secondary_40bar_R` for inspection but not aggregated here.
- v1 has no optimization, no filter sweep, no threshold tuning.
- Auction dimensions (location_quality, supply_overhead, demand_below) are diagnostic only.
