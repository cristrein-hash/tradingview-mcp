# Fund 32 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2025-11-25 | **Date/time:** 2025-12-18 14:45 (NY session, killzone=1) | **Tier:** FORTE | **leg_atr:** 25.21 | **power_score:** 3.8
**mfe12 = 6.91 ATR | mae12 = 1.4 ATR** (clean, high-R, low-heat leg).

---

## TL;DR
A **trend-continuation pullback bottom inside an already-bullish HTF**, NOT the canonical quiet-Asia stop-run reversal. The discriminator here is **cross-TF momentum alignment (4H AND 1H both bullish) + an immediate, no-look-back monotone reclaim with price already above the 15M EMA21 at the low.** Entry mechanic = **sweep + instant reclaim on bar +1, confirmed by a 15M CHoCH-up**. This is the "buy-the-discount-in-an-uptrend" variant of MON+FORTE, distinct from the exhaustion-reversal variant the angle agents mostly profiled.

---

## (a) ENTRY MECHANIC — where/when I actually enter

**Enter at the close of reaction bar +1.** Causally available facts by that bar:
- `swept_prior_low = 1` AND `sweep_depth_atr = 0.64` (a **very shallow** sweep — took out a local pool, not a deep flush) → liquidity-grab signature.
- `low_closepos = 0.92` on the low bar — price closed in the top 8% of the bottom bar's range: **buyers absorbed the sweep within the bar itself** (a delta-proxy bullish print, Angle 0 L4 `absorption_reload` / L5 delta-flip).
- `reclaim_ema_bars = 0` — price was **already above the 15M EMA21 at the low** (not below needing reclaim). The "pullback" only nicked the trend's mean and bounced.
- `first_higher_low_bar = 1` — the higher-low forms immediately (bar +1).
- Reaction bar +1 itself: `c_atr 2.32`, `l_atr 1.89`, **green** — an instant +2.3 ATR thrust off the low (Angle 4 L6 `pivot_engulf_thrust` / L2 `reclaim_jerk` front-load present).

**Trigger I'd act on:** shallow sweep of the prior local low → strong-close absorption bar → bar +1 green thrust that holds a higher low. `choch_15m_after = 1` confirms a 15M bullish CHoCH right after, so a conservative entry can also be the CHoCH break on bar +1/+2 with stop below the swept low (~−1.4 ATR, matching the realized mae of 1.4). Either way the entry sits in the first 1–2 reaction bars; the leg then ran to +6.9 ATR.

**Why not wait:** the reclaim is a pure monotone staircase — c_atr 2.32 → 2.59 → 3.01 → 3.09 → **5.60 → 6.14** with lows climbing 1.89 → 1.72 → 2.40 → 2.69 → 3.06 → 5.58 (only one tiny 1-bar low dip at bar 2). The biggest displacement is bars 5–6; waiting for "confirmation" past bar +2 sacrifices most of the R. This is a no-look-back launch — enter early.

---

## (b) Lenses PRESENT / STRONG here

### Cross-TF momentum & regime (Angle 5) — the dominant lens for THIS fund
- **`h4_trend = +1`** AND **`htf1_native.trend = +1`** — both HTF frames already bullish. This is the *opposite* of the typical MON+FORTE profile (where 4H is still −1 and 1H is just turning). Here it's a **continuation pullback in a confirmed uptrend**, not a phase-lag reversal. L5.1 phase-lag does NOT apply; instead this is full cross-TF agreement.
- **L5.3 HTF-RSI strength:** `htf1_native.rsi = 72.0`, `htf4.rsi = 59.1`, while 15M `rsi_low = 37.7`/`rsi_min8 = 32.8` — the 15M momentum dipped but the HTF momentum never broke (1H deeply bullish at 72). Textbook cross-TF RSI divergence: shallow 15M wash inside HTF strength.
- **L5.5 flush-spike isolation:** `flush_v_ratio = 0.54` (sharp-ish V) with `drop20_atr = 3.6` — a localized 15M dip the HTF absorbed.
- HTF `clean_sky_atr`: 4H = 0.2, 1H = 0.15 — **thin/near overhead supply on the HTF resample** (mild caution; the runway above the 1H is not wide, yet the leg still ran — the demand below was the driver).

### Inter-bar geometry & velocity (Angle 4) — STRONG
- **L1 `reclaim_low_monotone_k` ≈ 4+** — lows climb almost every bar (one trivial dip at bar 2). Climbing-floor / no-look-back.
- **L2 `reclaim_jerk` front-loaded** and **L4 `flush_then_snap`** — up-velocity matches/exceeds the flush; the snap-back is immediate.
- **L5 `close_progression_R2` high** — c_atr is a near-straight rising ramp through bar 6.
- **L8 `reclaim_dip_depth` shallow** — `mae12 = 1.4 ATR` total heat; the retest never threatens the low.
- **L6 `pivot_engulf_thrust`** — bar +1 is a decisive green thrust off a strong-close low.

### Liquidity / auction (Angle 1) — partial
- **`liquidity_grab_no_followthrough` (L7 of Angle 0 / Lens 1-2 Angle 1):** shallow sweep (0.64 ATR) + instant reclaim = stop-run that fails to extend. PRESENT and clean.
- **Lens 6 discount-not-breakdown:** `dealing_range_pos = −0.218` — in the discount third but NOT range-broken (>−1). Buy-the-discount.
- **Lens 3 liquidity asymmetry:** `in_demand = 1`, `dist_demand_atr = −0.13` (right at/just inside demand), `demand_fresh = 1`, `demand_virgin = 1` — a **fresh, virgin demand zone** defending the floor. `n_supply_overhead = 17` and `dist_supply_atr = −0.21` — supply is close (caution flag), but the fresh virgin demand won.

