# Angle 2 — Volatility-Structure Lenses for MON/FORTE Bottom Detection (XAU 15M LONG)

**Dimension:** volatility structure — ATR compression/expansion, coiled-spring, range dynamics, vol-of-vol, climax.
**Régua:** RAW-only (`series: t,o,h,l,c,v,rsi,nas_dist,atr,ema21`), as-of the bottom bar `i`, SHIFT1 for repainting layers. Everything below is computable from bars `≤ i` only. **No reaction_seq / post-entry fields** (those are exit-side).
**Author note on grounding (why volatility, not magnitude):** the existing fields already cover compression-pre, climax-volume, range_exp, flush_v. The *unexploited* signal I found in the dossiers is that MON/FORTE bottoms form in **lower absolute ATR regime** (atr_regime med 0.94 vs control 1.29), with **shallower drop20_atr** (4.49 vs 5.54) and **shallower sweep_depth** (1.26 vs 2.02). Translation: monsters are NOT the most violent flushes — they are *calm, efficient, controlled* lows where vol is **draining toward the low**, then springs. Control lows are still in expanded/disorderly vol. The lenses below are all built to fire rare on that disorderly/expanded majority and isolate the *drained-then-coiled* state. Existing static fields miss the **time-derivative and the asymmetry** of vol — that is the open space.

---

## Lens 1 — `atr_decel_into_low` (vol time-derivative at the low)
**Definition (as-of):** slope of ATR over the last K bars ending at `i`, normalized by ATR itself.
`atr_decel = (atr[i] - atr[i-K]) / atr[i-K]`, K=8. Strong-bottom candidate when `atr_decel < -0.15` (ATR *falling* into the low) AND price is making the leg low at `i`.
**Why specific to MON/FORTE:** the dossiers show monsters bottom while ATR is *already contracting* (atr_regime 0.94, compression_pre 0.90), i.e. the selling is exhausting before the print. Control/weak lows are made *on rising ATR* (panic still accelerating, atr_regime 1.29) — those fire `atr_decel > 0`. This is the **derivative** of the static `atr_compression_pre`; nobody mapped the *direction of change of vol at the low* itself, only the level. Fires rare on the expanding-vol majority.
**Combo:** `atr_decel_into_low` × `atr_regime<1.0` × `downleg_eff` (calm + drained + inefficient leg = coiled).

## Lens 2 — `vol_drain_asymmetry` (down-leg vol vs at-low vol)
**Definition:** ratio of ATR-equivalent realized range during the *down-leg* (mean true-range of the 20 bars BEFORE the low) to the range of the **last 3 bars** into the low.
`drain = mean_TR(i-20..i-4) / mean_TR(i-2..i)`. Candidate when `drain > 2.0` (down-leg was 2×+ more volatile than the immediate approach = vol collapsed right at the low).
**Why specific:** a true reversal low is where initiative selling *stops* — the bars carving the actual low go quiet relative to the cascade that produced it. Weak/continuation lows keep the same vol into the low (no drain, `drain ≈ 1`) or accelerate. This asymmetry (loud leg → silent low) is the **mechanical signature of exhaustion**, distinct from absolute `flush_v_ratio` which only looks at one bar. Disorderly control lows fail the silence test.
**Combo:** `vol_drain_asymmetry` × `flush_v_ratio` × `lower_wick_ratio` (drained + climactic flush bar + rejection wick).

## Lens 3 — `coiled_spring_squeeze` (range compression percentile, not absolute)
**Definition:** percentile rank of the **3-bar true range at the low** within the trailing 50-bar distribution of 3-bar ranges. `squeeze_pct = rank(TR3[i] in TR3[i-50..i])`. Candidate when `squeeze_pct ≤ 0.20` — i.e. the bars at the low are among the *tightest 20%* of the recent regime.
**Why specific:** absolute ATR is regime-dependent and noisy across 2 years; a **self-normalized squeeze** isolates the local "spring loading" regardless of whether XAU is in a high- or low-vol era. Monsters (atr_regime 0.94, calm) will frequently sit in the bottom quintile of local range right at the print; expanded control lows sit mid/high percentile. This re-expresses compression as a **local rarity score**, which is exactly what specificity needs (fires rare by construction — only 20% of any window can qualify, and weak lows over-represent the loud part).
**Combo:** `coiled_spring_squeeze` × `bars_in_zone` (tight inside the demand zone) × `atr_decel_into_low`.

## Lens 4 — `vol_of_vol_collapse` (second-order vol stability)
**Definition:** standard deviation of the last K ATR readings divided by their mean — the *dispersion* of volatility itself. `vov = stdev(atr[i-K..i]) / mean(atr[i-K..i])`, K=10. Candidate when `vov < 0.18` (vol has become *steady/quiet*, not whipsawing).
**Why specific to MON/FORTE:** controlled exhaustion shows up as **vol stabilizing** — the market stops convulsing. Disorderly bottoms (most control lows) have high vol-of-vol: big bar, small bar, big bar (still fighting). This is a genuinely new lens — nobody measured the *stability* of volatility at the low, only its level/expansion. A steady-low-vol state is rare and pairs with real bases.
**Combo:** `vol_of_vol_collapse` × `atr_regime<1.0` × `consec_down==0` (steady, calm, selling stopped).

