# Fund 27 — Deep Reading (XAU 15M MON+FORTE bottom)

- **Date / time:** 2025-01-08 04:45 UTC (ASIA session, killzone=0)
- **Tier:** FORTE — leg_atr 28.64, power_score 4.6, year 2025
- **Outcome geometry:** mfe12 5.0 ATR / mae12 0.75 ATR (clean +5R potential, tiny adverse)

---

## (a) ENTRY MECHANIC — where/when I would actually enter this leg

This is a **"quiet flush into fresh demand → immediate 2-bar EMA reclaim"** entry, NOT a climax-reversal entry. The trigger stack, read causally bar-by-bar:

1. **At the low bar (i):** price prints inside a **fresh, virgin 4H demand zone** (`in_demand=1, demand_fresh=1, demand_virgin=1, dist_demand_atr −0.29`) on a SHALLOW sweep of a prior low (`swept_prior_low=1, sweep_depth_atr=0.13` — barely undercut a local pool, not the chart low). Volume is quiet (`vol_climax 0.58`), RSI is **not oversold** (`rsi_low 39.7 / rsi_min8 39.5`). This is the absorption print — I do NOT enter here yet (no confirmation).
2. **Reaction bar w=1:** first bar already green, `c_atr 1.02`, and it is the **first higher-low** (`first_higher_low_bar=1`). The floor starts climbing.
3. **Reaction bar w=2 — THIS IS MY ENTRY BAR:** EMA21 reclaimed at **`reclaim_ema_bars=2`**, and a **15M bullish CHoCH prints just after the low** (`choch_15m_after=1`). c_atr jumps to 2.06 (the second green bar, low_atr holds at 0.85 above the w=1 low). The combination = (sweep + reclaim) + (EMA reclaim ≤2) + (CHoCH up) + (higher-low confirmed) all align on bar 2.

**Concrete trigger I would act on:** enter LONG on the close of reaction bar w=2 — the bar that reclaims EMA21 AND confirms the 15M CHoCH-up, sitting on a higher-low above the demand floor. SL goes just below the demand-zone low / the w=1 higher-low (≈ mae budget was only 0.75 ATR, so a ~1 ATR structural stop is ample). This is **sweep+reclaim → EMA-reclaim → CHoCH confirmation**, the cleanest of the entry families.

Why not wait longer: the reclaim is a **monotone staircase** (see below) — bars 1→9 are ALL green and lows never sag, so waiting costs R. Entering at the EMA/CHoCH confirmation on bar 2 captures ~4 of the 5 available ATR.

---

## (b) Lenses PRESENT / STRONG here

### Quiet-absorption (Angle 0 + Angle 2) — STRONGEST cluster
- **L2 `quiet_climax` (Angle 0): 3/3 FIRES.** vol_climax 0.58 < 1.35, sweep_depth 0.13 < 1.8, lower_wick 0.43 < 0.45. Textbook non-climactic low — the exact MONFORTE fingerprint (low made on modest volume, shallow sweep, no big rejection theatrics).
- **L1 `effort_vs_result_failure` / grindy absorption:** `downleg_eff 0.18` is extremely low (vs control 0.39) — the descent ground sideways, classic failed-supply absorption.
- **Angle 2 `coiled_spring` / compressed regime:** `atr_regime 0.94`, `atr_compression_pre 0.9` — calm, coiled vol pocket, energy stored not spent. `range_exp 1.0` confirms the expansion fires on the turn.
- **L10 `rsi_holds_above_floor` (Angle 0):** rsi_min8 39.5, NOT deeply oversold while making the low → momentum absorbed, not confirming the dump. Distinctive (control bottoms run 28–31).

### Liquidity / Auction (Angle 1)
- **Lens 1 `QUIET RECLAIM` (off-killzone × non-headline low): FIRES.** killzone=0 AND the sweep was only 0.13 ATR (a local pool, not the lowest-of-50). This is Angle 1's single strongest discriminator (8.1× lift). Strong polarity hit.
- **L7 `liquidity_grab_no_followthrough`:** swept_prior_low=1, shallow (0.13), reclaimed within ≤2 bars — shallow-grab + fast-reclaim, the discriminator.
- **Lens 3 liquidity asymmetry:** floor is right here (in fresh demand, dist −0.29) but `n_supply_overhead=111` is heavy — overhead is NOT thin. This is a *partial* miss vs the ideal "clean sky"; the floor is excellent, the runway is congested (more on this in distinctive).

### Time / Session (Angle 3) — STRONG
- **L1 `asia_offpeak_flush` / L3 first-session-hour:** 04:45 UTC is the late-Asia window, off-killzone — directly in the 2.3× Asia-enrichment band. Matches the off-killzone reversal thesis cleanly.

