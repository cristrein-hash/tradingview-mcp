# Fund 8 — DEEP READING (MONSTRO bottom, XAU 15M)

**Block** 2025-02-25 file · **Low bar** 2025-03-11 01:00 UTC (t=1741654800) · **Tier MONSTRO** · power 10.4 · leg_atr 42.94 · MFE12 7.09 ATR / MAE12 1.92 ATR · session **ASIA, 01:00 UTC, killzone=0**

Raw confirmed from primitives (bars relative to low):
```
-2 o2887.4 h2888.2 l2885.1 c2885.7  v2326  rsi46.5
-1 o2885.6 h2888.2 l2884.8 c2887.2  v2573  rsi42.8
 0 o2887.4 h2888.7 l2879.8 c2885.5  v4613  rsi43.3  <- LOW: sweep -7pt, close 0.64, vol ~2x, long lower wick
+1 o2885.5 h2890.3 l2885.4 c2889.3  v4098  rsi43.3  <- EMA21 reclaim (ema 2887.4), first HL, retakes prior bodies
+2 o2889.3 h2890.3 l2886.9 c2890.2  v3491  rsi52.1  <- RSI>50, micro-CHoCH over 2888.6
+3..+5 lows 2889.2 -> 2889.8 -> 2893.1, c climbs to 2898  <- no-look-back staircase
```

## (a) ENTRY MECHANIC — where I would actually enter

This is a **shallow-sweep + instant-reclaim** bottom, NOT a deep capitulation flush. The sequence:

1. **Bar 0 (the low, 01:00)** is a single liquidity-grab bar: it sweeps ~7pt below the prior consolidation lows (~2884.5) down to 2879.8 on a ~2× volume spike (4613 vs ~2.3–2.6k), then **closes back at 2885.5 (close-position 0.64) with a long lower wick** = a stop-run absorbed within the bar. This is an *absorption_reload* (volume spike + strong close), not a continuation bar. sweep_depth 0.9 ATR (very shallow), flush_v_ratio 0.24 (sharp V).
2. **Bar +1 (01:15) is the entry trigger.** It closes 2889.3 — **back above EMA21 (2887.4) and above the entire prior consolidation**, prints the **first higher-low** (2885.4 > 2879.8), and erases bar 0's body. `reclaim_ema_bars=1`, `first_higher_low_bar=1`, `swept_prior_low=1` all line up here. **I enter at the close of bar +1 (~2889.3).** SL below the swept low 2879.8 (≈ -1.0 ATR, the engineered stop-run extreme that should not be revisited).
3. **Confirmation add at bar +2 (01:30):** RSI crosses 50 (52.1) and price breaks the short-term swing high (~2888.6) = the **15M bullish CHoCH** (`choch_15m_after=1`). A risk-averse reader who wants structure can enter the full size here instead.

Trigger label: **shallow sweep + same-bar reclaim → EMA21 reclaim + first higher-low on bar +1 → 15M CHoCH on bar +2.** No NAS-LONG fired (`nas_long_after=0`); the trigger is pure sweep-reclaim + structure, not a signal print.

## (b) Lenses PRESENT / STRONG here

**Order-flow / microstructure (Angle 0) — strongly present (this is the textbook quiet-absorption bottom):**
- L2 `quiet_climax` = **3/3** (vol_climax 1.16 < 1.35, sweep_depth 0.9 < 1.8, lower_wick fine) — pure inverse-capitulation fingerprint.
- L4 `absorption_reload` PRESENT — bar 0 volume spike (~2×) with close-position 0.64 in the upper half = buyers absorbed the flush.
- L7 `liquidity_grab_no_followthrough` STRONG — swept prior low 0.9 ATR and reclaimed the SAME bar / next bar.
- L1 `effort_vs_result_failure` PRESENT — `downleg_eff 0.03` is extraordinarily grindy (effort spent, almost no net directional result) = absorption, not impulse.
- L3 `sell_bubble_exhaustion_gap` PRESENT — `sell_bub_w=12` with `sell_decel=12` (every sell bubble decelerating = supply footprint fading into the low). No large sell bubbles (sell_bub_L=0).
- L10 `rsi_holds_above_floor` PRESENT — `rsi_min8=36`, `rsi_low=43.3`, NOT deeply oversold despite the new low, and `rsi_bull_div=1`.

**Volatility-structure (Angle 2) — strongly present:**
- `atr_regime=0.55` (very calm — even lower than the MON median 0.94) + `atr_compression_pre=1.41` (high) → Lens 1/3/4/7 coiled-spring state. The low forms in a **drained, coiled, low-vol pocket** then springs (range_exp 2.9 on the turn). `consec_down=1` (no long down-run) confirms calm.

