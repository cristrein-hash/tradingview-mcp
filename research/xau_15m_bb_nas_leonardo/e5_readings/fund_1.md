# Fund 1 — DEEP READING (MONSTRO, 2026-01-22 03:15, block 2025-11-25)

**Tier:** MONSTRO · **leg_atr:** 63.32 · **power_score:** 16.9 · **year:** 2026 · **session:** ASIA · **killzone:** 0
**Outcome geometry:** mfe12 = 3.38 ATR, mae12 = 0.34 ATR → asymmetric, near-zero adverse excursion after the low. The low held to the tick once the reaction started.

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

This is a **micro-HL + fast EMA-reclaim continuation entry inside a still-intact bull structure**, NOT a capitulation-V reversal. The dossier is explicit and consistent:

- `entry_mechanics.first_higher_low_bar = 1` — the FIRST reaction bar already prints a higher low. The floor lifts immediately.
- `entry_mechanics.reclaim_ema_bars = 3` — price reclaims EMA21 by reaction bar 3.
- `entry_mechanics.swept_prior_low = 0` — **no liquidity sweep**. This bottom was NOT made by raiding a prior low; the leg low is held *above* the prior pool (consistent with `sweep_depth_atr = 0.0`).
- `entry_mechanics.choch_15m_after = 1` — a 15M bullish CHoCH confirms after the turn.
- `entry_mechanics.nas_long_after = 0` — no NAS LONG confirmation (NAS is silent on both 15M and HTF here; `nas_long_16=0`).

Reading `reaction_seq` bar-by-bar (close in ATR / low in ATR / green):
- w1 c0.37 l0.35 red — inside, low holds at the bottom (HL already vs the print).
- w2 c0.85 l0.34 **green** — first thrust, +0.48 ATR close gain, low essentially flat (floor defended).
- w3 c0.98 l0.74 green — EMA reclaim bar; low climbs to 0.74 (no look-back).
- w4–w8 c0.81→0.76, lows 0.62→0.73 — a **5-bar shallow consolidation / shelf** above the low (mae12 only 0.34 confirms the dip never threatened the bottom).
- w9 c1.17 green, then **w10 c2.76 (+1.59 ATR), w11 c2.53, w12 c3.10** — the real expansion / displacement leg fires from the shelf.

**Concrete entry:** I would enter on the **reclaim of EMA21 at reaction bar 3** (close ~+0.98 ATR off the low), risk under the w1–w2 micro higher-low / leg low (≈0.34 ATR below entry — a tight, structural stop). The 15M CHoCH then confirms. The cleaner add / re-entry is the **break of the w3–w8 shelf at bar 9–10** (the displacement candle), which is where the monster move actually pays. Trigger label: **micro-HL → EMA21 reclaim (bar 3) → shelf-hold → displacement break (bar 9-10)**. This is a *continuation* entry: there is no sweep, no climax, no CHoCH-of-a-downtrend — the bull trend simply paused and resumed.

Why not enter at the literal low (w1)? Because the trigger here is structural confirmation (HL + EMA reclaim + CHoCH), not a flush rejection. With mae12 = 0.34 ATR the late entry costs almost nothing and removes the guesswork.

---

## (b) LENSES PRESENT / STRONG here

