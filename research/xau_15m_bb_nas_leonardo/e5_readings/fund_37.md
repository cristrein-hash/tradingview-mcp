# Fund 37 — DEEP READING (XAU 15M FORTE bottom)

**Date:** 2024-07-10 01:00 UTC | **Block:** 2024-05-25_to_2024-08-25 | **Tier:** FORTE | **leg_atr:** 23.53 | **power_score:** 10.2
**Low bar:** series idx 2930, low=2363.24, close=2364.09 | **Session:** ASIA, killzone=0
**Outcome geometry:** mfe12=7.02 ATR, mae12=0.79 ATR (essentially never gave back — clean no-look-back leg)

---

## (a) THE ENTRY MECHANIC — where/when I actually enter

This is a **volume-climax flush-then-instant-snap** that I enter on the **close of reaction bar +1 (01:15 UTC)**, a single decisive bullish engulfing thrust. The raw bar-by-bar tape (causal, only bars ≤ entry):

| bar | time | O | H | L | C | v | rsi | atr |
|---|---|---|---|---|---|---|---|---|
| −1 | 00:45 | 2365.35 | 2365.47 | 2364.44 | 2364.67 | 2066 | 58.1 | 0.92 |
| **+0 LOW** | 01:00 | 2364.71 | 2365.09 | **2363.24** | 2364.09 | **4272** | 54.4 | 0.99 |
| **+1 ENTRY** | 01:15 | 2364.09 | **2368.06** | 2364.03 | **2367.19** | 4609 | 51.0 | 1.21 |
| +2 | 01:30 | 2367.18 | 2369.84 | 2366.87 | 2369.00 | 4918 | 63.3 | 1.34 |

**The trigger, causally:**
1. Bar +0 is a **volume-climax capitulation print** — v4272 is ~5× the trailing Asia baseline (~700–900), the largest of the leg, wicking down to 2363.24 then closing back at 2364.09 (close in mid-upper of the bar; lower_wick_ratio 0.46). This is *absorption under a volume spike* — the puke bar where supply got eaten.
2. Bar +1 is the **engulfing reclaim thrust**: opens exactly at the climax close (2364.09), drives +3.97 ATR (c_atr in reaction_seq), reclaims EMA21 **in 1 bar** (`reclaim_ema_bars=1`), and prints the **first higher-low immediately** (`first_higher_low_bar=1`). It also engulfs the prior down-bar's body.
3. `swept_prior_low=1` — the climax bar took out the local pool below (the 00:45/23:45 lows ~2364.4) by a shallow ~1.5 ATR (`sweep_depth_atr=1.51`) and **reclaimed within the very next bar** — classic shallow-grab-and-reclaim, not a deep flush.

**My entry:** market/stop entry on the **close of bar +1 at ~2367.19**, having seen (i) the climax-absorption bar, (ii) the 1-bar EMA reclaim, (iii) the immediate higher-low + engulf. SL below the climax low 2363.24 (~0.8 ATR risk — `mae12=0.79` confirms the low was never revisited). This is a **flush+reclaim** entry, NOT a CHoCH (`choch_15m_after=0`) and NOT a NAS-triggered one (`nas_long_after=0`). The leg then ran monotonically: closes 3.97 → 5.79 → 4.96…, lows climbing 2363.24 → 2364.03 → 2366.87 (no-look-back staircase), mfe 7.02 ATR.

---

## (b) Lenses PRESENT / STRONG here

### Strongly present (the defining stack)
- **Angle 3 L1/L3 — Asia off-peak flush + first-session-hour (STRONG):** 01:00 UTC = the Asia ramp, the single most-enriched hour (4.7× in grounding), `killzone=0`, `session=ASIA`. The bottom prints in the thin Asia window, exactly the off-killzone polarity that marks clean reversal legs. This is the most distinctive lens for fund 37.
- **Angle 4 L6 — pivot_engulf_thrust (STRONG):** bar +1 is a textbook decisive engulfing thrust (+3.97 ATR off a low, opens at climax close, blows through the down-bar). Discrete, large-bodied turn bar.
- **Angle 4 L1/L5 — reclaim_low_monotone_k + close_progression_R2 (STRONG):** lows climb every bar (2363.24→2364.03→2366.87→…), c_atr ramps cleanly 3.97→5.79→4.96; no-look-back staircase, mae 0.79 ATR.
- **Angle 4 L2/L9 — reclaim_jerk / velocity_regime_flip (STRONG):** front-loaded — bars +1/+2 do most of the reclaim (3.97 then +1.82), hard slope flip from a shallow down-drift into a steep up-thrust.
- **Angle 0 L4 — absorption_reload (STRONG):** the climax bar (+0) is the volume spike (4272 ≈ 5× median) that closes mid-upper (close-pos ~0.46–0.6), and the very next bar confirms buyers absorbed it. Volume *rose* into the turn rather than draining — this is the one place fund 37 DEPARTS from the "quiet" thesis.
- **Angle 0 L7 / Angle 1 L1 — liquidity_grab_no_followthrough / QUIET RECLAIM:** shallow sweep (1.51 ATR) of a local pool, reclaimed next bar, off-killzone. Strong.