**Time / session (Angle 3) — flagship match:**
- L1/L3 `asia_offpeak_flush` + first-Asia-hour: **01:00 UTC, ASIA, killzone=0** — sits exactly in the 4.7×-enriched 01:00 Asia-ramp / off-killzone window. This is one of the strongest single discriminators in the corpus and this fund nails it.

**Liquidity / auction (Angle 1):**
- Lens 1 `quiet reclaim` (off-killzone) PRESENT. Lens 6 `discount-not-breakdown` PRESENT (`dealing_range_pos=-0.431`, discount third, NOT range-broken). Lens 3/asymmetry partial: floor is right here (`dist_demand -0.04`, in fresh **virgin** demand) but overhead is HEAVY (`n_supply_overhead=90`) → the path up is NOT clean on the 15M — this is the one caution flag.

**Inter-bar geometry (Angle 4) — strongly present (the reaction is a clean staircase):**
- L1 `reclaim_low_monotone_k` = strong: lows climb 1.92→2.44→3.23→3.41→4.56 ATR (run≥5, no-look-back).
- L5 `close_progression_R2`: c_atr 3.26→3.55→3.71→4.84→6.24 = near-monotone clean ramp.
- L2 `reclaim_jerk` front-loaded: the very first reaction bar already reaches c_atr 3.26 (huge bar-1 thrust off the low), then keeps building.
- L6/L9 `pivot_engulf_thrust` / `hard_flip`: bar +1 engulfs bar 0 and the slope flips hard from down to up.

## (c) What is DISTINCTIVE about this bottom

- **Extreme grind, not flush.** `downleg_eff=0.03` is near-zero — this is the grindiest descent in the set; sellers expended effort and got almost nothing, the canonical absorption tell. The leg `consec_down=1` and `flush_v_ratio=0.24` confirm it was a sharp single-bar V on a calm base, not a multi-bar cascade.
- **Calmest regime in the corpus.** `atr_regime=0.55` is well below even the MON median (0.94) — a deeply compressed, coiled market. The 42.94-ATR leg is launched from *stored* energy.
- **Perfect temporal stamp.** 01:00 UTC Asia ramp, off-killzone — the single highest-conviction time lens.
- **One real caution:** overhead is congested (`n_supply_overhead=90`, dist_supply only +0.12 ATR — supply right above), so 15M run-room is NOT clean. The leg ran anyway (MFE 7 ATR) because the HTF context provided the room (see below). This is the rare case where the *quiet-absorption + coiled-regime + Asia-stamp + clean staircase* convergence overrides the dirty-overhead reading.

## (d) Macro / HTF context

- **Both 4H and 1H are still bearish** at the low (`h4_trend=-1`, `h1_trend=-1`; h4_rsi 36.6, h1_rsi 37.9). This fund does NOT exhibit Angle 5's flagship "1H-already-turned-bullish" phase-lag — that lens is **ABSENT** here. So this bottom is caught by the *microstructure + temporal + volatility* convergence, not by HTF momentum confirmation.
- **Both frames are inside their own demand** (`htf4_native.in_demand=1`, `htf1_native.in_demand=1`; 15M `in_demand=1`, `dist_demand -0.04`). The flush lands on a **stacked, nested 4H+1H+15M demand floor** that is **fresh and virgin** (`demand_fresh=1`, `demand_virgin=1`) — an untested institutional floor. The 1H sits a clear ATR off its own demand (`htf1_native.dist_demand_atr=0.54`), giving the bounce a defended origin.
- **Clean sky on the HTF** (`htf4_native.clean_sky_atr=0.63`, `htf1_native.clean_sky_atr=0.64`) — the overhead congestion that the 15M sees (n_supply 90) does NOT exist on the 4H/1D, which is why the leg had room to run despite the dirty 15M ceiling. macro_bull/macro_bear both 0 (neutral macro tag).

**Net read:** a fresh-virgin nested-demand floor + extreme-grind absorption + calmest-regime coil + the 01:00 Asia off-killzone stamp + an instant shallow-sweep reclaim that climbs as a clean staircase. HTF momentum is NOT yet confirming (still 1H/4H bearish) — this fund is a pure microstructure-exhaustion + temporal + coiled-volatility convergence, entered on the bar-+1 EMA/HL reclaim with a confirmation add on the bar-+2 CHoCH.
