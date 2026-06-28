# Fund 18 — DEEP READING (MONSTRO bottom, XAU 15M)

**Block:** 2024-05-25 | **Date:** 2024-07-10 20:45 UTC | **Tier:** MONSTRO | **leg_atr:** 32.3 | **power_score:** 13.6
**Bottom price:** ~2370.8 (low), close 2371.2 | **ATR@low:** 1.66 | **mfe12:** +2.13 ATR (dossier 12-bar), raw leg ran to **+6.6 ATR** by idx 3036 (07-11 04:30)
**Raw bottom bar idx:** 3009 in `primitives/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.primitives.json`

---

## (a) ENTRY MECHANIC — where/when I would actually enter

This is **NOT a sweep-and-snap** (`swept_prior_low=0`, `sweep_depth_atr=0.0`). It is a **quiet-absorption base + Asia-ramp ignition**. The low itself (20:45 UTC) is a non-event in real time: a 0.8-tick-range bar in a vol vacuum. The tradable mechanic is the *reclaim of the EMA21 + 15M CHoCH* that follows, igniting at the Asia open.

Bar-by-bar (raw, all as-of):
- **idx 3009 (low, 20:45):** c 2371.2, l 2370.8, ATR drained to 1.66 (from 3.72 at idx 2989). RSI 41.6 — NOT oversold. Tick-vol collapsing (3630→791→955→1481). Quiet.
- **idx 3010–3017 (22:00–23:45, LATE/Asia pre-ramp):** micro higher-lows form (l: 2371.4→2371.2→2372.3→2372.5...), a **climbing-floor staircase**; price coils tight just below EMA21 (~2372.9). This is the base — no revisit of 2370.8.
- **idx 3018–3022 (00:00–01:00, ASIA open):** volume returns hard (2529, then 4725 at 01:00). Price reclaims EMA21 (close 2374.2 > ema 2372.9 at idx 3021) and RSI crosses 50→56. **This is the trigger bar.**

**My entry:** on the **EMA21 reclaim + RSI>50 confirmation at idx 3021 (07-11 00:45–01:00), ~2374.2**, i.e. **8 bars after the printed low** (matches `entry_mechanics.reclaim_ema_bars=8` and `choch_15m_after=1`). The trigger is **reclaim, not sweep+reclaim**: there was no liquidity grab; the signal is the coiled base breaking up on returning Asia volume. SL below the staircase base (~2370.6, the swing-origin floor, ≈1.7 ATR risk). Entry is intentionally late/confirmed — acceptable because the leg ran +32 ATR; there is enormous R left after an 8-bar wait.

Alternative aggressive entry: first micro-HL reclaim of EMA at idx 3013 (22:45, ~2372.8) — but with dead Asia-pre volume that is a lower-conviction entry; I prefer waiting for the volume return.

## (b) Lenses PRESENT / STRONG here

**Strongest cluster — QUIET ABSORPTION / COILED SPRING (Angle 0, 2):**
- **A0-L2 `quiet_climax` = 3/3 (max):** vol_climax 0.39 (<1.35), sweep_depth 0.0 (<1.8), lower_wick_ratio 0.55 — modest/no-sweep low. Textbook anti-capitulation.
- **A0-L8 / A2-L1 `vol_drain_into_low`:** ATR 3.72→2.88→2.35→**1.66** monotonically into the low; tick-vol 3630→791. Selling fuel exhausted before the print. STRONG.
- **A2-L4 `vol_of_vol_collapse` / A2-L7 `gap_to_vol_floor`:** ATR keeps draining to 0.73 through the base — vol went steady-quiet, sitting near its floor. STRONG.
- **A0-L1 / A2-L5 `effort_vs_result_failure` / inefficient drop:** `downleg_eff=0.36`, `flush_v_ratio=0.31` (grindy V, not clean cascade) — churn with little net travel = absorption.
- **A2-L3/L6 coil/NR cluster:** the base bars (3010–3017) are narrow-range inside-bars under EMA — coiled-spring pre-expansion. STRONG.

**TIME / SESSION (Angle 3) — the distinctive macro fingerprint:**
- **A3 off-killzone:** `killzone=0`, `session=LATE`. Low at 20:45 UTC, leg ignites at **Asia open 00:00–01:00 UTC** — the 2.3×–4.7× Asia-enriched window. STRONG, on-thesis.
- **A3-L3 `time_since_session_open` / Asia-ramp:** the ignition is literally the first ~1h of the Asia session reacting to the prior session's grind-down. STRONG.

