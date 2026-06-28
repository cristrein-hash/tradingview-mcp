# ANGLE 0 — Order-flow & Microstructure lenses for MON+FORTE bottom detection (XAU 15M)

**Dimension:** order-flow / microstructure (bubbles BUY/SELL size, volume bursts, absorption-at-low, delta-like proxies). RAW-only, as-of bottom bar / SHIFT1.

## Grounding facts that REFRAME the dimension (61 MONFORTE vs 144 control)

I measured the order-flow E1 fields directly. The naive "capitulation climax" model is WRONG for these bottoms — that is the single most important discovery for this dimension:

| field | MONFORTE | CONTROL | direction |
|---|---|---|---|
| `sell_bub_w` (small-sell-bubble count) | 5.3 (med 1, 31/59 nonzero) | **10.0 (med 8, 115/140)** | MONFORTE has FEWER/smaller sell bubbles |
| `sweep_depth_atr` | **1.65** | 2.34 | MONFORTE sweeps SHALLOWER |
| `downleg_eff` | **0.28** | 0.39 | MONFORTE downleg is GRINDIER (less efficient/impulsive) |
| `atr_regime` | **0.99** | 1.41 | MONFORTE forms in a CALMER vol regime |
| `atr_compression_pre` | **1.07** | 0.86 | MONFORTE preceded by MORE compression |
| `rsi_low` / `rsi_min8` | **37 / 35** | 31 / 28 | MONFORTE is LESS oversold |
| `lower_wick_ratio` | 0.37 | 0.43 | MONFORTE low has SMALLER rejection wick |
| `vol_climax` | **1.23** | 1.54 | MONFORTE volume burst is SMALLER |
| `c_atr@bar6` (recovery height) | **3.37** | 2.77 | MONFORTE recovers HIGHER fast |

**Reframe:** the big clean reversal legs are NOT born from violent flush+climax+deep-sweep. They are born from **quiet, controlled absorption** — a grinding (low-efficiency) decline into a compressed-vol pocket, a shallow sweep, modest volume, RSI not deeply oversold, then an immediate, efficient lift. The control set is the one full of dramatic capitulation bars (deep sweeps, big sell-bubble clusters, high vol). So order-flow lenses here must reward **absorption WITHOUT climax** (effort fails to produce continuation) and **demand stepping in quietly**, and must PENALIZE the loud capitulation signatures that mark the weak/none bottoms. This is the novel angle — invert the usual "find the climax" detector into "find the quiet absorption + failed-effort" detector.

RAW available per bar (`series`): o,h,l,c,v(tick-vol),rsi,atr,ema21. Plus `nas_events`, `smc_events`, `zones`, and bubble counts (`pine_shapes_bubbles` plot activations) already in E1 as `*_bub_*`.

---

## NOVEL LENSES (6–10), each: name | causal def (as-of/SHIFT1) | why MON+FORTE-specific | combo

### L1 — `effort_vs_result_failure` (failed-supply absorption)
**Def:** over the last K=3 down-bars ending at the bottom bar i, compute Σ|v| (tick-volume effort) and the net price travel `(close[i] − close[i−K])/ATR` (result). Lens = `effort_z − |result_atr|` where `effort_z` = volume of those bars vs the 50-bar median volume. FIRES when **high tick-volume effort produced little net downward result** (classic absorption: sellers spent volume, price barely moved lower). All from bars ≤ i.
**Why specific:** MONFORTE has grindy low-`downleg_eff` (0.28) yet normal volume → effort spent, result poor = absorption. Control's efficient flush (0.39 eff) converts effort into travel → result follows effort, no divergence. This catches the "sellers are exhausted but price isn't collapsing" footprint that precedes a clean leg.
**Combo:** {effort_vs_result_failure, downleg_eff, atr_compression_pre}.

