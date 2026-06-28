# Fund 6 — DEEP READING — XAU 15M MONSTRO bottom 2025-10-10 04:00 UTC

**Tier:** MONSTRO · power_score 10.1 · leg_atr 48.11 · session ASIA · killzone 0 · block 2025-08-25
**Outcome geometry:** monotone staircase reclaim, mfe12 **3.47 ATR**, mae12 **0.15 ATR** (≈ zero post-low drawdown).

---

## (a) THE ENTRY MECHANIC — where/when I actually enter

This is a **shallow-sweep + immediate climbing-floor (no-look-back) entry**, NOT a CHoCH/retest entry.

Read the post-low bar-by-bar (`reaction_seq`, l_atr = bar low above the low in ATR):
- bar1 l_atr 0.15 c_atr 1.36 green — first higher-low prints **immediately** (`first_higher_low_bar=1`); bar closes +1.36 ATR off the low = a decisive engulfing thrust.
- bar2 l_atr 1.23 c_atr 1.88 green — low jumps a full ATR above bar1's low; floor climbing.
- bar3 l_atr 1.78 c_atr 2.19 green — floor still climbing, never revisits.
- bar4 l_atr 2.18 c_atr 2.85 green — **EMA21 reclaimed here** (`reclaim_ema_bars=4`).

The low (l_atr) climbs **every** bar 1→4 (0.15→1.23→1.78→2.18): a perfect monotone run of 4 (Angle-4 L1 = max). There is no dip, no retest, no CHoCH needed (`choch_15m_after=0`), no NAS confirmation (`nas_long_after=0`).

**Concrete trigger I would take:** the bottom is engineered as a stop-run — `swept_prior_low=1`, sweep_depth 2.58 ATR — that prints bar1 as a strong green reclaim back above the swept level with the low already a higher-low. The aggressive (best-R) entry is **on the close of reaction bar1** (the first higher-low / engulf thrust off the swept low). The conservative confirmation is **the EMA21 reclaim at bar4**; given mae12 is only 0.15 ATR, even the bar4 entry keeps essentially the entire leg with near-zero heat. SL sits just below the swept low (the spring-load floor). I prefer **bar1 close** here because the floor never looks back — waiting to bar4 costs ~1.5 ATR of the leg for no risk benefit.

---

## (b) LENSES PRESENT / STRONG

**Geometry & velocity (Angle 4) — the dominant signature here.**
- **L1 reclaim_low_monotone_k = 4 (max).** Climbing floor every bar; textbook no-look-back launch. STRONG.
- **L2 reclaim_jerk / front-loaded:** d[1]=+1.36, d[2]=+0.52 — biggest thrust is the first bar, then it eases. Front-loaded spring release. STRONG.
- **L5 close_progression_R2:** c_atr 1.36→1.88→2.19→2.85→2.91→3.13 is a near-straight rising ramp (high R², monotone through bar7). Clean one-directional control, no two-sided chop. STRONG.
- **L8 reclaim_dip_depth:** first real dip is only at bar8 (green-broken) and bar11/12; through bars 1–7 the lows never sag — shallow-retest holds far above the low. STRONG.
- **L9 velocity_regime_flip:** steep 7-bar down-leg (consec_down 7, drop20 5.31) inverts into a steep up-ramp = large hard flip. STRONG.
- **L6 pivot_engulf_thrust:** bar1 = +1.36 ATR off a 0.15 low = decisive engulf thrust. PRESENT.

**Liquidity / Auction (Angle 1).**
- **L1 QUIET RECLAIM (off-killzone × Asia):** killzone=0, session ASIA — the single strongest discovery polarity (off-KZ + Asia). STRONG / present.
- **L2 engineered raid + reclaim:** `swept_prior_low=1` and bar1 closes back above the swept level within the bar → sell-side liquidity raided then reclaimed. PRESENT (sweep is deeper than the median MON, 2.58 — see distinctive note).
- **L3 liquidity asymmetry:** dist_demand 0.13 (floor right under price) vs dist_supply 0.63 + clean_sky overhead; floor much nearer than ceiling, thin overhead (n_supply_overhead 34). STRONG.

**Order-flow / microstructure (Angle 0).**
- **L2 quiet_climax:** vol_climax 0.92 (modest), lower_wick_ratio 0.08 (tiny wick) — low made on quiet volume. The "absorption without theatrics" fingerprint. PRESENT.
- **L9 buy_bubble_first_print:** `buy_bub_w=1` with `sell_bub_w=0` — a BUY bubble prints at/near the low in a sell-bubble desert. Demand footprint emerging exactly where supply is absent. STRONG / distinctive.
- **L3 sell_bubble_exhaustion_gap:** sell_bub_w=0 (no sell bubbles at the low) = institutional sell-pressure footprint fully faded. PRESENT.

