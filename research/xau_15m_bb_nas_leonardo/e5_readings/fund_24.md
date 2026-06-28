# Fund 24 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2025-08-25→11-25 | **Low bar:** 2025-09-24 19:15 UTC (t=1758741300) | **Tier:** FORTE | **leg_atr:** 30.34 | **power_score:** 5.1
**Outcome (truth, not used as feature):** mfe12 = 5.46 ATR, mae12 = 0.20 ATR → near-zero giveback, a clean no-look-back leg.

Raw verified (bars ±12 around low, ATR≈5.1 → ~$5/ATR):

```
 -2 18:45  l3722.6 c3724.3 rsi19.6
 -1 19:00  l3718.9 c3720.3 rsi17.1   atr5.30
 +0 19:15  o3720.3 h3721.6 l3717.4 c3718.3 rsi15.1 atr5.09   <- LOW
 +1 19:30  o3718.5 h3727.5 l3718.4 c3727.3 rsi14.5           <- RECLAIM/ENGULF (+1.8 ATR, low never breaks)
 +2 19:45  o3727.3 h3731.8 l3727.1 c3730.1 rsi33.4
 +3 20:00  l3729.9 c3732.3 rsi38.1
 +5 20:30  c3736.5 rsi41.1
 +8 22:15  h3745.2 c3744.6 rsi52.6
```

---

## (a) ENTRY MECHANIC — where/when I actually enter

**Trigger: bullish-engulf reclaim bar at +1 (19:30 UTC), entry on its close ≈ 3727.3.**

Causal sequence up to entry (only closed bars used):
1. **Bar +0 (low, 19:15)** prints the leg low at 3717.4, RSI 15.1 (`rsi_low`/`rsi_min8`=15.1) — a washed-out terminal bar of a 9-bar grind (`consec_down`=9), but a *small* bar (range ≈ 0.8 ATR), small lower wick (`lower_wick_ratio`=0.23), close mid-bar. No climax. This bar alone is not tradeable — it's quiet, not a rejection.
2. **Bar +1 (19:30) is the signal.** It opens 3718.5 (right at the low), then thrusts to close 3727.3 — a **+1.8 ATR green bar that fully engulfs bar +0's range and its low (3718.4) never undercuts the 3717.4 low**. This is `pivot_engulf_thrust` + `reclaim_jerk` front-load: most of the reclaim happens in this single bar (Angle 4 L2/L6). EMA21 is reclaimed here (`reclaim_ema_bars`=5 is the dossier's slower count, but the structural turn is the engulf).
3. **Confirmation that arms the entry:** `swept_prior_low`=1 — bar +0/+1 swept the prior local low and **instantly reclaimed it within 1 bar** (Angle 0 L7 liquidity_grab_no_followthrough, sweep_depth 2.94 ATR but reclaimed same bar). `first_higher_low_bar`=1 and a **monotone climbing floor** follows (lows 3717.4 → 3718.4 → 3727.1 → 3729.9, Angle 4 L1 `reclaim_low_monotone_k`=run of 4). `nas_long_after`=1 (a NAS LONG prints right after the low, confluence).

**Why enter at +1 close, not wait:** the leg is large (30 ATR); the engulf+reclaim+swept-and-reclaimed-prior-low is the highest-information bar. mae12=0.20 ATR confirms a +1-close entry essentially never goes underwater — this is the textbook spring release. CHoCH-up did NOT print as a labeled event (`choch_15m_after`=0), so I rely on the engulf/reclaim mechanic, not a CHoCH stamp. Stop sits just under 3717.4 (≈1.0 ATR risk); the leg paid 5.46 ATR mfe.

---

## (b) Lenses PRESENT/STRONG here

