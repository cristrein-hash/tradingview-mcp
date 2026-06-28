# Fund 31 — DEEP READING (XAU 15M MON+FORTE bottom)

**Identity:** block 2024-05-25 · date **2024-06-18 10:45 UTC** · tier **FORTE** · leg_atr 25.61 · power_score 4.8 · session **LONDON** · killzone **1**.
**Outcome geometry:** mfe12 8.74 ATR, mae12 0.06 ATR — i.e. price essentially **never traded below the entry-bar low** after the print (mae 0.06 ATR). A near-perfect no-look-back launch.

All facts below are as-of the entry bar (only bars ≤ entry count for the trigger). Raw bars confirmed from `primitives/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.primitives.json`, bottom index 1517.

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

The low is a **shallow liquidity sweep of the prior-50 low + close-back-inside**, but the *clean* trigger is a delayed displacement, not the low bar itself. Bar-by-bar (low = bar 0 = 10:45):

| bar | time | O/H/L/C | read |
|---|---|---|---|
| −1 | 10:30 | 2310.1→**2306.76**→2307.30 | down thrust, sets the pool |
| **0** | 10:45 | 2307.33→2309.12→**2306.55**→**2308.31** | **sweeps prior-50 low (2306.76) by ~0.2, closes back UP at 0.68 of bar** (low_closepos 0.68, small wick) — stop-run that fails to extend |
| 1 | 11:00 | low 2306.69 — higher low, holds | first_higher_low_bar = 1 |
| 2–6 | 11:15–12:15 | 2309→2313 grind, RSI 31→48 | quiet absorption / coil; lows climb, never revisit the low |
| **7** | **12:30 (NY open)** | 2312.67→**2322.38**→C2322.16, **V 14,275** | **displacement bar: +10 ATR-equivalent thrust, closes at high, reclaims EMA21 decisively, 15M CHoCH up** |

**Two valid entries, both causal:**
1. **Aggressive (sweep-reclaim):** enter on the close of bar 1 (11:00) once the bar-0 low held with a higher low and the prior-50 sweep was reclaimed. SL just below 2306.55 (sweep low). This captures the full leg (mae only 0.06 ATR → the structural stop is never threatened) but requires trusting a quiet grind.
2. **Confirmation (displacement/CHoCH):** enter on the close of the **NY-open displacement bar 7 (12:30)** — the 15M CHoCH-up + EMA21 reclaim on a 14k-volume thrust closing at the high. This is the highest-conviction trigger; you forfeit ~2.7 ATR of the move (entry ~2322 vs low 2306.55) but the leg still has ~6 ATR of mfe left and the signal is unambiguous.

**The defining trigger: sweep-of-prior-low + close-back-inside + held higher-low, then NY-open displacement/CHoCH confirms.** dossier `entry_mechanics`: swept_prior_low=1, first_higher_low_bar=1, reclaim_ema_bars=4, choch_15m_after=1, nas_long_after=2.

---

## (b) Lenses PRESENT / STRONG here

**Order-flow & volatility (Angle 0 / Angle 2) — the "quiet absorption, not climax" fingerprint fits cleanly:**
- **A0-L2 quiet_climax — STRONG.** vol_climax 1.01 (vs control med 1.54), sweep_depth_atr 1.71 (shallow), lower_wick_ratio 0.30 (small). All three conditions met → this is the textbook MONFORTE inverse-capitulation low.
- **A0-L7 / A1-L2 liquidity_grab_no_followthrough (shallow-sweep + fast reclaim) — STRONG.** Swept prior-50 low by only 0.2pt, reclaimed within the same/next bar. Marginal undercut of an *advertised* pool, instant reclaim.
- **A2-L1 atr_decel_into_low / A0-L8 vol_drain — PRESENT.** ATR drifts 2.20→2.27 into the low (regime atr 1.25, modest); volume into the low (2448, 3815, 3454, 3309) is *not* climactic — fuel draining, not a blow-off. downleg_eff 0.56 grindy; consec_down 0 (chop-down, two-sided).
- **A0-L10 rsi_holds_above_floor — MIXED.** rsi_low 24.1 / rsi_min8 24.1 is actually *deeper* than the MONFORTE median (~35) — this bottom IS oversold, a deviation from the quiet-RSI thesis. But rsi_head 1.15 (RSI lifted off its min before the low) shows momentum already turning.

