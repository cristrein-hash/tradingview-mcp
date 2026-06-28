# Fund 30 — DEEP READING (XAU 15M MON+FORTE bottom)

**Identity:** block 2025-05-25 · date **2025-08-01 01:45 UTC** · tier **FORTE** · power **8.8** · leg **26.56 ATR** · session **ASIA** · killzone **0** (off-killzone).

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

**Verdict: enter on the CLOSE of reaction bar 1 — an immediate sweep+reclaim thrust off a defended demand floor. No need to wait for a CHoCH or higher-low; the structure is already done at bar 1.**

The reaction sequence is textbook front-loaded spring-release:

| bar | c_atr | l_atr | green | read |
|---|---|---|---|---|
| 1 | **2.46** | **0.42** | ✓ | explosive thrust: +2.46 ATR close off a 0.0-ATR low. The whole reclaim happens in ONE bar. |
| 2 | 2.08 | 1.66 | ✗ | shallow inside pullback — floor holds at 1.66 ATR (well above the low) |
| 3 | 2.01 | 1.42 | ✗ | minor dip, still ~1.4 ATR above the low — retest holds |
| 4 | 2.66 | 1.69 | ✓ | resumes |
| 5 | 3.70 | 2.64 | ✓ | peak push (mfe 3.98 area) |
| 6–12 | ~2.6–2.9 | climbing | mixed | consolidates higher, floor never returns to the low |

The causal trigger chain available **at the close of bar 1**:
- `swept_prior_low = 1` — price took out a prior fractal low (engineered stop-run).
- `sweep_depth_atr = 1.26` — SHALLOW sweep (vs control ~2.3). Liquidity grab without follow-through.
- `reclaim_ema_bars = 1` and `first_higher_low_bar = 1` — EMA21 reclaimed and a higher-low confirmed on the FIRST reaction bar.
- The bar itself: c_atr 2.46 / l_atr 0.42 = a **+2 ATR engulfing thrust bar** that opened at/near the low and closed in the upper portion (close-location strong, low_closepos at the low bar was 0.29 but the THRUST bar buys it all back).

**Mechanic name: SWEEP + INSTANT RECLAIM (no-look-back launch).** Entry = market/stop order on the close of the first green reclaim bar. SL = below the swept low (mae12 = 0.42 ATR → a tight ~0.5 ATR stop survives the entire run). This is NOT a CHoCH-confirmed entry (`choch_15m_after=0`) nor a NAS-triggered entry (`nas_long_after=0`) — it is a pure liquidity-sweep-reclaim, and waiting for CHoCH would have you enter ~1.5 ATR higher with no structural gain.

**MAE/MFE asymmetry:** mae12 = 0.42 ATR vs mfe12 = 3.98 ATR ⇒ ~9:1 favorable excursion. The leg never threatens the entry after bar 1. This is the "buyers defend every bar's low" signature.

---

## (b) LENSES PRESENT / STRONG here

### STRONGLY PRESENT — the core thesis of this bottom

**Angle 1 (Liquidity/Auction) — DOMINANT.**
- **Lens 1 QUIET RECLAIM (off-killzone × Asia):** `killzone=0`, `session=ASIA`, 01:45 UTC — squarely in the Asia-ramp window that is 2.3–4.7× enriched in strong bottoms. This is THE highest-lift discovery lens (off-killzone non-headline → 8.1×) and it is PRESENT and clean here.
- **Lens 6 DISCOUNT-NOT-BREAKDOWN:** `dealing_range_pos = −0.662` — deep in the discount third but NOT beyond −1.0 (no range break). Exactly the "buy the discount, don't fade the break" band. Strong.
- **Lens 7 LIQUIDITY GRAB no-followthrough:** shallow sweep (1.26) + instant reclaim (1 bar). Present and decisive.
- **Lens 3 asymmetry (partial):** `dist_demand_atr = 0.19` (floor right under price) but `n_supply_overhead = 462` and `dist_supply_atr = 0.06` (supply almost touching) — the overhead is THICK here. This is the one liquidity lens that is WEAK/contrary (see distinctive section).

