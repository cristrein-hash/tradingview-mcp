# ANGLE 4 — Inter-bar Geometry & Velocity (down-leg shape, reclaim trajectory, candle anatomy)

*Discovery agent. Dimension: the SHAPE and VELOCITY of price as a sequence of bars — how the down-leg was carved and how the reclaim is launched. RAW-only, as-of bottom bar / SHIFT1. n=61 MON+FORTE vs n=144 control.*

## Grounding (what the data already says)
Existing static scalars (`flush_v_ratio`, `downleg_eff`, `lower_wick_ratio`, `sweep_depth_atr`, `low_closepos`) barely separate MON from control (medians ~identical, often WORSE for MON). What DOES separate, in the dossiers:
- `reclaim_ema_bars` 3 (MON) vs 5 (ctl); `maxc_atr_by4` 3.01 vs 2.29; `mfe12_atr` 5.19 vs 3.79.
- Inspecting `reaction_seq` bar-by-bar: the MONSTRO 2025-08-27 reclaims as a **monotone staircase** — c_atr 1.58→2.72→2.93→3.62, and crucially `l_atr` (the bar LOW) climbs EVERY bar (0.28→1.45→2.51→2.90): price never revisits, a "no-look-back" launch. The FRACO 2024-11-28 **chops**: c_atr 2.45→2.28→2.06→2.39 with lows dipping back. **The discriminator is the TRAJECTORY SHAPE, not any single-bar statistic.**

The static scalars collapse a sequence into one number and lose the geometry. These lenses are second-order (velocity/acceleration/monotonicity) — angles nobody has scalarized.

All reclaim features compute over `reaction_seq` w=1..k (post-low, already-closed bars; entry can be a few bars after the low because the MON+FORTE leg is large — fully causal). All down-leg features compute over the `series` bars BEFORE the low (i-N..i, all closed).

---

## LENS 1 — `reclaim_low_monotone_k` (climbing-floor / no-look-back launch)
**Definition:** over reaction bars w=1..k (k=4), count consecutive bars where `l_atr[w] > l_atr[w-1]` (each bar's LOW is strictly above the prior bar's low). Output = length of the leading monotone run (0..k). Strong = k or k-1; the floor only goes up. Computed from `reaction_seq.l_atr` (or `series` lows post-low).
**Why MON-specific:** MONSTRO had l_atr 0.28→1.45→2.51→2.90 (run=4). FRACO had lows dipping back (run breaks at bar 2). A real institutional reversal does not let price re-test — buyers defend every new bar's low. Chop / dead-cat bounces let lows sag. This is RARE on weak bottoms because a weak bounce is mean-reverting (lows oscillate), so the monotone-low run is short. Targets the "never look back" signature directly, which `low_revisit` (binary, computed at the low) misses because it doesn't track the POST-low floor.
**Combo:** {`reclaim_low_monotone_k`, `reclaim_ema_bars`, `maxc_atr_by4`} — the "clean staircase launch" trio.

