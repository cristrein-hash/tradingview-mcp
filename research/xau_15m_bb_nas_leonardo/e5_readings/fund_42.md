# Fund 42 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2024-11-25 · **Date:** 2025-02-14 20:30 UTC (session LATE, killzone=0) · **Tier:** FORTE · **power_score 3.5**
**leg_atr:** 22.35 · **mfe12_atr:** 4.86 · **mae12_atr:** 0.40 (≈12:1 favorable excursion — exceptionally tight)
**Low:** 2876.73 · **ATR at low:** 3.5 · **Raw bar idx 5281**

---

## (d) MACRO / HTF CONTEXT — the textbook Angle-5 phase-lag bottom: fast frame already up, slow frame still down

This is the **purest cross-TF regime-onset case** in the set, and it directly matches the Angle-5 thesis (unlike fund 38, which contradicted it):

- `h1_trend = −1` (E1, the longer-window 1H resample) but **`htf1_native.trend = +1`** (native 1H, rsi 78.4) — the fast frame has ALREADY turned up at the low.
- **`htf4_native.trend = −1`** (native 4H still bearish, rsi 59) — the slow frame has NOT confirmed. This is the *1H-leads-4H disagreement* Angle-5 L5.1 is built to detect: fast up, slow still down = regime ONSET, not regime, and it means the leg has 4H room above (no 4H supply mitigated yet).
- `h4_trend = +1` / `hd_trend = +1` on the E1 (longer-window) resamples with **hd_rsi 77.8, hd_pos 0.70, hd_slope_atr +13.8** — the Daily is in a strong uptrend. So the bigger picture is bull; this 15M flush is a **deep dip inside a Daily uptrend that the native 4H is reading as a counter-trend wash.**
- `macro_bull=0 / macro_bear=0` (no extreme macro flag). `dealing_range_pos = −0.108` — right at the LOWER edge of the dealing range but NOT broken beyond −1 (Angle-1 L6 / discount-not-breakdown PRESENT, marginal: it is at the very bottom of the discount band, almost a break).

**Special structural fact (raw bars):** the low printed at **20:30 UTC on Friday Feb 14**, and the next bar in the series is **Feb 16 23:00** — i.e. this is a **Friday-late / weekend-edge bottom right into the cash close.** The market carved the low on thin Friday-evening liquidity, then the genuine reaction leg (reaction bars 6+, c_atr 4.7) launched on the **Sunday/Monday re-open.** This is causally important: the entry holds across a weekend gap, and the big thrust is the re-open repricing back up toward the Daily uptrend.

---

## (a) ENTRY MECHANIC — vol-drained grind into fresh demand + NAS-LONG cluster; enter on the bar-1 reclaim close (or on the Sunday re-open thrust)

This is NOT a sharp flush-V. Reading the raw down-leg (bars 5267→5281): price **grinds** lower in small steps while **ATR drains monotonically 8.0 → 7.7 → 5.8 → 4.9 → 4.5 → 3.9 → 3.46** and **volume fades into the low** (4578 → 2742 at 20:15). That is the canonical Angle-0/Angle-2 *quiet drain* signature: selling runs out of fuel, the bars get quieter, the low is made on a small bar (range 5.7 pts, only ~1.6 ATR), NOT on a climax.

reaction_seq (post-low, ATR units):

| bar | c_atr | h_atr | l_atr | green | note |
|---|---|---|---|---|---|
| 1 | 2.44 | 2.71 | 0.40 | ✓ | bar 5282: +6.4 pt thrust off the low, instant reclaim |
| 2–5 | 2.06→1.76 | — | 1.5–1.9 | ✗ | shallow hold (Fri 20:45–21:45), lows stay WELL above 0 |
| 6 | **4.70** | 4.86 | 2.17 | ✓ | Sun/Mon re-open thrust — the real leg |
| 7–9 | 1.91→0.72 | — | dip to 0.51 | ✗ | pullback (holds above the low) |
| 10 | 2.55 | 3.08 | 0.74 | ✓ | resumes |
| 12 | 2.31 | 3.01 | — | ✓ | mfe 4.86 reached |

Entry mechanics: `swept_prior_low=1`, `first_higher_low_bar=1` (HL on bar 1), `reclaim_ema_bars=6` (EMA21 only reclaimed by bar 6 — slow, because of the Friday-night dead bars 2–5), `choch_15m_after=0`, `nas_long_after=0`.

