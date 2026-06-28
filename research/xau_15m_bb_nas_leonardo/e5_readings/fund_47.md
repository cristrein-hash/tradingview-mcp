# Fund 47 — DEEP READING (XAU 15M MON+FORTE bottom)

**Date:** 2025-07-09 08:30 UTC · **Block:** 2025-05-25→08-25 · **Tier:** FORTE · **leg_atr:** 19.86 · **power_score:** 3.3
**Low:** 3282.41 (bar i, idx 2955) · **Session:** LONDON · **killzone:** 1
**Outcome (12-bar):** mfe 2.93 ATR / mae 0.41 ATR (clean, no deep retest)

> Régua: only info up to the entry bar is used. ATR at low ≈ 4.66. The dossier `reaction_seq.c_atr` is normalized on the larger leg-ATR baseline and reads as a slow staircase to ~2.8; the RAW 15M window below is the actual fine structure I traded off of.

---

## (a) THE ENTRY MECHANIC — sweep + instant reclaim of a fresh demand, confirmed by a monotone higher-low

This is a textbook **shallow liquidity-grab → same-bar reclaim → higher-low retest** bottom. Bar-by-bar:

- **i−1 (08:15):** the terminal flush bar — biggest red of the leg, range 1.16 ATR, body −3.2, v3636 (highest volume of the window). Velocity spike INTO the low.
- **i (08:30, the low):** prints 3282.41, **sweeping the prior-50-bar low 3284.17 by only 0.38 ATR** (shallow grab), then **closes at 3287.0 — cpos = 1.00 (close on its high), a +1.2 bullish reversal/engulf bar back INSIDE the demand zone born 07:30 (3285.39–3289.48).** RSI 34.9 (washed but not extreme). This single bar IS the rejection.
- **i+1 (08:45):** shallow dip (low 3284.4) — holds ABOVE the i low → first higher-low (`first_higher_low_bar=1`).
- **i+2 (09:00):** +3.4 green bar, close 3288.3, cpos 0.86 — reclaims back above the demand zone and confirms the higher-low. **This is the cleanest causal ENTRY: close of i+2 (3288.3).** Sweep is confirmed reclaimed, HL is in, and the structure is back inside/above the 07:30 demand. SL below the i low 3282.4 (~1.3 ATR risk).
- Post-low floor climbs monotonically: 3282.4 → 3284.4 → 3284.3 → 3288.0 → 3287.7 → 3287.4 = a "no-look-back" base (mae only 0.41 ATR over 12 bars).
- EMA21 reclaim is slow (bar +8) — so the trade is **not** an EMA-reclaim entry; it is a **demand-reclaim + HL** entry. Waiting for EMA would forfeit ~6 ATR of the leg.

**Trigger label: shallow sweep of prior low + same-bar reclaim into fresh demand + confirmed micro higher-low (no 15M CHoCH needed; `choch_15m_after=0`).**

## (b) Lenses PRESENT / STRONG here

**Order-flow / Vol (Angle 0 & 2) — the "quiet absorption, not climax" thesis fits strongly:**
- `quiet_climax` (A0-L2): vol_climax 1.35 (modest), sweep_depth 1.27/raw 0.38 ATR (shallow), wick small → **PRESENT, the MON fingerprint.**
- `liquidity_grab_no_followthrough` (A0-L7): swept_prior_low=1, shallow 0.38 ATR, reclaimed SAME bar → **STRONG.**
- `absorption_reload` / `delta_proxy_reversal` (A0-L4/L5): the low bar v3442 with cpos 1.00 = volume absorbed, closed on the high → **STRONG** (positive aggressor flip at the low).
- `flush_then_freeze` / `downleg_gap_velocity_spike` (A2-L8 / A4-L7): i−1 is the climax flush (1.16 ATR range, max vol) and i reverses immediately → **PRESENT.**
- `atr_decel / coiled` (A2): atr_regime 1.17, compression_pre 0.94 — moderate, NOT the deeply-compressed monster ideal. **PARTIAL.**

