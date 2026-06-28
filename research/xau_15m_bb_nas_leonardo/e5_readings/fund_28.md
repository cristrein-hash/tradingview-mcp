# Fund 28 — Deep Reading (XAU 15M MON+FORTE bottom)

**Date:** 2025-07-17 12:45 UTC · **Block:** 2025-05-25→08-25 · **Tier:** FORTE · **Year:** 2025
**leg_atr:** 27.15 · **power_score:** 7.1 · **Session:** NY · **killzone:** 0
**Outcome (post-hoc, exit-side only):** mfe12 = 6.04 ATR, mae12 = 0.30 ATR — a near-perfect no-look-back launch.

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

Confirmed bar-by-bar from RAW (`series` around t=1752756300, bar idx 3524):

```
-1  12:30  o3326.1 h3326.7 l3312.7 c3312.9   <- CLIMAX FLUSH bar (-14 pts, range 4.7 ATR, closes on its low)
+0  12:45  o3312.8 h3315.4 l3309.7 c3313.1   <- THE LOW. sweeps 3312.7, closes 3313.1 (upper-third, closepos 0.59), rsi 28
+1  13:00  o3313.0 h3317.2 l3311.1 c3316.7   <- first higher-low (3311.1>3309.7) + green reclaim, CHoCH-up forms
+2  13:15  ...l3314.0 c3317.6                 <- floor climbs again
+5  14:00  ...l3318.1 c3324.6                 <- thrust through prior structure
+6  14:15  ...l3324.5 c3330.2 > ema 3323.9    <- EMA21 RECLAIMED (close back above the 21)
```

This is a **two-state turn: one climax flush bar, then immediate absorption.** The mechanic is a *sweep + reclaim + micro-HL + CHoCH*, NOT a deep V-flush:

- The **flush bar (-1)** drives price 14 points down in one candle to take out the local pool.
- The **low bar (+0)** undercuts the prior low (`swept_prior_low=1`, sweep_depth 2.6 ATR) but **closes back in the upper third of its range** (closepos 0.59, lower_wick 0.55) — supply tried, failed to hold the low.
- **Bar +1 prints the first higher-low** (`first_higher_low_bar=1`) AND a 15M bullish CHoCH (`choch_15m_after=1`). The lows then climb monotonically.

**My entry:** I would NOT chase the low bar (RSI 28, still falling, no confirmation). The clean, causal trigger is **bar +1 close (13:00, ~3316.7)** — first higher-low + green reclaim of the flush-bar body + CHoCH-up. A more conservative variant takes the **EMA21 reclaim at bar +6 (14:15, ~3330)**; but on this fund the floor never gives a retest (mae only 0.30 ATR), so the +1 micro-HL entry captures the entire 6 ATR leg with risk defined just below 3309.7. Trigger label: **sweep + reclaim → micro-HL/CHoCH at bar +1.**

## (b) Lenses PRESENT / STRONG here

**Inter-bar geometry (Angle 4) — DOMINANT.** This fund is the textbook staircase:
- **L1 `reclaim_low_monotone_k` = STRONG (~run 4+):** l_atr 0.3→0.91→(0.84)→1.16→1.78→3.12→4.2→4.43 — lows climb essentially every bar after +2. No-look-back floor.
- **L5 `close_progression_R2` = STRONG:** c_atr 1.47→1.66→1.23→1.99→3.13→4.32→4.87→5.14 is a near-straight rising ramp (high R²), accelerating not chopping.
- **L8 `reclaim_dip_depth` = STRONG (shallow retest):** mae12 0.30 ATR — the first dip barely retraces; the higher-low holds far above the low.
- **L9 `velocity_regime_flip` = STRONG:** steep down-slope (−14 pt flush bar) inverts into a steep up-ramp (hard V).
- **L6/L7 `pivot_engulf_thrust` / `downleg_gap_velocity_spike` = PRESENT:** bar −1 is the biggest bar of the leg (climax flush, range 4.7 ATR), immediately reversed by a green +1 — the canonical "biggest bar then instant reversal."

**Auction / liquidity (Angle 1):**
- **L7 `liquidity_grab_no_followthrough` = PRESENT:** prior-low swept then reclaimed fast (within 1 bar). (sweep 2.6 ATR is on the deeper side vs MON median, so this is a *moderate*, not shallow, grab.)
- **L6 `discount-not-breakdown`:** `dealing_range_pos = −1.353` — this is BELOW −1, i.e. a *range break*, the polarity Angle 1/6 flags as the weaker, continuation-leaning side. NOTABLE divergence from the MON profile (see distinctiveness).
- **L3 liquidity asymmetry:** `dist_demand_atr −0.23` (inside/at demand floor) vs `dist_supply_atr −0.30` — floor and overhead both essentially at price; `n_supply_overhead=307` is HIGH (congested overhead) — does NOT fire clean-sky.

