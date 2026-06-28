# Fund 44 — DEEP READING (XAU 15M MON+FORTE bottom)

**Identity:** block 2025-08-25 · low at **2025-09-15 01:00 UTC** · tier **FORTE** · leg_atr 21.5 · power 5.4 · session **ASIA**, killzone=0 (hour 01:00 UTC = the Asia-ramp hour).

---

## (a) THE ENTRY MECHANIC — where/when to actually get in

This is a **deep flush + sharp-V sweep-and-reclaim** into virgin 4H demand, NOT a slow grinding base. The reaction tells the whole story:

| react bar | l_atr | c_atr | green |
|---|---|---|---|
| +1 | 0.08 | 1.53 | 1 |
| +2 | 0.62 | 1.32 | 0 |
| +3 | 0.94 | 2.21 | 1 |
| +4 | 2.18 | 3.99 | 1 |
| +5 | 3.94 | 4.67 | 1 |
| +6 | 4.25 | 5.11 | 1 |

- The low prints, then **bar +1 immediately reclaims +1.53 ATR off a 0.08 low** — a single decisive engulf/thrust bar (Angle 4 L6 `pivot_engulf_thrust`, L7 `flush reversed next bar`). `first_higher_low_bar = 1` and `swept_prior_low = 1`: the low swept a prior fractal low and the very next bar made a higher low.
- The **floor never looks back**: l_atr climbs 0.08→0.62→0.94→2.18→3.94 — a 5-bar monotone climbing-floor run (Angle 4 L1 `reclaim_low_monotone_k` ≈ full). `mae12_atr = 0.08` confirms the entry essentially never went underwater.
- `reclaim_ema_bars = 4`: EMA21 reclaimed by react bar 4. `nas_long_after = 1`: a NAS-LONG confirms after the turn. `choch_15m_after = 0` (no clean 15M CHoCH — the move was too vertical to carve a structural CHoCH).

**Concrete entry:** The cleanest causal entry is the **sweep+reclaim on react bar +1 close** — the low at 01:00 swept the prior low, and bar +1 closed +1.53 ATR back above it with a strong thrust. That is the "shallow-grab-fails / instant reclaim" trigger (Angle 0 L7) realized as a single engulfing bar. A more conservative version is the **first-higher-low retest entry**: bar +2 makes a higher low (l_atr 0.62 > 0.08) without breaking — buy the held HL on bar +2/+3. Either way the EMA21 reclaim (bar +4) is a confirmation, not the trigger; waiting that long still leaves ~+1.5R of the +5.75 ATR mfe. **Trigger identified: sweep of prior low at the Asia-ramp hour + immediate same-direction reclaim thrust on the next bar (no-look-back HL).**

---

## (b) WHICH LENSES ARE PRESENT / STRONG