**Concrete entry — two valid points:**
1. **Bar-1 close (2885.3, idx 5282):** the cleanest causal trigger. The low bar swept the leg low (lowest of trailing 50) and the very next bar is a +6.4 pt green reclaim (c_atr +2.44 off a 0.40-ATR low = a strong bar-1 thrust, Angle-4 L6 `pivot_engulf_thrust` PRESENT) AND it prints the first higher-low. SL goes below the swept low ~2876 (≈ −1.0 ATR); mae12 was only **0.40 ATR**, so the stop was never threatened. This entry carries through the weekend.
2. **Re-open / bar-6 confirmation (the EMA21 reclaim):** more conservative — wait for `reclaim_ema_bars=6`, i.e. the Sunday re-open displacement bar (c_atr 4.7). Gives up the first ~2.4 ATR but only enters once the 15M has structurally reclaimed the EMA. Given the Friday-night dead zone, a disciplined trader could legitimately wait for the re-open thrust rather than hold a small position over the weekend.

**The trigger is: vol-drained grind into fresh virgin demand + a dense NAS-LONG cluster + shallow-sweep-reclaim with an immediate higher-low** — NOT a CHoCH and NOT a climax flush. Best R/R is bar-1 close with the sub-low stop.

---

## (b) LENSES PRESENT / STRONG

**STRONG — the core signature here:**
- **Angle-5 L5.1 / L5.2 PHASE-LAG TURN** — `htf1_native.trend=+1` while `htf4_native.trend=−1`: the single cleanest cross-TF separator in the catalog, and it is textbook here. The native 1H has turned up; the native 4H has not. This is the highest-conviction Angle-5 grounding (MON med h1nat=+1 vs CON −1).
- **NAS-LONG cluster into the low** — `nas_long_16=6`, and the RAW shows 6 consecutive NAS-LONG prints from 17:00→20:30, one firing **on the low bar itself** (price 2879.09). A dense, accelerating LONG-signal cluster confirming the bottom in real time. (fund 38 had zero NAS — this bottom is NAS-confirmed.) Angle-0 L9 / Angle-3 L6 supportive.
- **Angle-0 L2 `quiet_climax` / Angle-2 vol-drain — STRONG.** All three quiet-climax conditions met: `vol_climax=0.95` (<1.35), `sweep_depth_atr=0.58` (extremely shallow, far under 1.8), `lower_wick_ratio=0.39` (<0.45). RAW confirms ATR draining 8.0→3.46 into the low and volume fading (Angle-2 L1 `atr_decel_into_low` PRESENT; Angle-0 L8 `vol_drain_into_low` PRESENT). This is the cleanest quiet-absorption fingerprint of the set.
- **Angle-2 / Angle-0 grindy inefficient leg** — `downleg_eff=0.6` is higher than the MON median, but `flush_v_ratio=0.22` (sharp-V flag on the magnitude side) and `consec_down=1` (NOT a long impulsive cascade) — the descent was a stair-step grind, not a clean crash.
- **Fresh virgin demand floor** — `in_demand=1`, `demand_virgin=1`, `dist_demand_atr=−0.11` (flushed right into it), `n_demand_near=8`. RAW confirms a fresh DEMAND zone id 5572 at **2871.23–2874.39** (born Feb 10) directly under the low. The floor is real and defended.
- **`atr_compression_pre=2.11` (very high) with `atr_regime=0.84` (low)** — Angle-2 L1/L3/L6 coiled-spring PRESENT: the bottom forms in a compressed, calm-regime pocket (coil ratio compression/regime ≈ 2.5, among the highest). Angle-5 L5.4 compressed-regime onset STRONG (0.84 << CON 1.28).
- **`rsi_bull_div=1`** — RAW shows price making the lowest low of 50 while rsi prints 27.8 (rsi_min8 23.3, rsi_head 1.06) — RSI did not make its lowest at the price low (it dipped to 22–23 a few bars earlier at 18:00–20:00 then ticked up to 27.8 on the low bar). Hidden/regular bullish divergence PRESENT (Angle-0 L10).

