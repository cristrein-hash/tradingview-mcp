# Fund 23 — DEEP READING (XAU 15M MON+FORTE bottom)

**Identity:** block `2024-11-25` (primitives file `..._2024-11-25_to_2025-02-25`), bottom bar **2025-02-09 23:00 UTC (Sunday re-open)**, raw idx 4827, price low **2855.70 / close 2863.22**. Tier **FORTE**, leg_atr 30.49, power_score 15.3. Session=LATE, killzone=0.

---

## (a) THE ENTRY MECHANIC — *where/when I would actually enter*

**Verdict: enter at the CLOSE of the bottom bar itself (bar +0, 23:00 UTC). This is a single-bar SWEEP+RECLAIM reversal candle — no waiting needed.** `reclaim_ema_bars`=0, `first_higher_low_bar`=1, `swept_prior_low`=1.

The raw bars make the mechanic unambiguous:
- Friday 02-07 closed its evening session with lows pinned ~2859.5–2860.5 (a tight resting-liquidity shelf) and EMA21 ≈ 2862.6.
- The **Sunday-open bar gapped DOWN**: open 2855.81, low **2855.70** — slicing straight through the entire Friday-evening low shelf (a clean sell-side liquidity raid of the weekend pool), then **closed at 2863.22 = top 9% of its own range** (`low_closepos`=0.91, `lower_wick_ratio`=0.01 i.e. the bar IS the wick — a giant rejection from below). On the SAME bar it reclaimed back above EMA21 (2862.63).
- So the entry trigger is **sweep of the Friday/weekend low + instant intra-bar reclaim above EMA21**, confirmed at the 23:00 close. Stop logically sits just under the swept low (2855.70 / flush-low convention).

The reaction then validates the entry as a **no-look-back monotone staircase** (`reaction_seq.l_atr`: 2.42 → 3.84 → 3.96 → 3.42 → 3.60 → 4.00 → … never returns to the entry zone; lows climb after the dip at bar 4). MFE12 = +7.34 ATR (hit on bar +8, the 01:00 UTC Asia-ramp volume burst v=4566), MAE12 = 2.42 ATR (i.e. price never traded back to the low after entry). Entry at the bottom-bar close captures essentially the whole leg.

**Distinctive entry caveat:** the low is **NOT the lowest-of-50** (2855.70 > 2852.17 set earlier in the leg). This is a *local* pool sweep (Friday shelf), not the obvious chart low — exactly the "quiet, non-headline" reclaim profile (Angle 1 Lens 1).

## (b) Lenses PRESENT / STRONG here

**STRONG — the quiet-absorption / drained-vol cluster (Angles 0 & 2):**
- `quiet_climax` (A0-L2): vol_climax 0.62 (tiny), sweep_depth 1.27 (shallow), lower_wick 0.01 — all three conditions met. Textbook non-capitulation low.
- Drained vol regime: atr@low 2.85 vs median-50 3.95 → ATR ~28% below baseline; `atr_regime`=0.75, `atr_compression_pre`=1.63 (high). ATR fell into the low across bars -10→0 (4.36→2.52) = `atr_decel_into_low` / `coiled_spring_squeeze` / `gap_to_vol_floor` all fire (A2-L1/L3/L7). This is a coiled, drained pocket, not a panic flush.
- `effort_vs_result_failure` / grindy leg: `downleg_eff`=0.16 (very low), `flush_v_ratio`=0.32 — a grinding, inefficient descent, not a clean cascade (A0-L1, A2-L5).
- `rsi_holds_above_floor` (A0-L10): rsi_low/rsi_min8 = 36.2 — NOT deeply oversold despite the new local low. Strong-bottom signature (control sags to ~28).

**STRONG — liquidity / auction (Angle 1):**
- Lens 1 QUIET RECLAIM: killzone=0 AND non-lowest-of-50 — the single best raw probe (S 39% vs C 5%). Present.
- Lens 6 DISCOUNT-NOT-BREAKDOWN: `dealing_range_pos`=−0.905 — deep discount band but NOT broken beyond −1.0. Present.
- Lens 3 LIQUIDITY ASYMMETRY: `dist_demand_atr`=0.13 (floor right under), in_demand=1, demand_virgin=1; `dist_supply_atr`=−0.25 (just under a supply lip) — mixed, but the floor is defended and fresh.
- Lens 7 STOP-RUN EXHAUSTION: shallow sweep (1.27) + instant reclaim = `liquidity_grab_no_followthrough` (A0-L7). Present.