**STRONG (the spine of this bottom):**
- **Angle 0 L2 `quiet_climax` / Angle 2 thesis / Angle 5 L5.4** — this is the canonical *quiet absorption, not capitulation* bottom. ATR drains into the low (6.75 → 5.09 over the last ~12 bars; `atr_decel_into_low` strongly negative), `vol_climax`=1.0 (no volume blow-off — bar +0 vol 4884 is below the leg's bars), `atr_regime`=1.14 modest, `atr_compression_pre`=1.32 high (coiled). Angle 2 L1/L9 (`atr_decel_into_low`, `range_regime_shift`) fire — note post-low ATR keeps falling to 4.1 and volume collapses (4884 → 1949–2596 on the up-leg): the market *froze* after the low (Angle 2 L8 `flush_then_freeze`).
- **Angle 4 L1 `reclaim_low_monotone_k` + L5 `close_progression_R2` + L6/L9** — climbing-floor staircase, near-linear clean reclaim, hard slope-flip. This is the most distinctive, visually obvious feature: lows climb every bar, closes ramp 3718→3727→3730→3732→3736→3744 with high R². This separates it from chop decisively.
- **Angle 3 L1/L3/L5 (time/session)** — `session`=LATE, `killzone`=0 (off-killzone), low at 19:15 UTC (NY winding into the late/Asia handoff). Mid-week (Wednesday 2025-09-24). Exactly the off-killzone, non-headline, mid-week profile that Angle 3 says is enriched in MON+FORTE.
- **Angle 5 L5.2/L5.6 (cross-TF demand/room)** — 15M flushed INTO 4H demand region context: `in_demand`=1, `dist_demand_atr`=0.06 (sitting right on the 4H demand floor), `demand_virgin`=1 (fresh, untested floor → defended). 4H trend native +1 (`h4_trend`=1, `h4_slope_atr`=+3.01), Daily strongly up (`hd_trend`=1, `hd_slope`=+10.25, `hd_rsi`=82.6) → **a 15M deep-flush against an intact bullish 4H/Daily structure = multi-TF spring** (the leg is a pullback inside an HTF uptrend, not a reversal of a downtrend).

**PRESENT (confluence boosters):**
- `nas_long_16`=4 (cluster of NAS LONG into the low), `nas_short_16`=0, `nas_long_after`=1 — directional NAS hand-off (Angle 5 L5.7 partial).
- `sell_decel`=-4 and `sell_bub_w`=16 then *drying* — sell-bubble effort present in the leg but the low itself is quiet (Angle 0 L3 `sell_bubble_exhaustion_gap`).
- `downleg_eff`=0.78 — note this is the ONE field that runs against the "grindy" thesis (this leg was fairly efficient); but the bar-by-bar shows a slow, low-range grind (each bar ~0.8 ATR) into the low, not a violent flush. `flush_v_ratio`=0.12 (sharp V on the turn).
- `dealing_range_pos`=-0.368 (discount third, not range-break — Angle 1 L6 discount-not-breakdown).

**WEAK / CONTRA (honest flags):**
- `htf4_native.trend` field = **-1** while `features_E1.h4_trend` = **+1** — the two HTF reads disagree (native resample vs E1). The Daily (`hd`) is unambiguously up (rsi 82.6, slope +10.25), so net HTF context is bullish-pullback; flag the 4H-trend discrepancy.
- `h1_trend`=0/`htf1_native.trend`=1: the 1H is flat-to-just-turning (Angle 5 L5.1 phase-lag mild) — not the cleanest +1 1H read, but `h1_rsi`=28.9 washed with 1H above its demand (`htf1_native.dist_demand_atr`=0.96).
- `rsi_low`=15.1 is DEEPLY oversold — this CONTRADICTS Angle 0/L10 "MON is less oversold" prior. Here the 15M momentum genuinely capitulated; the strength came from the *instant reclaim + HTF bullish backdrop*, not from a non-oversold low. Honest: this bottom is oversold-and-snapped, not the quiet-non-oversold archetype.

---

## (c) What is DISTINCTIVE about this bottom

1. **It is a PULLBACK in a strong HTF uptrend, not a reversal.** Daily RSI 82.6, Daily slope +10.25 ATR, `hd_pos`=0.79, `hd_dist`=+17 ATR. The 15M simply flushed into a fresh, virgin 4H demand (`dist_demand_atr`=0.06, `demand_virgin`=1) and was bought instantly. The "monster leg" is the resumption of an existing trend, which is why mae=0.20 — there was never any doubt.
2. **The reclaim is the cleanest single bar of the whole sample-feel:** a +1.8 ATR engulf at +1 that never lets the low be retested, followed by a volume-and-vol *freeze* on the way up (the opposite of a fight). Climbing-floor staircase for 4+ bars.
3. **Off-killzone, LATE-session, mid-week timing** — the textbook Angle 3 profile, with the low forming in the NY→late handoff (19:15 UTC) where thin liquidity let the grind overshoot just enough to grab the prior low, then snap.
4. **Quiet at the low despite deep RSI:** no volume climax (vol_climax=1.0), small bar, small wick, ATR draining — the capitulation theatrics are absent even though RSI hit 15. Absorption signature without the loud flush.

## (d) MACRO / HTF context

Daily: strong uptrend, overbought (rsi 82.6) but slope steeply positive — a momentum bull market in gold (Sep 2025). 4H: bullish slope (+3.01), price pulled back to ~-4 ATR from its mean into a fresh 4H demand. 1H: washed (rsi 28.9) and sitting just above its own demand (0.96 ATR), flat-to-turning. The 15M flush is the deepest leg of a normal pullback against an intact, powerful HTF bull. There is clean sky / room overhead on the HTF (Daily far from any ceiling). This is a **buy-the-dip in a runaway uptrend**, defended at virgin 4H demand, triggered by an instant engulf reclaim off a quiet, oversold 15M low in thin late-session liquidity.

---
**Convergence summary:** quiet-absorption vol profile + climbing-floor/engulf reclaim + off-killzone LATE/mid-week timing + flush into virgin 4H demand inside a powerful Daily uptrend. The entry is the **+1 bullish-engulf reclaim bar (19:30, ~3727)** that swept-and-reclaimed the prior low in one bar and never looked back.
