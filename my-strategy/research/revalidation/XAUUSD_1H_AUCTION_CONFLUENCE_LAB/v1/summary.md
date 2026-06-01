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

---

## Corrective regime diagnosis (added 2026-06-01)

Post-publication audit found that the regime treatment in v1 is conceptually
too coarse and the per-archetype conclusions need re-reading. The script
and `report.json` aggregates are **not changed** (the run is reproducible
as-is); only this corrective interpretation is appended.

### What was inadequate

1. **`regime_for_year(y >= 2024) = "bull_recent"`** is a single bucket for
   the entire 2-year window. 100% of trades (295/295) carry the same
   `regime_1d` value. **It does not discriminate intraday phases**
   (markup, continuation, pullback, correction, distribution).

2. **`d1a_1d_bullish=True` in 295/295 trades.** D1a (`close_1D > EMA200_1D
   AND EMA50_1D > EMA200_1D`) is structurally TRUE across the whole window
   because gold rallied from ~$2k to ~$5k+ without breaking EMA200_1D.
   D1a cannot separate trades in this dataset.

3. **A4 is empty as a side-effect of (2).** The script's split
   `A5 if d1a_bullish else A4` always selected A5. A4 emptiness is NOT
   evidence that supply-rejection setups were not captured — it is a
   regime-rule artefact.

4. **The label `A5_BAD_SHORT_IN_BULL_REGIME` is misleading.** A5 ended
   with `total_R = +1.28` (essentially flat over n=64) rather than the
   negative edge the "BAD" prefix implies. A more accurate descriptive
   label is `SHORT_IN_D1A_BULL_FRAME` (non-normative).

### What discriminates in this window (4H phase)

Recomputed post-hoc using 4H EMA50 / EMA200 / ATR-expansion (no slim
change required; computed in the diagnosis script):

| 4H phase | n | %  |
|---|---:|---:|
| `bull_pullback`        | 82 | 28% |
| `bear_or_distribution` | 67 | 23% |
| `bull_continuation`    | 66 | 22% |
| `bull_markup`          | 65 | 22% |
| `unclear`              | 15 |  5% |

The 4H slim has 4 meaningfully distinct phases across the same window
where 1D EMA-based regime is monotonically bullish.

### Period split (entry_iso)

| Period | n | wr | totR | PF |
|---|---:|---:|---:|---:|
| 2024-05 → 2024-12 | 92 | 0.500 | **+24.76** | **1.600** |
| 2025-01 → 2025-12 | 144 | 0.375 | **−5.98** | 0.929 |
| 2026-01 → 2026-05 | 59 | 0.492 | **+16.28** | 1.561 |

The aggregate total_R = +35.06 is dominated by 2024-H2 and 2026-H1.
**2025 was net negative.** Edge stability across calendar periods is not
demonstrated.

### Conclusions corrected

| v1 claim | Corrected reading |
|---|---|
| "Window 100% bull_recent regime" | **Replace:** "Window 100% D1a-bullish (1D EMAs stacked) but 4H has 4 distinct phases. Bucket-by-year is a label, not a regime classifier for intraday." |
| "A4 structurally empty" | **Replace:** "A4 empty by regime-rule choice (D1a=True everywhere). Not evidence that supply rejection setups are absent." |
| "A5 = bad short class" | **Replace:** "A5 ended flat (+1.28R, n=64). Rename conceptually to `SHORT_IN_D1A_BULL_FRAME` (descriptive)." |
| "Edge = +35.06R / PF 1.228 aggregate" | **Qualify:** "+24.76R in 2024-H2 and +16.28R in 2026-H1; **−5.98R in 2025**. Aggregate hides per-period instability." |

### Conclusions that remain valid

- **A2_CLEAN_DEMAND_REJECTION_LONG** retains the strongest per-archetype
  signal: PF 1.586 aggregate, survives 4H-phase cross-tab (markup 2.57,
  continuation 1.26, pullback 1.39, distribution 1.62).
- **SELL bubble recent correlates with worse LONGs** (PF 0.973 vs 1.432).
  Consistent with prior labs (BB Confluence v1, BREAKOUT_CONTINUATION 4H).
- **NAS SHORT label recent in last 15 bars** discriminates SHORT outcomes
  positively (PF 1.62 in n=16, NAS-confirmed SHORTs).

### Conclusions suspended

- **A1_DEMAND_ABSORPTION_LONG** edge: collapses in 2025 (PF 0.88, −5.44R)
  while positive in 2024 and 2026. Cannot claim aggregate edge.
- **"SHORTs cannot work in this window"**: per-period, 2024-H2 and
  2026-H1 SHORTs are positive (PF 1.23 and 1.91 respectively); only
  2025 SHORTs are negative (PF 0.67). The aggregate flat outcome is
  the average of opposite sub-regimes.
- **Edge stability**: 2025 negative result raises overfit concern. A
  walk-forward by 4H phase or quarter is required before any further
  conclusion.

### What must change before v2

1. **Regime must be dynamic per trade**, not bucket-by-year. Primary
   discriminator should be 4H phase (markup / continuation / pullback /
   correction / distribution / unclear), not 1D EMAs in this window.
2. **Rename A5** descriptively (`SHORT_IN_D1A_BULL_FRAME`) and introduce
   a **regime-agnostic A4** that fires for every supply rejection. Use
   4H phase as a post-hoc cross-tab, not a precondition.
3. **Walk-forward by quarter or by 4H phase** required before any
   archetype is treated as having edge.
4. **Validate A2 specifically per sub-period** before declaring it
   robust. So far it appears robust but the 2026-H1 sub-bucket showed
   negative R (n=6, totR −1.55, PF 0.61) — small but worth flagging.
5. **Consider whether 2025 should be carved out** if the hypothesis
   becomes "system works in markup OR correction, NOT in slow
   continuation". That would be honest segmentation, not overfit, IF
   stated up-front.

### What this corrective section is NOT

- It is **not** a re-run of the lab. Numbers in the aggregate tables
  above are unchanged. The 295 trades in `trades.jsonl` are not
  re-classified.
- It is **not** a v2. No new script, no new archetype definitions are
  shipped here.
- It is **not** a promotion decision. The lab remains diagnostic-only.

This corrective interpretation is the prerequisite for any future v2.