**STRONG — cross-TF momentum & regime (Angle 5) — this is the dominant signature of this fund:**
- This bottom is NOT a 1H-leads-4H phase-lag turn (L5.1) — it is the **stronger case: ALL frames already bullish.** `h4_trend=+1` (rsi 61.2, slope +3.82 ATR, pos 0.69), `hd_trend=+1` (rsi **79.1**, dist +17.36, slope +6.93, pos 0.84, eff 0.82), `htf4_native.trend=+1` (rsi 74.3), `htf1_native.trend=+1` (rsi 78.1). Daily is in a powerful, efficient up-leg (hd_eff 0.82). The only soft frame is the native 15M `h1` (trend 0, slope −0.94, rsi 44.8, pos 0.28) — a shallow pullback inside a roaring HTF uptrend.
- **L5.2 1H Room-Above — STRONG/present in spirit:** `htf1_native.in_demand=0`, `dist_demand_atr=2.30` (well clear of demand, far above the catalog's 0.8 threshold), and `htf4_native.in_demand=0`, `dist_demand_atr=2.45`. Both HTF frames sit ABOVE their demand with room — the MON profile (above-demand, not pinned).
- **L5.4 Compressed-Regime Onset — STRONG:** `atr_regime=0.69` (very low, well under 1.0 — even calmer than the MON median 0.94) and `atr_compression_pre=1.34` (high). Textbook coiled/quiet regime. The flush is a small dip inside an otherwise compressed market.
- **L5.6 Multi-TF Demand Stack — partial:** 15M `in_demand=1`, `demand_fresh=1`, `demand_virgin=1`, `dist_demand_atr=0.37` (15M flushed onto a fresh, virgin demand). But the HTF frames are NOT in their own demand here (price is mid-range on 4H/1D, above their floors) — so it is "15M lands on fresh 15M demand under a clean HTF uptrend," not a nested HTF-demand. `clean_sky` on 1H is 99 (effectively clear), 4H clean_sky 1.35.

**STRONG — volatility structure (Angle 2):**
- **L4 vol_of_vol_collapse / L7 gap_to_vol_floor — present:** `atr_regime=0.69` near the vol floor; a steady, quiet regime, `consec_down=0` (selling already stopped at the print).
- **L6 coiled_spring_squeeze / compression_break_imminence — likely present:** high compression_pre (1.34), low range_exp (0.89), `vol_climax=0.87` (BELOW the climax threshold — no volume blow-off). The low is made *quietly*, then expands (w10 range 2.8 ATR). This is a coil-then-expand, not a flush-then-bounce.

**PRESENT — inter-bar geometry (Angle 4):**
- **L1 reclaim_low_monotone_k — PRESENT (with a shelf):** lows 0.35→0.34→0.74→0.69→0.62→0.63→0.61→0.73 — the floor lifts to 0.74 by bar 3 then holds a shelf (a small sag to 0.61 mid-shelf, so not strictly monotone like the textbook MONSTRO). The "no deep look-back" property holds (mae12 0.34).
- **L8 reclaim_dip_depth — STRONG:** the post-reclaim dip is extremely shallow (shelf lows 0.61–0.73 vs reaction high ~1.14 at bar 3) — the retest holds far above the low. This is the structural quality marker.
- **L5 close_progression_R2 — moderate:** the reclaim is two-phase (ramp to bar 3, flat shelf bars 4–8, then explosive bars 9–12) — not a single clean straight ramp, so R² over w1–6 is modest; the cleanliness lives in the *second* leg.
- **L2 reclaim_jerk / L6 pivot_engulf_thrust:** front-loaded thrust is modest (bar 1 is red, real thrust at bar 2–3); the violent acceleration is delayed to bar 10. So this is NOT a front-loaded spring — it's a measured continuation that detonates later.

**Order-flow (Angle 0):**
- **L2 quiet_climax — STRONG (2-3/3):** `vol_climax=0.87` (low), `sweep_depth_atr=0.0` (no sweep at all), `lower_wick_ratio=0.39` (modest). This is the quiet-absorption fingerprint, NOT capitulation.
- **L9 buy_bubble_first_print — STRONG:** `buy_bub_w=15` (heavy small-BUY-bubble presence) with `sell_bub_w=0` — buy-side footprint dominant, ZERO sell bubbles. This is a notable demand-print signature. (`buy_bub_L=0` — small bubbles only.)
- **L1 effort_vs_result_failure / downleg grind:** `downleg_eff=0.28` (grindy, inefficient descent — the MON profile), `flush_v_ratio=0.37`.

**Time/session (Angle 3):**
- **L1/L3 Asia off-peak — PRESENT:** session=ASIA, time 03:15, killzone=0. Sits in the off-killzone, Asia/late-hours pocket where MON+FORTE bottoms are 2.3× enriched. Mid-week-ish year-2026 bar.

**Liquidity/auction (Angle 1):**
- **Lens 1 QUIET RECLAIM — partial:** off-killzone YES; but the low is NOT a sweep (swept_prior_low=0, sweep_depth 0). So it's the "quiet" half without the "engineered raid" half.
- **Lens 6 DISCOUNT-NOT-BREAKDOWN — present:** `dealing_range_pos=0.319` (lower portion of the dealing range, NOT a range break) — buy-the-discount, not fade-the-break.
- **Lens 3 asymmetry:** `dist_demand_atr=0.37` (floor very near) vs `dist_supply_atr=0.49` (supply also near) and `n_supply_overhead=12` — overhead is somewhat congested, so the runway is not perfectly clean on 15M (the run-room comes from the HTF trend, not a thin 15M ceiling).

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is a continuation bottom, not a reversal bottom.** Every HTF frame (1D rsi 79, 4H rsi 61–74, native 1H rsi 78) is already strongly bullish; the 15M just pulled back into a fresh virgin demand and resumed. There is NO sweep (`sweep_depth_atr=0.0`, `swept_prior_low=0`) — this breaks the "engineered stop-run" model in Angles 0/1/3. The edge is *trend-continuation-from-discount*, not *reversal-from-capitulation*.
2. **Zero adverse excursion (mae12 = 0.34 ATR).** Once the low printed, price never came back. Combined with mfe12 = 3.38, this is a near-perfect asymmetric entry — the rare "buy the pause, no heat" trade.
3. **Pure buy-side order flow:** `buy_bub_w=15, sell_bub_w=0, sell_decel=0` — buyers printing, sellers absent. The most one-sided bubble book in the absorption thesis.
4. **Two-phase reaction (shelf then detonation):** unlike the textbook monotone-staircase MONSTRO, this one reclaims, builds a 5-bar shelf (w4–w8) above the low, THEN displaces hard (w10 +1.59 ATR close). The shelf is the accumulation; the breakout is the payday. Entry on the EMA reclaim is early-but-cheap; the shelf-break (bar 9–10) is the confirmed trigger.
5. **Very compressed vol (atr_regime 0.69) — even calmer than the MON median (0.94).** A coil inside a strong trend.
6. **NAS and SMC-BOS are silent** (`nas_long_16=0`, `smc_bos=0`, `nas_long_after=0`). This fund did NOT need a NAS trigger — the trigger is purely structural (HL + EMA reclaim + CHoCH) within HTF trend alignment. A caution for any NAS-gated detector: it would MISS this monster.
7. **RSI not deeply oversold** (`rsi_low=44`, `rsi_min8=40`) — consistent with the MON "less-oversold" fingerprint; an oversold-required detector would also miss it.

---

## (d) MACRO / HTF CONTEXT

A **textbook HTF bull-trend continuation**. The Daily is in a strong, efficient markup (hd_trend +1, hd_rsi 79.1, hd_pos 0.84, hd_eff 0.82, dist +17.36 ATR above demand, slope +6.93) — gold is trending hard up on the Daily. The 4H confirms (h4_trend +1, rsi 61–74, slope +3.82, pos 0.69, above demand). `macro_bull=1, macro_bear=0`. The native 1H is also up (trend +1, rsi 78). The ONLY pullback is on the 15M intrabar frame (h1 trend 0, rsi 44.8, slope −0.94, pos 0.28) — a shallow, grindy 15M dip (drop20_atr 4.21, downleg_eff 0.28) into a **fresh, virgin 15M demand zone** (`in_demand=1, demand_fresh=1, demand_virgin=1, dist_demand_atr=0.37`) during the quiet Asia session, with vol compressed (atr_regime 0.69, vol_climax 0.87 — no panic). The setup: roaring HTF uptrend → 15M takes a breath into untouched demand at the discount of the dealing range → buyers immediately defend (HL bar 1, buy bubbles, zero sell bubbles) → EMA reclaim + 15M CHoCH → shelf → displacement to +3.38 ATR. The leg ran because the HTF trend supplied the fuel and direction; the 15M demand supplied the precision low.

**Detector implication:** this fund is the *continuation/discount-pullback* sub-class of MONFORTE bottom — driven by HTF trend alignment (Angle 5 L5.2/L5.4/L5.6) + quiet absorption (Angle 0 L2/L9) + fresh-virgin-demand, NOT by sweep/climax/NAS/oversold. Any convergent detector should keep an HTF-trend-aligned-continuation path that does NOT require a sweep or an oversold RSI, or it will miss monsters like this one.