**STRONG / present:**
- **Angle 3 (TIME) — top conviction here.** Asia session + hour **01:00 UTC** (the 4.7× enriched Asia-ramp hour) + killzone=0. L3 `time_since_session_open` (bottom in the first session-hour = reaction to the prior session's excess) and L4 `overnight_low_sweep_clock` (Asia opens, sweeps the overnight low, reverses) fit perfectly: `swept_prior_low=1` at 01:00 = textbook cross-session liquidity grab in thin Asia liquidity. This is the single best-fitting dimension for this fund.
- **Angle 5 (Cross-TF) — strong.** `htf1_native.trend = +1` while `htf4_native.trend = −1` = the **phase-lag turn (L5.1)**: fast frame already bullish, slow frame still down (room overhead). `htf1_native.in_demand = 0`, `dist_demand_atr = 5.87`, `h1_pos` lifted — the 1H has already left its own floor (L5.2 room-above) while the 15M flushed onto 4H demand (`htf4_native.in_demand = 1`). `htf1_native.rsi = 77.5` (1H momentum never broke; L5.3 HTF-RSI hook) and **`htf1_native.clean_sky_atr = 99`** (totally clear runway up = L5.6 clean-HTF-sky). NAS-LONG present (`nas_long_16=1`) for the cross-TF NAS context (L5.7 booster).
- **Angle 4 (Geometry/velocity) — strong.** Monotone climbing floor (L1), front-loaded reclaim (L2 — bar +1 does +1.53 then it keeps thrusting), clean rising ramp (L5), hard slope-flip down→up (L9 `velocity_regime_flip`), shallow/no retest (L8 — mae 0.08). The reclaim trajectory is the cleanest staircase, exactly the discriminator the static scalars miss.
- **Angle 1 / Angle 0 (Liquidity / order-flow) — partial.** `swept_prior_low=1` + instant reclaim (Angle 0 L7, Angle 1 L1/L2). Landed in **virgin demand** (`demand_virgin=1`, `in_demand=1`, `dist_demand_atr=0.05`) — a defended fresh floor (Angle 1 L3 asymmetry partial).

**WEAK / ABSENT (and this is the key caveat):**
- **Angle 0 / Angle 2 "quiet absorption / coiled-spring" thesis FAILS here.** This fund is the *opposite* of the modal MONFORTE quiet-low: `sweep_depth_atr = 3.73` (DEEP, vs MON med ~1.65), `drop20_atr = 6.17` (DEEP), `downleg_eff = 0.6` (EFFICIENT impulsive crash, vs MON med ~0.28), `vol_climax = 1.55`, `sell_bub_w = 22` (lots of sell-bubbles — supply was loud, not faded). So Angle 0 L1/L2/L3/L8 (effort-failure, quiet-climax, sell-bubble-exhaustion, vol-drain) and Angle 2 L1/L3/L4/L7 (atr-decel, squeeze, vol-of-vol-collapse, vol-floor) are **NOT the mechanism** of this bottom. `atr_regime = 1.11` and `atr_compression_pre = 0.62` are mid/low — no strong coil.
- **Angle 1 L6 discount-band FAILS:** `dealing_range_pos = −4.588` is a **range BREAK**, not the discount band (−1..−0.2). By the dealing-range lens this looks like continuation, yet it reversed — meaning the reversal here is driven by the deep-sweep-into-virgin-demand + cross-TF turn, not by range position.

---

## (c) WHAT IS DISTINCTIVE ABOUT THIS BOTTOM

This is a **"deep impulsive flush" FORTE bottom that contradicts the quiet-absorption prototype.** Where most MON+FORTE bottoms are calm, shallow, grindy absorption events, fund 44 is a **violent, efficient, climactic V-flush** (deep sweep, efficient down-leg, loud sell bubbles) that still produced a clean +5.75 ATR leg with ~zero drawdown. What carries it is NOT the down-leg quality — it's:
1. **the cross-TF phase-lag** (1H already +1, RSI 77.5, off its demand, clean sky 99 ATR) that gave the flush room and fuel, and
2. **the Asia-ramp timing** (01:00 UTC, off-killzone) that made the flush a thin-liquidity stop-run into virgin demand, and
3. **the no-look-back reclaim geometry** (monotone climbing floor, front-loaded thrust, mae 0.08).

Distinctive lesson: a deep climactic flush is usually a *control / weak-bottom* signature — but when it lands in **virgin 4H demand under an already-bullish 1H with clean sky overhead**, the same violence becomes the launchpad. The discriminator is the **HTF context + reclaim shape**, not the flush statistics. This fund is the case that proves the quiet-absorption lenses must be ORed with a "deep-sweep-into-stacked-demand + 1H-already-turned" lens, or it gets missed.

---

## (d) MACRO / HTF CONTEXT

- **1D native:** `trend = +1`, `rsi = 77.5`, `dist_demand_atr = 5.87` (far above daily demand), `in_demand = 0` — daily is in a strong uptrend, overbought-ish, well above its floor. The 15M flush is a **pullback inside a daily bull**, not a counter-trend reversal. (Note: E1 `hd_*` daily fields are null; the htf1_native here is the live native-resample read.)
- **4H native:** `trend = −1` natively (the recent 4H leg was down into demand) but E1 `h4_trend = +1` / `h4_slope_atr +1.26` / `h4_pos 0.35` — the broader 4H is up; the native −1 reflects the immediate down-swing that made the flush. `htf4_native.in_demand = 1`, `dist_demand_atr = −0.15`, `clean_sky_atr = 0.73` — flush landed right on a 4H demand zone.
- **1H:** already turned bullish (native trend +1, RSI strong) — the fast frame leads the turn while the 4H micro-leg was still printing down. This **1H-leads-4H phase lag inside a 1D uptrend** is the macro engine of the leg: buy the deep Asia flush into 4H demand when the 1H/1D are already pointing up.

**Causality note:** all reads above use info up to the entry bar (low bar + the immediate reclaim bars, which are closed). The native HTF states (htf1/htf4_native) are as-of snapshots at the low; reaction_seq bars +1..+6 are post-low closed bars usable for the reclaim-confirmation entry. No look-ahead beyond the reclaim thrust used as the trigger.
