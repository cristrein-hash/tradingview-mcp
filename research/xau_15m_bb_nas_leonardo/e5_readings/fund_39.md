# Fund 39 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2025-11-25 file · **Date:** 2026-01-16 15:30 UTC · **Tier:** FORTE · **power_score 8.6** · **leg_atr 23.2**
**Session:** NY · **killzone:** 1 · low=4536.56 close=4555.24 (idx 3341)

This fund is a **NY-session, killzone, two-bar capitulation flush** — i.e. it sits on the *control-typed* side of several MONFORTE priors (NY not Asia, in-killzone, deep sweep, expanded vol, low RSI). It is FORTE not because it is "quiet absorption" but because the **reclaim trajectory after the flush is textbook clean**. The edge here lives almost entirely in the *post-low geometry* (Angle 4), not in the pre-low quiet-absorption fingerprint (Angle 0/1/2/3). Reading it as a quiet-Asia bottom would MISS it; reading it as a sharp-V flush-and-snap CAUGHT it.

---

## (a) ENTRY MECHANIC — where/when I would actually enter

Raw sequence at the turn (UTC, ATR≈15–17 at the low):

| bar | time | o/h/l/c | what happened |
|---|---|---|---|
| −2 | 15:00 | 4607.7 / **4620.3** / 4607.7 / 4616.1 | local swing HIGH (the liquidity above) |
| −1 | 15:15 | 4616.2 / 4617.6 / 4564.6 / **4565.3** | **capitulation marubozu** — −51pt, ~4 ATR, closes on its low |
| **+0** | **15:30** | 4565.4 / 4570.3 / **4536.56** / 4555.24 | **flush LOW** — extends 28pt lower, then **closes back at 4555 (upper ~55% of bar)**, RSI 33 |
| +1 | 15:45 | 4555.7 / 4575.6 / **4555.7** / 4571.3 | green, **low never revisits 4536** (climbing floor), closes above +0 close |
| +2 | 16:00 | 4571.1 / **4593.1** / 4567.7 / **4592.7** | **engulfing thrust**, +21pt, tags EMA21 (4594.7) — reclaim done |

**The trigger is a flush-and-snap with strong-close absorption at the low, confirmed by a higher-low + engulfing thrust:**