**Liquidity / auction (Angle 1):**
- **A1-L6 discount-not-breakdown — STRONG.** dealing_range_pos −1.169 → price is at/just beyond the discount extreme of its dealing range (note: slightly beyond −1, so a marginal range-undercut, consistent with the sweep).
- **A1-L3 liquidity asymmetry — STRONG.** dist_demand_atr −0.14 (floor right here / just inside demand), dist_supply_atr 0.82 (ceiling only ~1 ATR up) — but htf4 clean_sky_atr 0.53 and demand_virgin=1 (untested floor). Floor is defended and fresh.
- **A1-L7 stop-run exhaustion (NAS) — PRESENT.** nas_short_16 = 0 (no fresh shorts into the low), nas_long_16 = 2 (long signals arming). sell_decel −14 + sell_bub_w 16 / sell_bub_L 1: heavy small-sell-bubble print BUT decelerating — supply effort fading.

**Inter-bar geometry (Angle 4) — strong on the post-low launch:**
- **A4-L1 reclaim_low_monotone — STRONG.** reaction l_atr climbs every bar 0.06→1.02→1.24→1.91→2.21 (run of 4-5) — buyers defend every new low, classic no-look-back staircase. mae 0.06 ATR proves it.
- **A4-L2 reclaim_jerk / A4-L7 downleg_velocity_spike — STRONG (delayed front-load).** The thrust isn't on bar 1; it explodes on bar 7 (c_atr jumps 2.31→6.44, +14k volume) — a single displacement bar carrying the reclaim. This is the spring release, just time-shifted to the NY open.
- **A4-L8 reclaim_dip_depth — STRONG (shallow retest).** No meaningful pullback toward the low; the higher-low at bar 1 held all the way.

**Demand / structure:**
- in_demand=1, demand_virgin=1, n_demand_near 37 — deep, fresh demand cluster. macro_bull=0/macro_bear=0 (neutral macro tag).

---

## (c) What is DISTINCTIVE about this bottom

1. **It is a KILLZONE / LONDON counter-example to the Asia-off-peak thesis (Angle 3).** killzone=1, session=LONDON. Angles 1 & 3 claimed strong bottoms cluster OFF-killzone in Asia (off-killzone lift 8.1×). Fund 31 directly contradicts that on the *timing* axis — yet it is a genuine FORTE. So the killzone-polarity rule is **not universal**; this fund's edge comes from the order-flow/auction lenses (quiet sweep + shallow + held HL + displacement), not from the clock. Flag for the validation pass: the Asia rule will fail to recall this case.
2. **The 1H/4H are still −1 (Angle 5 phase-lag thesis does NOT hold here).** h1_trend −1, h4_trend −1, htf1 in_demand=1, htf4 in_demand=1 — both HTFs are still bearish and *pinned inside* demand, the opposite of the "1H-leads-4H, 1H room-above" MONFORTE profile. The turn here is a pure 15M event into a stacked HTF demand floor, confirmed only after the displacement. The cross-TF-momentum angle would miss this one too.
3. **Deeper-than-typical RSI (24.1) but with rsi_head 1.15** — this bottom *is* oversold, unlike the quiet-RSI median. The exhaustion is real (London sell-off into 08:00–10:30 dumped RSI to 23–26), and the absorption shows as the bar-0 close-back-inside, not as a non-oversold print.
4. **Delayed, single-bar displacement at the NY open (12:30).** The reaction grinds quietly for 6 bars (the absorption window) and only releases on the NY-session open with a 14k-volume marubozu. The *trigger time* (NY open) and the *bottom time* (London) are different sessions — the bottom is built in London, the leg is launched at NY open. This NY-open ignition is the single cleanest entry.

---

## (d) Macro / HTF context

- **Both HTFs bearish and inside demand (htf4 trend −1 in_demand=1; htf1 trend −1 in_demand=1, rsi ~47).** This is a counter-trend reversal off a *defended, fresh* multi-TF demand floor (demand_virgin=1, dist_demand −0.14/−0.04/−0.19 on 15M/4H/1H), with thin clean sky above (clean_sky ~0.52–0.53 ATR on both HTFs). Floor below + air above = the structural precondition for a leg, but **without** HTF trend confirmation — so this is a "buy the discount into stacked HTF demand" bottom, riskier than a phase-lag turn.
- **Auction read:** a London down-auction grinds price into the bottom of its dealing range (pos −1.17), marginally sweeps the prior-50 sell-side pool, fails to follow through (close back inside, fading sell bubbles, no fresh shorts), then the NY open prints displacement that reclaims EMA21 and triggers a 15M CHoCH. The leg runs 8.7 ATR with essentially zero giveback.
- **Convergence verdict:** STRONG on the order-flow + auction + inter-bar-geometry axes (quiet sweep, shallow, held HL, defended fresh demand, decisive displacement); WEAK/ABSENT on the time-of-day and cross-TF-momentum axes. A multi-factorial reader keyed on *sweep-reclaim + absorption + displacement into fresh stacked demand* catches this; a reader gated on Asia-timing or 1H-leads-4H does not. Good stress-case for the no-OOS-within-corpus validation.