## LENS 2 — `reclaim_jerk` (acceleration of the bounce, not just speed)
**Definition:** from `reaction_seq.c_atr` series, compute first differences d[w]=c_atr[w]−c_atr[w-1] for w=1..4 (per-bar reclaim velocity), then the early-vs-late ratio: `(d[1]+d[2]) / max(d[3]+d[4], eps)`. Also flag `front_loaded = (d[1]+d[2]) >= 1.5*(d[3]+d[4])`. Strong reversals are FRONT-LOADED: the first 2 bars do most of the reclaim (impulsive thrust off the low), then it eases — positive jerk early.
**Why MON-specific:** the MONSTRO did +1.58 then +1.14 in bars 1-2 (most of the move) before flattening. Grind/control bounces are LINEAR or back-loaded (chop then a late spike, like FRACO's bar 7 +1.32 spike after dead bars). A genuine spring-load releases its energy immediately. Front-loaded reclaim is rare in control because weak bottoms lack the trapped-shorts fuel for an instant thrust. Captures *initiative* vs *drift* — a true Auction-Theory rejection is violent at the turn.
**Combo:** {`reclaim_jerk`, `vol_climax`, `range_exp`} — "spring release" (acceleration + climax volume + expansion bar).

## LENS 3 — `downleg_capitulation_taper` (exhausting descent — bars shrinking INTO the low)
**Definition:** over the last M=4 down-bars BEFORE the low (`series`, closed), compute each down-bar's body-range in ATR; fit the sign of the slope. Flag `tapering` if the descent's bar-ranges are SHRINKING (last bar smaller than 3-bars-prior) AND the final bar is a wide-range REJECTION (range>1.5*ATR with close in upper third). I.e. the seller's stride is shortening (running out of supply) and then one violent rejection bar prints the low.
**Why MON-specific:** an exhaustion low is preceded by *decelerating* selling (institutions absorbing), then a capitulation flush + immediate rejection. A weak/continuation low is a STEADY or ACCELERATING drop straight through (no taper, supply still in control). `downleg_eff` is a single ratio that can't tell a steady -0.39 drop from a tapering one. The taper signature (deceleration then rejection) is the literal as-of fingerprint of exhaustion and is rare when the down-leg is impulsive-continuation.
**Combo:** {`downleg_capitulation_taper`, `lower_wick_ratio`, `sell_decel`}.

## LENS 4 — `flush_then_snap` (V-velocity asymmetry: down-speed vs up-speed at the pivot)
**Definition:** velocity_down = ATR-displacement of the last 3 bars INTO the low / 3 (using `series`). velocity_up = `c_atr` reached by reaction bar 3 / 3. Output ratio `snap = velocity_up / max(velocity_down, eps)` and flag `snap_dominant = velocity_up >= velocity_down`. A true flush-V has the UP-leg as fast or faster than the down-leg (instant absorption + reversal). `flush_v_ratio` (existing) only measures the down-leg shape; this measures the SYMMETRY of the turn.
**Why MON-specific:** MON+FORTE legs reverse with up-velocity matching the flush (the MONSTRO snapped +2.72 ATR by bar 2 vs a sharp flush in). A grind-low has slow recovery (up-velocity << down-velocity) — price oozes back up, never matching the drop. Specific because weak bottoms recover lazily; only real reversals snap back with mirror velocity. This is the inter-bar realization of "flush-V vs grind" that no current scalar captures (current ones look only at one side).
**Combo:** {`flush_then_snap`, `flush_v_ratio`, `sweep_depth_atr`}.

## LENS 5 — `close_progression_R2` (linearity / cleanliness of the reclaim path)
**Definition:** linear-fit `c_atr` over w=1..6; output R² of the fit AND the slope. `clean_launch = slope>0 AND R²>0.85`. Measures how STRAIGHT the reclaim is — a clean monotone ramp has high R²; a chop has low R² even if it ends higher.
**Why MON-specific:** the MONSTRO's c_atr is a near-straight ramp (high R²). The FRACO oscillates (low R²) yet still drifts up — so an endpoint-only or "green-count" feature would falsely score it. A high-R² rising reclaim means one-directional control = institutional initiative with no two-way auction. Rare in control because weak bounces are two-sided (whipsaw → low R²). This separates "trended up cleanly" from "noisily ended up", which `green4` (3 vs 3, no separation!) cannot.
**Combo:** {`close_progression_R2`, `reclaim_low_monotone_k`, `choch_15m_after`}.

## LENS 6 — `pivot_engulf_thrust` (single-bar reversal anatomy at/after the low)
**Definition:** identify the reversal bar (first green bar with close > prior bar's high, w∈1..3 of reaction). Compute its body-range/ATR and whether it ENGULFS the prior 1-2 down-bars' ranges (its low ≤ prior low AND close ≥ prior open-of-down-bar). Output `thrust_atr` (the engulfing bar's net displacement in ATR) and binary `bullish_engulf_thrust`. This is candle-anatomy of the turn bar, as-of when it closes.
**Why MON-specific:** real reversals print a decisive engulfing/thrust bar (the MONSTRO's bar 1 = +1.58 ATR off a 0.28 low = strong thrust). Weak bottoms turn with small-bodied dojis / indecision bars (no engulf). The engulfing thrust = a single bar where buyers overwhelm the prior sellers — a discrete, rare event on weak lows where the turn is gradual/muddy. Specific because the magnitude+engulf condition both must hold; chop produces neither.
**Combo:** {`pivot_engulf_thrust`, `vol_climax`, `low_closepos`}.

## LENS 7 — `downleg_gap_velocity_spike` (terminal acceleration / climax flush bar)
**Definition:** over the final 2 bars into the low, detect a VELOCITY SPIKE: the last down-bar's range/ATR ≥ 2× the median range of the preceding 6 down-bars (a climactic widening — capitulation candle). Flag `climax_flush`. Pair with the IMMEDIATE next bar being green (`flush_reversed_next = reaction bar1 green`).
**Why MON-specific:** monster bottoms are often a single climactic capitulation bar (max velocity) that immediately reverses — stop-run + absorption. A continuation low has no terminal spike (steady drop) or spikes and KEEPS going. The combination "biggest-bar-of-the-leg then immediate reversal" is the textbook exhaustion event and is rare: most lows lack a climax bar, and of those with one, only true bottoms reverse the very next bar. Distinct from `vol_climax` (volume) — this is RANGE/velocity climax, a different RAW axis (price displacement, robust even where tick-volume is unreliable).
**Combo:** {`downleg_gap_velocity_spike`, `vol_climax`, `flush_then_snap`}.

## LENS 8 — `reclaim_dip_depth` (post-low pullback shallowness — the retest holds)
**Definition:** after the reaction high of bars 1..3, find the deepest pullback low in bars 4..8 and measure how far it retraces toward the original low: `dip_frac = (reaction_high − pullback_low) / (reaction_high − 0)` in ATR terms (0 = the original low). Flag `shallow_retest = dip_frac < 0.5` (the first dip holds well above the low). Computed from `reaction_seq.l_atr`.
**Why MON-specific:** in a real reversal the first pullback is shallow and held by buyers (higher-low forms well above the bottom) — the MONSTRO's lows kept climbing. In a weak bounce the first pullback returns most of the way to the low (deep retest → eventual breakdown). This measures *quality of the higher-low*, the structural confirmation, as a continuous depth rather than `first_higher_low_bar` (just timing, 1 for both MON and ctl — no separation). Rare on weak bottoms because they cannot hold a shallow retest — supply re-enters.
**Combo:** {`reclaim_dip_depth`, `reclaim_low_monotone_k`, `choch_15m_after`}.

## LENS 9 — `velocity_regime_flip` (sign-flip sharpness: bearish-to-bullish slope reversal magnitude)
**Definition:** slope_pre = OLS slope of `c` over the 5 closed bars before/at the low (in ATR/bar, negative). slope_post = OLS slope of `c_atr` over reaction bars 1..4 (positive). Output `flip_magnitude = slope_post − slope_pre` (both in ATR/bar; larger = sharper V). Flag `hard_flip = flip_magnitude > 1.5 ATR/bar`.
**Why MON-specific:** captures the DERIVATIVE discontinuity at the pivot — how hard the trend's slope inverted. A monster bottom inverts a steep down-slope into a steep up-slope (huge flip). A grind low flips a shallow down-slope into a shallow up-slope (small magnitude) or barely flips. Specific because it requires BOTH a real prior descent AND a real thrust; chop has neither steep side. This is the cleanest single scalar for "sharp V vs rounded/grind", and it's a derivative — orthogonal to all level/distance features.
**Combo:** {`velocity_regime_flip`, `flush_then_snap`, `reclaim_jerk`}.

---

## Specificity priors (which lenses likely fire RARE on control)
Highest expected specificity (fire rare on weak/none, from the bar-by-bar contrast): **L1 (monotone climbing floor)**, **L5 (clean-ramp R²)**, **L9 (hard slope-flip)** — these directly encode the staircase-vs-chop difference that the endpoint scalars (`green4`, `low_revisit`, `downleg_eff`) provably FAILED to separate. **L8 (shallow retest)** encodes higher-low quality that `first_higher_low_bar` missed. L2/L4/L7 target the impulsive thrust (fuel-dependent) and should be rarer on weak lows. L3/L6 are exhaustion-anatomy on the down-leg (may be noisier — flush is common; the discriminator is taper/engulf, test before trusting).

## Causality / honesty notes
- All reclaim lenses use bars AFTER the low → entry is a few bars late (acceptable: MON+FORTE legs are large, plenty of R left; matches the plan's "entry can be several bars after the minimum").
- All down-leg lenses use bars ≤ the low (closed) → as-of/SHIFT1 clean.
- Endpoint-collapsing scalars failed; these are sequence/derivative features by design — the bet is that SHAPE (monotonicity, R², slope-flip) carries the signal that magnitudes lost.
- n=61: any lens must pass per-year + leave-block + null-of-max + no-concentration before being called specific. Specificity (rare on control), not recall, is the gate.
