# Fund 14 — DEEP READING (MONSTRO)

**Date:** 2025-04-17 19:15 UTC (block 2025-02-25) · **Tier:** MONSTRO · **leg_atr:** 36.41 · **power_score:** 14.2
**Session:** LATE · **killzone:** 0 (off-killzone)
**Entry one-liner:** instant V-snap — reclaim of EMA21 in 1 bar + sweep of prior low + first higher-low at bar 1 + 15M CHoCH-up = enter at close of reaction bar 1 (or stop above bar-1 high), this is a continuation-pullback into fresh virgin demand inside a raging multi-TF uptrend, NOT a capitulation reversal.

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

This is the rare archetype where almost every trigger fires on the SAME bar — there is no "wait for confirmation" lag.

`entry_mechanics`: `reclaim_ema_bars=1`, `first_higher_low_bar=1`, `swept_prior_low=1`, `choch_15m_after=1`, `nas_long_after=0`. `mae12_atr=0.23` (the low bar's wick was the deepest point reached — price NEVER went meaningfully against entry), `mfe12_atr=8.09`.

The reaction sequence is a textbook **no-look-back staircase**:
- `l_atr` (bar lows, in ATR above the bottom): 0.23 → 1.58 → 1.37 → 1.87 → 2.53 → 2.94 → 3.49 → 5.23 → 5.78 → 6.09 → 6.25 → 6.37. Monotone from bar 2 onward; the only blemish is bar 3's 1.37 (a 0.21-ATR shallow inside-dip), never threatening the low.
- `c_atr`: 1.80 → 1.87 → 2.13 → 2.68 → 3.11 → 3.13 → 5.28 → 6.28 → 6.89 → 6.74 → 7.12 → 7.33. Every reaction bar green for the first 9 bars; the leg accelerates (bar 7 jumps +2.15 ATR — the displacement leg).

**Where I enter:** at the **close of reaction bar 1** (c_atr 1.80, off a 0.23 ATR low). Bar 1 is an engulfing thrust: it reclaims EMA21 (`reclaim_ema_bars=1`), it is the first higher-low (`first_higher_low_bar=1`), it follows a swept prior low (`swept_prior_low=1`), and the 15M CHoCH-up prints right after (`choch_15m_after=1`). Stop below the swing low (the 0.23-ATR wick / `mae` floor → ~0.3–0.4 ATR risk). Because `dist_demand_atr=0.14` (price is literally sitting on fresh virgin demand) and `sweep_depth_atr=0.63` (a tiny shallow grab), the invalidation is razor-thin and the R:R is enormous (8.09 ATR MFE on ~0.4 ATR risk).

The DISTINCTIVE entry note: I do not need a deep flush or a violent climax candle to commit here. The trigger is **structural**, not exhaustion-based — a shallow sweep of a local pool + instant reclaim of the fast EMA inside an already-bullish HTF. This is "buy the discount pullback in an uptrend," executed at the first higher-low.

## (b) Lenses PRESENT / STRONG here

**Cross-TF Momentum & Regime-Onset (Angle 5) — STRONGEST cluster, but in an unusual mode:**
- This bottom is NOT the canonical "1H-leads-4H phase lag" (L5.1) — here ALL frames are ALREADY bullish: `h4_trend=+1` (rsi 59.7), `hd_trend=+1` (rsi 74.5, pos 0.89, slope +15.81 — daily is screaming up), `htf1_native.trend=+1` (rsi 75.1), `htf4_native.trend=+1` (rsi 69.1). So instead of regime *onset*, this is regime *continuation* — a pullback inside an established multi-TF bull. The "phase-lag" lens INVERTS for this fund: there is no lag, there is full HTF agreement.
- **L5.2 1H Room-Above:** PARTIAL. `htf1_native.in_demand=0`, `dist_demand_atr=3.77` (1H well above its demand → big room overhead), `h1_pos=0.40`. But note `features_E1.h1_trend=0 / h1_eff=0.10 / h1_slope_atr=−1.14 / h1_rsi=50.1` — the *E1* 1H view shows the 1H is locally flat/just-dipping (the pullback), while `htf1_native` (native resample) shows the broader 1H still up. Reconciles as: a shallow 1H dip inside an up-1H. This is the only "discount" texture on an otherwise overbought HTF.

**Liquidity / Auction Theory (Angle 1) — STRONG:**
- **Lens 6 Discount-not-breakdown:** PRESENT — `dealing_range_pos=−0.403` sits cleanly in the discount band (−1.0, −0.2), NOT a range break. Buy-the-discount.
- **Lens 1 Quiet Reclaim (off-killzone):** PRESENT — `killzone=0`, session LATE. Forms off the London/NY kill windows, matching the off-killzone polarity. (Caveat: LATE/post-NY, not strictly Asia.)
- **Lens 3 Liquidity Asymmetry:** MIXED — `dist_demand_atr=0.14` (floor is right here) but `dist_supply_atr=−0.23` and `n_supply_overhead=15` (some overhead supply just above on the 15M). However `htf4_native.clean_sky_atr=1.02` and `htf1_native.clean_sky_atr=99` (huge clean sky on the 1H) → HTF runway is wide open even if the immediate 15M has a thin supply cap. The leg blew straight through it (mfe 8.09).
- **L7 liquidity_grab_no_followthrough (Angle 0):** PRESENT in pure form — `swept_prior_low=1`, `sweep_depth_atr=0.63` (extremely shallow), reclaim within 1 bar. Shallow grab + instant reclaim = the cleanest version of this lens.

**Inter-bar Geometry & Velocity (Angle 4) — STRONGEST behavioral fingerprint:**
- **L1 reclaim_low_monotone_k:** STRONG (run ≈ 4+, only bar-3 micro-dip breaks strict monotonicity, but the floor never re-tests).
- **L5 close_progression_R2:** STRONG — c_atr is a clean rising ramp (1.80→6.89 over 9 bars, all green), high R² launch.
- **L2 reclaim_jerk / L4 flush_then_snap / L9 velocity_regime_flip:** STRONG — `mae12=0.23` vs `mfe12=8.09` is a near-pure one-directional V; the up-velocity dwarfs any down-side.
- **L8 reclaim_dip_depth (shallow retest):** STRONG — the deepest post-launch pullback is trivial; lows keep climbing.

**Volatility-Structure (Angle 2):**
- `atr_regime=0.79` (calm/compressed — below the MON median 0.94, well below control 1.29) → forms in a quiet vol pocket. `atr_compression_pre=1.95` (very high compression pre — coiled). **L3 coiled_spring_squeeze / L6 compression_break_imminence / L1 atr_decel_into_low:** likely PRESENT (calm + compressed → coil-launch). `range_exp=1.09` modest. `vol_climax=0.70` (LOW — no climax volume at all; matches the "no-capitulation" MON profile).

**Order-flow / Microstructure (Angle 0):**
- **L2 quiet_climax:** STRONG — `vol_climax=0.70` (modest), `sweep_depth_atr=0.63` (shallow), `lower_wick_ratio=0.35` (small wick) → all 3 quiet-climax conditions met. This is absorption WITHOUT theatrics.
- `downleg_eff=0.13` (very grindy/inefficient descent → **L1 effort_vs_result_failure** territory: lots of churn, little net travel).
- `sell_bub_w=3, sell_decel=3` → sell-bubble effort decelerating (**L3 sell_bubble_exhaustion_gap** plausible); `buy_bub_w=0` (no buy-bubble first-print — L9 ABSENT).
- **L10 rsi_holds_above_floor / L5.3 HTF-RSI:** EXTREME version — `rsi_low=50.5`, `rsi_min8=50.5`. RSI never went oversold at all. This is the opposite end of the spectrum from a capitulation low; momentum was barely dented.

**Time/Session (Angle 3):**
- `session=LATE`, `killzone=0` → off-killzone (matches the off-peak thesis). Not Asia, so the Asia-hour enrichment lens does NOT apply; this is a post-NY/late-day pullback low. `low_revisit=2` (base touched twice).

## (c) What is DISTINCTIVE about THIS bottom

1. **It is NOT a reversal bottom — it is a continuation pullback into fresh virgin demand inside a powerful uptrend.** `rsi_low=50.5` (never oversold), `drop20_atr=2.25` (shallow drop), `dealing_range_pos=−0.403` (discount, not break), `in_demand=1 / demand_fresh=1 / demand_virgin=1 / dist_demand_atr=0.14` (sitting precisely on first-touch fresh demand). The MON profile usually means "quiet absorption at a washed low"; THIS fund is the other valid MON archetype: **a high-momentum pullback that barely dips, then resumes** — the trend itself is the edge.
2. **Daily is the dominant lens:** `hd_slope_atr=+15.81`, `hd_rsi=74.5`, `hd_pos=0.89`, `hd_dist=34.37`. The daily is in a strong, extended uptrend; this 15M dip is a buy-the-dip continuation within that, not a bottom-fishing reversal.
3. **The "quiet-climax" microstructure (Angle 0/2) is present but for a DIFFERENT reason** than the absorption thesis: there's no climax because there was barely any selling to begin with (downleg_eff 0.13 grind, vol_climax 0.70, RSI 50). It's quiet because it's a controlled pullback, not because sellers got absorbed at a washout.
4. **Entry confluence is maximally co-incident:** reclaim + higher-low + sweep + CHoCH all on bar 1. Most funds need a few bars; this one triggers immediately with a 0.23-ATR max-adverse — among the cleanest entries in the set.
5. **One contrary texture:** `n_supply_overhead=15` and `dist_supply_atr=−0.23` (immediate 15M supply just overhead). In a weaker context this caps the bounce; here the HTF clean-sky (`htf4 clean_sky 1.02`, `htf1 clean_sky 99`) and daily momentum overran it (mfe 8.09).

## (d) Macro / HTF context

All higher frames aligned bullish, with the daily extended and overbought:
- **Daily (E1 hd_*):** trend +1, rsi 74.5, pos 0.89, slope +15.81 ATR — strong, mature uptrend, near the top of its range (extended).
- **4H (E1 h4_* / htf4_native):** trend +1, rsi 59.7 / 69.1, pos 0.72, slope +5.9 — solidly bullish, room before its own demand (htf4 dist_demand 3.92), modest clean sky 1.02.
- **1H:** broader native 1H bullish (htf1_native trend +1, rsi 75.1, dist_demand 3.77, clean_sky 99), with a shallow local dip in the E1 view (h1_trend 0, h1_slope −1.14, h1_rsi 50.1) — i.e. exactly the pullback we are buying.
- **macro_bull=1, macro_bear=0.** Off-killzone LATE session, calm vol regime (atr_regime 0.79) with high pre-compression (1.95).

**Read:** strong multi-TF bull, daily extended/overbought → a shallow 15M pullback flushes a local liquidity pool (sweep 0.63 ATR), taps fresh virgin demand, and resumes immediately. The edge is **trend continuation + fresh-demand defense + instant structural reclaim**, not exhaustion/absorption. Buy the first higher-low at the demand touch with a tight structural stop; let it run toward the open HTF sky.
