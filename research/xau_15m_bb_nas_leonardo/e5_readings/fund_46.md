# Fund 46 — DEEP READING (XAU 15M MON+FORTE bottom)

**Date:** 2025-09-04 03:00 UTC · **Block:** 2025-08-25_to_2025-11-25 · **Tier:** FORTE
**Leg:** 19.98 ATR · power 4.2 · **Session: ASIA, killzone=0** · year 2025
**Low bar (i):** o3530.8 h3531.9 **l3511.2** c3514.9 (raw, series idx 743)

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

This is a **single-bar climax-flush → immediate engulf-reclaim** turn. The geometry in the raw bars is unambiguous:

- **Bar i (the low):** a wide-range capitulation candle. Range = 3531.9−3511.2 = 20.7 (~2.5 ATR), close in the **lower 18%** of its own range (low_closepos 0.18). This is the terminal flush of a 3-bar accelerating descent (consec_down=3; closes 3537.7→3530.9→3514.9, ATR ramping 6.56→6.98→8.18). RSI=24.7 (genuinely washed). It swept a prior fractal low (`swept_prior_low=1`), sweep_depth 4.98 ATR — a DEEP grab.
- **Bar i+1 (THE TRIGGER):** o3514.9 → **c3529.8**, a +1.85 ATR bullish bar that **engulfs/reclaims essentially the entire prior flush bar's body in one candle**, and its low (3514.5) NEVER revisits the 3511.2 low. `first_higher_low_bar=1`. This is a textbook **pivot-engulf-thrust** (Angle 4 L6) + **flush_then_snap** (Angle 4 L4): the up-velocity off the low matches the flush-in velocity.
- **Bars i+2..i+7:** a tight 6-bar consolidation pinned 3526–3534 (l_atr in reaction_seq holds 1.81→2.29, never sags toward the low) — a **held shallow base / no-look-back floor** (Angle 4 L1 monotone climbing floor: l_atr 0.40→1.81→1.84→2.16, run intact; Angle 4 L8 shallow-retest holds).

**WHERE I ENTER:** at the **close of bar i+1** (the engulf-reclaim), stop below the i low (3511.2). This is the decisive, causal trigger — by that close you have (1) the flush swept liquidity, (2) the bar reclaimed it without revisiting, (3) RSI at the absolute extreme on a bar that closed strongly. Entry mechanic = **sweep + same-/next-bar reclaim (engulf), NOT a later CHoCH** (`choch_15m_after=0`, `reclaim_ema_bars=null` — price stays under EMA21 for the captured window, so the EMA reclaim is NOT the trigger; the structural reclaim of the swept low is). A patient alternative is to add on the i+2..i+7 base hold (higher-low confirmed above 3526), but the primary R is captured at i+1.

**Honest caveat on leg capture:** mfe12 is only **2.83 ATR** and mae12 0.40 — the *labeled* leg here is short-lived in the +12 window even though tier=FORTE/leg_atr=19.98 (the 19.98 leg is the larger structural move the dossier anchors to, not the +12-bar reaction). The clean R lives in the **first ~2 bars off the low**; this is a fast scalp-style turn, not a slow grinder.

---

## (b) LENSES PRESENT / STRONG here

**STRONG — the turn anatomy (Angle 4, inter-bar geometry):** this is the dominant signature for fund 46.
- L6 `pivot_engulf_thrust` ✅ STRONG — bar i+1 engulfs the flush bar (+1.85 ATR thrust off a 0.40-ATR low).
- L4 `flush_then_snap` ✅ — up-velocity ≈ down-velocity at the pivot (sharp symmetric V).
- L1 `reclaim_low_monotone_k` ✅ — climbing floor, lows never revisit (run ≥3).
- L8 `reclaim_dip_depth` ✅ — first pullback shallow, base holds well above the low.
- L9 `velocity_regime_flip` ✅ — steep down-slope (3 accelerating down-bars) inverts to a hard up-thrust.
- L2 `reclaim_jerk` ✅ front-loaded — bar1 does +2.27 c_atr, the bulk of the reclaim.

**STRONG — climax/exhaustion (Angle 2 / Angle 4 down-leg):** this bottom IS the dramatic-flush archetype.
- L8 `flush_then_freeze` (Angle 2) ✅ — one big puke (bar i, 2.5 ATR range, close in lower 18%) then bars i+2..i+7 contract to NR (range collapses to ~3–5 points). Textbook climax→absorption→freeze.
- vol_climax 1.29, range_exp 3.21, vol_climax bar present.

**PRESENT — time/session (Angle 3):** ✅✅ strongly on-profile.
- L1 `asia_offpeak_flush` ✅ — 03:00 UTC, deep Asia/late window, killzone=0, AND an outsized candle (2.5 ATR) in thin liquidity — exactly the "large candle in a thin window = forced-liquidation snap" lens. This is the single most on-archetype lens for fund 46 (Asia off-peak is 2.3× enriched in MON+FORTE).
- Session=ASIA, week mid-phase (Thu 2025-09-04).

