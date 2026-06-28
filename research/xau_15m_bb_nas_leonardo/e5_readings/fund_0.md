# DEEP READING — Fund 0 — MONSTRO

**Block 2025-08-25 · Bottom 2025-08-27 07:15 UTC · LONDON · MONSTRO · leg 69.71 ATR · power 15.2 · mfe12 4.08 / mae12 0.28**

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

This is a **shallow-sweep + immediate-reclaim, no-look-back staircase** launch. The entry is *early and clean*; you do not need to wait for confirmation deep into the reaction.

The reaction_seq decides it for me:

| w | c_atr | l_atr | green |
|---|-------|-------|-------|
| 1 | 1.58 | **0.28** | 1 |
| 2 | 2.72 | 1.45 | 1 |
| 3 | 2.93 | 2.51 | 1 |
| 4 | 3.62 | 2.90 | 1 |

- **Bar +1 is the trigger bar**: a +1.58 ATR green thrust off the very low, closing at 1.58 ATR while its own low only printed 0.28 ATR above the bottom. That is an engulfing thrust off a shallow sweep (`sweep_depth_atr` 0.12, `swept_prior_low`=1) — the stop-run took out a local pool by a sliver and instantly reversed.
- **`first_higher_low_bar` = 1** and **`reclaim_ema_bars` = 2**: the first higher-low forms immediately, EMA21 is reclaimed within 2 bars, and **`choch_15m_after` = 1** prints a 15M bullish CHoCH right after the low.

