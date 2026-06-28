# Fund 55 — DEEP READING (XAU 15M MON+FORTE bottom)

- **Block:** 2024-11-25 file · **Low bar:** 2024-12-20 **01:00 UTC** (Asia ramp) · idx 1738
- **Tier:** FORTE · **leg_atr:** 17.68 · **power_score:** 7.2 · **year:** 2024
- **Outcome geometry:** mfe12 = 5.39 ATR, mae12 = 2.11 ATR (favorable, retest held above the low)

This is one of the **cleanest "quiet-absorption Asia stop-run" bottoms** in the corpus. The whole reversal is delivered in a **single engulfing bar** that absorbs supply on the biggest volume of the window inside thin Asia liquidity, then stair-steps away with no look-back. Almost every "anti-capitulation / quiet absorption" lens across the six angles lights up here; the loud-capitulation lenses correctly stay dark.

---

## (a) ENTRY MECHANIC — where/when to actually enter

**The low and the trigger are the SAME bar (bar +0, 01:00 UTC).** Raw anatomy of that bar:
`O 2590.9 / H 2599.3 / L 2589.7 / C 2598.8`, range ≈ 9.6 pts (~3.6 ATR), close in the **top ~95%** of its own range, **v = 4532 = the largest volume in the entire ±10-bar window** (prior bars ran 800–2000).

Sequence of causation (only info ≤ entry bar):
1. **Grind-down approach** (bars −9..−1): price oozes from 2596 → 2590.9 on rising-but-modest volume (824→2073), RSI sagging 47→38. Extremely **inefficient/grindy descent** (downleg_eff 0.04) — two-sided fighting, not a clean cascade.
2. **Liquidity grab:** bar +0 prints L 2589.7, **undercutting the prior-bar low 2590.6** (`swept_prior_low=1`) — a **shallow** sweep (sweep_depth 0.91 ATR) of the resting local pool, NOT the lowest-of-50 headline low.
3. **Instant absorption + reclaim:** same bar closes 2598.8, +8.9 pts off its own low, **engulfing** bars −1/−2 and **reclaiming EMA21 in 0 bars** (`reclaim_ema_bars=0`; close 2598.8 > ema21 2595.1). This is the bullish-engulf thrust on climactic-for-the-window volume.

**Actionable entry:** enter on the **close of bar +0** (the engulf/reclaim bar) — sweep + instant reclaim + EMA21 reclaim all confirmed at that close. SL below the swept low 2589.7 (≈ 1.1 ATR risk → swing-origin SL of this fund is tight). Confirmation that follows (already not needed to enter, but validates): **15M CHoCH up** (`choch_15m_after=1`), and a **monotone climbing floor** bars +1..+3 (lows 2596.4 → 2597.4 → 2598.2, never revisiting). A retest-buyer who waits gets the first-higher-low at bar +1; the leg pulls back to ~2595.3 around bars +5/+6 (mae 2.11) but holds well above the 2589.7 low — a **shallow retest that holds**.

Trigger classification: **shallow sweep + same-bar reclaim/engulf at EMA21**, confirmed by a 15M CHoCH. Not a deep-flush capitulation; not a multi-bar base.

## (b) Lenses PRESENT / STRONG here

**Order-flow / microstructure (Angle 0):**
- **L4 absorption_reload — STRONG.** Bar +0 = volume spike (4532, ≫1.4× local median) with close in upper 95% of bar → buyers absorbed supply at the low. Textbook.
- **L7 liquidity_grab_no_followthrough — STRONG.** `swept_prior_low=1`, shallow (0.91 ATR), reclaimed within the same bar.
- **L2 quiet_climax — PARTIAL/STRONG.** sweep 0.91 (✓<1.8), wick small-ish; vol_climax 1.46 sits just above the 1.35 line (the reload bar is volume-heavy *by design*) — so this is "quiet in price geometry, loud in absorptive volume." Reads as absorption, not panic.
- **L10 rsi_holds_above_floor — STRONG.** rsi_low/rsi_min8 = 35.5, **not deeply oversold** while making the low — momentum absorbed, classic MON signature (vs ~28 control).
- L1 effort_vs_result_failure — PRESENT (grindy 0.04 downleg_eff = effort spent, little net travel).

**Liquidity / auction (Angle 1):**
- **Lens 1 QUIET RECLAIM — STRONG (the headline 8.1× separator).** `killzone=0` AND the low only undercut a *local* pool (not lowest-of-50) → the off-killzone, non-headline reclaim that most separates MON from control.
- **Lens 6 DISCOUNT-NOT-BREAKDOWN — PRESENT.** `dealing_range_pos = −0.295` → discount third, not a range break.
- Lens 3 asymmetry — MIXED: dist_demand 1.1 vs dist_supply 3.8 (floor nearer than ceiling ✓), but n_supply_overhead = 177 (heavy overhead — the one caution flag; supply is thin *immediately* above, congested further up).

