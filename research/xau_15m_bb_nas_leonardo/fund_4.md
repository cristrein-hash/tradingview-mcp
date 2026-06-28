# Fund 4 — DEEP READING — XAU 15M MONSTRO bottom 2025-04-08 23:30 UTC

**Tier:** MONSTRO · **leg_atr:** 51.06 · **power_score:** 11.6 · **block:** 2025-02-25 file (2025-04-08)
**Outcome:** mfe12 7.61 ATR, mae12 0.05 ATR (essentially NO heat after the print — a near-perfect no-look-back launch)

Raw reconcile (primitives, bar idx 2859):
- Bottom bar 23:30: o2981.0 h2981.3 **l2970.1** c2973.88 v3175 rsi42.3 atr5.40 ema21 2983.8
- The bottom is a **single sharp flush bar** that drove ~11pts (~2 ATR) below a tight coiled base, then closed back in the **upper third** of its own range (low_closepos 0.34 → closed 34% up off the low). It swept the local low pool (the 2977/2980 base built 20:15→23:15) and reclaimed it intrabar.

---

## (a) ENTRY MECHANIC — where/when I actually enter

This is a **sweep + reclaim → base-hold → displacement** sequence, NOT a buy-the-flush.

1. **The flush bar (23:30, the low):** price coils tight from 20:00→23:15 (range ~2977–2987, ATR draining 7.17→5.0), then a single bar stabs to 2970.1 (sweeps the local equal-low base) and snaps back to close 2973.9 (upper third). This is the *signal* but not yet the entry — close is only at ema−1.8ATR, no structure confirmed.
2. **Higher-low base (bars 1–5, 23:45→01:00):** the reaction holds entirely ABOVE 2970 — bar lows 2970.4 / 2974.9 / 2975.4 / 2976.8 / 2974.7 / 2972.1. Price never revisits the flush low (`low_revisit=0`, mae12=0.05 ATR). A constructive higher-low base forms ~2972–2976.
3. **ENTRY = the EMA21-reclaim displacement bar (bar 7, 01:15 UTC):** a +12pt green marubozu (o2978.4 → c2990.2) that closes back **above EMA21** (2983.2) and breaks the 15M structure up (`choch_15m_after=1`, `reclaim_ema_bars=3`). This is the bar where initiative is confirmed. Trigger type = **CHoCH / EMA-reclaim after a sweep+reclaim base** (not a naked reclaim, not a deep retest).
   - Conservative alt: enter on bar-1 reclaim (23:45 close 2978.4, above the swept level) with stop under 2970 — viable here because mae12 is essentially zero, but the *clean, repeatable* trigger is the 01:15 displacement.
4. **Stop:** below the flush low 2970.1 (≈ 0.4–0.8 ATR below entry-base). Run-room is huge: leg = +51 ATR, mfe 7.61 ATR in 12 bars; price runs 2990→3008 within 3 bars of the trigger.

**One-line entry:** *Asia-session shallow sweep of a coiled base → strong-close rejection → 5-bar higher-low hold above the low → enter on the EMA21-reclaim/CHoCH displacement bar (01:15).* 

---

## (b) Lenses PRESENT / STRONG here

### Old features_E1 / HTF — strongly present
- **Off-killzone / LATE session** (`session=LATE`, `killzone=0`) — the core MON profile (Angle 1 L1, Angle 3). Print is 23:30 UTC = Asia/late, the off-killzone window where monsters bottom.
- **Compressed-coil regime** — `atr_regime=0.76` (very calm, below even the MON median 0.94) + `atr_compression_pre=1.29` (high). Textbook drained-and-coiled (Angle 2, Angle 5 L5.4). Raw confirms: ATR fell 7.17→5.0 into the low.
- **Discount, not broken** — `dealing_range_pos=-0.822` (deep discount third but ≥ -1, no range break → reversal band, Angle 1 L6).
- **In 4H demand, flush lands on the floor** — `in_demand=1`, `dist_demand_atr=0.03`, `htf4_native.in_demand=1`, `htf4 dist_demand=0.02`. The 15M flush lands exactly on 4H demand = nested stacked floor (Angle 5 L5.6). **`demand_virgin=1`** (fresh floor) and **`htf4_native.clean_sky_atr=0.46`** (some near supply but thin).
- **Shallow sweep + reclaim** — `sweep_depth_atr=1.29` (shallow, below MON median), `swept_prior_low=1`, reclaimed intrabar (Angle 0 L7, Angle 1 L2-style local-pool raid).
- **RSI holds above floor + bull div** — `rsi_min8=38.7` (NOT deeply oversold — above MON median 35), `rsi_bull_div=1`, `rsi_low=42.3`. Momentum absorbed (Angle 0 L10).
- **Modest volume / low climax** — `vol_climax=0.68` (very modest), no big sell-bubble spray. Quiet absorption, not capitulation (Angle 0 L2, Angle 2).

