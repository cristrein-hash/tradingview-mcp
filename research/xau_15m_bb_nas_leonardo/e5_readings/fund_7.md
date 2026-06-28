# DEEP READING — Fund 7 (0-based) · MONSTRO · 2026-05-05 22:30 · block 2026-02-25

**Tier:** MONSTRO · **leg_atr:** 43.92 · **power_score:** 11.4 · **session:** LATE · **killzone:** 0
**mfe12:** 16.08 ATR · **mae12:** 0.15 ATR (price never came back — near-perfect launch)

---

## (a) ENTRY MECHANIC — where/when I actually enter

**Enter on the close of reaction bar 1 (the very next 15M bar after the low), trigger = shallow sweep + 1-bar EMA reclaim + immediate CHoCH, all firing on the same bar.**

The entry stack from `entry_mechanics` is the cleanest possible:
- `swept_prior_low = 1` — the low bar took out a prior fractal low (a stop-run).
- `sweep_depth_atr = 1.06` — but the sweep was **shallow** (control median ≈2.34). It grabbed a local pool, not a chart-low cascade.
- `reclaim_ema_bars = 1` — price reclaimed EMA21 in **one bar**.
- `first_higher_low_bar = 1` — the first higher-low formed immediately.
- `choch_15m_after = 1` — a 15M bullish CHoCH printed right after the low.

The `reaction_seq` confirms there was **no second chance to enter lower**: bar 1 is green and closes at `c_atr 5.37` off an `l_atr 0.15` — a single explosive thrust of >5 ATR from the low, and the bar's own low (0.15) is essentially the swing low itself. `mae12 = 0.15` means after the low prints, price NEVER revisits it. So the only viable entry is *aggressive on bar-1 close* (the sweep-reclaim-CHoCH confluence on that bar), or you miss the leg. There is no patient retest-of-demand entry here — the demand retest *was* the low bar, and the reclaim was vertical.

Concrete rule that fires here: **bottom bar sweeps a prior low by ≤1.5 ATR AND the next bar closes back above EMA21 with a 15M CHoCH → enter at that close, stop below the swept low (~−1.2 ATR, very tight given mae 0.15).**

## (b) Lenses PRESENT / STRONG

### Order-flow (Angle 0)
- **L2 `quiet_climax` — STRONG (3/3).** `vol_climax 0.57` (far below 1.35), `sweep_depth_atr 1.06` (<1.8), `lower_wick_ratio 0.08` (<<0.45). This is a textbook quiet, non-climactic low — the MONFORTE fingerprint, made on tiny volume with almost no rejection wick.
- **L6 `compressed_then_expand` — STRONG.** `atr_compression_pre 1.34` (very high) / `atr_regime 0.62` (very low) = coil ratio ≈2.16. The leg launched from *stored* energy, not spent energy. This is arguably the most distinctive single read here.
- **L10 `rsi_holds_above_floor` — PRESENT.** `rsi_low/rsi_min8 = 34.4` (not deeply oversold; control med ≈28), with `low_revisit = 1`. Momentum was absorbed, not confirmed-down.
- **L3/L8 sell-bubble/vol-drain — MIXED / the one anti-fingerprint.** `sell_bub_w = 18` and `sell_decel = 2` is the ONE place this fund breaks the quiet-absorption mold (MONFORTE median sell_bub_w ≈1). There was loud small-sell-bubble effort INTO the low — yet `vol_climax 0.57` is tiny. Read causally: heavy *advertised* sell signaling that produced almost no volume and almost no wick = **effort-without-result absorption (L1)**. The sellers sprayed signals but couldn't move price or generate real volume → exhaustion. So this is not a contradiction; it is L1 in its purest form (failed supply).

### Liquidity / Auction (Angle 1)
- **Lens 1 `quiet_reclaim` (off-killzone × non-headline) — STRONG.** `killzone 0` + LATE session — the single strongest discriminator (off-killzone S/C lift 8.1×). This bottom formed away from the crowd's flush windows.
- **Lens 6 `discount_not_breakdown` — PRESENT.** `dealing_range_pos = −0.615` sits in the discount band (−1.0, −0.2) — accumulation discount, NOT a range break.
- **Lens 7 (shallow grab + reclaim) — STRONG.** swept + reclaim within the bar, shallow depth.
- Lens 3 asymmetry is NEUTRAL/weak: `n_supply_overhead = 418` is heavy overhead (not the thin-runway profile) — yet the leg ran 16 ATR anyway, so overhead congestion did not cap it. Worth noting as the lens that *failed* to predict here.

### Volatility-structure (Angle 2)
- **L1 `atr_decel_into_low` / L4 `vol_of_vol_collapse` / L7 `gap_to_vol_floor` — ALL STRONG by regime.** `atr_regime 0.62` is exceptionally compressed (MON med ≈0.94, control ≈1.29). Vol had fully drained to its floor before the print — the calmest-regime read in the catalog's framing.