**Inter-bar geometry (Angle 4) — STRONG:**
- `reclaim_low_monotone_k`: post-low lows climb every bar (run ≥3) → **STRONG no-look-back floor.**
- `pivot_engulf_thrust`: the i bar itself (cpos 1.00, +1.2 off a 0.38-ATR sweep) + i+2 (+3.4) → **PRESENT.**
- `reclaim_dip_depth` (shallow retest): i+1 dip held high above the low → **STRONG** (mae 0.41 ATR confirms).

**Liquidity / Auction (Angle 1) — mixed:**
- `discount_not_breakdown` (A1-L6): `dealing_range_pos −0.78` = discount third, not range-broken → **PRESENT.**
- `engineered EQL raid` (A1-L2): an EQH printed 07-07; the structure had repeated CHoCH/BOS sweeping lows down to 3296.5 then this final 3282 sweep → liquidity-cycle complete. **PARTIAL.**
- **AGAINST:** `quiet_reclaim`/off-killzone (A1-L1, A3) — this bottom is **IN London killzone (killzone=1)**, the inverted-polarity wrong side of the strongest discriminator. Distinctive (see c).

**Cross-TF (Angle 5) — WEAK / against:**
- htf1_native.trend −1, htf4_native.trend −1 → **no 1H-leads-4H phase-lag turn** (the best cross-TF MON separator is ABSENT here). h1_pos 0.05, h1_rsi 35.8 (sagging with the 15M, no HTF RSI hook). Both 15M and 1H pinned `in_demand=1`.
- `nested demand` (A5-L6): the 15M flush lands ON a fresh 4H/1H demand (in_demand=1 both frames), clean_sky ~0.75–0.82 ATR → **demand floor PRESENT but overhead room is thin (n_supply_overhead 297).**
- NAS hand-off: a 4-print NAS-LONG cluster fired 07-08 15:30 (~17h prior, stale), none at the low → **WEAK/stale.**

## (c) What is DISTINCTIVE about this bottom

1. **It violates the "off-killzone Asia" monster profile.** This FORTE bottom forms squarely in the **London killzone** with HTF still fully bearish (1H & 4H trend −1, both pinned in demand). It is NOT the quiet-Asia-spring archetype the angles favor — it is the **structural variant**: a London continuation-flush that gets reclaimed by a *fresh demand zone created minutes earlier* (07:30) plus a *same-bar sweep-and-close-on-high*. The edge here is pure **micro-structure (sweep+reclaim+HL+monotone floor)**, not timing or HTF alignment.
2. **Tiny MAE (0.41 ATR) despite no HTF support and no EMA reclaim for 8 bars** — the demand reclaim + monotone HL alone held the entire base. This is a "structure carries it" bottom.
3. **Recovery is a grind, not a snap** (dossier c_atr crawls; EMA21 only reclaimed at +8). So it is FORTE-by-extension (19.86 ATR leg) rather than a violent V — fitting the grindy `downleg_eff 0.19` reading.

## (d) Macro / HTF context

Multi-day downtrend: continuous CHoCH/BOS cascade 07-06→07-09 stepping price down from ~3338 to the 3282 low (sell-side liquidity progressively taken: BOS 3296.5, 3299.46, CHoCH 3304/3297). 1H and 4H both bearish, RSI 35–37, hd_trend −1 (daily down, hd_rsi 43, hd_pos 0.20 = lower portion of daily range). Price flushed into a **stacked fresh demand** (15M zone 3285–3289 born 07:30, inside 1H/4H demand, dist_demand ≈ −0.2 ATR = right at the floor). Overhead is congested (n_supply_overhead 297 — the run had to grind up through prior CHoCH levels). So: **a final shallow sweep of an exhausted multi-day London down-leg, reclaimed by a fresh demand floor, launching a slow but large (≈20 ATR) reversal against an as-yet-unturned HTF.**

---

**Honesty:** killzone/off-killzone and cross-TF phase-lag (the two best-calibrated MON separators) are ABSENT/inverted here — this fund would NOT be selected by the Asia-timing or 1H-leads-4H lenses. It IS captured by the micro-structure family (shallow-sweep+same-bar-reclaim+fresh-demand+monotone HL). Calibration-grade, single fund.
