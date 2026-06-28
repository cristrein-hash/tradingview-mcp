# Fund 38 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2024-11-25 · **Date:** 2025-02-04 07:30 UTC (LONDON, killzone=1) · **Tier:** FORTE · **power_score 8.0**
**leg_atr:** 23.46 · **mfe12_atr:** 4.56 · **mae12_atr:** 0.76

---

## (d) MACRO / HTF CONTEXT — the dominant fact: this is a PULLBACK-IN-UPTREND, not a counter-trend reversal

Every HTF frame is aligned bullish and trending UP at the low:
- `h1_trend=+1`, h1_rsi 52.2, h1_slope_atr +0.84 (1H rising)
- `h4_trend=+1`, h4_rsi 66.2, h4_slope_atr +3.9, h4_pos 0.73 (4H strong, upper half of range)
- `hd_trend=+1`, **hd_rsi 72.5**, hd_slope_atr +9.66, hd_pos 0.89 (Daily in a powerful, near-overbought uptrend, top of its range)
- `htf1_native.trend=+1` (rsi 70.1), `htf4_native.trend=+1` (rsi 63.4)

This is the OPPOSITE of the Angle-5 phase-lag thesis (which expects 4H still −1 while 1H turns up). Here ALL frames are already up — there is no regime to *turn*; the market is simply in an established multi-TF bull and this 15M low is a **shallow buy-the-dip into a daily uptrend**. `macro_bull=0/macro_bear=0` (no extreme macro flag), `dealing_range_pos=−0.329` = lower third (discount band, Angle-1 L6 / Angle-1 discount-not-breakdown PRESENT) but the Daily is at hd_pos 0.89 — i.e. price flushed into a 15M-local discount while the higher frame sits high. The "discount" is local, not structural. **This bottom's edge is trend-continuation, not exhaustion-reversal.**

Caveat per memory: hd_rsi 72.5 + hd_pos 0.89 means buying into a stretched Daily — the let-run target is real (clean sky, see below) but the entry is late-cycle on the Daily.

---

## (a) ENTRY MECHANIC — sweep + immediate reclaim, enter on the bar-1 thrust close

The reaction_seq is a textbook **front-loaded, no-look-back staircase**:

| bar | c_atr | l_atr | green |
|---|---|---|---|
| 1 | 1.71 | 0.76 | ✓ |
| 2 | 2.17 | 0.93 | ✓ |
| 3 | 3.01 | 2.17 | ✓ |
| 4 | 1.74 | 1.55 | ✗ (pullback, holds 1.55 >> 0) |
| 5 | 2.43 | 1.41 | ✓ |
| 6 | 2.80 | 2.12 | ✓ |
| 7→9 | 3.06→3.81→**4.13** | rising | ✓✓✓ |

Entry mechanics confirm: `swept_prior_low=1` (took out a prior fractal low), `first_higher_low_bar=1` (HL on the very first bar), `reclaim_ema_bars=3` (EMA21 reclaimed in 3 bars).

**Concrete entry:** the trigger is **shallow sweep + instant reclaim** (Angle-0 L7, Angle-1 Lens 2). The cleanest causal entry is the **close of reaction bar 1** (c_atr +1.71 off a 0.76 low = a +1.71 ATR engulfing thrust bar — Angle-4 L6 `pivot_engulf_thrust` PRESENT), confirmed by the bar-1 higher-low. A slightly more conservative entry is the **close of bar 3** when EMA21 is reclaimed (`reclaim_ema_bars=3`) and c_atr=3.01 — but that gives up ~1.7R of the leg. Best risk/reward: **enter bar-1 close, SL below the swept low (~ −1.0 ATR, mae12 was only 0.76 ATR so the stop never came close)**. The bar-4 pullback (l_atr 1.55) was the only retest and it was shallow (Angle-4 L8 `reclaim_dip_depth` shallow — held well above 0) → the HL structure was respected the whole way to mfe 4.56.

Note: `choch_15m_after=0` and `nas_long_after=0` — there was NO 15M CHoCH or NAS-LONG confirmation. The entry is purely **sweep-reclaim + HL + EMA reclaim**, NOT a structure-break or NAS trigger. Waiting for a CHoCH would have missed this leg.

---

## (b) LENSES PRESENT / STRONG