**PRESENT but mixed / weaker:**
- **Off-killzone / LATE session** — `killzone=0`, `session=LATE` (20:30 UTC). Matches the Angle-1/Angle-3 "off-killzone, quiet-hours" enrichment (the 8.1× discriminator). But it is the *Friday-evening dead zone*, not the Asia ramp — and Angle-3 L5 `weekly_phase_position` is actually NEGATIVE-leaning (Friday-late, which Angle-3 lists among the depleted phases). So timing is off-killzone-positive but weekly-phase-ambiguous.
- **`range_exp=1.76`** — moderate range expansion (not a pure coil bar), and `sell_bub_w=6` (a fair number of small sell bubbles in the leg) — sellers were still printing footprint, so Angle-0 L3 `sell_bubble_exhaustion_gap` is only partial.
- **`low_closepos=0.39`** — the low bar closed in the LOWER part of its own range (Angle-0 L4 `absorption_reload` is WEAK on the low bar itself; the absorption shows up on the NEXT bar's reclaim, not the low bar's close).

**ABSENT / against the thesis:**
- **No 15M CHoCH after** (`smc_bos=0`, `choch_15m_after=0`; the only nearby SMC event is a *bearish* CHoCH at 15:30, mid-down-leg). The reclaim was not structure-break-confirmed.
- **`buy_bub_w/L=0`** — no buy-bubble print at the low.
- **`htf1_native.in_demand=0` with dist_demand 2.89** — the 1H is well ABOVE its own demand (room above on the 1H, consistent with the phase-lag thesis), but `htf1_native.rsi=78.4` is extremely hot — the native 1H is already overbought at the low, a caution flag for how much 1H room actually remains.

---

## (c) WHAT IS DISTINCTIVE ABOUT THIS BOTTOM

1. **It is the catalog's cleanest "quiet-drain + phase-lag" bottom AND it is NAS-confirmed.** Where fund 38 was a context-trend pullback that the off-killzone/quiet-coil lenses would have *rejected*, fund 42 is the opposite: nearly every Angle-0/2/5 quiet-absorption lens fires (vol drained 8.0→3.5, sweep 0.58 ATR, vol_climax 0.95, compressed regime 0.84, 1H-turned-while-4H-down) AND it adds a dense NAS-LONG cluster firing on the low bar. This is the convergent "monster-as-quiet-absorption" archetype the catalogs were built around.

2. **Exceptionally low risk.** `mae12=0.40 ATR` vs `mfe12=4.86 ATR` — the bottom never traded meaningfully against the bar-1 entry. The shallow sweep (0.58 ATR, the shallowest in the set) and the immediate higher-low gave an unusually tight, well-defined stop.

3. **The weekend-edge structure is the operational catch.** The low is a Friday-20:30 print; reaction bars 2–5 are the dead Friday-evening tail (price just holding flat above the low), and the *real* leg is the Sunday/Monday re-open thrust (bar 6, c_atr 4.7). `reclaim_ema_bars=6` is "slow" only because of those dead bars — mechanically the reclaim was instant (bar 1) but EMA21 confirmation waited for the re-open. A trader must decide between holding a tight-stop position over the weekend (bar-1 entry, justified by the 0.40 mae) or waiting for the re-open displacement (bar-6 entry, gives up ~2.4 ATR but no weekend exposure).

4. **Two honest caution flags:** (i) the leg launches into a heavy supply ceiling — `n_supply_overhead=44`, `dist_supply_atr=−0.12` with a RAW supply wall at 2924–2940 and even a micro-supply zone (id 5664, 2883.8–2886.0) born AT the low, capping immediate upside; the leg ran +4.86 ATR but had to grind through overhead. (ii) `htf1_native.rsi=78.4` and `hd_rsi=77.8` — buying into a hot 1H/Daily; the dip is bought low but the larger frames are stretched, so this reads as a *late-cycle continuation dip*, not a fresh trend birth.

---

## Summary signature
FORTE quiet-drain phase-lag bottom: native 1H already +1 while native 4H still −1 (Angle-5 regime-onset, the cleanest in the set), inside a strong but stretched Daily uptrend. Low made on a Friday-20:30 vol-drained grind (ATR 8.0→3.5, volume fading, sweep only 0.58 ATR, vol_climax 0.95) into a FRESH VIRGIN DEMAND zone (2871–2874), with a dense NAS-LONG cluster (6 prints, one ON the low bar) and bullish RSI divergence. Entry = bar-1 reclaim close (2885.3) with sub-low stop (~2876, mae only 0.40 ATR ≈ 12:1 R), or the conservative Sunday re-open EMA-reclaim thrust (bar 6). NO CHoCH/buy-bubble needed. Quiet-absorption + compressed-regime + phase-lag lenses fire STRONG; off-killzone PRESENT but weekly-phase (Friday-late) and overhead-supply (44 zones) are the caution flags.
