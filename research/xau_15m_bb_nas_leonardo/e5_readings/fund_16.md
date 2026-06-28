# Deep Reading — Fund 16 (MONSTRO)

**Date:** 2026-01-08 12:15 (NY session) | **Block:** 2025-11-25 | **Tier:** MONSTRO | **power 9.2** | **leg_atr 33.76**
**Outcome geometry:** mfe12 = 7.05 ATR, mae12 = 1.48 ATR → ~4.8:1 MFE/MAE, a clean monster leg with almost no post-entry heat.

---

## (a) ENTRY MECHANIC — where/when I would actually enter this leg

**Trigger: sweep + immediate 1-bar reclaim → enter on the close of reaction bar 1 (the first green thrust bar).**

The entry-mechanics stack is maximally tight here and all four causal triggers fire on the SAME bar:
- `swept_prior_low = 1` — the low took out a prior fractal low (a stop-run, `sweep_depth_atr = 2.35`).
- `reclaim_ema_bars = 1` — EMA21 reclaimed in ONE bar.
- `first_higher_low_bar = 1` — the higher-low formed on bar 1.
- `choch_15m_after = 1` — a 15M bullish CHoCH printed right after the low.

So this is not a "wait for retest / wait for CHoCH" setup — the reclaim, the HL, and the CHoCH are all simultaneous on the first reaction bar. `reaction_seq[w=1]` confirms it mechanically: c_atr 3.25 closing well above the low (l_atr 1.91), green, a decisive thrust off the bottom. That bar IS the engulfing/reclaim event.

**Concrete plan:** enter LONG on the close of reaction bar 1 (the sweep+reclaim bar), stop just under the swept low. mae12 = 1.48 ATR means after entry the trade barely dipped — the structural stop (≈ below the sweep low, ~2 ATR) is never threatened. The leg then climbs in a near-monotone staircase (lows: 1.91→2.89→1.48[shallow dip bar3]→1.98→… closes ramp 3.25→3.06→2.01→4.10→…→6.16 by bar 11). Note bar 3 dips l_atr to 1.48 (a shallow retest near the low) — this is the only soft spot; the climbing-floor resumes immediately after, so the HL structure holds and the leg runs to +7 ATR.

**Caveat (causal honesty):** `nas_long_after = 0` — no NAS-LONG confirmation. The trigger is purely structural (sweep+reclaim+CHoCH), not signal-confirmed. That is the entry to take here.

---

## (b) Lenses PRESENT / STRONG here

### Order-flow / microstructure (Angle 0)
- **L7 liquidity_grab_no_followthrough — PARTIAL.** `swept_prior_low=1` + reclaim within 1 bar = textbook shallow-grab-fast-reclaim. BUT `sweep_depth_atr = 2.35` is DEEPER than the MONFORTE median (~1.65) — this is a deeper, more "control-like" sweep that still reclaimed instantly. The reclaim speed carries it, not the shallowness.
- **L4 absorption_reload — PRESENT.** `low_closepos = 0.87` (very strong close-in-range at the low) with `vol_climax = 1.10` — buyers absorbed at the low and closed near the top of the bar. Strong delta-proxy positive.
- **L2 quiet_climax — WEAK/MIXED.** vol_climax 1.10 (quiet ✓), lower_wick_ratio 0.33 (small wick ✓), but sweep_depth 2.35 (NOT shallow ✗). 2-of-3 → leans quiet-absorption, not climactic.
- **L10 rsi_holds_above_floor — PRESENT.** `rsi_low / rsi_min8 = 32.8` — NOT deeply oversold (MONFORTE fingerprint; control bottoms median ~28). Momentum was absorbed, not confirmed-broken.

### Liquidity / Auction (Angle 1)
- **Lens 1 QUIET RECLAIM — MIXED.** `killzone = 0` ✓ (off the London/NY kill window despite being NY session-tagged — the 12:15 timestamp sits outside the strict KZ). But the low is deep (`dealing_range_pos = -1.32`, a RANGE BREAK below the discount band, not inside it).
- **Lens 6 DISCOUNT-NOT-BREAKDOWN — ABSENT/INVERTED.** `dealing_range_pos = -1.32` is BEYOND −1.0 → this is a range-BREAK low, the opposite of the "buy the discount, don't buy the break" Lens-6 polarity. This bottom is a flush THROUGH the range, reclaimed — closer to a deep-sweep-reclaim than a clean discount accumulation.
- **Lens 3 LIQUIDITY ASYMMETRY — STRONG.** `dist_demand_atr = 0.0` (sitting exactly on demand), `in_demand = 1`, `demand_fresh = 1`, `demand_virgin = 1`. Floor is at price; `dist_supply_atr = 0.07` (supply essentially overlapping — see distinctive note). `n_supply_overhead = 78` is HIGH (congested above), which slightly caps the clean-sky reading.

