# Fund 13 — DEEP READING (MONSTRO, 2025-09-19 01:45 UTC, ASIA)

**Identity:** MONSTRO, power_score 12.3, leg_atr 37.45 (huge clean reversal leg). Block 2025-08-25→11-25. Session = ASIA, killzone = 0. Native low bar = idx 1750, low 3632.2, close 3639.9, atr ≈ 4.25.

---

## (a) THE ENTRY MECHANIC — where/when I actually enter

This is a **single-bar sweep-and-reclaim** bottom, NOT a multi-bar base. The raw tape (confirmed from primitives):

- Bars 1744–1746 (00:15–00:45) carve a local down-leg with lows 3636.7 / 3636.2 / 3637.8 — a resting local low pool ~3636.
- Bar 1747 (01:00) is a **+1.1 ATR green thrust** (o 3640.0 → c 3648.4, RSI 39→44, vol 5843) that **reclaims EMA21** (ema ≈ 3642) and lifts price ABOVE the prior down-leg. So before the low even prints, the 15M has already turned up and reclaimed its mean.
- Bars 1748–1749 hold above EMA (closes 3647.6 / 3646.3, RSI 60s).
- **Bar 1750 (01:45) = the sweep candle:** opens 3646.3, spikes DOWN to **3632.2** (sweeps the 3636 pool AND undercuts to a fresh local low — `swept_prior_low=1`, sweep_depth ≈ 0.94 ATR, SHALLOW), then **closes back at 3639.9** — close in the upper ~54% of the bar (`lower_wick_ratio 0.54`, `low_closepos 0.54`). This is a stop-run that fails to extend and reclaims **within the same bar**.

**ENTRY TRIGGER: sweep + intrabar reclaim, confirmed on the close of bar 1750.** `reclaim_ema_bars=1` and `first_higher_low_bar=1` both = 1 → entry can be taken either on the close of 1750 (sweep reclaimed, back above the swept level and near EMA) or, more conservatively, on the open/close of the **green confirmation bar 1751** (02:00, o 3639.9 → c 3646.8, a +1.6 ATR push that prints the first higher-low and confirms the staircase). I would enter at the **close of 1750** (most R captured — leg ran to mfe 6.55 ATR with mae only 1.58 ATR) with stop just under 3632.2.

Note: this is NOT a CHoCH entry (`choch_15m_after=0`) and NOT a NAS entry (`nas_long_after=0`). It is a **shallow liquidity-grab + immediate reclaim into an already-rising EMA**.

---

## (b) Lenses PRESENT / STRONG here

**STRONG (multi-lens convergence):**

- **Angle 3 L1 / Angle 1 Lens 1 — Quiet off-killzone Asia reclaim (PRESENT, textbook).** ASIA session, killzone=0, 01:45 UTC (hour 01 = the 4.7× Asia-ramp enrichment bucket). The low prints in the thin Asia window and snaps — the single strongest discriminator in the catalog fires cleanly here.
- **Angle 5 L5.1 — HTF phase-lag turn (STRONG).** `htf1_native.trend = +1` (1H already bullish) while `htf4_native.trend = −1` (4H still bearish). This is the exact 1H-leads-4H signature. Confirmed in tape: 15M had already reclaimed EMA21 (bar 1747) before the sweep.
- **Angle 4 L1/L5/L8 — Monotone climbing-floor / clean-ramp reclaim (STRONG).** reaction_seq l_atr: 1.58→2.69→2.76→2.90→3.10→3.44→5.02→5.04→6.09 — a near-perfect no-look-back staircase (the floor climbs essentially every bar). c_atr ramps 3.44→3.16→3.33→3.58→...→6.4 with high linearity. mae12 = 1.58 ATR (price never revisited the low). `reclaim_dip_depth` shallow, `reclaim_low_monotone_k` ≈ max.
- **Angle 0 L7 / Angle 1 Lens 1 — Liquidity-grab-no-followthrough (PRESENT).** Shallow sweep (0.94 ATR < 1.8 threshold) of the 3636 pool, reclaimed inside one bar. Pure stop-run-that-fails.
- **Angle 0 L10 / E1 — RSI holds above floor on the new low (PRESENT).** Sweep-bar RSI = 56.8, rsi_min8 = 35.7 (NOT deeply oversold), `rsi_bull_div=1`. Momentum refused to confirm the price low.