**INTER-BAR GEOMETRY (Angle 4):**
- **A4-L1 `reclaim_low_monotone_k`:** climbing floor through the base and into the leg (lows never revisit 2370.8). STRONG.
- **A4-L5 `close_progression_R2`:** the post-ignition ramp (cATR 0→1.8→2.4→3.6→4.3→5.0→6.6) is a clean near-monotone staircase. STRONG.
- **A4-L9 `velocity_regime_flip`:** steep down-slope into 18:00 flipped into a steady up-ramp. Present (moderate — flip is via base, not a violent V).

**CROSS-TF / REGIME-ONSET (Angle 5):**
- **A5-L1 phase-lag turn:** `h1_trend=+1, h4_trend=+1, hd_trend=+1` — here ALL frames are already bullish (`htf4_native.trend=1, rsi 64.5`; `htf1_native.trend=1`). This is NOT the classic "1H-leads-still-bearish-4H" monster profile; it is a **pullback-in-uptrend** monster (all HTF up, deep 15M flush into demand). So A5-L1's specific divergence is ABSENT, but the bullish HTF backbone is fully PRESENT.
- **A5-L6 multi-TF demand stack:** `in_demand=1`, `htf4_native.in_demand=1`, `demand_fresh=1`, `demand_virgin=1`, `dist_demand_atr=0.26` — 15M flush lands ON a fresh/virgin demand nested inside 4H demand. STRONG.

**WEAK / ABSENT:**
- Order-flow bubbles all zero (`buy_bub_*`, `sell_bub_*` = 0), no NAS (`nas_long_16=0`), no SMC BOS, no `rsi_bull_div`. There is **no bubble/NAS/SMC confluence** — this bottom is read purely by vol-drain + coil + HTF backbone + clean reclaim.
- `clean_sky` mixed: 4H clean_sky 0.29 (thin), 15M `n_supply_overhead=37` (some overhead) — runway adequate, not pristine.

## (c) What is DISTINCTIVE about this bottom

1. **It is a textbook QUIET monster — the catalog's central thesis incarnate.** Zero sweep, zero climax, RSI ~41 (not oversold), vol draining to a dead floor (791 ticks). Anyone hunting capitulation/oversold/sweep would NEVER see this low. It is detectable ONLY by the absorption/coil/vol-drain lenses + the HTF backbone.
2. **The low and the entry are decoupled in time.** The price low prints in the LATE vacuum (20:45), but the leg only IGNITES at the Asia open (00:00–01:00) when volume returns. The 8-bar reclaim wait is structural, not noise — entry is on the *ignition*, not the *low*.
3. **Pullback-in-confirmed-uptrend, not a regime turn.** Unlike the prototypical "1H-leads-bearish-4H" monster, here every HTF (1H/4H/1D) is already bullish and the 15M is a deep, controlled flush into fresh virgin demand. The "monster" comes from a strong trend resuming off a coiled base, not from a phase-lag reversal.
4. **No order-flow theatrics at all** (no bubbles, NAS, SMC, divergence). Pure price/vol/structure read.

## (d) Macro / HTF context

Strong, intact multi-TF uptrend in gold (July 2024). `hd_trend=1, hd_rsi 56, hd_slope_atr 10` (1D rising, ~15 ATR above 1D demand — extended but trending). `h4_trend=1, h4_rsi 55.9, h4_slope 2.37, h4_pos 0.5` (4H mid-range, rising). `h1_trend=1` but `h1_dist=-0.86, h1_pos 0.34` — the 1H pulled back below its EMA into the lower third = the controlled retracement that created the entry. The flush bottoms exactly on a **fresh, virgin, defended 4H/15M demand confluence** (`dist_demand_atr 0.26, n_demand_near 17`). Read: trend-up market, healthy pullback into a stacked demand floor, quiet absorption coils the spring, Asia-open volume releases it. Defended floor + bullish HTF + clean reclaim = the let-run +32 ATR leg.

---
**Validation status:** descriptive single-fund reading (calibration), not edge. Lens labels reference Angle catalog hypotheses (calibration-grade, not validated). All entry logic uses only info ≤ entry bar idx 3021.
