# XAUUSD 1H AUCTION CONFLUENCE LAB v1 — Methodology

**Purpose:** map each of the 5 main indicators (BigBeluga/Custom OB, SMC,
NAS Top/Bottom, Market Order Bubbles, RSI) to an **explicit auction-theory
function** and test **5 archetypes** of intraday auction reads on XAUUSD 1H,
to discover which combinations capture real auction behaviour and which
are noise/mechanical.

**Premise:** BB = **BigBeluga**, not Bollinger Bands.

**Not for promotion.** v1 is diagnostic.

## 1. Data

- **Source:** canonical slim features on disk:
  `/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/{1H,4H,1D}/`
- **Coverage windows:**
  - 1H: 2024-05-24 → 2026-05-25 (**bottleneck**)
  - 4H: 2016-05-24 → 2026-05-25
  - 1D: 2012-06-19 → 2026-05-25
- **Effective lab window: 2024-05-24 → 2026-05-25** (~2 years, entirely
  inside `bull_recent` regime).
- **Read-only.** No slim mutation, no operational change.
- **No TradingView/MCP calls.**

## 2. Indicator roles (auction mapping)

| Indicator | Auction function |
|---|---|
| BigBeluga / Custom OB | **Location** — where price is in the auction (premium/discount; supply/demand) |
| SMC (BOS / CHoCH / OB) | **Structure / Acceptance / Character change** |
| NAS Top/Bottom | **Exhaustion / Defense / Local pressure** |
| Market Order Bubbles | **Aggressor pressure** — absorption candidate or climax candidate |
| RSI | **Confirmation / Divergence / Exhaustion** (context only) |

## 3. Zone definition (BigBeluga proxy)

The slim does not expose explicit `bigbeluga_zone_*` fields. The canonical
representation in the slim is **Custom OB**:

- `custom_ob_demand_active`, `custom_ob_supply_active`
- `nearest_demand_high/low`, `nearest_supply_high/low`
- `nearest_demand_dist`, `nearest_supply_dist`

**v1 uses Custom OB as the only zone source.** SMC OB
(`smc_nearest_bullish_ob_*`, `smc_nearest_bearish_ob_*`) is the documented
fallback but NOT used in this lab.

## 4. Timeframe hierarchy

- **1H:** execution / signal / trigger TF.
- **4H:** structural zone TF. For each 1H bar, the parent 4H bar is looked
  up via `bisect_right(ts, child_ts) - 1` (no lookahead).
- **1H also serves as its own zone source** (each 1H bar's own
  `nearest_demand/supply` fields). The zone whose edge is closer to current
  1H close is picked between 1H and 4H.
- **1D:** macro regime. Used only for the A5 D1a regime check
  (`close_1D > EMA200_1D AND EMA50_1D > EMA200_1D`).

## 5. The 5 archetypes

### A1 — DEMAND_ABSORPTION_LONG

Auction reading: **sellers attacked the demand zone but were absorbed; the
market reclaims above the zone top — responsive buying confirmed.**

Triggers (all required, evaluated at close of 1H bar `i`):
1. Parent 1H or 4H demand zone exists and was entered: `low[i] <= zone_high`.
2. Sell pressure recent: `bubble_sell_recent OR (nas_label_short_event count in last 5 bars >= 1)`.
3. **Reclaim:** `close[i] > zone_high`.
4. Bullish close: `close[i] > open[i]` AND `body_pct[i] >= 0.40`.
5. RSI not in deep exhaustion: `rsi[i] > 30`.

### A2 — CLEAN_DEMAND_REJECTION_LONG

Auction reading: **price touches demand and rejects cleanly with no recent
seller activity and no buy climax — pure responsive buying.**

