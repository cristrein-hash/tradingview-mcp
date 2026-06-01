# XAUUSD 1H AUCTION CONFLUENCE LAB v1 — Summary

- Strategy: `XAUUSD_1H_AUCTION_CONFLUENCE_LAB`
- Config: `AUCTION_v1`
- Generated: 2026-06-01T14:24:33.663616+00:00
- 1H window: 2024-05-24T23:59:59+00:00 → 2026-05-25T00:59:59+00:00
- Bars: 1H=11764 4H=15413 1D=3576
- **Trades:** 295
- Per-archetype counts: {'A5_BAD_SHORT_IN_BULL_REGIME': 64, 'A2_CLEAN_DEMAND_REJECTION_LONG': 74, 'A1_DEMAND_ABSORPTION_LONG': 151, 'A3_BAD_FALLING_KNIFE_LONG': 6}
- Discards: atr_null=26 no_zone_long=0 no_zone_short=585 risk_skip=0

## Totals

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALL | 295 | 0.437 | +0.119 | +35.06 | 1.228 | +1.20 | -1.09 |

## By archetype

| Archetype | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1_DEMAND_ABSORPTION_LONG | 151 | 0.444 | +0.066 | +10.03 | 1.128 | +1.06 | -1.02 |
| A2_CLEAN_DEMAND_REJECTION_LONG | 74 | 0.473 | +0.280 | +20.75 | 1.586 | +1.25 | -1.02 |
| A3_BAD_FALLING_KNIFE_LONG | 6 | 0.500 | +0.500 | +3.00 | 2.000 | +2.68 | -4.71 |
| A5_BAD_SHORT_IN_BULL_REGIME | 64 | 0.375 | +0.020 | +1.28 | 1.034 | +1.33 | -1.01 |

## By direction

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| LONG | 231 | 0.455 | +0.146 | +33.78 | 1.289 | +1.17 | -1.12 |
| SHORT | 64 | 0.375 | +0.020 | +1.28 | 1.034 | +1.33 | -1.01 |

## By zone_tf

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1H | 213 | 0.437 | +0.153 | +32.65 | 1.289 | +1.25 | -1.09 |
| 4H | 82 | 0.439 | +0.029 | +2.41 | 1.059 | +1.08 | -1.11 |

## By location_quality

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| acceptable | 262 | 0.435 | +0.093 | +24.32 | 1.177 | +1.13 | -1.04 |
| bad | 6 | 0.500 | +0.500 | +3.00 | 2.000 | +2.78 | -1.01 |
| good | 25 | 0.480 | +0.370 | +9.26 | 1.780 | +1.59 | -0.77 |
| unclear | 2 | 0.000 | -0.760 | -1.52 | 0.000 | +0.34 | -12.46 |

## By rsi_context

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| bull_confirmation | 1 | 0.000 | -1.000 | -1.00 | 0.000 | +0.34 | -1.83 |
| exhaustion | 5 | 0.200 | -0.400 | -2.00 | 0.500 | +1.86 | -6.61 |
| neutral_no_trigger | 91 | 0.418 | +0.027 | +2.45 | 1.049 | +1.15 | -1.06 |
| overextended | 13 | 0.692 | +0.761 | +9.90 | 3.662 | +1.35 | -0.69 |
| unclear | 185 | 0.438 | +0.139 | +25.72 | 1.270 | +1.20 | -0.98 |

## By Bubbles (buy_recent / sell_recent)

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| BUY recent yes | 25 | 0.560 | +0.486 | +12.15 | 2.134 | +1.29 | -1.04 |
| BUY recent no | 270 | 0.426 | +0.085 | +22.91 | 1.160 | +1.19 | -1.10 |
| SELL recent yes | 127 | 0.417 | -0.015 | -1.88 | 0.973 | +1.08 | -1.20 |
| SELL recent no | 168 | 0.452 | +0.220 | +36.94 | 1.432 | +1.29 | -1.01 |

## By NAS labels (last 15 bars)

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| NAS LONG present | 70 | 0.471 | +0.135 | +9.42 | 1.276 | +1.18 | -1.22 |
| NAS LONG absent | 225 | 0.427 | +0.114 | +25.64 | 1.214 | +1.21 | -1.05 |
| NAS SHORT present | 59 | 0.492 | +0.305 | +18.02 | 1.620 | +1.28 | -1.10 |
| NAS SHORT absent | 236 | 0.424 | +0.072 | +17.04 | 1.136 | +1.18 | -1.09 |

## By SMC BOS / CHoCH recent

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| BOS present | 172 | 0.459 | +0.194 | +33.36 | 1.384 | +1.23 | -1.13 |
| BOS absent | 123 | 0.407 | +0.014 | +1.70 | 1.025 | +1.16 | -1.04 |
| CHoCH present | 188 | 0.441 | +0.118 | +22.22 | 1.235 | +1.20 | -0.97 |
| CHoCH absent | 107 | 0.430 | +0.120 | +12.84 | 1.217 | +1.20 | -1.32 |

## Within-archetype breakdowns

### A1_DEMAND_ABSORPTION_LONG × location_quality

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| acceptable | 146 | 0.438 | +0.052 | +7.64 | 1.100 | +1.06 | -1.03 |
| bad | 1 | 0.000 | -1.000 | -1.00 | 0.000 | +0.66 | -1.81 |
| good | 4 | 0.750 | +0.847 | +3.39 | 4.386 | +1.45 | -0.58 |

### A2_CLEAN_DEMAND_REJECTION_LONG × location_quality

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| acceptable | 62 | 0.452 | +0.192 | +11.93 | 1.379 | +1.15 | -1.08 |
| good | 11 | 0.636 | +0.850 | +9.35 | 3.748 | +1.86 | -0.68 |
| unclear | 1 | 0.000 | -0.520 | -0.52 | 0.000 | +0.64 | -0.91 |

### A3_BAD_FALLING_KNIFE_LONG × location_quality

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| bad | 5 | 0.600 | +0.800 | +4.00 | 3.000 | +3.21 | -0.85 |
| unclear | 1 | 0.000 | -1.000 | -1.00 | 0.000 | +0.05 | -24.01 |

### A4_SUPPLY_REJECTION_SHORT × regime_1d

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|

### A5_BAD_SHORT_IN_BULL_REGIME × regime_1d

| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| bull_recent | 64 | 0.375 | +0.020 | +1.28 | 1.034 | +1.33 | -1.01 |

## Notes
- Zones use Custom OB (canonical slim representation of BigBeluga-style zones).
- Parent 4H zone looked up by `bisect_right(ts) - 1` (no lookahead).
- 1D regime bullishness (used for A5) = `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D` (D1a definition from BREAKOUT_CONTINUATION revalidation).
- All archetypes use the same entry/stop/target rule (entry=close, stop=zone edge ± 0.1×ATR_1H, target=2R, timeout=20 1H bars).
- No-overlap is per-direction (LONG and SHORT can run concurrently).
- v1 has no parameter sweep, no filter selection, no threshold tuning.
