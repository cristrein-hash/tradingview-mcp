# XAUUSD 4H BREAKOUT_CONTINUATION v1 — Methodology

**Purpose:** produce a trade-level `trades.jsonl` for visual auction-theory review.
**Not for promotion.** Promotion decision is separate and requires the visual pass.

**Sources of strategy spec (frozen):**
- `my-strategy/research/experimental/xauusd_4h_long_breakout_continuation_regime_filtered.md`
- `my-strategy/pine_alerts/01_xauusd_4h_breakout_continuation.pine`

**Catalog entry:** `my-strategy/strategies/catalog.json` → `XAUUSD_4H_BREAKOUT_CONTINUATION`.

## 1. Data

- **Source:** canonical 4H slim of XAUUSD (`/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/4H/*.jsonl`).
- **Loader:** `scripts/build_crosstf_dataset.load_tf("4H")` + `dedup_keep_last` + `add_close_epochs`.
- **No TradingView, no MCP, no chart, no live broker.**
- **Read-only.** No mutation of slim or registry.

## 2. Indicators

Slim already provides: `close, open, high, low, atr14_wilder, body_pct, swing_high_10, close_above_swing_high_10, rsi, rsi_ma, rsi_above_ma`.

Computed in Python from O/H/L/C:
- `EMA(50)` and `EMA(200)` — standard exponential moving average, `alpha = 2/(period+1)`.
- `EMA(50) slope` = `EMA(50)_now > EMA(50)_5_bars_ago`.
- `ATR_MA(20)` = SMA of `atr14_wilder` over 20 bars.
- `ADX(14)` — Wilder DMI: TR, +DM, −DM with Wilder smoothing; DI±; DX; then Wilder smoothing of DX.

Warmup: 200 bars discarded for indicator stabilization (EMA200 needs ~200).

## 3. Signal rules (canonical, frozen)

Long signal on bar `i` if **all** of:

### Triggers
1. `close[i] > swing_high(10)[i-1]` — proxied by the slim's `close_above_swing_high_10 == True`.
2. `close[i] > open[i]` — bullish close.
3. `body_pct[i] >= 0.5` — body at least half the candle range.
4. `rsi(14)[i] > rsi_ma[i]` — proxied by the slim's `rsi_above_ma == True`.

### Regime filters (`S_full_trend_htf` — winning combo from 2026-05-12 sweep)
5. `ADX(14)[i] >= 20`.
6. `close[i] > EMA(200)[i]`.
7. `EMA(50)[i] > EMA(200)[i]`.
8. `EMA(50)[i] > EMA(50)[i-5]` — slope positive over 5 bars.
9. `atr14_wilder[i] > ATR_MA(20)[i]` — volatility expanding.

### Sanity
- `stop_price = low[i] - 0.5 * atr14_wilder[i]`.
- `risk = entry_price - stop_price > 0`.
- `risk <= 5 * atr14_wilder[i]`.
- Otherwise skip.

## 4. Entry

- `entry_bar = signal_bar + 1`.
- `entry_price = open[entry_bar]` — **next bar open** (standard backtest realism; the strategy spec's "ideal entry at close" is replaced by next-bar-open to avoid lookahead).
- Direction: LONG only.

## 5. Stop

- `stop_price = low[signal_bar] - 0.5 * atr14_wilder[signal_bar]`.
- **BE move at +1R:** if at the end of any bar `j` after entry, `high[j] >= entry_price + 1 * risk`, the stop is moved to `entry_price` for all subsequent bars' stop checks. The move applies starting on `j+1` (no lookahead within bar `j`).

## 6. Target

- Primary `target_price = entry_price + 4 * risk` (4R, per official spec).
- Stop-first intrabar: each bar after entry, check `low[j] <= stop_price` FIRST; if not hit, then check `high[j] >= target_price`.

## 7. Time limit

- `max_hold = 24` bars (= 96 hours / 4 days).
- If neither stop nor target hits within 24 bars after entry, exit at `close[entry_bar + max_hold - 1]` with `exit_reason = "time_limit"`.
- `right_censored = true` when `exit_reason == "time_limit" AND exit_bar == entry_bar + max_hold - 1`.

## 8. No-overlap

- If a signal's `signal_bar <= last_exit_bar`, the signal is skipped (no overlapping trades).
- One trade per signal episode (signal episode = single bar, no episode aggregation).

## 9. MFE / MAE

For every trade, computed over `[entry_bar .. exit_bar]`:
- `MFE_R = max((high[k] - entry_price) / risk for k in range)`
- `MAE_R = min((low[k]  - entry_price) / risk for k in range)`

## 10. Regime segmentation

By entry year (per official `experimental/...md` table):
- 2016-2018 → pre_covid
- 2019      → bull_pre_covid
- 2020      → covid_rally
- 2021      → chop_post_covid
- 2022      → chop_inflation_bear
- 2023      → chop_macro
- 2024-2026 → bull_recent

## 11. Outputs

- `trades.jsonl` — one trade per line; fields per `config.json` + plot-required:
  `strategy_id, config_id, stop_variant, direction, signal_bar, signal_iso, entry_bar, entry_iso, exit_bar, exit_iso, entry_price, stop_price, target_price_primary, exit_price, atr14, risk, R_multiple, MFE_R, MAE_R, exit_reason, be_moved, right_censored, regime, registry_entry`.
- `report.json` — aggregate stats (n, win_rate, avg_R, total_R, PF, exit reasons, regime breakdown).
- `summary.md` — human-readable.

## 12. Reconciliation

- **Skipped.** The 2026-05-12 audit CSV is aggregate-only (parameter sweep stats). No trade-level legacy dump is available to reconcile against. The winning config from that audit (`S_full_trend_htf`) reported `n=234, total_net_r=+64.57, pf=1.64, win_rate=0.286` over 7.4 years.
- Aggregate-vs-aggregate informal comparison is recorded in `report.json` (`legacy_aggregate_comparison`).

## 13. Decision gates (not for promotion in v1)

- Purpose of v1 = produce plotable trades.jsonl.
- Decision gates in `config.json` are loose; final promotion decision happens after visual auction-theory review by the operator.

## 14. Non-determinism check

- None. Backtest is deterministic given fixed canonical slim. Re-runs produce bit-identical `trades.jsonl`.

## 15. Out of scope

- No live broker fill modeling.
- No spread/commission applied to R (gross R only; cost overlay deferred to report stage if needed).
- No alternative stop/target sweeps.
- No EMA reversal trailing.
- No `chop_inflation_bear` regime mitigation beyond the standard filters.