**STRONG — inter-bar geometry (Angle 4):**
- `reclaim_low_monotone_k` (L1): the climbing-floor staircase is the dominant signature here.
- `pivot_engulf_thrust` / `flush_then_snap` (L4/L6): the bottom bar engulfs and snaps — bar +1 immediately extends to 2869.92 (+1.58 ATR thrust). Front-loaded reclaim (`reclaim_jerk`, L2).
- `reclaim_dip_depth` (L8): the only pullback (bars 3-4 to l_atr 3.42) is shallow and holds far above the low → higher-low confirmed.

**PRESENT but WEAKER / nuanced (cross-TF, Angle 5):**
- HTF stack is BULLISH-dominant, not the classic "1H-leads-4H phase-lag." Here BOTH frames are already up: `htf4_native.trend`=+1 (rsi 57.2), `htf1_native.trend`=+1 (rsi 73.6), `h4_trend`=+1 (slope +2.53), `hd_trend`=+1 (1D rsi **75.2**, slope +15.4, pos 0.88). `macro_bull`=1.
- L5.2 1H Room-Above: htf1 in_demand=0, dist_demand 2.86 — 1H well above its floor with room. Present.
- This is **a pullback-in-a-strong-uptrend bottom**, not a regime-onset turn. The 4H/1D were never bearish; the 15M flushed into 4H demand (htf4 dist_demand 1.04, near) within an intact HTF bull.

**ABSENT / NOT firing (honest):**
- All bubble lenses zero: buy_bub_w/L=0, sell_bub_w/L=0, sell_decel=0 — no bubble footprint at all (so A0-L3/L9 do not apply).
- NAS: nas_long_16=0, nas_short_16=0, choch_15m_after=0, nas_long_after=0, smc_bos=0 — no NAS/SMC trigger confluence. (A5-L7/L9 absent.)
- rsi_bull_div=0, vol_climax low → no momentum-divergence or volume-climax fingerprint.
- consec_down=0 at the low (the low bar itself is green) — there is no multi-bar capitulation sequence; the "leg" is mostly a single weekend gap-down rejection.

## (c) What is DISTINCTIVE about this bottom

1. **It is a WEEKEND-GAP sweep-reclaim, printed on the Sunday 23:00 re-open.** The entire reversal is one candle that gapped under the Friday liquidity shelf and closed back above EMA21. This is the rarest entry-mechanic flavour in the set — the "leg down" is essentially the weekend gap, not an intraday cascade (`consec_down`=0, `downleg_eff`=0.16).
2. **Tension with the week-phase lens (Angle 3 L5):** strong bottoms are statistically *depleted* at week-open (Sun/Mon 13% vs 28%). This fund is a Sunday-open low — a counter-example to that lens. But it is squarely off-killzone (LATE) and Asia-ramp adjacent (MFE realized at 01:00 UTC), so it still honours the off-killzone polarity (A1/A3 headline). Treat the week-open flag as a *false-negative risk*, not a disqualifier.
3. **Quiet-everything fingerprint at an extreme:** vol_climax 0.62 and lower_wick 0.01 are about as non-climactic as a true bottom gets — the leg reverses on the absence of theatrics, exactly the inverted-capitulation thesis. Yet it still produced a FORTE +7.34 ATR leg. Pure HTF-trend fuel + a thin-liquidity weekend sweep, not capitulation.
4. **Floor is fresh & defended:** demand_virgin=1, in_demand=1, dist_demand 0.13 — the flush landed on an untested 4H/15M demand with the trend behind it.

## (d) Macro / HTF context

This bottom forms inside a **mature, strong gold uptrend**, not at a regime turn:
- 1D: trend +1, RSI **75.2** (overbought-strong, not a turn signal), pos 0.88 in range, slope +15.4 ATR — powerful daily bull, price high in its range.
- 4H: trend +1, RSI 56-57, slope +2.53 ATR, but `h4_eff`=0.07 (4H grinding, low efficiency) and 15M flushed into nearby 4H demand (dist 1.04) → a healthy pullback to a 4H value floor.
- 1H native: trend +1, RSI 73.6, above demand with room (dist 2.86) — the fast frame stayed bullish throughout; momentum never broke.

So the read is: **a strong-trend, high-on-the-daily pullback that used a low-liquidity Sunday-open gap to raid the weekend low shelf, instantly reject, and reclaim EMA21 — then resumed the trend.** The edge is HTF bull-continuation + clean sweep-reclaim mechanics + drained/coiled vol, NOT capitulation or a cross-TF regime onset. The one yellow flag for any detector is the 1D RSI 75.2 / pos 0.88 (buying a pullback while the daily is extended) — managed here by the trend's strength and the fresh defended demand, but a generic "don't buy when daily overbought" filter would wrongly skip this winner.

---
*Causal note: every (a)/(b) statement uses only data up to the 23:00 bottom-bar close except reaction_seq/MFE, which are post-entry exit-side confirmation (the entry decision is fully as-of). Grounding lifts in the angle catalogs are calibration on 61/144, not validation.*
