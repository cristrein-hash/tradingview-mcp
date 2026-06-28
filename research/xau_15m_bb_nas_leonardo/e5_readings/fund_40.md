# Fund 40 — DEEP READING (XAU 15M MON+FORTE bottom)

**Date:** 2026-02-17 14:00 (NY session) · **Block:** 2025-11-25 · **Tier:** FORTE · **leg_atr:** 23.06 · **power_score:** 4.7 · **t:** 1771336800

---

## TL;DR
A **NY-session, climactic capitulation flush straight into a fresh virgin 4H+1D-nested demand zone**, where the very first reaction bar is a +3.2 ATR engulfing thrust off the low (bar-1 entry, no patience needed). This is the *counter-archetype* to the "quiet Asia absorption" MONFORTE thesis — it is loud, deep-sweeping, oversold and in-killzone — yet it qualifies FORTE because the **floor is impeccable (dist_demand 0.02, virgin, fresh, nested 4H+1D, daily already bull) and the snap-back is instant and violent.** The edge here is *floor quality + V-snap*, not *quietness*.

---

## (a) ENTRY MECHANIC — where/when to actually enter

**Trigger = bar-1 bullish engulf thrust off a swept low, taken on the close of reaction bar 1.**

- `swept_prior_low = 1` → the flush bar took out a prior fractal low (stop-run / liquidity grab) and `low_closepos = 0.95` → it **closed in the top 5% of its own range** = the rejection was already visible ON the low bar itself (no waiting).
- `reaction_seq w=1`: `c_atr 3.2, h_atr 3.54, l_atr 2.71, green=1` — a single explosive bar that recovers >3 ATR off the low. This is Angle-4 **L6 `pivot_engulf_thrust`** + **L2 `reclaim_jerk` front-loaded** in textbook form (bar 1 does almost all the work).
- `first_higher_low_bar = 1` → the higher-low confirmation is immediate.
- `reclaim_ema_bars = null` → price never needed to "reclaim" EMA21 from below in the usual lagged sense; it gapped straight up through it on bar 1 (consistent with a V-snap that closes the bar above structure).

**Realistic execution:** the cleanest causal entry is the **close of reaction bar 1** (the engulf-thrust confirmation), accepting that the low bar's 0.95 close-position already telegraphed it. SL = below the swept flush low (the bar-1 l_atr region / the demand-zone low at dist 0.02). A more conservative entry survives the bars-2→4 pullback (lows sag from 2.71 → 0.42 ATR, i.e. a deep ~0.5 retrace of the bar-1 thrust — **Angle-4 L8 `reclaim_dip_depth` is NOT shallow here**, dip_frac ≈ 0.85), so a "wait for the retest higher-low" plan would risk getting stopped or buying the bottom of the pullback. **Bar-1 thrust entry is the cleaner read; the pullback is a chop interlude, not a constructive shallow retest.** `nas_long_after = 1` and `swept_prior_low = 1` both corroborate the long.

mfe12 = 3.69 ATR, mae12 = 0.42 ATR → the trade is well in profit early but the post-thrust path is choppy (bars 2-4 give most of bar 1 back to l_atr 0.42 before the second leg lifts to c_atr 2.36 by bar 8). Manage as a V-snap scalp/runner, not a clean staircase.

---

## (b) Lenses PRESENT / STRONG vs ABSENT here

### STRONG (the reason it's FORTE)
- **Floor quality (Angle 1 L3 / Angle 5 L5.6 — STACKED-FLOOR LAUNCH):** `dist_demand_atr 0.02` (price sitting *on* demand), `in_demand 1`, `demand_fresh 1`, `demand_virgin 1`; **nested multi-TF**: `htf4_native.in_demand 1` (dist 1.21) AND `htf1_native.in_demand 1` (dist 0.6). The 15M flush lands inside a 4H demand that sits inside a 1D context. This is the cleanest lens on the fund.
- **Daily already bullish (Angle 5 phase context):** `hd_trend +1`, `hd_slope_atr +1.95`, `hd_rsi 53.4` — the *Daily* has turned up while 1H/4H are still −1. A 1D-leads bullish backdrop = the leg has the highest frame's blessing and overhead room on the slow frame.
- **V-snap velocity (Angle 4 L4 `flush_then_snap`, L6 `pivot_engulf_thrust`, L2 `reclaim_jerk`):** down-flush (`drop20_atr 5.78`) mirrored by an up-thrust of c_atr 3.2 in ONE bar. Velocity-up matches velocity-down — `snap_dominant` true. This is the fund's signature.
- **Liquidity grab (Angle 1 L7 / Angle 3 L4):** `swept_prior_low 1` + `sweep_depth_atr 4.5` (deep) + instant reclaim (`low_closepos 0.95`). A stop-run that failed to follow through.
- **Buy-bubble footprint (Angle 0 L9 `buy_bubble_first_print`):** `buy_bub_w 1`, `sell_bub_w 0` — a small BUY bubble printed and ZERO sell bubbles at the low. Demand footprint appearing while sell-effort is fully absent (`sell_bub_w 0` is the cleanest possible `sell_bubble_exhaustion_gap`, Angle-0 L3).
- **NAS long after (Angle 5 L5.7 partial):** `entry_mechanics.nas_long_after 1` — directional confirmation prints after the low.
- **Killzone timing (here, conventional polarity):** `session NY`, `killzone 1` — this fund is a *NY reversal*. Distinctive given the corpus tilt toward Asia/off-killzone (see distinctive).