### Inter-bar geometry / velocity (Angle 4) — STRONGEST single discriminator
- **L1 `reclaim_low_monotone_k`: FULL FIRE.** reaction l_atr: 0.75→0.85→2.0→2.12→2.0→2.87→2.82→3.35→3.57 — the floor climbs essentially every bar through bar 9; price never looks back. The "no-look-back staircase" that separates MON from chop.
- **L5 `close_progression_R2` clean ramp: FIRES.** c_atr 1.02→2.06→2.35→2.59→3.09→3.49→3.68→3.73→4.58 — near-monotone rising ramp, high R², one-directional control.
- **L2 `reclaim_jerk` front-loaded:** bar1 +1.02, bar2 +1.04 (the first two bars do a big chunk impulsively) — front-loaded thrust off the low.
- **L8 `reclaim_dip_depth` shallow retest:** the only real dip is bars 10–11 (c 4.14→3.6) but that is AFTER +4.5 ATR of advance and the low only pulls to l_atr 3.51 — far above the entry. The early retest holds beautifully.
- **L6/pivot_engulf_thrust:** bar w=1 already green and thrusting off a 0.75 low.

### Cross-TF (Angle 5) — MIXED (see distinctive)
- **L5.6 nested demand stack: FIRES.** 15M flush lands inside demand that is coincident with BOTH `htf4_native.in_demand=1` AND `htf1_native.in_demand=1` — a nested multi-TF value floor.
- **L5.3 HTF RSI:** h1 rsi 52.4 / h4 rsi 56.8 — HTF momentum NOT broken while 15M washed; the slow frames held strong.
- **L5.1 phase-lag turn: DOES NOT fire** — both h1_trend AND h4_trend are already +1 (and hd_trend 0). This is NOT a 1H-leads-4H phase-lag bottom; both HTFs are already aligned bullish. That is a different (continuation-in-uptrend) flavor.

---

## (c) What is DISTINCTIVE about this bottom

1. **It is a pullback-in-an-already-bullish-HTF, not a regime-turn reversal.** Both 4H and 1H trend = +1 with h4_slope 2.17 / hd_slope 2.87 strongly positive; daily pos 0.78 (high in range). This is a healthy uptrend buying a shallow Asia dip into fresh demand — the Angle-5 "phase-lag" thesis (1H up / 4H down) is ABSENT. The edge here is "buy the discount of a strong trend," not "catch the falling knife."
2. **Extreme quietness of the low.** sweep_depth 0.13 and downleg_eff 0.18 are among the gentlest possible — there was almost no flush at all; price simply ground into demand and turned. This is the purest expression of the Angle-0 "absorption WITHOUT climax" reframe.
3. **Heavy overhead supply (n_supply_overhead=111) yet it ran +5 ATR anyway.** The congested ceiling did NOT cap it — the HTF trend strength and clean staircase overrode the overhead. So the `clean_sky` lens is a partial miss but was overruled by trend momentum. (htf1 clean_sky 0.29 is also thin — the 1H itself had little room, yet ran.)
4. **Tiny adverse excursion (mae12 0.75 ATR).** The entry on the bar-2 reclaim almost never went underwater — a high-quality, low-heat entry. Risk was structurally minimal.
5. **dealing_range_pos −0.073** — basically at mid-range / shallow discount, NOT a deep-discount flush. Consistent with "shallow pullback in trend," not "deep capitulation."

---

## (d) Macro / HTF context

- **Daily:** trend flat-to-up (hd_trend 0 but hd_slope +2.87, hd_pos 0.78, hd_dist 5.89 ATR above its demand, hd_rsi 51) — price is high in the daily range, daily structure constructive, room above on the daily.
- **4H:** clearly bullish (h4_trend +1, h4_slope +2.17, h4_pos 0.64, h4_rsi 56) — the dominant frame is in an uptrend; this 15M low is a pullback within it.
- **1H:** bullish (h1_trend +1, h1_slope +0.31, h1_rsi 49.5) but pulled back near its own demand (h1_dist −0.56, h1_pos 0.34) — the 1H gave back to support inside an up-bias, then the 15M reclaimed.
- **Multi-TF demand stack:** the 15M low coincides with both 4H and 1H demand zones (`in_demand=1` on both natives) → a nested institutional floor. The leg launched off this stacked floor in the quiet Asia window and stair-stepped up +5 ATR with negligible heat.

**Net:** A FORTE bottom of the "shallow Asia pullback into a fresh, nested multi-TF demand floor within a strong 4H/1D uptrend, confirmed by a 2-bar EMA reclaim + 15M CHoCH, launching as a no-look-back monotone staircase." The convergent lenses are quiet_climax (Angle 0/2), off-killzone Asia timing (Angle 1/3), nested demand stack (Angle 5.6), and the monotone-staircase reclaim geometry (Angle 4 L1/L5) — the last being the cleanest confirmation of leg quality. The one non-fire of note is the Angle-5 phase-lag (this is trend-continuation, not regime-turn), and overhead supply was heavy but overridden by trend strength.