**Time / session (Angle 3).**
- **L1 asia_offpeak_flush:** 04:00 UTC Asia/late window with range_exp 2.06 (outsized candle in thin liquidity) = forced-liquidation-into-vacuum snap. STRONG.
- **L3/L9 session & HTF clock:** 04:00 is a clean 4H boundary (a fresh 4H auction opening, htf_clock_alignment). PRESENT.

**Volatility structure (Angle 2).**
- **L7 gap_to_vol_floor / regime:** atr_regime 0.92 + atr_compression_pre 0.82 → coiled, near-vol-floor launch. PRESENT (the leg fires from stored, not spent, energy).
- **range_exp 2.06 / flush_v_ratio 0.29:** sharp V flush. PRESENT.

**RSI (Angle 0 L10).**
- **rsi_holds_above_floor:** rsi_low/rsi_min8 = 34.1 — NOT deeply oversold while making the low. The counterintuitive "non-oversold bottom" MON fingerprint. PRESENT.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **Near-zero post-low heat (mae12 0.15).** This is one of the cleanest no-look-back launches in the set: the floor climbs every bar 1→4 and mfe reaches 3.47 ATR with virtually no adverse excursion. Any reasonable entry (bar1 thrust or bar4 EMA reclaim) is essentially un-stoppable.

2. **Sweep is DEEPER than the canonical MON profile (2.58 vs MON-median ~1.65).** Unlike the "quiet shallow sweep" thesis, fund 6 ran a *deep* stop-run — yet it still snapped (because it was off-killzone, in thin Asia liquidity, into fresh virgin demand). Here the depth is a *forced-liquidation-into-vacuum* signature (Angle-3 L1), not a continuation flush. The reclaim velocity, not the sweep depth, is what marks it.

3. **dealing_range_pos -1.365 = range BREAK, not discount-band.** This violates Angle-1 Lens 6 (which wants -1.0..-0.2). Fund 6 undercut the whole dealing range. The reversal still held because the undercut landed on **fresh, virgin demand** (demand_fresh=1, demand_virgin=1, in_demand=1, dist 0.13) — a defended floor below the visible range, classic engineered-raid-then-accept.

4. **BUY bubble at the low with ZERO sell bubbles.** sell_bub_w=0 / buy_bub_w=1 is a clean polarity event — the demand footprint appears precisely where supply has dried up (Angle-0 L3+L9 confluence).

5. **HTF posture is split, not the canonical 1H-leads:** h1_trend = **-1** (1H still bearish on the E1 snapshot) while htf1_native.trend = +1. So this is NOT the "1H already turned" profile (Angle-5 L5.1); it is a **15M-only spike the higher frames swallow** (Angle-5 L5.5): daily strongly bullish (hd_trend +1, hd_rsi 84.5, hd_pos 0.74) absorbing a 15M Asia flush into 4H demand.

---

## (d) MACRO / HTF CONTEXT

- **Daily (hd):** strongly bullish — hd_trend +1, hd_slope_atr +10.14, hd_pos 0.74, hd_rsi 84.5, hd_dist +12.18. The higher-order trend is firmly up; this 15M low is a pullback *within a strong daily uptrend*, not a counter-trend catch. This is the macro fuel: dip-buy into a daily-bull regime.
- **4H (h4 / htf4_native):** h4_trend +1 (E1) / htf4_native.trend -1 (native resample, still working off the pullback) — 4H is at/inside its demand (htf4_native.in_demand=1, dist 2.37) with clean_sky 2.71 above = floor + runway. The 15M flush lands ON the 4H demand (nested floor, Angle-5 L5.6).
- **1H:** h1_trend -1, h1_rsi 36.7, h1_pos 0.03 — the 1H is washed at the bottom of its range but htf1_native.rsi 74.8 / trend +1 shows the native 1H momentum already lifting. The 15M panic is the *terminal flush* of the 1H pullback, swallowed by an up-trending daily.
- **Net read:** strong daily uptrend → 4H pullback into virgin 4H demand → a thin-liquidity Asia (04:00) stop-run that deep-swept the dealing-range low into fresh demand, printed a BUY bubble with no sell bubbles, and reversed on a quiet-volume, non-oversold, climbing-floor staircase with near-zero heat. Floor below (nested demand) + air above (clean sky, thin supply) + macro tailwind (daily bull) = the MONSTER let-run leg.

---

### Convergence summary
Dominant lenses: Angle-4 geometry (L1 monotone floor=4, L5 clean-ramp, L9 hard-flip, L8 shallow-retest) + Angle-1/3 off-killzone Asia engineered raid into virgin demand + Angle-0 BUY-bubble/sell-exhaustion + daily-bull macro tailwind. The atypical notes (deep sweep, range-break dealing_range_pos, 1H still bearish on E1) are reconciled by the **forced-liquidation-into-thin-Asia-vacuum-onto-virgin-demand** model and the **15M-spike-the-daily-swallows** model — both still MON-consistent.