### Volatility structure (Angle 2)
- **Compressed-then-coiled regime — PRESENT.** `atr_regime = 0.94` (calm, MONFORTE-typical) + `atr_compression_pre = 1.08` (coiled pre-flush). Coil ratio high. The leg launched from stored energy in a low-vol pocket.
- **`downleg_eff = 0.20` — STRONG.** Grindy/inefficient descent (MONFORTE median ~0.28; this is even grindier) = two-sided fighting / absorption on the way down, the base-building signature.
- **`range_exp = 2.91` — PRESENT.** The reaction expands hard on the turn (coil → release).
- **`drop20_atr = 4.49`** = moderate, not an extreme cascade — fits the calm-controlled profile.

### Time / Session (Angle 3)
- **Killzone = 0 — PRESENT** (off-KZ ✓, the MONFORTE-enriched polarity).
- **Session = NY — AGAINST profile.** NY is DEPLETED in strong bottoms (15% strong vs 46% control). This monster bottoms in NY, which is the counter-thesis case. The off-killzone flag rescues it partially, but this is NOT the Asia-offpeak archetype the time-angle favors.

### Inter-bar geometry / velocity (Angle 4)
- **L1 reclaim_low_monotone_k — MOSTLY PRESENT.** Lows: 1.91→2.89 (up), →1.48 (DOWN, breaks at bar 3), →1.98→2.79→2.15… Monotone run = 2 then a dip, then resumes. Not a perfect no-look-back staircase, but the floor recovers and never revisits the entry low.
- **L2 reclaim_jerk / L6 pivot_engulf_thrust — STRONG.** Bar 1 is front-loaded: c_atr leaps to 3.25 immediately off the low — a decisive single-bar thrust (the spring release). The biggest displacement is up-front.
- **L4 flush_then_snap — STRONG.** Up-velocity (3.25 ATR reached by bar 1) matches/exceeds the flush velocity — a symmetric V-turn, the initiative signature.
- **L8 reclaim_dip_depth — HOLDS.** The bar-3 dip (l_atr 1.48) is a shallow retest that holds above the entry low; the higher-low quality is intact, then the leg accelerates (bars 10–11: c_atr 3.9→6.16).

### Cross-TF momentum / regime-onset (Angle 5) — STRONGEST CLUSTER HERE
- **L5.1 HTF Phase-Lag Turn — PRESENT (textbook).** `htf4_native.trend = -1` (4H still bearish) while `htf1_native.trend = +1` AND `hd_trend = +1` (daily bullish, `hd_slope_atr = 3.95`, `hd_rsi = 61.5`). The fast frame (1H) and the Daily have already turned UP while 4H lags down — the classic 1H-leads-4H regime-onset with a still-bearish 4H giving the leg ROOM.
- **L5.2 1H Room-Above — PRESENT.** `htf1_native.in_demand = 0`, `htf1_native.dist_demand_atr = 1.01` (≥0.8 ✓), `h1_pos = 0.09` while the 15M is flushed deep. The 1H has lifted off its own floor while the 15M tags the bottom — the multi-TF spring.
- **L5.4 Compressed-Regime Onset — PRESENT.** atr_regime 0.94 (<1.0 ✓) + compression_pre 1.08 (≥0.85 ✓). The sharp 15M flush inside an otherwise compressed market = stop-run inside accumulation.
- **L5.3 HTF RSI Hook — PARTIAL.** 15M `rsi_min8 = 32.8` is washed (but not <25), `htf1_native.rsi = 49.6` (borderline, just under the 52 threshold), `hd_rsi = 61.5` strong. The Daily momentum never broke.
- **The REGIME-ONSET TRIAD (L5.1 × L5.2 × L5.4) FIRES CLEAN** — this is the dominant convergence for fund 16.

---