**MODERATE / context:**

- **E1 demand stack:** `in_demand=1`, `demand_fresh=1`, `demand_virgin=1`, dist_demand_atr −0.2 (flushed exactly into a fresh, untested 4H demand). `dealing_range_pos = −0.27` → discount band (Angle 1 Lens 6: discount, NOT a range break). htf4 `clean_sky_atr = 0.02` (tight overhead on 4H is the one cap), but 1D `clean_sky = 99` and 1D trend = +1 (room on the daily).
- **vol_climax 1.47, range_exp 4.66, atr_regime 1.28:** Here the bottom is moderately climactic, not the "quiet/compressed" archetype (atr_compression_pre 0.49 is LOW). So Angle 2 / Angle 5 L5.4 (compressed-coil) do **NOT** fire — this is a sharper, more energetic Asia flush than the median monster.

**ABSENT:** bubbles (buy/sell all 0), NAS (long/short 16 = 0), SMC BOS = 0, sell_decel = 0. No order-flow-bubble or NAS confluence — the read is purely **structural + liquidity + cross-TF momentum**.

---

## (c) What is DISTINCTIVE about this bottom

1. **The reclaim PRECEDED the sweep.** Unusually, the 15M reclaimed EMA21 (bar 1747) and pushed up BEFORE the 3632.2 sweep bar. The sweep is a late shake-out *under* an already-turning structure — the deepest part of the candle is a liquidity grab, not the bottom of a falling leg. This makes the entry exceptionally safe (mae only 1.58 ATR).
2. **Single-bar V, not a base.** No `low_revisit` (=0), no multi-bar accumulation. The whole reversal is one sweep candle + an immediate monotone staircase. Pure flush-then-snap.
3. **Energetic, NOT quiet.** It violates the catalog's dominant "quiet/compressed monster" thesis — atr_compression_pre is LOW (0.49) and vol_climax is elevated (1.47). This monster is a sharp Asia-window liquidity flush + instant reclaim, carried by the cross-TF momentum (1H already up) rather than by coil/absorption.
4. **No exotic confluence needed.** No bubbles, no NAS, no SMC BOS. The edge is entirely: off-killzone Asia + shallow sweep/reclaim of a local pool + fresh virgin 4H demand + 1H-leads-4H phase lag + monotone climbing floor.

---

## (d) MACRO / HTF context

- **Daily (1D):** trend = +1, RSI 69.4, price 5.78 ATR above 1D demand, clean_sky = 99 → the daily is in a strong uptrend with wide-open room above. The whole setup is a **discount pullback inside a daily bull** — the safest LONG context.
- **4H:** trend = −1 (RSI 42.7, h4_pos 0.15, slope −1.71) → 4H is in a corrective down-swing, flushed into a **fresh/virgin 4H demand zone** (dist −0.2, in_demand=1). 4H clean_sky is tight (0.02) — the only overhead concern, mitigated by the 1D room.
- **1H:** trend = +1 already (RSI 39.8 in E1 but native h1 RSI 43.5; h1_pos 0.27, h1 slope −1.15 decelerating). The fast frame has turned while the 4H lags → classic regime-onset window.
- **Read:** a daily-uptrend pullback that flushed into fresh 4H demand during thin Asia liquidity, ran the stops on a local low pool, and reversed the instant the 1H momentum (already bullish) reasserted. Floor below (virgin demand + daily trend), air above (1D clean sky), and a 1H-leads-4H momentum turn — the structural launchpad for the 37.45-ATR leg.