### Moderately present (context confluence)
- **`in_demand=1`, dist_demand −0.21 ATR, demand_fresh=1, demand_virgin=1:** flush lands ON a fresh, untested 4H/15M demand zone (`htf4_native.in_demand=1`). Defended-floor reading (Angle 1 L3 / Angle 5 L5.6 nested demand) is present — the floor is right under price.
- **Angle 1 L6 — discount, not breakdown:** `dealing_range_pos=−0.838` (deep in the discount third) but NOT beyond −1.0, so a discount-accumulation pullback, not a range break.
- **atr_compression_pre=1.26 (high) + atr_regime=0.39 (very low):** coiled, calm regime — Angle 2 L1/L3/L7 / Angle 5 L5.4 (compressed-regime onset). The leg launched from stored, not spent, energy (atr expands 0.99→2.0 over the reaction). This is strong.
- **HTF aligned bullish:** `htf4_native.trend=+1`, `htf1_native.trend=+1`, `hd_trend=+1` (daily uptrend, hd_slope +16.7). Unlike the deeper-flush MON profile, here the phase-lag lens (Angle 5 L5.1) is muted — both HTF frames are *already* up. This is a **pullback-in-uptrend** bottom, not a regime-onset bottom.

### Notably ABSENT / against type
- **Climax-volume present (anti-quiet):** vol_climax=1.17 and the actual raw tape shows a 5× volume spike at the low. This is closer to the *absorption-reload* (Angle 0 L4) reading than the *quiet-drain* (Angle 0 L2 / Angle 2 L1) reading. So the "quiet absorption" thesis only **partially** applies — the regime was calm (low atr) but the turn bar itself was a volume event.
- **RSI not oversold at all:** `rsi_low=54.4`, `rsi_min8=54.4` — RSI never went oversold (Angle 0 L10 "rsi holds above floor" is present in the extreme: there was no flush in momentum, just a shallow price dip). No bull-div needed (`rsi_bull_div=0`) because RSI never broke.
- **No bubble/NAS/SMC confluence:** all bubble counts 0, `nas_long_16=0`, `nas_short_16=0`, `smc_bos=0`, `macro_bull/bear=0`. The trigger is pure price/volume geometry, no indicator confluence.
- **`downleg_eff=0.09` (very grindy/shallow):** the "down-leg" was barely a leg — `drop20_atr=3.31` is modest, `h1_eff=0.09`, `h4_eff=0.26`. This was a shallow consolidation pullback, not a capitulation cascade.

---

## (c) What is DISTINCTIVE about THIS bottom

1. **It is a shallow pullback-in-uptrend, not a capitulation reversal.** Both 1H and 4H were already bullish (trend=+1), daily strongly up (hd_slope +16.7, hd_dist +18 ATR). Price merely dipped into a fresh demand at the discount of the dealing range and snapped. The FORTE label comes from the *cleanliness and follow-through* (mfe 7.02, mae 0.79), not from a violent turn.
2. **The turn is a single volume-climax bar absorbed and reclaimed in ONE bar.** The discriminator is speed: low at 01:00, full EMA reclaim + engulf + higher-low by 01:15. Everything happened in 15 minutes. This is the rarest/cleanest version of the flush+reclaim mechanic.
3. **Calm regime, loud turn:** atr_regime 0.39 (extremely compressed) but the turn bar carries a 5× volume spike. Coiled-spring (Angle 2) + absorption-reload (Angle 0 L4) combine — stored energy released on a single absorptive print.
4. **Asia-ramp timing (01:00 UTC) off-killzone** — the textbook quiet-window engineered reversal of Angle 1/Angle 3.

## (d) Macro / HTF context

- **Daily:** strong uptrend (`hd_trend=+1`, `hd_slope_atr=16.72`, `hd_rsi=56.1`, `hd_pos=0.71`). Price is high in its daily range — this is a dip *within* a powerful daily advance (July 2024 gold rally toward the August ATH).
- **4H:** trend +1 but `h4_pos=0.35`, `h4_slope −1.2`, RSI 52.9 — a 4H pullback to the lower third / into 4H demand (`htf4_native.in_demand=1`, dist −0.22). Clean sky overhead on 4H is thin (`clean_sky_atr=0.09`) but `n_supply_overhead=44` — some overhead congestion, yet the daily fuel overrode it.
- **1H:** trend +1, RSI 51.6, `h1_pos=0.67`, sitting 0.57 ATR above its own demand (`htf1_native.dist_demand_atr=0.57`, in_demand=0) — the 1H had already lifted off its floor while the 15M did its final dip. Mild multi-TF spring (Angle 5 L5.2), though weaker than the MON phase-lag profile.
- **Net read:** a fresh-demand pullback inside an aligned multi-TF uptrend, flushed in the quiet Asia ramp on a single absorptive climax bar, reclaimed instantly. Floor below (nested demand), daily fuel above. The leg ran because the HTF trend was intact and the dip was shallow/defended, not because a regime turned.

---

**SUMMARY:** FORTE — entry on the **close of reaction bar +1 (01:15 UTC)**: a single-bar volume-climax absorption (5× vol) at fresh 4H/15M demand in the quiet Asia ramp, reclaimed via a +3.97 ATR engulfing thrust + immediate higher-low + 1-bar EMA reclaim (shallow sweep-and-reclaim, no CHoCH/NAS needed).