**Cross-TF / regime onset (Angle 5) — MIXED:**
- **L5.6 nested demand = PRESENT:** 15M `in_demand=1`, `htf4_native.in_demand=1`, `htf1_native.in_demand=1` — a fully stacked multi-TF demand floor. `demand_virgin=1` (fresh untested value).
- **L5.1 phase-lag turn = WEAK/ABSENT:** h1_trend=−1, h4_trend=0, hd_trend=0 — the 1H has NOT yet flipped bullish (the classic MON 1H-leads-4H signature is missing here). BUT the **Daily is already constructive**: `hd_pos 0.51, hd_slope_atr +1.41, hd_rsi 51` — the higher frame is mid-range and rising. So the HTF support comes from the **Daily uptrend**, not a 1H hook.
- **L5.3 HTF RSI hook = PARTIAL:** htf1 rsi 49.6 / htf4 rsi 40.9 / hd rsi 51.1 — none deeply oversold while 15M rsi_low=28.1 → cross-TF RSI divergence (15M washed, HTF holding) is PRESENT.
- `clean_sky_atr` ~0.16–0.21 on both HTFs — overhead is NOT clean (tight), consistent with the high `n_supply_overhead`.

**Order-flow (Angle 0) — DIVERGENT from the quiet-absorption thesis:**
- `vol_climax = 2.08` (HIGH), `lower_wick_ratio = 0.55` (LARGE rejection wick), `rsi_low 28.1` (genuinely oversold), `range_exp 1.42`, `vol_climax 2.08` — this bottom is the **climactic / capitulation flavor**, the OPPOSITE of the "quiet, off-climax" MON median. The quiet_climax lens (L2) does NOT fire here.
- `sell_bub_w=12, sell_decel=10, buy_bub_w=0` — heavy sell-bubble effort into the low; `sell_decel=10` is the only fade signal. No buy-bubble first-print.
- `atr_compression_pre 0.79` (LOW), `atr_regime 1.36` (HIGH) — coil/quiet-regime lenses (Angle 2 L1/L4, Angle 5 L5.4) do NOT fire; vol is expanded.

**Time/session (Angle 3) — ANTI-profile:** NY session, off-killzone (0). The MON median is Asia/late; this is a NY-hours bottom. Time lenses do not support it.

## (c) What is DISTINCTIVE about this bottom

This fund is a **climactic NY-session capitulation reversal carried by GEOMETRY + nested demand + a rising Daily** — it is the *counter-example* to the dominant "quiet Asia absorption" MON template:

1. **It wins on TRAJECTORY, not on the entry-bar fingerprint.** The order-flow/vol/session lenses (quiet_climax, off-killzone, compressed regime, coil) all point the WRONG way (loud, NY, expanded vol, range-break below −1). What makes it a monster is purely the *post-low shape*: a perfect monotone staircase (mae 0.30, mfe 6.04, R² high). It is the clearest demonstration that the **reclaim geometry (Angle 4) can carry a bottom even when the static/order-flow lenses say "weak/control."**
2. **The HTF support is DAILY, not 1H.** Unlike the canonical MON 1H-leads-4H phase-lag, here the 1H/4H are still bearish/flat; the constructive frame is the Daily (hd_pos 0.51, hd_slope +1.41). The 15M flush dropped INTO a nested 15M+4H+1H demand stack that sits within a rising Daily — a deep retrace within a higher-TF uptrend.
3. **Congested overhead, yet it ran 6 ATR.** `n_supply_overhead=307`, clean_sky ~0.16 — there was NO clean runway, which normally caps the leg. It ran anyway because the flush was a single-bar liquidity event the demand absorbed instantly. This argues the *initiative/absorption* (failed flush + instant reclaim) overpowered the overhead, rather than a clean-path setup.
4. **Climax IS the signal here.** `vol_climax 2.08` + `lower_wick 0.55` + the −14pt flush bar −1: this is genuine selling-climax → absorption (Angle 2 L8 `flush_then_freeze` / Angle 4 L7), the one order-flow lens that DOES fire — just the opposite branch from the quiet-absorption median.

## (d) Macro / HTF context

- **Daily:** uptrend-constructive — price mid-range (hd_pos 0.51), Daily EMA slope rising (+1.41 ATR), RSI 51 neutral-up. This is a **pullback inside a Daily uptrend**, not a bottom of a downtrend.
- **4H:** flat/transitioning (trend 0, slope −0.52, rsi 40.9, pos −0.11) — the 4H is at the lower edge of its range, sitting on its own demand (in_demand=1, dist −0.22), absorbing.
- **1H:** still bearish (trend −1, slope −1.31, rsi 36.1, pos −0.16) — the fast frame had not yet turned at entry; the turn is confirmed only on the 15M (CHoCH +1) and validated by the Daily backdrop.
- **Structure:** 15M flushed into a fresh, virgin, nested demand floor (demand_virgin=1, in_demand on all 3 frames) during NY hours, swept the local low, and reversed on a single climax bar. The leg is a **Daily-uptrend dip-buy executed via a 15M sweep-reclaim**, with the entire edge expressed in the no-look-back reclaim geometry rather than the entry-bar character.

---
**Caveats:** order-flow/session/regime lenses are anti-profile here (loud climax, NY, expanded vol, range-break < −1); only geometry + nested demand + rising-Daily carry it. tick-volume (vol_climax) is the documented-unreliable axis — treat as directional only. This fund is a strong argument that the MON cohort contains (at least) two families: the quiet-Asia-absorption type AND this climactic-NY-dip-in-Daily-uptrend type.