**Angle 3 (Time/Session) — DOMINANT.**
- **L1 asia_offpeak_flush, L3 first-session-hour:** Asia, ~01:45 UTC, killzone 0. The single best-enriched temporal profile. Present.

**Angle 0 / Angle 2 (Order-flow / Volatility — QUIET ABSORPTION) — STRONGLY PRESENT.**
- **quiet_climax (A0 L2):** `vol_climax = 1.23` (modest, < 1.35), `sweep_depth = 1.26` (< 1.8), `lower_wick_ratio = 0.29` (small) — ALL THREE conditions met. This is the empirical MONFORTE fingerprint (calm absorption, not violent flush). Strong.
- **compressed_then_expand / coiled spring (A0 L6, A2 L3/L4):** `atr_regime = 1.06` (calm), `atr_compression_pre = 0.71` — moderate compression into a calm regime, then `range_exp = 1.86` on expansion. Coil-then-release present (though compression is a touch lighter than the 1.07 median).
- **downleg grindy:** `downleg_eff = 0.21` (very inefficient/grindy, well below control 0.39), `consec_down = 3`, `flush_v_ratio = 0.32` (sharp-ish V). Grind-down-then-snap. Strong.

**Angle 4 (Inter-bar Geometry) — STRONGLY PRESENT.**
- **L2 reclaim_jerk / front-loaded:** bar1 does almost the entire reclaim (+2.46 ATR in one bar). Maximally front-loaded. Strong.
- **L1 monotone climbing floor:** PARTIAL — l_atr 0.42→1.66 then a small dip to 1.42 at bar3 (monotone run breaks at bar3), but the dip is shallow and stays >1.4 ATR above the low.
- **L8 shallow retest:** the bars 2–3 pullback holds ~1.4 ATR above the low (deepest dip never approaches the bottom). `dip_frac` small. Strong — the higher-low quality is high.
- **L6 pivot_engulf_thrust:** bar1 is a +2 ATR engulfing thrust. Strong.

**Angle 5 (Cross-TF momentum) — MIXED, leaning ABSORPTION-onset.**
- **L5.5 cross-TF flush-spike isolation:** 15M `drop20_atr = 3.51` flush but it bottoms in a calm regime — the panic is a 15M/Asia spike, the kind the slower frame swallows. Plausible/present.
- **htf1_native.choch_rec = 1** — the 1H already registered a recent CHoCH. Constructive structural hand-off (A5 L5.9 flavor).
- **rsi divergence:** `rsi_bull_div = 1`, `rsi_min8 = 38.8`, `rsi_low = 41.0` — NOT deeply oversold (A0 L10 `rsi_holds_above_floor`). 1H rsi 42.9 / 4H rsi 37.3. Present (the non-oversold-bottom).

### ABSENT / CONTRARY (honest)
- `buy_bub_w/L = 0`, `sell_bub_w = 0`, `nas_long_16 = 0`, `nas_short_16 = 0`, `smc_bos = 0` — **NO bubble or NAS footprint at all.** The bubble/NAS confluence lenses (A0 L3/L9, A1 L7, A5 L5.7) are simply not triggered here. This bottom is read purely by price/liquidity/time, not by indicator events.
- **Angle 5 L5.1/L5.2 phase-lag turn: FAILS.** `htf1_native.trend = −1`, `htf4_native.trend = −1`, `hd_trend = −1` — ALL THREE HTF frames still bearish. The 1H has NOT led the turn here (h1_pos = −0.1, h1_slope_atr = −0.83). So the "1H-leads-4H regime onset" thesis is NOT how this bottom is built. It is a deep-discount flush into demand inside a still-bearish multi-TF tape — a counter-trend snap, not a confirmed regime turn.
- **htf*_native.in_demand = 1 on both 1H and 4H** — contrary to the A5 "room-above" finding (strong bottoms usually 1H above demand). Here the 15M, 1H and 4H are ALL pinned in/at demand.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is a PURE liquidity-sweep-reclaim in the Asia vacuum — zero indicator confluence.** No bubbles, no NAS, no SMC BOS. Every other lens family that relies on event footprints is dark. The signal lives entirely in (i) the off-killzone Asia timing, (ii) the shallow sweep + 1-bar reclaim, (iii) the quiet-absorption vol profile, (iv) the discount dealing-range position. This is the cleanest example of the "engineered quiet stop-run" archetype that Angle 1/3 identified as the real MONFORTE signature.

