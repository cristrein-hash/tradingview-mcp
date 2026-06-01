# XAUUSD_INTRADAY_BB_CONFLUENCE — Historical Lab v1 — Methodology

**Purpose:** answer one question — *does the BigBeluga zone-rejection thesis
have a raw historical edge on XAUUSD when measured against canonical slim
data, before any forward test or operational promotion?*

**Premise:** **BB = BigBeluga**, not Bollinger Bands.

**Not for promotion.** v1 is diagnostic. It does not optimize, does not
tune thresholds, does not select filters, and does not propose any
operational change.

## 1. Data

- **Source:** canonical slim features on disk:
  `/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/{15M,30M,1H,4H,1D}/`
- **Loader:** in-script, with `dedup_keep_last` per timeframe and `bisect_right`
  parent lookups.
- **Coverage windows:**
  - 15M: 2024-05-24 → 2026-05-25 (**bottleneck**)
  - 30M: 2024-05-24 → 2026-05-25
  - 1H:  2024-05-24 → 2026-05-25
  - 4H:  2016-05-24 → 2026-05-25
  - 1D:  2012-06-19 → 2026-05-25
- **Effective lab window: 2024-05-24 → 2026-05-25** (limited by 15M slim).
  This is ~2 years and falls **entirely within the `bull_recent` regime** —
  no regime variation possible in this lab.
- **Read-only.** No mutation of slim, registry, or any operational file.
- **No TradingView/MCP calls.** No backtest of forward signals.

## 2. Zone definition (BigBeluga proxy)

The slim does not expose explicit `bigbeluga_zone_*` fields. The canonical
representation of BigBeluga-style supply/demand zones in the slim is the
**Custom OB** family of fields:

- `custom_ob_demand_active`, `custom_ob_supply_active` (booleans)
- `nearest_demand_high`, `nearest_demand_low`
- `nearest_supply_high`, `nearest_supply_low`
- `nearest_demand_dist`, `nearest_supply_dist`

**v1 uses Custom OB as the only zone source.** SMC OB fields
(`smc_nearest_bullish_ob_*`, `smc_nearest_bearish_ob_*`) are NOT used in v1
to keep the lab single-source.

This choice is documented for clarity: when summary references "BigBeluga
zone", read it as "Custom OB canonical zone as recorded in slim".

## 3. Timeframe hierarchy

- **15M:** execution / trigger TF. All signal-bar evaluation happens here.
- **1H / 4H:** structural zone TFs. For each 15M bar, the parent 1H and
  parent 4H bars are looked up via `bisect_right(parent_ts_list, child_ts) - 1`
  (returns the most recent parent bar with `ts <= child_ts`, no lookahead).
  Of the two parent zones (1H and 4H), the one whose boundary is closer to
  the current 15M close is picked. This produces a single `zone_tf` per
  signal.
- **1D:** macro context only. Used to record `regime_1d` (entry-year
  bucket).
- **30M:** loaded for compatibility but **not used in v1 trigger logic**.
  The user's broader thesis treats 30M as reaction TF; v1 simplifies to 15M
  reaction only.

## 4. Signal triggers (canonical v1, frozen)

### LONG (DEMAND zone rejection)

On a 15M bar `i`:
1. Parent 1H/4H demand zone exists (Custom OB demand active, `nearest_demand_*`
   not null).
2. `low[i] <= zone_high` — bar entered the zone.
3. `close[i] > zone_low` — bar did not break the zone (closed above zone low).
4. `close[i] > open[i]` — bullish close.
5. `body_pct[i] >= 0.30` — body at least 30% of range.

### SHORT (SUPPLY zone rejection)

On a 15M bar `i`:
1. Parent 1H/4H supply zone exists.
2. `high[i] >= zone_low` — bar entered the zone.
3. `close[i] < zone_high` — bar did not break the zone (closed below zone high).
4. `close[i] < open[i]` — bearish close.
5. `body_pct[i] >= 0.30`.

### Sanity (both directions)

- `atr14_wilder` not null at `i` (else skip; warmup 200 bars).
- `risk = |entry - stop| > 0` and `risk <= 8 * ATR_15M` (else skip; zone too wide).

## 5. Entry / Stop / Targets