Triggers:
1. Parent 1H or 4H demand zone exists and was entered.
2. `close[i] > zone_low` (didn't break the zone).
3. **No sell pressure:** NOT `bubble_sell_recent` AND `nas_label_short_event count in last 5 bars == 0`.
4. **No buy climax:** NOT `bubble_buy_recent`.
5. **Supply far overhead:** `nearest_supply_dist > 2 × ATR_1H` OR null.
6. Bullish close AND `body_pct >= 0.40`.

### A3 — BAD_FALLING_KNIFE_LONG (diagnostic negative class)

Auction reading: **price enters demand but the seller is still active and
there is no reclaim, with bear structural bias — classic falling-knife
attempt.**

Triggers:
1. Parent 1H or 4H demand zone entered.
2. Sell pressure recent (as in A1).
3. **No reclaim:** `close[i] <= zone_high`.
4. `location_quality` in {`bad`, `unclear`}.
5. SMC bear bias: `BOS bear recent OR CHoCH bear recent`.

### A4 — SUPPLY_REJECTION_SHORT (regime-conditioned positive class)

Auction reading: **price reaches supply and rejects cleanly; macro 1D
regime is NOT confirmed bullish (no D1a).**

Triggers:
1. Parent 1H or 4H supply zone exists and was entered: `high[i] >= zone_low`.
2. `close[i] < zone_high` (didn't break).
3. **No buy pressure:** NOT `bubble_buy_recent` AND `nas_label_long_event count in last 5 bars == 0`.
4. **No sell climax:** NOT `bubble_sell_recent`.
5. **Demand far below:** `nearest_demand_dist > 2 × ATR_1H` OR null.
6. Bearish close: `close < open` AND `body_pct >= 0.40`.
7. **1D regime NOT bullish** (`close_1D <= EMA200_1D OR EMA50_1D <= EMA200_1D`).

### A5 — BAD_SHORT_IN_BULL_REGIME (diagnostic negative class)

Auction reading: **same supply rejection setup as A4 but 1D macro is
bullish (D1a) — short is fighting the tape.**

Triggers: same as A4 except condition #7 is inverted: **1D regime IS bullish (D1a).**

## 6. Mutual exclusivity

- A1 and A2 are exclusive (A1 requires sell pressure recent; A2 forbids it).
- A1 and A3 are exclusive (A1 requires reclaim; A3 forbids reclaim).
- A2 and A3 are exclusive (A2 forbids sell pressure; A3 requires it).
- A4 and A5 are mutually exclusive by 1D regime.
- A bar may produce a LONG candidate (one of A1/A2/A3) AND a SHORT
  candidate (one of A4/A5) independently — recorded as two separate
  trades. No-overlap is enforced per-direction.

## 7. Entry / Stop / Target / Outcome

Same simple rules across all 5 archetypes:

- **Entry:** `close` of the signal 1H bar.
- **Stop:**
  - LONG: `zone_low - 0.1 × ATR_1H`.
  - SHORT: `zone_high + 0.1 × ATR_1H`.
- **Targets:** `entry ± 1R` (intermediate, MFE bookkeeping only) and
  `entry ± 2R` (primary outcome).
- **Risk sanity:** `0 < risk <= 8 × ATR_1H` else discard.
- **Outcome:** walk forward up to 20 1H bars; intrabar stop-first; tracks
  `MFE_R`, `MAE_R`, `bars_held`, `exit_reason ∈ {hit_target_2, hit_stop, timeout}`.

## 8. Regime segmentation

By entry-year bucket (consistent with prior labs). Lab window = `bull_recent`
only. **Consequence:** the A4 class is structurally empty in this window
(every SHORT is A5). This is documented explicitly; it is a window
limitation, not a script bug.

## 9. Diagnostic fields recorded per trade (NOT used as filters)

- `location_quality`, `supply_overhead`, `demand_below`, `acceptance_quality`,
  `entry_timing` (defaulted to `unclear` in v1).
- `rsi_value`, `rsi_context`, `rsi_above_ma`, `rsi_div_bullish_event`,
  `rsi_div_bearish_event`.
- All `bubble_*` fields from the signal bar.
- `nas_long_recent`, `nas_short_recent`, `nas_long_count_15`,
  `nas_short_count_15`.
- `smc_bos_recent`, `smc_choch_recent`, `smc_direction`.
- `d1a_1d_bullish` (the boolean used to split A4 vs A5).

## 10. What v1 does NOT do

- No parameter sweep.
- No threshold tuning (MIN_BODY_PCT, SUPPLY_FAR_ATR_MULT, sell pressure
  lookback fixed at 5 bars).
- No filter selection on any diagnostic field.
- No multi-config comparison.
- No promotion decision.
- No operational change.

## 11. Outputs

- `trades.jsonl` — gitignored (per existing `**/trades.jsonl` rule).
- `report.json` — aggregate + per-archetype + per-dimension cross-tabs.
- `summary.md` — human-readable.

## 12. Known limitations

- 2-year window only (1H slim bottleneck).
- All trades in one macro regime (`bull_recent`) → A4 empty, A5 dominates SHORTs.
- Custom OB ≠ literal BigBeluga indicator; it is the slim's canonical proxy.
- `acceptance_quality` is outcome-derived (cheating for diagnostic purposes
  only — should not be treated as a real-time signal).
- `entry_timing` deferred to v2.
- No DXY / macro overlay.
- No cost overlay; R is gross.
- A3 sample expected to be small (intentional — A3 is a tight negative
  class).