2. **Thrust over structure — the entry is a single bar, not a sequence.** bar1 does ~62% of the reclaim. Unlike funds where you wait for CHoCH/HL to build, here CHoCH never prints (`choch_15m_after=0`) and you would MISS the leg if you required it. The trigger is the engulfing reclaim bar itself.

3. **Heavy overhead supply (462 zones, dist_supply 0.06 ATR) — yet it ran 3.98 ATR.** This contradicts the "clean sky / thin overhead" thesis (A1 L3, A5 L5.6). The leg punched THROUGH near-touching supply. The distinctive lesson: this bottom's fuel was the deep discount + trapped shorts from the sweep, not a clear runway. Treat overhead-supply as NOT disqualifying when the sweep/reclaim + discount are this clean.

4. **Counter-trend on ALL HTF frames.** 1H/4H/Daily all bearish (hd_dist −13.63, hd_slope −4.92 — a steep daily downtrend). This is a deep-discount mean-reversion snap inside a macro down-tape, captured by the dealing-range discount band, NOT by HTF trend alignment. It is the inverse of the Angle-5 phase-lag archetype.

5. **Calm, grindy, not-oversold low.** downleg_eff 0.21 (grind), vol_climax 1.23 (modest), rsi_min8 38.8 (not washed). Absorption without theatrics — the inverted-capitulation fingerprint.

---

## (d) MACRO / HTF CONTEXT

- **Daily:** strong downtrend — `hd_trend=−1`, `hd_dist=−13.63 ATR` below daily anchor, `hd_slope_atr=−4.92` (steep), `hd_rsi=40.3`, `hd_pos=0.09` (bottom of daily range). The market is in macro discount.
- **4H:** bearish — `h4_trend=−1`, `h4_dist=−6.49`, `h4_slope=−2.09`, `h4_rsi=37.3`, in_demand=1. 4H flushed into its demand.
- **1H:** bearish but with a recent CHoCH — `h1_trend=−1`, `h1_rsi=43.1`, `h1_pos=−0.1`, `htf1_native.choch_rec=1`. The 1H is the first frame showing a crack (CHoCH printed), but slope is still negative.
- **15M:** flushed into a FRESH, VIRGIN demand zone — `in_demand=1`, `demand_fresh=1`, `demand_virgin=1`, `dist_demand_atr=0.19`, `n_demand_near=46`. Deep dealing-range discount (−0.662).

**Macro read:** a steep daily/4H downtrend reaches a deep-discount extreme; in the thin Asia window (01:45 UTC, off-killzone) price engineers a shallow stop-run below a prior low INTO a fresh virgin 15M demand that coincides with 4H demand, then instantly reclaims with a +2 ATR thrust on calm volume while the 1H has just put in a CHoCH. The leg is a counter-trend liquidity-snap from macro discount — entered at the close of the reclaim bar, stop under the swept low (~0.5 ATR), run targeted to the overhead supply shelf (which it cut through to +3.98 ATR).

---

**1-line summary:** FORTE bottom — entry trigger = **shallow sweep of prior low + instant 1-bar EMA reclaim thrust** (off-killzone Asia, deep-discount fresh virgin demand, quiet-absorption profile; no CHoCH/NAS/bubble confluence, counter-trend on all HTF frames).