**Volatility structure (Angle 2):**
- **Lens 1 atr_decel_into_low — STRONG.** ATR fell 2.89 → 2.16 over the approach (decel ≈ −0.25) → vol draining into the low.
- **Lens 7 gap_to_vol_floor — STRONG.** `atr_regime = 0.72` (very compressed) — among the calmest regimes in the corpus.
- L3 coiled_spring_squeeze / L4 vov_collapse — PRESENT (atr_compression_pre 1.11, steady pre-low ranges).

**Time / session (Angle 3):**
- **L1 asia_offpeak_flush — STRONG.** session=ASIA, **01:00 UTC** = the 4.7× hour-enrichment bucket. Outsized candle in thin liquidity = forced-liquidation snap-back.
- **L3 time_since_session_open — STRONG.** First ~3h of the Asia session = reaction to the prior session's excess.
- **L4 overnight_low_sweep_clock — PRESENT.** Sweep of the overnight grind-low then reclaim.

**Inter-bar geometry / velocity (Angle 4):**
- **L1 reclaim_low_monotone_k — STRONG.** Lows climb +1..+3 (2596.4→2597.4→2598.2), no-look-back launch.
- **L6 pivot_engulf_thrust — STRONG.** Bar +0 IS the engulfing thrust bar (+8.9 pts, engulfs prior down-bars).
- **L7 downleg_gap_velocity_spike + L4 flush_then_snap — STRONG.** Biggest-range/biggest-volume bar of the leg, reversed within the same bar (flush-V ratio 0.28 = sharp V). Up-velocity matches/exceeds down-velocity.
- **L8 reclaim_dip_depth — PRESENT (shallow retest holds):** dip to ~2595.3 (mae 2.11) stays far above the 2589.7 low.

**Cross-TF momentum / regime-onset (Angle 5):**
- **L5.9 Cross-TF structure hand-off — STRONG.** 15M CHoCH-up (`choch_15m_after=1`) nested in a **1H that already printed a recent CHoCH** (`htf1_native.choch_rec=1`).
- **L5.4 Compressed-regime onset — STRONG.** atr_regime 0.72, compression_pre 1.11.
- **L5.3 HTF RSI hook — PARTIAL.** 1H rsi 40.6 > 15M rsi 35.5 (1H less washed), but 1H rsi not ≥52 — softer than the prototype.
- **Counter-flags vs the Angle-5 ideal:** `htf1_native.trend=−1` and `in_demand=1` (1H still pinned in demand, NOT the "1H already lifted off" profile) — so the L5.1/L5.2 "1H-leads-4H room-above" triad is **WEAK here**. This bottom's edge is microstructure + session + the 1H CHoCH, *not* the 1H phase-lag.

## (c) What is DISTINCTIVE about this bottom

1. **One-bar reversal.** Sweep, absorption, engulf, EMA21 reclaim, and the largest volume of the window all happen in the SAME bar (+0). Most funds spread these across several bars; here the entire turn is a single decisive footprint — the cleanest possible entry.
2. **"Quiet in geometry, loud in volume."** It is NOT a deep climactic flush (sweep only 0.91 ATR, RSI only 35.5, calm 0.72 regime) — yet the turn bar carries the biggest volume of the window. That is **absorption**, not capitulation: a lot of supply hit, price barely went lower, then snapped up. This is the exact MON-vs-control inversion the angle authors flagged.
3. **Textbook Asia stop-run timing** (01:00 UTC, off-killzone) — the single strongest contextual separator (Angle 1's 8.1× / Angle 3's 4.7×).
4. **Caveat:** heavy overhead congestion (n_supply_overhead=177) and a still-bearish, in-demand 1H mean this fund leans on **microstructure + session absorption**, not on a clean HTF-room-above thesis. The leg still delivered (mfe 5.39 ATR) because the immediate sky was clear (dist_supply 3.8 ATR) even if congestion lurked further up.

## (d) Macro / HTF context

- **4H:** trend −1, rsi 33.7, **in_demand=1** (price flushed into 4H demand), dist_demand −0.23 ATR (just inside it), h4_pos 0.21 (low in its range), clean_sky 0.42 ATR immediately above. So the 15M low lands **on a 4H demand floor** — a defended origin.
- **1H:** trend −1, rsi 40.6, in_demand=1, dist_demand +0.6, **choch_rec=1** (1H has already printed a CHoCH — the fast frame is hooking) , clean_sky 0.97 ATR.
- **Regime:** no macro_bull / macro_bear flag; very **compressed vol (atr_regime 0.72)** — a sharp local flush inside an otherwise quiet market = stop-run inside balance, the precondition for a clean snap.
- **Structure read:** a multi-session grind into a 4H/1H demand confluence, a thin Asia liquidity sweep of the local low, and an immediate same-bar absorptive reclaim with a 1H CHoCH already in place. The 4H/1H trends are still technically down (leg has room before mitigating 4H supply), and the 1H CHoCH supplies the "fast frame turning" half — a phase-lag-LITE version of the regime-onset thesis.

---
**One-line summary:** FORTE Asia (01:00 UTC, off-killzone) quiet-absorption bottom — entry on the CLOSE of the single sweep+engulf bar that undercuts the prior local low (shallow 0.91 ATR), instantly reclaims EMA21 on the window's largest volume, and is confirmed by a 15M CHoCH into a 4H/1H demand floor.