### ABSENT / INVERTED (this fund violates the dominant MONFORTE archetype)
- **Quiet-absorption thesis (Angle 0 L2 `quiet_climax`, Angle 2 drained-coiled):** REJECTED here. `vol_climax 1.78` (loud, > control median), `sweep_depth_atr 4.5` (deep, control-like), `rsi_low 26.9 / rsi_min8 26.9` (genuinely oversold, control-like), `atr_regime 1.39` (EXPANDED vol, not the calm 0.94 MONFORTE median). This is a **climactic capitulation low, not a quiet one.**
- **Off-killzone / Asia (Angle 1 L1, Angle 3 L1):** ABSENT — NY + killzone=1 is the *control-leaning* polarity. Yet still FORTE → the killzone-polarity lens is overridden by floor quality + snap here.
- **HTF phase-lag 1H-leads (Angle 5 L5.1/L5.3):** WEAK — `htf1_native.trend −1` (1H still bearish, not the MON +1), though `htf1_native.rsi 54.4` is non-oversold (1H momentum never broke — partial L5.3). The "lead" here comes from the **Daily** (`hd_trend +1`), not the 1H.
- **Coiled-spring / compression (Angle 2 L3/L6, Angle 0 L6):** ABSENT — `atr_compression_pre 0.61` (LOW), `range_exp 5.48` and `atr_regime 1.39` (expanded). No coil; energy was spent in the flush, not stored.
- **Clean staircase reclaim (Angle 4 L1 `monotone-floor`, L5 `R²`):** ABSENT — lows sag (2.71→1.45→0.79→0.42) before re-lifting; the reclaim is a V-then-chop, low monotonicity / low R². It runs on V-snap impulse, not a no-look-back ramp.

---

## (c) What is DISTINCTIVE about this bottom

**It is the loud capitulation counter-example that still earns FORTE.** The dominant MONFORTE fingerprint across the corpus is *quiet, off-killzone Asia, shallow sweep, non-oversold, coiled-vol*. Fund 40 is the **exact opposite on the order-flow/vol/time axes** — NY killzone, deep 4.5-ATR sweep, vol_climax 1.78, rsi 26.9, expanded ATR regime — yet it is a strong bottom. The reconciliation: what carries it is **(1) an impeccable defended floor** (virgin/fresh demand at dist 0.02, nested 4H+1D, daily already bull) and **(2) a violent V-snap** (engulf thrust +3.2 ATR bar 1). 

Causal lesson for the engine: the "quiet absorption" detector would **miss this fund entirely** (it would score it as control). The complementary detector that catches it is **floor-quality × V-snap × daily-trend-up × sell-bubble-absence** — a *climactic-but-defended* archetype. Two non-overlapping bottom families exist in the corpus; fund 40 is the flagship of the *climactic-defended* family. Also notable: the post-thrust pullback is DEEP (l_atr 0.42 by bar 4), so this fund punishes "buy the shallow retest" plans — the only clean entry is the bar-1 thrust close.

---

## (d) MACRO / HTF context (as-of)

- **Daily (1D):** bullish and accelerating — `hd_trend +1`, `hd_slope_atr +1.95`, `hd_rsi 53.4`, `hd_pos 0.41` (mid-range, room above). The highest frame supports longs.
- **4H:** still bearish — `h4_trend −1`, `h4_dist −5.01` (deep below structure), `h4_pos 0.17`, `h4_rsi 40.7`, `h4_slope −1.14`. The 15M low is a **flush into 4H demand (`htf4_native.in_demand 1`, dist 1.21, clean_sky 2.05)** while the 4H is still technically down → room overhead on the 4H, demand defended.
- **1H:** bearish but momentum intact — `h1_trend −1`, `h1_rsi 32` (washed on the snapshot E1 field) yet `htf1_native.rsi 54.4` (native resample shows 1H momentum NOT broken), `h1_pos 0.27`, `htf1_native.in_demand 1` (dist 0.6, clean_sky 0.54 — thin sky just overhead on 1H).
- **Regime flags:** `macro_bull 0 / macro_bear 0` (neutral macro), `atr_regime 1.39` (expanded vol environment — a genuine volatility event, not a quiet drift).
- **Structure of the read:** *Daily up + 4H/1H flushed into a nested, virgin, defended demand + NY stop-run capitulation + instant V-snap rejection with a fresh buy-bubble and zero sell-bubbles.* The bottom is a **higher-timeframe (Daily) buy executing through a lower-timeframe (4H/1H) panic flush** — the classic "strong hands buy the weak-hand capitulation at a defended floor."