### L2 — `quiet_climax` (anti-capitulation absorption)
**Def:** at bottom bar i, `quiet_climax = (vol_climax < 1.35) AND (sweep_depth_atr < 1.8) AND (lower_wick_ratio < 0.45)` — i.e. the low is made on MODEST volume, SHALLOW sweep, SMALL rejection wick. A boolean/graded score (count of conditions met, 0–3). Pure as-of.
**Why specific:** This is the empirical MONFORTE fingerprint (vol 1.23/sweep 1.65/wick 0.37 vs control 1.54/2.34/0.43). It is the INVERSE of the standard capitulation detector, so it fires RARE on the dramatic control bottoms by construction. The novelty: detecting strength via the *absence* of climax theatrics.
**Combo:** {quiet_climax, atr_regime, rsi_min8}.

### L3 — `sell_bubble_exhaustion_gap` (bubble effort drying at the low)
**Def:** count small+large SELL-bubble activations in the 8 bars BEFORE the low vs the 3 bars AT/AROUND the low (using `pine_shapes_bubbles` plot_6/8/10 activations, SHIFT1). Lens = `sell_bub_pre8 − sell_bub_at3` (bubble effort DECELERATING into the low), combined with `sell_decel` already in E1. FIRES when sell-bubble effort was present then DROPS OFF right at the low.
**Why specific:** MONFORTE `sell_bub_w` median = 1 (effort already thin) — the institutional sell-pressure footprint *fades* at the true bottom. Control keeps spraying sell bubbles (median 8) all the way down = supply still active = no reversal. The drop-off (not the level) is the signal — a derivative nobody mapped.
**Combo:** {sell_bubble_exhaustion_gap, sell_decel, buy_bub_w}.

### L4 — `absorption_reload` (volume burst with bullish close-location)
**Def:** at bottom bar i (or i−1), `reload = (v[i] > 1.4×med50_v) AND (close_position_in_bar = (c−l)/(h−l) > 0.6)` — a volume SPIKE where price CLOSES in the upper part of the bar = buyers absorbed the volume at the low. Graded by `v_z × close_pos`. As-of (bar i closed).
**Why specific:** Distinguishes a high-volume bar that CLOSES strong (demand absorbed supply) from a high-volume bar that closes weak (supply winning — the control pattern, `low_closepos` 0.585 weak-leaning). This is a delta-proxy: close-in-range under volume ≈ positive aggressor delta. The combination v-spike + strong-close is what marks the absorptive turn vs a continuation flush.
**Combo:** {absorption_reload, low_closepos, vol_climax}.

### L5 — `delta_proxy_reversal_2bar` (close-location momentum flip)
**Def:** delta-proxy per bar = `sign(c−o) × (v / med50_v) × ((c−l)/(h−l))` (volume weighted by direction and close-location). Compute cumulative over bars i−1,i (the low and the bar before). Lens FIRES when the **2-bar cumulative delta-proxy flips from strongly negative (i−1) to ≥0 (i)** — aggressor pressure turned at the low without needing a big bar.
**Why specific:** A true reversal shows the order-flow flip AT the low; an absorptive control bottom that fails keeps negative cumulative delta. Because MONFORTE recovers efficiently (`c_atr@bar6` 3.37 > 2.77), the flip is real and early. Microstructure delta-flip on tick-vol is a genuinely new lens here (E1 only had raw `low_closepos`).
**Combo:** {delta_proxy_reversal_2bar, low_closepos, reclaim_ema_bars(entry_mechanics)}.

### L6 — `compressed_then_expand` (volatility-coil order-flow)
**Def:** `coil = atr_compression_pre / atr_regime` measured as-of, requiring `atr_compression_pre > 1.0` AND the bottom bar's own range `(h−l)/ATR` NOT extreme (< 2.0). I.e. the low forms inside a coiled, low-energy pocket rather than a blow-off bar.
**Why specific:** MONFORTE: compression 1.07 HIGH, regime 0.99 LOW → coil ratio high; control: compression 0.86, regime 1.41 → coil ratio low (energy already released in the flush). The clean leg launches from stored, not spent, energy. Coil-launch as an order-flow precondition is unmapped (E1 had the two raw atr fields but never their ratio/gate).
**Combo:** {compressed_then_expand, range_exp, effort_vs_result_failure}.