- **entry_price** = `close[i]` of the signal bar.
- **stop_price**:
  - LONG: `zone_low - 0.1 * ATR_15M`.
  - SHORT: `zone_high + 0.1 * ATR_15M`.
- **target_1_price** = entry ± 1R (intermediate, used only for MFE bookkeeping).
- **target_2_price** = entry ± 2R (primary target).
- **No BE move**, no trailing, no scaling. v1 is structural.

## 6. Outcome simulation

For each trade, walk forward from `entry_bar = signal_bar + 1`:

- **Primary horizon:** 20 15M-bars (5 hours).
- **Secondary horizon:** 40 15M-bars (10 hours), recorded per-trade
  (`secondary_40bar_R`, `secondary_40bar_exit_reason`) but **not aggregated** in
  v1 stats. Purpose: sanity comparison.
- **Intrabar check order:** stop_first (within each bar, check whether
  `low <= stop_price` (LONG) / `high >= stop_price` (SHORT) before checking
  target).
- **Tracked:** `MFE_R`, `MAE_R`, `bars_held`, `exit_reason` ∈ {`hit_target_2`,
  `hit_stop`, `timeout`}.
- **Timeout exit price** = `close` of bar at `entry + 20`.

## 7. No-overlap

If a signal's `signal_bar <= last_exit_bar`, the signal is skipped. One
trade per signal episode; episodes are single bars.

## 8. Regime segmentation

- By entry year (consistent with `XAUUSD_4H_BREAKOUT_CONTINUATION/v1` schema):
  - 2024-2026 → `bull_recent`.
- All trades in v1 fall in `bull_recent`. Regime cross-sectional comparison
  is therefore not informative in this lab.

## 9. Diagnostic fields (recorded per trade, NOT used as filters)

These are recorded for post-hoc cross-tabulation. v1 does not use them to
accept/reject any trade.

- `rsi_context`: from `rsi`, `rsi_div_bearish_event`, `rsi_div_bullish_event`.
  Values: `bull_confirmation`, `bear_divergence`, `neutral_no_trigger`,
  `overextended`, `exhaustion`, `unclear`.
- `bubble_context`: coarse classification from `bubble_buy_current`,
  `bubble_sell_current`, `bubble_large_current`. Values: `none`,
  `absorption_base`, `continuation_support`, `climax_top`,
  `rejection_supply`, `unclear`.
- `location_quality`, `supply_overhead_15m`, `demand_below_15m`,
  `entry_timing`: coarse auction dimensions derived from 15M Custom OB
  distances. `entry_timing` is left at `unclear` in v1 (deferred to v2 with
  pre-signal momentum tracking).
- `nas_short_count_10`, `nas_short_count_15`, `nas_long_count_10`,
  `nas_long_count_15`: counts of NAS TOP/BOTTOM label events in lookback
  windows.
- `smc_has_recent_bos`, `smc_has_recent_choch`, `smc_last_bos_dir`,
  `smc_last_choch_dir`.

All `*_quality`, `*_context` fields default to `unclear` when ambiguous.

## 10. What v1 does NOT do

- No parameter sweep.
- No threshold tuning (body_pct, stop_buffer, max_risk_vs_atr fixed).
- No filter selection on any diagnostic field.
- No multi-config comparison.
- No promotion decision.
- No operational change.
- No backtest of multiple zone definitions in the same run.
- No use of 30M slim in signal logic.

## 11. Outputs

- `trades.jsonl` — one trade per line, gitignored (per `.gitignore`
  `**/trades.jsonl`).
- `report.json` — aggregate stats and per-dimension cross-tabulations.
- `summary.md` — human-readable.

## 12. Non-determinism check

None. Backtest is deterministic given fixed slim files. Re-runs produce
bit-identical `trades.jsonl`.

## 13. Known limitations

- 2-year window only (15M slim bottleneck).
- All trades in one macro regime (`bull_recent`).
- Custom OB ≠ literal BigBeluga indicator; it is the slim's proxy.
- 30M slim available but not used (v1 simplification).
- `bubble_context` and `location_quality` classifications are coarse;
  many trades land in `unclear`.
- No DXY / macro overlay (v1 omits it; matches the strategy's v1.0 spec
  which deferred DXY to v1.1).
- No real cost overlay (spread/commission); R is gross.