**Concrete entry:** enter on the close of reaction bar +1 (the engulf/reclaim thrust through the prior bar's high), OR — for the more conservative fill — on the bar +2 retest that never came back (l_atr climbed 0.28→1.45, the floor lifted). Both fills have a defended structural stop at the swept low (mae over 12 bars was only 0.28 ATR — price NEVER revisited). This is the textbook **sweep+reclaim → micro-HL → CHoCH** sequence, taken at the +1/+2 close. The staircase is monotone for all 4 opening bars (l_atr strictly rising) — a "no-look-back" launch, so an early fill is safe; there is no deep retest to wait for.

The only reason to delay would be confirmation, and confirmation arrived on bar +1 itself (engulf + reclaim). Waiting longer just costs R (price was already +2.7 ATR by bar +2).

---

## (b) LENSES PRESENT / STRONG here

### STRONG — inter-bar geometry (Angle 4) — the dominant signature
- **L1 `reclaim_low_monotone_k` = MAX (run = 4).** l_atr 0.28→1.45→2.51→2.90, every bar's low strictly above the prior — perfect climbing floor. This is the single cleanest "monster" fingerprint and it is maxed out.
- **L2 `reclaim_jerk` — FRONT-LOADED.** d[1]=+1.58, d[2]=+1.14 (first two bars do +2.72), then it eases (d[3]=+0.21, d[4]=+0.69). Front-loaded spring release.
- **L4 `flush_then_snap` — snap-dominant.** Up-velocity matches/exceeds the flush; +2.72 ATR reached by bar +2.
- **L5 `close_progression_R2` — clean ramp.** c_atr 1.58→2.72→2.93→3.62 over w1–4 is near-linear rising = high R², one-directional control.
- **L6 `pivot_engulf_thrust` — PRESENT.** Bar +1 = +1.58 ATR thrust off a 0.28 low, green, engulfing.
- **L8 `reclaim_dip_depth` — shallow (passes).** No meaningful dip back toward the low; mae12 = 0.28 ATR confirms the retest held.
- **L9 `velocity_regime_flip` — hard flip.** Steep down-slope inverted to steep up-slope.

### STRONG — cross-TF / regime (Angle 5) — but with a TWIST
- **L5.6 `multi_tf_demand_stack` — PRESENT and clean.** 15M `in_demand`=1, `demand_fresh`=1, `demand_virgin`=1, `dist_demand_atr` −0.28 (flushed into the floor); `htf4_native.in_demand`=1 (15M demand nested inside 4H demand); `htf4_native.clean_sky_atr` 0.05 and 15M `dist_supply_atr` 0.27 / `n_supply_overhead` 12 → floor below + air above. Stacked nested demand with a runway.
- **L5.9 `cross_tf_structure_handoff` — PRESENT.** 15M CHoCH-up (`choch_15m_after`=1) printing into an HTF that is structurally bullish.
- **L5.3 HTF RSI Hook — partial.** 15M deeply washed (`rsi_min8` 21.9) while `htf1_native.rsi` 53.2 and `htf4_native.rsi` 65.1 never broke — the slower frames refused to confirm the 15M panic.

### PARTIAL — liquidity / auction (Angle 1)
- **Lens 7 stop-run exhaustion — YES.** `sell_decel` = −6, `sell_bub_w` = 6 then fading; sell-side initiative decelerating into the low.
- **Lens 1 quiet-reclaim — FAILS on timing** (see below): this bottom is IN-killzone (London).

### PARTIAL — momentum (Angle 0 L10)
- `rsi_bull_div` = 1, `rsi_head` 0.91. There IS a bullish divergence, but note `rsi_min8` 21.9 means RSI *did* confirm a deeply oversold low — so L10's "RSI holds above floor" does NOT fire here (this low is genuinely oversold).

---

## (c) WHAT IS DISTINCTIVE — where this fund DEFIES the catalog priors

This MONSTRO is a **counter-example to two of the catalog's headline theses**, which makes it diagnostically important:

1. **It is IN-killzone, LONDON — not off-killzone Asia.** Angles 1 and 3 built their strongest probe on "MON+FORTE bottoms form OFF killzone, in quiet Asia." Fund 0 is `session`=LONDON, `killzone`=1. So the killzone-polarity lens, the single highest-lift discovery in Angle 1 (8.1×), would MISS this monster entirely. → killzone-off is at best a *recall-limited* booster, never a gate; this fund proves real monsters also print inside London KZ.

2. **It is DEEPLY oversold, not "less-oversold quiet absorption."** Angle 0 / Angle 2's whole reframe is "monsters form on modest sell-off, RSI ~35, calm vol, shallow flush — NOT capitulation." Fund 0 has `rsi_low` 33.6, **`rsi_min8` 21.9** (more oversold than the MON median), `drop20_atr` 4.48, `vol_climax` 1.05 (low) but `atr_regime` 1.21 (slightly ELEVATED, not the MON-typical 0.94). So the "quiet-absorption / non-oversold" fingerprint does NOT describe this fund. → the anti-capitulation lenses (Angle 0 L2/L8/L10, Angle 2 vol-floor) would also miss it.

**So which lenses DO catch it?** The **trajectory-shape lenses (Angle 4)** and the **nested HTF-demand-with-aligned-trend lenses (Angle 5.6 / 5.9)**. The signal here lives in *what happened at and after the turn* (perfect monotone staircase, front-loaded thrust, instant CHoCH, mae 0.28) and in the *structural launchpad* (fresh virgin 4H demand, clean sky, both HTF already bullish), NOT in the climax/vol/session statistics of the low itself.

The deepest distinctive trait: **mae12 = 0.28 ATR with mfe12 = 4.08 ATR.** Price literally never came back. This is the rarest, most monster-defining property — a sweep so shallow and a reclaim so immediate that there was zero post-entry adverse excursion. The entry stop was never threatened.

---

## (d) MACRO / HTF CONTEXT

Unlike the canonical "1H-leads-4H phase-lag" monster (Angle 5.1, where 4H is still bearish), **fund 0's HTF is already fully bullish on BOTH frames:**
- `htf4_native.trend` = +1, RSI 65.1, `in_demand`=1, `clean_sky_atr` 0.05.
- `htf1_native.trend` = +1, RSI 53.2.

This is therefore a **pullback-into-fresh-demand inside an established HTF uptrend**, not a regime-onset reversal. The 15M flushed −4.5 ATR into a virgin 4H demand zone (`demand_virgin`=1, `demand_fresh`=1) that sits with clean air above (4H clean_sky 0.05, only modest 15M overhead supply). The 1H is mid-range (`h1_pos` 0.29, `h1_eff` 0.49, `h1_rsi` 46.6) — a healthy pullback, not a broken structure.

So macro read = **trend-continuation buy of a high-quality discount**: strong 4H uptrend, deep-but-shallow-sweep 15M flush into a defended fresh demand floor, instant absorption and no-look-back staircase reclaim, with a clean overhead runway for the leg to run (it ran to mfe 4.08 ATR within 12 bars, peaking c_atr 3.82 at bar +7 before the orderly w8–w12 give-back). The `dealing_range_pos` −0.044 (basically the lower-mid of the range, not a range-break) confirms a discount pullback rather than a trend-breakdown.

---

### One-line synthesis
A LONDON-killzone, deeply-oversold pullback into FRESH VIRGIN 4H demand within an already-bullish HTF — caught not by the off-killzone/quiet-absorption priors (which miss it) but by the **shallow-sweep+instant-reclaim, perfectly-monotone front-loaded staircase** (Angle 4) launching off a **nested 4H+15M demand stack with clean sky** (Angle 5.6); mae 0.28 / mfe 4.08 = a textbook no-look-back monster.