- The actual edge-defining event is bar **+0**: a deep wick (down to 4536.6) that **closes 18.6pt off its low (close-location 0.55)** — the flush is rejected *within the same bar*. That is the absorption print (Angle 0 L4 `absorption_reload` close-in-range under high volume v=7515, the leg's peak volume).
- I would **NOT** enter on +0 (no confirmation yet, RSI still 30 on +1). 
- **Entry = close of bar +2 (16:00), at ~4592.7**, on the engulfing thrust that (i) confirms the **higher-low** (bar +1 low 4555.7 > +0 low 4536.6, holds well above), and (ii) **reclaims EMA21** (dossier `reclaim_ema_bars=4`, but price tags the EMA at +2). This is the "sweep+reclaim → micro-HL → thrust" stack.
- **Stop:** below the flush low 4536.6 (≈1.3 ATR risk from entry). **Target/let-run:** the leg ran mfe12_atr=4.12 (close basis); the swing high 4620 then the larger structure overhead is the magnet.
- Honest caveat: `choch_15m_after=0` and `first_higher_low_bar=1` — the structural CHoCH never formally printed in 15M, so the confirmation is **HL + EMA-reclaim + thrust**, not a labeled CHoCH. Entry at +2 captures most of the leg with mae12=1.26 ATR (the +0 low was never retested → a +0/+1 aggressive entry would also have survived, but +2 is the disciplined causal trigger).

## (b) Lenses PRESENT / STRONG here

**STRONG (this is where the fund qualifies):**
- **Angle 4 L4 `flush_then_snap` / L9 `velocity_regime_flip`** — down-velocity bars −1/+0 (~4 ATR + 28pt) immediately mirrored by up-velocity (+1 +16pt, +2 +21pt). Steep down-slope flips to steep up-slope. This is the dominant lens.
- **Angle 4 L1 `reclaim_low_monotone_k`** — bar lows climb monotonically post-low: 4536.6 → 4555.7 → 4567.7 → 4588.2 (run ≥3, no look-back). reaction_seq l_atr 1.26→2.05→3.15→3.40 confirms.
- **Angle 4 L6 `pivot_engulf_thrust`** — bar +2 is a clean bullish engulfing thrust (+21pt, closes near high, swallows +1).
- **Angle 0 L4 `absorption_reload`** — peak-volume bar (+0, v=7515 = highest of the window) closing in the upper half of its range = buyers absorbed the flush.
- **Angle 4 L7 `downleg_gap_velocity_spike`** — bar −1 range ≈2× the prior bars (terminal velocity spike), immediately reversed.
- **Angle 1 L2/L5 + L8 (liquidity)** — swept the prior low (`swept_prior_low=1`, sweep_depth 3.92 ATR), and there is an overhead magnet: the 4620 swing high (untested buy-side liquidity, EQH-style draw) gives the leg a destination.

**PRESENT but only as context / mixed:**
- **Angle 5 L5.1/L5.2 phase-lag:** `htf1_native.trend=+1` and `hd_trend=+1, hd_rsi 71.5` (Daily strongly bullish, hd_eff 0.76) while `htf4_native.trend=−1` — classic **1H/Daily-leads-4H** onset. 1H is above demand (in_demand=0, dist 2.46) = room. This is the textbook MON cross-TF stack and is genuinely strong here.
- **Demand:** `demand_virgin=1` (fresh untested demand), but `in_demand=0` and `dist_demand_atr=1.61` — the flush stopped *just above* a virgin demand, not inside it.

**ABSENT / INVERTED (why naive MON detectors miss it):**
- **Angle 3 (time):** NY session + killzone=1 — the *opposite* of the Asia/off-killzone MON enrichment. This fund refutes "MON bottoms are off-killzone" as a hard rule.
- **Angle 2 / Angle 0 quiet-absorption:** vol_climax 1.63, sweep_depth 3.92 ATR (DEEP), atr_regime 2.25 (EXPANDED), drop20_atr 5.52 (steep) — every "quiet/calm/shallow" MON fingerprint is INVERTED. `quiet_climax` would score 0/3.
- **Order-flow bubbles:** sell_bub_w=4, sell_bub_L=1, buy_bub_w=4 — sell pressure still present, NO buy-bubble first-print, NO NAS-long, smc_bos=0. The order-flow confirmation is weak/absent.
- **RSI:** rsi_low 33, rsi_bull_div=0 — no divergence; a momentum-divergence detector would skip it.

## (c) What is DISTINCTIVE about this bottom

It is a **"loud" FORTE bottom that the quiet-absorption thesis would reject** — a clean **single-stride V-flush in NY killzone into expanded volatility**, where the edge is NOT pre-low character but the **immediacy and cleanliness of the snap-back** (strong-close at the low → monotone climbing floor → engulfing thrust → EMA reclaim in 4 bars). It is the archetype for **Angle 4 (inter-bar geometry) over Angle 0/2/3 (quiet character)**. The deep sweep (3.92 ATR) that *instantly* reclaims is the tell: the flush ran stops below the prior low and was absorbed in one-and-a-half bars, not a slow grind. This is a *stop-run-and-reverse*, not an *accumulation-grind* bottom — both produce big legs but via different fingerprints, and a single "quiet" gate would only catch one family.

## (d) Macro / HTF context

- **Daily: strongly bullish** — hd_trend +1, hd_pos 0.76, hd_eff 0.76, hd_rsi 71.5, hd_dist +4.88 ATR above demand. The higher-TF trend is firmly up; this 15M flush is a **pullback inside a Daily uptrend**, not a counter-trend bottom.
- **1H: turned up** (htf1 trend +1, rsi 69.5, above demand) — the fast HTF already reclaimed.
- **4H: still −1** (native) but h4_trend=+1 in E1 resample with h4_slope_atr +0.31 rising — the 4H is the **lagging frame curling up**. Classic **1H/Daily-leads-4H phase-lag onset** (Angle 5 L5.1).
- **Structure:** flush into the discount of a strongly-bullish Daily, stopping just above virgin demand, with a clean 4620 swing-high magnet overhead. macro_bull=0/macro_bear=0 (no explicit macro flag) — the bullishness reads off the Daily trend/position, not a label.
- **Net read:** a high-momentum buy-the-dip in an uptrend, triggered by a deep NY stop-run that snapped back fast. Entry on the +2 engulf/EMA-reclaim, stop under 4536.6, ride toward the 4620 high and beyond.