## Lens 5 — `expansion_efficiency_of_drop` (how much vol it cost to make the drop)
**Definition:** ratio of the net down-move to the *cumulative true range spent* over the 20-bar leg.
`drop_eff_vol = abs(close[i] - close[i-20]) / sum_TR(i-19..i)`. Candidate when `drop_eff_vol < 0.30` (the drop was **inefficient** — lots of vol churned, little net distance) AND `drop20_atr` is moderate (not a clean cascade).
**Why specific:** monsters in the data have *lower* `downleg_eff` (0.25 vs 0.39) — they grind/chop down rather than crash cleanly. An inefficient, vol-churning descent = two-sided fighting = buyers already present = base-building. Clean efficient crashes (high eff, control) tend to keep going (continuation, not reversal). This is `downleg_eff` re-expressed through the **vol-spent denominator** instead of bar-count, adding the volatility lens specifically.
**Combo:** `expansion_efficiency_of_drop` × `low_revisit` × `vol_drain_asymmetry` (churned + retested + then went quiet).

## Lens 6 — `compression_break_imminence` (NR + inside coil at the low)
**Definition:** count of the last K=6 bars at the low that are **narrow-range AND inside** the prior bar's range, scaled by ATR. A bar qualifies if `TR[j] < 0.7*atr[j]` AND `high[j] ≤ high[j-1]` AND `low[j] ≥ low[j-1]` (inside-narrow). `coil = count_qualifying / 6`. Candidate when `coil ≥ 0.5` (≥3 of last 6 are inside-narrow).
**Why specific:** an NR/inside cluster at a swing low is the textbook coiled-spring pre-expansion that precedes a big leg. It is *rare* (most lows are V-flush, not a coil) and structurally precedes the kind of clean displacement that defines MON/FORTE. Control lows that are flush-and-bounce (no coil) won't fire. This is a pure **micro-structure compression** lens absent from the current map.
**Combo:** `compression_break_imminence` × `coiled_spring_squeeze` × `range_exp` (coil now → expansion on entry bar).

## Lens 7 — `gap_to_vol_floor` (distance below a quiet-vol baseline)
**Definition:** establish a recent **vol floor** = the 20th-percentile ATR over the trailing 100 bars (`atr_floor`). Measure how close current ATR is to that floor: `floor_ratio = atr[i] / atr_floor`. Candidate when `floor_ratio ≤ 1.3` (vol has returned near its quiet baseline at the low).
**Why specific:** a reversal that *holds* needs vol to have already normalized — the panic priced out. Monsters sit near the vol floor (calm regime). Control lows made mid-panic sit at 2–4× the floor and keep bleeding. Anchoring to a *trailing percentile floor* (not absolute) makes this regime-robust and naturally rare (only lows near the quiet baseline qualify).
**Combo:** `gap_to_vol_floor` × `vol_of_vol_collapse` × `dist_demand_atr` (calm + steady + at a fresh demand zone).

## Lens 8 — `flush_then_freeze` (climax bar followed by vol contraction)
**Definition:** a **two-state sequence**: bar `i-k` (k∈1..4) is a vol-climax flush (`TR[i-k] > 1.8*atr` AND closes in lower 40% of its range = capitulation), AND the bars from there to `i` *contract* (`mean_TR(i-k+1..i) < 0.6*TR[i-k]`). Candidate when both conditions hold = "one big puke, then silence."
**Why specific to MON/FORTE:** this is the canonical *selling-climax → absorption* footprint — the single capitulation bar that flushes weak hands, immediately followed by the market refusing to follow through (vol freezes). Distinct from `vol_climax` (which only checks the bar) by requiring the **post-climax freeze** as-of (within bars ≤ i). Weak lows either have no climax, or climax-then-keep-falling (no freeze) — both fail. The sequence is rare and high-conviction.
**Combo:** `flush_then_freeze` × `sweep_depth_atr` (climax swept liquidity) × `atr_decel_into_low` (and then drained).

## Lens 9 — `range_regime_shift` (structural break in the vol regime AT the low)
**Definition:** compare mean ATR of the **descent window** (i-20..i-8) vs the **base window** (i-7..i): `regime_shift = mean_atr(i-7..i) / mean_atr(i-20..i-8)`. Candidate when `regime_shift < 0.55` (vol regime has *halved* — a true regime change, not just one quiet bar).
**Why specific:** a genuine bottom is a **regime transition** from impulsive-down to balanced; a sustained (multi-bar) halving of ATR encodes that the *character* of the market changed at the low. This is more robust than single-bar drain (Lens 2) because it requires a multi-bar regime, filtering noise. Continuation lows keep the same vol regime (`regime_shift ≈ 1`) — they don't qualify. Captures the macro-of-micro vol shift no current feature touches.
**Combo:** `range_regime_shift` × `op_flow` (regime shift + first 15M CHoCH) × `expansion_efficiency_of_drop`.

---

## Cross-cutting design notes
- **Specificity-first:** Lenses 3, 6, 7 are self-normalized percentile/floor scores — rare *by construction* (only ~20% of any window can qualify), which is what a low false-positive gate needs. Lenses 2, 8, 9 are *asymmetry/sequence* tests (loud→quiet) that the disorderly control majority structurally fails.
- **Convergence over thresholds:** the headline thesis is **drained-and-coiled, not climactic** — the highest-value combo is likely `atr_decel_into_low` (L1) × `vol_of_vol_collapse` (L4) × `flush_then_freeze` (L8): vol falling, vol steady, one puke then silence. Three orthogonal vol time-views of the same exhaustion event.
- **Honesty hook:** if these fire as often on control as on MON (the "wall" outcome), report it — calm/coiled may simply be common at *all* fractal lows. The empirical contrast (MON atr_regime 0.94 vs control 1.29; sweep 1.26 vs 2.02; downleg_eff 0.25 vs 0.39) is the prior that says they *should* separate, but it must be tested on the 205 dossiers with per-year + leave-block before claiming edge.