**PRESENT — liquidity/auction (Angle 1):** mixed.
- swept_prior_low=1, sweep then instant reclaim ✅ (L7-style stop-run-fails-to-extend) — BUT the sweep here is DEEP (4.98 ATR), not the shallow-quiet profile Angle 0/1 favor. So it reads as a **deep liquidity grab into thin Asia liquidity that snaps**, not a quiet absorption.
- dealing_range_pos = **−3.59** → this is a RANGE-BREAK flush (Angle 1 L6 wants −1.0..−0.2 discount band; this is far beyond −1 = break, NOT the discount-band reading). So the "buy the discount, not the break" lens is ABSENT here — fund 46 is a break-and-reclaim, a different sub-archetype.
- demand_virgin=1 ✅ (fresh demand below), but in_demand=0, dist_demand 2.58 ATR (not landing on a defended floor).

**CONTRA / ABSENT — the "quiet absorption" thesis (Angle 0):** fund 46 is the **opposite** of the quiet-absorption fingerprint.
- vol_climax 1.29 modest-ish but sweep_depth 4.98 (DEEP, not shallow <1.8), rsi_low 24.7 (genuinely oversold, not the MON-typical ~35), sell_bub_w=8 (heavy sell-bubble spray, sell_decel −8), atr_regime 1.72 (EXPANDED vol, not the calm <1.0 MON regime), atr_compression_pre 0.53 (LOW). So Angle 0's `quiet_climax` / `vol_drain` / `compressed_then_expand` lenses are all **FALSE/absent** here. Fund 46 is a loud, deep, oversold capitulation — the dramatic archetype, not the quiet one.

**CONTRA — cross-TF phase-lag (Angle 5):** fund 46 does NOT fit the canonical "1H-leads-4H" MON template.
- htf4_native.trend=+1 AND htf1_native.trend=+1 (BOTH HTF already bullish) — there is no 4H-still-bearish phase lag. Instead, h4_rsi 79.3 / htf4 rsi 74.1 / htf1 rsi 76.5 are **deeply overbought**. So this is a **flush WITHIN an established multi-TF uptrend** (a pullback into trend), not a regime-onset reversal. L5.1 phase-lag, L5.4 compressed-regime = ABSENT.
- This reframes fund 46: it is a **trend-continuation buy-the-deep-flush in a hot 4H/1D uptrend**, mechanically reversing via a deep Asia stop-run, NOT a fresh bottom in a falling market.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is the "dramatic capitulation" archetype, not the "quiet absorption" one.** Deep sweep (4.98 ATR), genuinely oversold (rsi 24.7), heavy sell-bubble spray (8, sell_decel −8), expanded vol regime (atr_regime 1.72). It is exactly the kind of loud flush that Angles 0/1/2 say is *over-represented in the CONTROL set* — yet here it produced a FORTE leg. **The thing that saved it is the turn anatomy: an instant engulf-reclaim that never revisited the low.** The discriminator for THIS fund is post-low SHAPE (Angle 4), not the pre-low quietness.

2. **Asia off-peak deep stop-run.** 03:00 UTC, killzone=0 — a forced-liquidation overshoot into thin liquidity that snapped back. This is the cleanest single on-archetype lens (Angle 3 L1) and it pairs with the deep sweep to explain the violence + the snap.

3. **Range-BREAK, not discount-band.** dealing_range_pos −3.59 — price broke clean below its dealing range then reclaimed. A break-and-reclaim, structurally distinct from the "accumulate in the discount third" funds.

4. **Trend-continuation, not reversal.** Both 1H and 4H were already up and overbought (RSI 74–79). The leg is a hot-uptrend pullback being defended, not a bottom in a downtrend.

5. **Fast/short reaction window.** mfe12 only 2.83 ATR — the R is front-loaded into the first 1–2 bars; this trades like a scalp turn, not a slow runner within the +12 horizon.

---

## (d) MACRO / HTF CONTEXT

- **4H:** trend +1, RSI 79.3 (very overbought), price 0.73 ATR above demand, h4_pos 0.55, h4_slope_atr +3.68 (strong up-slope), h4_eff 0.80 (efficient up-leg). A powerful, extended 4H uptrend.
- **1H:** trend +1, RSI 40.4 / htf1 rsi 76.5 (the native-1H resample reads hot), h1_pos −0.21, h1_dist −4.31, h1_eff 0.54, h1_slope_atr +0.04 (1H momentum cooling/flat at the flush). So the 15M flush is a pullback that cooled the 1H while the 4H stayed strongly bid.
- **1D:** null in dossier (no daily resample for this row).
- **Macro flags:** macro_bull=1, macro_bear=0, nas_long_16=1 (a 15M NAS-LONG cluster fired at the low — directional confluence), smc_bos=0.
- **Read:** a hot 4H/1D uptrend took a sharp Asia-session liquidity flush (deep stop-run below the dealing range, into fresh virgin demand 2.58 ATR below), got instantly absorbed and reclaimed on the next bar, and resumed up. The macro context is **trend-pullback-buy**, and the trigger is the **sweep+engulf-reclaim** at 03:00 UTC.

---

## Summary line
FORTE | trend-pullback deep Asia stop-run: enter at close of bar i+1, the bullish engulf that reclaims the swept flush low (never revisits 3511.2); dramatic-capitulation archetype saved by instant no-look-back reclaim, NOT quiet absorption.