### Time / Session (Angle 3)
- **L1 `asia_offpeak_flush` / off-hours timestamp — STRONG.** 22:30 = the LATE/Asia-ramp window. This is the 2.3×–4.7× enriched zone. The low formed in thin liquidity and snapped back hard.
- `range_exp 0.99` on the bottom bar (not an outsized blow-off bar) — consistent with the leg launching from a coil, not a panic candle.

### Inter-bar geometry / velocity (Angle 4)
- **L1 `reclaim_low_monotone_k` — STRONG (run = 3).** Lows climb 0.15→4.65→7.18 (bars 1-3), small dip at bar 4 (6.66), then resume. A near no-look-back staircase.
- **L2 `reclaim_jerk` / L6 `pivot_engulf_thrust` / L9 `velocity_regime_flip` — VERY STRONG.** Bar-1 delta is +5.37 ATR off the low — an enormous front-loaded thrust, a hard slope-flip from the prior descent. This is the most violent, front-loaded reclaim shape in the dimension's framing.
- **L4 `flush_then_snap` — STRONG.** Up-velocity dwarfs down-velocity (5+ ATR in one bar).

### Cross-TF momentum / regime-onset (Angle 5)
- **L5.4 Compressed-Regime Onset — STRONG.** `atr_regime 0.62` + `atr_compression_pre 1.34` → coiled HTF regime with a single sharp 15M flush inside it.
- **L5.1 Phase-Lag Turn — PARTIAL.** `h1_trend = 0` (flat/inflecting, not yet +1) while `h4_trend = −1` and `hd_trend = −1`. The 1H is *just* turning (not the clean +1 the strongest funds show), but the fast-up/slow-down disagreement is present (`h1_slope_atr +0.15` positive while `h4_slope_atr −2.22`, `hd_slope_atr −10.74` deeply negative).
- **L5.2 1H Room-Above — WEAK/INVERTED.** `htf1_native.in_demand = 1`, `dist_demand_atr 0.88`, `h1_pos 0.39` — the 1H is pinned near/in its demand, not lifted off it. This is the one cross-TF lens that does NOT match the strong profile.
- **L5.7 HTF NAS hand-off — PARTIAL.** `htf4_native.nas_long_rec = 1` (a recent 4H NAS-LONG context is armed), though 15M `nas_long_16 = 0` (no 15M NAS cluster at the bottom — the trigger here was structural, not NAS).

## (c) What is DISTINCTIVE about THIS bottom

1. **A vertical, mae≈0 launch.** `mae12 = 0.15 ATR` / `mfe12 = 16.08` is essentially a perfect bottom — price left and never returned. Bar-1 alone did +5.37 ATR. This is the most front-loaded reclaim in the framing — almost all the geometry/velocity lenses fire at extreme values, not borderline.
2. **The deepest-coil / calmest-regime fund.** `atr_regime 0.62` and the coil ratio ≈2.16 are unusually extreme even for MONFORTE (which medians ≈0.94). The leg was a spring release from a fully-drained, compressed pocket.
3. **The "loud-sell-bubbles but zero result" paradox.** `sell_bub_w = 18` is the *opposite* of the MONFORTE quiet-bubble fingerprint — yet it coexists with `vol_climax 0.57` and `lower_wick_ratio 0.08`. The distinctive causal read: this is failed-supply absorption (L1) caught red-handed — heavy advertised selling that generated no volume and no downside follow-through, then a vertical reversal. It is the cleanest effort-without-result case rather than a counterexample.
4. **Triggered by structure, not by NAS.** `nas_long_16 = 0`, `smc_bos = 0` at entry — the edge came purely from sweep + 1-bar EMA reclaim + 15M CHoCH inside a coiled, off-killzone, late-session demand. A NAS-free monster.

## (d) MACRO / HTF context

All three higher frames are **bearish** at the bottom: `h4_trend −1` (rsi 43.3, `h4_dist −4.5`, slope −2.22), `hd_trend −1` (rsi 37.8, `hd_dist −23.8`, slope −10.74 — a steep daily downtrend), `h1_trend 0` (flat, rsi 50.6, slope just positive +0.15). So this is the **classic 1H-leads-4H phase-lag**: the 15M flushes into a *fresh, virgin* 4H demand (`demand_fresh 1`, `demand_virgin 1`, `in_demand 1`, `dist_demand_atr ≈0`, `htf4_native.in_demand 1`) while the slower frames are still falling. The reversal is a multi-TF spring: a 15M stop-run into an untouched 4H demand floor, fired in the quiet late session, that the fast frame had already begun to flatten. Overhead is heavy (`n_supply_overhead 418`, `htf4 clean_sky_atr 0.02` — no clean 4H sky), yet the daily clean-sky (`htf1_native.clean_sky_atr 2.28`) and the sheer coil energy let the leg run 16 ATR regardless.

---
**Honesty:** all lens framings are calibration on 61/144 curated dossiers, not validation. This fund's loud `sell_bub_w 18` and pinned-1H (`htf1 in_demand 1`) are the two reads that diverge from the canonical MONFORTE profile — kept visible rather than smoothed. The robust, multi-lens convergence is: off-killzone late session + extreme coil/drained-vol + shallow sweep + 1-bar vertical reclaim with CHoCH into a fresh virgin 4H demand.
