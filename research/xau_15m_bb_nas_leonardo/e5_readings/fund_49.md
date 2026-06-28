# Fund 49 — DEEP READING (XAU 15M MON+FORTE bottom)

**Identity:** block `2024-08-25` · date **2024-09-26 00:00 UTC** · tier **FORTE** · leg_atr **19.58** · power_score **9.2** · year 2024.
**Raw location:** `primitives/XAUUSD_15m_replay_2024-08-25_to_2024-11-25.primitives.json`, bottom bar idx **2119**, low **2655.33**, close 2655.57.

This is the launch low of the late-Sept-2024 gold rally (XAU ramped from ~2655 toward 2685+). It is a textbook **quiet-absorption Asia bottom**, NOT a capitulation flush — which is exactly the MON+FORTE fingerprint the angle catalog says to reward and the control-set climax model says to reject.

---

## (a) ENTRY MECHANIC — where/when I actually enter

**Sequence as it printed (all causal, bars closed):**
- **Bar 0 (00:00, the low, 2655.33):** down-bar on a **volume spike** (v=2035 vs prior ~800–900), closes near its low (close 2655.6, low 2655.3). Took out only a *local* pool — the trailing-40-bar min was 2649.55, so this low is **not the lowest-of-50** (a non-headline, engineered local sweep, not the chart low). `swept_prior_low=1`, `sweep_depth_atr=0.59` (very shallow). RSI 43 — **not oversold**.
- **Bar +1 (00:15):** immediate green reclaim, close 2657.8 at the TOP of its bar (c_atr 1.6, low only 0.12 ATR below entry — `mae12_atr=0.12`). This is the **first higher-low** (`first_higher_low_bar=1`) and the **absorption-reload** confirmation — the volume that printed at the low was absorbed by buyers one bar later.
- **Bar +2 (00:30, ~2659.0):** close reclaims **EMA21** (`reclaim_ema_bars=2`); a **15M BOS** prints at 00:55 and a bullish **CHoCH** at 01:00 (`choch_15m_after=1`).

**Where I enter:** on the **bar +1 reclaim / first-higher-low** (00:15, ~2657.8), with the trigger = *shallow sweep of the local low + instant strong-close reclaim (absorption)*, confirmed by the EMA21 reclaim two bars in and the 15M BOS→CHoCH right after. This is **sweep+reclaim → micro-HL → CHoCH** stacked, not a deep-flush V. SL sits just under the 2655.33 low (the leg ran with `mae12_atr=0.12` — it essentially never looked back; `mfe12_atr=4.05`). Entering at the EMA21 reclaim (bar +2, ~2659) is the more conservative confirmation if one waits for the BOS/CHoCH.

## (b) Lenses PRESENT / STRONG here

**STRONG (high-conviction, directly fired):**
- **Angle 1 / Lens 1 — QUIET RECLAIM (off-killzone × non-headline low):** PRESENT and textbook. `session=ASIA`, `killzone=0`, low at 00:00 UTC (the 4.7× Asia-ramp hour), and the low is **only a local undercut**, not the lowest-of-50 (prior-40 min was 2.6 pt lower). This is the single strongest lens (8.1× lift in calibration) and it fires cleanly.
- **Angle 3 / L1 asia_offpeak_flush + L3 first-session-hour + L9 htf_clock_alignment:** Asia off-peak window, bottom prints **exactly on the 00:00 boundary** (HTF clock alignment), early-session reaction. All three time lenses converge.
- **Angle 0 / L2 quiet_climax + L8 vol_drain + L7 liquidity_grab_no_followthrough:** `vol_climax=0.91` (modest), `sweep_depth_atr=0.59` (shallow), `lower_wick_ratio=0.13` (tiny wick) → quiet_climax = 3/3. Shallow grab + reclaim within 1 bar = L7. The leg is grindy (`downleg_eff=0.26`, `flush_v_ratio=0.4`).
- **Angle 1 / Lens 5 — DUAL-SIDED RAID:** both an **EQH (2661.54)** and an **EQL (2659.24)** printed in the bars just before the low — a complete liquidity-sweep cycle (both crowd pools raided) leaving a one-sided book.
- **Angle 4 / L1 monotone-floor + L5 clean-ramp R² + L8 shallow-retest:** the reaction floor climbs **monotonically** (l_atr 0.12→1.51→1.79→2.16) and close ramps cleanly (c_atr 1.6→2.39→2.42→3.48) — a no-look-back staircase. `mae12=0.12` confirms the retest never came back near the low.
- **Angle 0 / L10 + Angle 1 — RSI-holds-above-floor:** `rsi_low=43`, `rsi_min8=43` — the low is made WITHOUT being oversold (control bottoms are ~28–31). Momentum was already absorbed.
- **Demand backbone:** `in_demand=1`, `dist_demand_atr=0.01` (sitting ON fresh demand), `demand_fresh=1`, `demand_virgin=1`, `n_demand_near=13` — a defended, virgin floor.