### Order-flow / microstructure (Angle 0) — MIXED, leans absorption
- **`low_closepos = 0.92` + `lower_wick_ratio = 0.26`:** strong close, modest wick → **absorption-at-low** (L4 absorption_reload PRESENT).
- **`sell_decel = 6`, `sell_bub_w = 40`, `sell_bub_L = 8`:** sell-bubble effort was HEAVY into the low (this is NOT the quiet-no-sell-bubble fingerprint). But `sell_decel` flags the deceleration — sell effort was present then **decelerated** (Angle 0 L3 `sell_bubble_exhaustion_gap` — effort spent, then drying).
- **`buy_bub_w = 0`** — no buy-bubble first-print (Angle 0 L9 absent).
- **`rsi_bull_div = 1`** (Angle 0 L10 / Angle 5 L5.3): RSI bullish divergence present; `rsi_min8 = 32.8` (NOT deeply oversold — matches MON "less oversold" profile).

### Volatility structure (Angle 2) — DOES NOT fit the quiet-coil archetype
- **`atr_regime = 2.14`** (HIGH, vs MON median ~0.94) and **`vol_climax = 1.55`, `range_exp = 2.97`** — this bottom formed in an **EXPANDED, climactic vol regime**, the *opposite* of the drained-coiled MON archetype. So Angle 2's coiled-spring lenses (L1 atr_decel, L4 vov_collapse, L7 vol-floor) are **ABSENT/inverted** here.
- `atr_compression_pre = 0.43` (low) — no pre-compression coil. This is a flush-bottom, not a coil-bottom.

### Time / session (Angle 3) — INVERTED vs archetype
- **NY session, `killzone = 1`** — the *opposite* of the off-killzone-Asia MON profile. This fund is a counter-example to the killzone-polarity finding: a strong bottom that formed INSIDE the NY killzone. The session lens does NOT carry this one.

---

## (c) What is DISTINCTIVE about this bottom

1. **It is a continuation pullback, not an exhaustion reversal.** Both HTF frames (4H +1, 1H +1, 1H RSI 72) are already bullish — this is a dip-buy in a running uptrend, not a counter-trend turn. Most MON+FORTE funds the angle agents profiled have 4H still bearish; this one has 4H confirmed up.
2. **Price never lost the trend mean.** `reclaim_ema_bars = 0` — the low printed *with price already above the 15M EMA21*. The pullback was shallow and immediately reclaimed.
3. **It violates THREE of the angle archetypes simultaneously:** formed in NY killzone (not quiet Asia), in expanded/climactic vol (atr_regime 2.14, not coiled 0.94), with heavy sell-bubble effort (40 small / 8 large, not the quiet-absorption desert). Yet it is still FORTE — proving the **cross-TF momentum-alignment + monotone-reclaim path is an independent route to a big clean leg** that does not require the quiet-stop-run signature.
4. **Extremely efficient leg:** mfe 6.91 / mae 1.4 ATR (R-multiple of the leg ~5:1 of heat). The reclaim staircase is one of the cleanest possible shapes.
5. **Shallow everything on the down-side:** sweep 0.64 ATR, drop20 3.6 ATR — the dip barely went anywhere before snapping. The "bottom" is more a controlled shake-out than a capitulation.

---

## (d) Macro / HTF context

- **4H (`htf4_native`):** trend +1, RSI 59.1, dist_demand 1.32 ATR (above its 4H demand, not pinned), in_demand 0, clean_sky 0.2 ATR. The 4H is in a healthy uptrend, pulling back to mid-structure — room overhead is modest but the trend is the tailwind.
- **1H (`htf1_native`):** trend +1, **RSI 72.0** (strongly bullish), dist_demand 1.72 ATR above its 1H demand. The 1H is the strongest frame — the 15M flush is just noise against a forcefully bullish 1H.
- **15M structure at the low:** inside a **fresh, virgin demand zone** (`in_demand 1, demand_fresh 1, demand_virgin 1, n_demand_near 34`), at dealing-range discount (−0.218), with a shallow sweep of local liquidity and immediate absorption (low_closepos 0.92).
- **macro flags:** `macro_bull = 1`, `macro_bear = 0` — aligned long.
- **Caution noted honestly:** supply is near overhead (dist_supply −0.21, n_supply_overhead 17, HTF clean_sky thin 0.15–0.2). In a less bullish HTF this could cap the bounce; here the 4H+1H bullish stack + fresh virgin demand overwhelmed it and the leg ran +6.9 ATR.

**Synthesis:** This is the **"HTF-aligned continuation dip-buy" sub-type of MON+FORTE** — the edge comes from full cross-TF bullish alignment (Angle 5) plus a textbook no-look-back monotone reclaim (Angle 4), entered on bar +1 after a shallow sweep + strong-close absorption + 15M CHoCH. It deliberately does NOT fit the quiet-Asia / coiled-vol / exhaustion-reversal archetype, which is exactly why it is a useful, orthogonal example for the engine: a strong bottom can be a trend-pullback, and for those the HTF momentum lenses and reclaim-geometry lenses — not the capitulation/quiet-climax lenses — are what fire.