**STRONG (the core signature here):**
- **Angle-4 L1 `reclaim_low_monotone_k` / L5 `close_progression_R2`** — the staircase is near-monotone (lows climb 0.76→0.93→2.17, only the bar-4 dip interrupts; closes ramp cleanly 1.71→2.17→3.01) = clean front-loaded launch. THIS is the distinctive strength.
- **Angle-4 L6 `pivot_engulf_thrust` / L2 `reclaim_jerk`** — bar-1 is a decisive +1.71 ATR thrust off the low (front-loaded; bars 1-2 do the work).
- **Angle-0 L7 / Angle-1 Lens 2 `liquidity_grab_no_followthrough`** — `swept_prior_low=1`, `sweep_depth_atr=1.11` (SHALLOW, well under the 1.8 threshold; even shallower than the MON median 1.65), reclaimed immediately. Clean engineered stop-run.
- **Angle-1 L6 / discount-band** — `dealing_range_pos=−0.329` in the (−1.0, −0.2) accumulation band, no range break.
- **Demand quality** — `demand_fresh=1`, `demand_virgin=1`, `dist_demand_atr=1.63`, `n_demand_near=9`: flushed toward a fresh, untested demand floor. `clean_sky_atr` on 1D = 99 (Angle-5 L5.6 STACKED-FLOOR / clean runway above PRESENT — the let-run target is open).
- **`low_closepos=0.8`** (Angle-0 L4 `absorption_reload` close-location strong — buyers closed the low bar in the upper part) and **`low_revisit=1`**.

**PRESENT but weaker / mixed:**
- `vol_climax=1.25` and `vol_climax<1.35` → Angle-0 L2 `quiet_climax` partially holds, BUT `range_exp=1.78` (range expansion, not a coil) and `drop20_atr=5.32` (a fairly deep flush, above MON median) → this is NOT a pure quiet-coil bottom. `atr_compression_pre=1.03`, `atr_regime=1.07` (just above 1.0) — mildly compressed, not the textbook calm regime.
- `rsi_low=31.1`/`rsi_min8=31.1` — moderately oversold (right at the MON/control boundary; Angle-0 L10 `rsi_holds_above_floor` weak — it DID dip near 31). `rsi_bull_div=0`.
- `flush_v_ratio=0.37` — a reasonably sharp V (Angle-4 L4 `flush_then_snap` supportive: up-velocity by bar 3 ~1.0 ATR/bar matched the flush).

**ABSENT / against the usual MON thesis:**
- **killzone=1, session=LONDON** — this bottom formed INSIDE the London killzone, directly AGAINST the Angle-1/Angle-3 "off-killzone, Asia" enrichment. So the timing lens (the single strongest discriminator in Angle-1, 8.1× off-killzone) is NEGATIVE here.
- **No NAS confirmation** (`nas_long_16=0`, htf nas_long_rec=0), **no SMC BOS** (`smc_bos=0`), **no CHoCH** after.
- **`sell_bub_w=1`** (one small sell bubble), `sell_decel=−1`, no buy bubbles — minimal bubble footprint, neither confirming nor denying.
- Angle-5 phase-lag triad ABSENT (all frames already +1).

---

## (c) WHAT IS DISTINCTIVE ABOUT THIS BOTTOM

1. **It is a trend-continuation pullback, not an exhaustion reversal.** The 6 angle catalogs are overwhelmingly built around the "quiet absorption / regime-turn at a counter-trend low" thesis (off-killzone, Asia, 4H-still-bearish, drained-vol). Fund 38 satisfies almost NONE of those macro/timing premises — yet it produced a clean FORTE leg (mfe 4.56 ATR, mae only 0.76). **The leg came from full multi-TF bull alignment + a shallow sweep of demand inside an established uptrend.** The catalogs' main discriminators (off-killzone, Asia, phase-lag, quiet-coil) would have REJECTED this winner.

2. **The edge that DID fire is the geometry/mechanics, not the context:** shallow sweep (1.11 ATR) + instant reclaim + front-loaded monotone staircase + fresh virgin demand + clean sky above. The Angle-4 (inter-bar geometry) lenses are the ones that correctly flag this bottom; the Angle-1/3 (liquidity/time) lenses misfire on it.

3. **Lowest-risk entry of the catalog type:** mae12 0.76 ATR vs mfe12 4.56 ATR = ~6:1 favorable excursion, with the entry available on bar-1 close. The sweep-reclaim + HL gave an unusually tight, well-defined stop.

4. **Honest flag:** entry is into a stretched Daily (hd_rsi 72.5, hd_pos 0.89). The leg ran, but this is buying near the top of the larger range — durability of the let-run depends on the Daily not topping. The 12-bar window shows the leg fading bars 10-12 (c_atr 4.13→2.90→2.74→2.18) — a single clean leg, then it gave back, consistent with a continuation pop rather than a fresh trend birth.

---

## Summary signature
FORTE pullback-in-uptrend: all HTF frames bull (Daily rsi 72.5), flush into fresh virgin demand (discount band, clean sky above) via a SHALLOW prior-low sweep (1.11 ATR), entered on the bar-1 engulfing reclaim thrust (+1.71 ATR, HL on bar 1, EMA reclaim by bar 3), no CHoCH/NAS needed. Geometry lenses (monotone staircase / engulf thrust / shallow-sweep-reclaim) fire STRONG; the catalog's off-killzone/Asia/phase-lag/quiet-coil lenses are NEGATIVE — this winner is context-trend-driven, not exhaustion-driven.