**PRESENT but weaker / mixed:**
- **Angle 5 cross-TF momentum is the one place this fund DIVERGES from the canonical MON profile:** here the HTF is *already in full uptrend* — `h1_trend=+1, h4_trend=+1, hd_trend=+1`, with `h4_rsi=68, hd_rsi=76` (HTF overbought, not the "1H-leads-bearish-4H phase-lag" the angle-5 grounding describes). `htf4_native.in_demand=0`, `htf1_native.in_demand=0` (room above — matches L5.2), and native `clean_sky_atr` ~0.21 (4H) shows limited immediate overhead. So this is **not** a regime-onset/turn bottom; it is a **continuation pullback inside a strong multi-TF uptrend** that bought the discount.
- **Order-flow bubbles / NAS:** all zero (`buy_bub_*`, `sell_bub_*`, `nas_long_16`, `nas_short_16`, `smc_bos`=0 in E1). No bubble/NAS confluence — the edge here is structural+time+absorption, not order-flow signals. (Raw smc_events DID show BOS/CHoCH around the low even though E1 `smc_bos`=0.)
- **dealing_range_pos = −0.27** (discount band, not a range break) — Angle 1 Lens 6 PRESENT (buy-the-discount).

**ABSENT:** capitulation theatrics (no deep sweep, no big wick, no climax volume, not oversold), no rsi_bull_div, no bubble/NAS prints.

## (c) What is DISTINCTIVE about this bottom

1. **It is a SHALLOW continuation-pullback launch, not a reversal of a downtrend.** Only ~12 pt / ~1.5 ATR off the 09-25 14:30 swing high, dipping into fresh virgin demand at the 00:00 Asia open, then ramping. The 19.58-ATR `leg_atr` is the *continuation* leg of an already-bullish multi-TF trend (h1/h4/hd all +1), not a V-reversal.
2. **HTF is overbought (h4 RSI 68, hd RSI 76) yet it still ran 4 ATR with mae 0.12.** This contradicts the angle-5 "1H-leads-bearish-4H phase-lag" thesis — here ALL frames already aligned bullish. The lens that explains the strength is **clean-sky / room-above** (in_demand=0 on both HTF) + **discount entry into virgin demand within an uptrend**, not regime onset.
3. **Quietest possible bottom signature:** vol_climax 0.91, sweep 0.59 ATR, wick 0.13, RSI 43 — near the extreme of the "quiet absorption" fingerprint. The volume *spike* on the low bar (2035) was immediately absorbed (next bar closes at top) — effort spent, no downside result.
4. **Perfect no-look-back launch:** monotone climbing floor + clean close-ramp + mae 0.12 = institutional one-directional control.

## (d) Macro / HTF context

Late-September 2024, the heart of gold's post-Fed-cut breakout rally. **All native HTF trends UP** (1H/4H/Daily = +1), Daily slope +24.8 ATR, Daily pos 0.93 (price high in its range), HTF RSI hot (4H 68 / D 76). This is a **strong-trend continuation buy-the-dip**: a thin Asia-session pullback into fresh, virgin 4H/15M demand (`dist_demand_atr=0.01`, `demand_virgin=1`) with room overhead (HTF not pinned in demand, clean-sky present), engineered as a shallow local-liquidity sweep (EQL/EQH cycle just raided) that reclaimed within one bar. The edge here is **time (off-killzone Asia open) + discount-into-virgin-demand + absorption (vol-spike swallowed) + clean monotone reclaim**, all inside a powerful established uptrend — the opposite of a capitulation reversal.