## (c) What is DISTINCTIVE about this bottom

1. **Supply and demand are stacked ON TOP of each other at the low.** `dist_demand_atr = 0.0` AND `dist_supply_atr = 0.07` — price is simultaneously on fresh virgin demand AND right under overhead supply, with `n_supply_overhead = 78` (heavily congested above). This is a bottom carved at a precise supply/demand inflection: it had to power straight UP through congestion. That it produced a +7 ATR monster despite 78 supply nodes overhead is the remarkable part — the cross-TF fuel (1H+Daily up, 4H room) overwhelmed the overhead.

2. **It is a "deep-sweep that instantly reclaimed," not the quiet-shallow archetype.** `sweep_depth_atr = 2.35` and `dealing_range_pos = -1.32` (range-break) make this a more violent, control-LIKE flush by the magnitude lenses — yet it reversed because the reclaim was 1-bar and the HTF regime had already turned. The discriminator was NOT a quiet low; it was the speed of the reclaim against an aligned 1H/Daily.

3. **NY-session, off-killzone monster.** Most strong bottoms in this corpus prefer Asia/off-peak. Fund 16 bottoms in NY at 12:15 but with killzone=0 — a less-typical timing footprint that the cross-TF and structural lenses carried instead of the time lens.

4. **Sell-bubble effort is present but not climactic** (`sell_bub_w = 34`, `sell_bub_L = 5`, `sell_decel = -8`) — selling was active and decelerating into the low (sell_decel negative = effort drying), with ZERO buy bubbles (`buy_bub_w/L = 0`). The turn was structural (sweep+reclaim+CHoCH+HTF), NOT bubble-confirmed and NOT NAS-confirmed (`nas_long_16=0`, `nas_long_after=0`). A pure price/structure monster.

5. **`flush_v_ratio = 0.36`** — a sharp-ish V, and `low_closepos = 0.87` (strong close at the low) with `lower_wick_ratio = 0.33` — the rejection is in the close-position, not a long tail. Absorption shown by where it closed, not by a spike-wick.

---

## (d) Macro / HTF context

- **Daily (hd):** BULLISH and strong — `hd_trend = +1`, `hd_pos = 0.54` (mid-range, room both ways), `hd_slope_atr = +3.95` (steep up), `hd_rsi = 61.5`, `hd_dist = +4.94` (well above daily demand). The higher-TF tide is UP. This is a pullback-into-strength on the Daily, not a counter-trend catch.
- **1H (h1 / htf1_native):** Has TURNED UP — native trend +1, but the E1 `h1_trend = -1` with `h1_rsi = 36.0`, `h1_slope_atr = -1.06`, `h1_pos = 0.09` shows the 1H was still washing locally at the print (the resample/native disagreement is the phase-lag itself: the slower native read flipped, the raw 1H momentum still negative-but-decelerating). Either way the 1H is at/near its turn, NOT confirming continuation down.
- **4H (h4 / htf4_native):** STILL BEARISH — `h4_trend` E1 = +1 but `htf4_native.trend = -1`, `h4_pos = 0.23` (low in range), `h4_rsi = 46.5`, `h4_slope_atr = +0.08` (flat). The 4H lag = overhead room for the leg (no 4H supply mitigated yet).
- **Synthesis:** A Daily-uptrend pullback that flushed the 15M deep into fresh virgin demand, swept stops, and reversed in 1 bar while the 1H had already turned — the 4H lagging-bearish provided the runway. The macro read is **buy-the-dip in a bullish Daily, timed by a 15M stop-run reclaim, fueled by 1H-leads-4H regime onset.** The risk note: heavy overhead supply (78 nodes) meant the leg had to grind through congestion — it did (+7 ATR), but this is the type of bottom where a tighter let-run / acceptance check above the first supply band would matter.

---

**Convergence verdict:** The dominant, cleanest-firing cluster is the **Angle-5 REGIME-ONSET TRIAD (L5.1 phase-lag + L5.2 1H room-above + L5.4 compressed regime)**, supported by Angle-4 front-loaded thrust (reclaim_jerk / flush_then_snap) and Angle-1 fresh-virgin-demand asymmetry. The order-flow "quiet absorption" angle is only PARTIAL here (deep sweep, range-break) — this monster reversed on **reclaim SPEED against an already-turned HTF**, not on quietness.