### NEW angles — STRONG
- **Angle 4 L1 `reclaim_low_monotone_k` / L5 `close_progression_R2` / L8 `reclaim_dip_depth` — VERY STRONG.** The reaction floor climbs and the low is never revisited (mae12=0.05). reaction_seq l_atr: 0.05→0.89→0.98→1.25 then accelerates 1.34→3.37→5.45→6.31. c_atr ramps 1.54→1.46→2.63→2.66 then 3.71→5.56→7.13 — a clean staircase after the base. Shallow-retest holds perfectly (the first dip never goes near the low).
- **Angle 4 L2 `reclaim_jerk` / L6 `pivot_engulf_thrust` / L9 `velocity_regime_flip` — STRONG.** The 01:15 bar is a front-loaded engulfing thrust (+12pt marubozu) that hard-flips the slope from down to a steep up-ramp.
- **Angle 2 L1 `atr_decel_into_low` / Lens 7 `gap_to_vol_floor` — STRONG.** ATR is already contracting into the low (7.17→5.0) and sits near its quiet floor — energy stored, not spent.
- **Angle 1 L6 discount-band + L3 liquidity-asymmetry — PRESENT.** Floor (demand) is right under price (dist 0.03 ATR) while in discount; though `n_supply_overhead=162` is high (overhead congestion is the one weak note — see distinctive).
- **Angle 0 L4 `absorption_reload` — MODERATE.** Bottom bar v=3175 is above the coil baseline (~1600–2600) with a strong-close (upper third) → absorptive print. Tick-vol caveat applies; treat as confluence not gate.

### Lenses ABSENT / against
- **Angle 5 L5.1/L5.2/L5.3 (1H-leads-4H phase-lag) — ABSENT.** `htf1_native.trend=-1` (1H still bearish, NOT the +1 MON median), `h1_trend=-1`, `htf1_native.in_demand=0` is present but `h1_pos=-0.02` (not the +0.19 lift-off). The 1H has NOT turned here — this monster does NOT fit the cross-TF phase-lag profile. **But `hd_trend=+1` (Daily is bullish, hd_slope +1.34)** — the higher-frame bullish backdrop is the macro support instead.
- **Buy bubbles / NAS — ABSENT.** `buy_bub_w=0`, `nas_long_16=0`, `nas_short_16=0`, `smc_bos=0`, `choch_rec=0`. No order-flow/structure event confirmation at the print — this fund is carried by **price geometry + location + session**, not by NAS/bubble triggers. `sell_bub_w=3`, `sell_decel=3` (sell effort present then decelerating — Angle 0 L3 mild).
- **macro_bear=1** (regime tag bearish) — the leg fires AGAINST the labeled bear regime, consistent with "monster reversal off exhausted multi-session decline."

---

## (c) What is DISTINCTIVE about this bottom

1. **Near-zero adverse excursion (mae12 0.05 ATR).** This is one of the cleanest "no-look-back" launches in the set — the flush low is never retested. Whoever bought the higher-low base was never underwater. The bottom is *precise*.
2. **Carried by GEOMETRY + LOCATION, not by triggers.** No NAS, no SMC BOS, no buy bubble, and the 1H frame has NOT turned. What makes it work is the convergence of: off-killzone Asia timing + drained/coiled ATR + shallow sweep of a local pool landing exactly on a *virgin* 4H demand + a monotone climbing-floor reclaim. This argues the strongest signal family here is the **price-shape/location lenses (Angle 2/4) + session (Angle 3)**, NOT the event lenses (Angle 5 cross-TF / NAS).
3. **The flush is a single shallow stab, not a cascade.** sweep_depth 1.29, vol_climax 0.68, RSI only 38.7 — quiet absorption fingerprint (Angle 0/2 thesis confirmed) despite a big 51-ATR leg following.
4. **Two-stage launch:** a 5-bar quiet higher-low base (23:45→01:00) THEN a sudden displacement (01:15). The patient base is what gives a low-risk entry; the displacement is the confirmable trigger. Distinctive vs a pure V-snap.
5. **Overhead congestion present** (`n_supply_overhead=162`, `dist_supply_atr=1.27`) — the one lens AGAINST a clean runway, yet the leg ran +51 ATR anyway. Suggests overhead-supply count is not a hard gate when the launch displacement is decisive.

---

## (d) Macro / HTF context

- **Daily = BULLISH** (`hd_trend=+1`, hd_slope +1.34, hd_rsi 42.3) — the dominant-frame backdrop is an uptrend; this 15M flush is a pullback INTO a bullish daily, landing on fresh demand. This is the real macro support, in lieu of a 1H turn.
- **4H = bearish but flushed into demand** (`h4_trend=-1`, h4_rsi 37, `in_demand=1`, dist 0.02, clean_sky 0.46) — the 4H is at its floor and oversold; room for a mean-reversion bounce within the bullish daily.
- **1H = still bearish, washed** (`h1_trend=-1`, h1_rsi 38.8, h1_eff 0.66) — the 1H has NOT yet turned at entry; the trade is taken on the 15M displacement ahead of the 1H confirming. (This is the deviation from the Angle-5 "1H-leads-4H" monster median.)
- **Regime:** labeled `macro_bear=1` — a counter-regime reversal off an exhausted, grinding (`downleg_eff 0.18`) multi-session decline that capitulated quietly in the Asia window, on a compressed-vol coil, against a bullish daily.