### L7 — `liquidity_grab_no_followthrough` (shallow-sweep + instant reclaim)
**Def:** at the low, `swept_prior_low=1` (took out a prior fractal low — from RAW) AND `sweep_depth_atr < 1.8` (shallow) AND reclaim of the swept level within ≤2 bars (close back above prior low). Microstructure stop-run that FAILS to extend. Boolean/graded by reclaim speed.
**Why specific:** MONFORTE sweeps SHALLOW (1.65) and reclaims fast (entry_mechanics `swept_prior_low` common, `reclaim_ema_bars` small); control sweeps DEEP (2.34) = real continuation, no fast reclaim. The discriminator is **shallow-grab + fast-reclaim**, the opposite of the deep-flush most detectors chase. Pairs sweep depth with reclaim latency — a 2-feature interaction nobody combined.
**Combo:** {liquidity_grab_no_followthrough, sweep_depth_atr, first_higher_low_bar}.

### L8 — `vol_drain_into_low` (effort exhaustion derivative)
**Def:** slope of tick-volume over the last 4–6 down-bars approaching the low: `vol_slope = (med(v[i-1,i]) − med(v[i-5,i-4])) / med50_v`. FIRES when volume is DECLINING into the low (sellers running out of fuel) — negative slope, not the rising-into-climax pattern.
**Why specific:** MONFORTE makes its low on SMALLER volume than the leg (`vol_climax` 1.23 modest) → fuel draining; control bottoms are made ON the volume peak (1.54, climactic). Detecting the *drain* (declining volume into the turn = quiet exhaustion) is orthogonal to peak-detection and matches the quiet-absorption thesis.
**Combo:** {vol_drain_into_low, quiet_climax, sell_bubble_exhaustion_gap}.

### L9 — `buy_bubble_first_print` (demand footprint appearing)
**Def:** first appearance of any BUY bubble (plot_0/2/4 activation, SHIFT1) within the [i−2, i+0] window at/just before the low — `buy_bub_w/L > 0` after a stretch of zero buy bubbles. Graded: first-print + size.
**Why specific:** MONFORTE `buy_bub_w` nonzero 12/59 vs control 37/140 — RARE in both, but when present near the low it's a positive aggressor footprint emerging exactly where sell bubbles fade (pairs with L3). The first BUY print after a sell-bubble desert is a high-specificity, low-base-rate confluence event.
**Combo:** {buy_bubble_first_print, sell_bubble_exhaustion_gap, absorption_reload}.

### L10 — `rsi_holds_above_floor_on_lower_low` (momentum absorption / hidden divergence)
**Def:** at the low bar i, price makes a lower low vs `low_revisit` reference but `rsi_min8 > 32` (RSI did NOT confirm new low / stayed above an oversold floor). This is regular/hidden bullish divergence computed as-of from RAW rsi. Graded by `rsi_min8 − price_new_low_flag`.
**Why specific:** MONFORTE `rsi_min8` = 35 (NOT deeply oversold) while still making the low; control = 28 (RSI confirming the dump). RSI refusing to break down under a price new-low = momentum absorbed = the leg has support. The non-oversold-bottom is counterintuitive and high-specificity (most bottom detectors REQUIRE oversold, which would select the weak control bottoms).
**Combo:** {rsi_holds_above_floor_on_lower_low, rsi_bull_div, downleg_eff}.

---

## Priority (by expected specificity, fires rare on weak/none)
1. **L2 quiet_climax** + **L8 vol_drain_into_low** — the cleanest empirical separation (inverts capitulation). 
2. **L1 effort_vs_result_failure** + **L3 sell_bubble_exhaustion_gap** — true absorption derivatives.
3. **L4 absorption_reload** + **L7 liquidity_grab_no_followthrough** — the turn confirmation.
4. **L10 rsi_holds_above_floor** + **L6 compressed_then_expand** — preconditions.
5. L5 delta_proxy / L9 buy_bubble_first_print — lower base rate, use as confluence boosters.

**Caveat (honesty):** tick-volume on the frozen replay is unreliable in absolute terms (memory: use Session VP for real volume). All volume lenses (L1/L4/L5/L8) should be expressed as *ratios/z-scores within the same block* and validated against the documented tick-volume limitation before any promotion; if they survive only on tick-vol, flag as WEAK. The non-volume lenses (L2 sweep/wick parts, L6, L7, L10) are robust to that limitation.
