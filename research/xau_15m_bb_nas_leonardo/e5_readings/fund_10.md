# Fund 10 — DEEP READING (MONSTRO, 2024-07-30 01:30 UTC, block 2024-05-25)

**Tier:** MONSTRO · power_score 12.4 · leg_atr 40.67 · session ASIA · killzone 0
**Outcome:** mfe12 5.88 ATR / mae12 0.82 ATR (one-sided no-look-back leg).

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

This is **not** a sweep-and-snap V. The raw bars say it is a **quiet absorption + slow-coil reclaim**, so the entry is a *confirmation* entry, not a knife-catch.

The play-by-play (ATR≈2.0, bottom bar idx +0 = 01:30):
- **−2/−1 (01:00, 01:15):** the only real "effort" — V8460 then V7376 (5–8× the prior baseline of ~1–2.7k) pushing price from 2382→2378. Big volume, but net travel is small (~4 pts). This is the **absorption print**: maximum seller effort, minimal result.
- **+0 (01:30, the low 2376.45):** V8280 (still climactic) but the bar **closes at 2379.5, up in the upper half (low_closepos 0.67)** — sellers spent their biggest volume and price closed back GREEN off the low. Effort failed.
- **+1..+3 (01:45–02:15):** volume **drains** to 5092→4569→2238 while the floor holds and ticks up (lows 2378.1→2378.6→2379.4). No look-back. This is the "loud leg → silent base" drain.
- **+4 (02:30):** close 2381.3 **reclaims EMA21 (2380.9)** — `reclaim_ema_bars = 4`. RSI lifts 36→43→50.
- **+5..+7:** clean monotone staircase up, RSI breaks 50→57, leg accelerates.

**Where I enter:** the cleanest causal trigger is the **EMA21 reclaim on bar +4 (02:30, ~2381.3)**, confirmed by the higher-low floor already built across +1..+3 and the volume drain. A more aggressive (and here, valid) variant is the **first higher-low + green-reclaim on bar +1** (`first_higher_low_bar = 1`) right after the absorption bar closed green — but +4 EMA reclaim is the higher-conviction, fully-confirmed entry that still leaves ~4.5 ATR of runway (mfe 5.88). The 15M bullish **CHoCH printed after** (`choch_15m_after = 1`), which would confirm even a +4 entry as structurally sound.

**Trigger label: absorption (effort-fail at the low) → micro higher-low → EMA21 reclaim (bar +4).** NOT a deep sweep, NOT a flush-V.

---

## (b) Lenses PRESENT / STRONG here

**Order-flow (Angle 0) — the core of this bottom:**
- **L1 effort_vs_result_failure — VERY STRONG.** Bars −2/−1/+0 = V8460/7376/8280 (huge effort) for only ~4–6 pts down then a green close. Textbook absorption.
- **L4 absorption_reload — STRONG.** Bottom bar +0: volume spike (8280) with close in upper half (low_closepos 0.67) = buyers absorbed at the low.
- **L8 vol_drain_into_low / drain-after-low — STRONG.** Volume collapses 8280→5092→2238 over +1..+3 = sellers out of fuel.
- **L2 quiet_climax — PARTIAL.** sweep shallow-ish (1.85), wick small (0.34), but vol_climax 1.74 is elevated (one effort spike), so 2/3. The "modest volume" leg of the fingerprint is the weakest match — this had one genuine volume burst.
- **L10 rsi_holds_above_floor — STRONG.** rsi_low/rsi_min8 = 36 (NOT deeply oversold), well above the control's ~28. Momentum never confirmed the dump.

**Liquidity / Auction (Angle 1):**
- **L1 QUIET RECLAIM (off-killzone × non-headline low) — VERY STRONG, the signature.** killzone 0, ASIA, AND the low 2376.45 is **NOT the trailing-50 low** (prior-50 min = 2369.51). It undercut only a *local* pool, not the obvious chart low. This is the single highest-lift lens in the catalog (8.1×) and it fires cleanly.
- **L6 discount-not-breakdown — PRESENT.** dealing_range_pos −1.028 sits right at the discount edge (marginally below −1.0, a fraction into break territory — borderline, not a clean range-break continuation).
- **L3 liquidity asymmetry — WEAK/MIXED.** n_supply_overhead 135 is HIGH (thick overhead), dist_supply −0.17 (price actually just under a supply edge). The runway is *not* clean — this leg ran INTO overhead, which makes the 5.88 ATR result more impressive but is not a "thin-sky" setup.

**Volatility structure (Angle 2):**
- **L1 atr_decel_into_low — STRONG.** ATR fell 1.98→1.86→1.64→1.54 across −12..−4 (vol draining into the low) before the spike. atr_regime 0.67 = very calm regime.
- **L3/L4/L7 coiled-spring / vol-floor — STRONG.** atr_regime 0.67 (deeply compressed), atr_compression_pre 0.93. Low formed in a quiet, coiled pocket, then expanded (ATR 2.0→2.79 post).
- **L8 flush_then_freeze — PARTIAL.** one big effort bar (−2, V8460) then the freeze/drain — sequence present on volume even if not a range-climax bar.

**Cross-TF momentum (Angle 5):**
- **L5.4 compressed-regime onset — VERY STRONG.** atr_regime 0.67 vs control 1.28 — the cleanest regime gate, deeply in MON territory.
- **L5.1/L5.2 phase-lag — DOES NOT FIRE (notable miss).** htf1_native.trend −1 AND htf4_native.trend −1 (both still bearish), htf1_native.in_demand 0 but h1_pos 0.37. The 1H has NOT turned up here — this bottom was caught *before* the HTF phase-lag signal, on order-flow/absorption alone. h1_eff 0.39 (above the anti-range floor 0.15, so not chop).
- **L5.6 multi-TF demand stack — PARTIAL.** in_demand 1, htf4_native.in_demand 1, demand_fresh 1, demand_virgin 1 (flushed into FRESH VIRGIN 4H demand) — strong floor — but clean_sky only 0.08 ATR (supply right above) so the "air above" half is absent.

**Inter-bar geometry (Angle 4):**
- **L1 reclaim_low_monotone — STRONG.** reaction l_atr 0.82→1.08→1.46→1.01... floor climbs (one minor dip at +4 then resumes); no return to the low.
- **L5 close_progression_R2 — STRONG.** c_atr 1.59→1.73→1.48→2.43→2.69→3.34... a near-monotone ramp after +3, high linearity once launched.

---

## (c) What is DISTINCTIVE about this bottom

1. **It is an ABSORPTION bottom, not a capitulation flush.** The defining footprint is three back-to-back huge-volume bars (−2/−1/+0, V7–8k) that produced almost no net downward travel, then a green close and an immediate volume drain. Sellers emptied the clip and price refused to fall. This is the purest "effort fails → result divergence" specimen.
2. **The low is a LOCAL higher-low, not the obvious chart low** (2376.45 vs trailing-50 low 2369.51). It is the textbook off-killzone, non-headline quiet reclaim (Angle 1 L1, 8.1× lift) — the smart-money low away from the crowd flush.
3. **Deeply compressed, calm regime** (atr_regime 0.67 — far below even the MON median 0.94). The leg launched from *stored* energy, ASIA session, 01:30 UTC (the 4.7×-enriched Asia-ramp hour).
4. **It ran INTO overhead supply, not clean sky** (n_supply 135, clean_sky 0.08). The 5.88-ATR leg punched through congestion — the fuel came from absorption + trapped sellers, not an empty runway. This makes it distinctive vs the "thin-sky let-run" archetype.
5. **HTF had NOT turned** (1H and 4H both −1). This was a *leading* entry on micro order-flow, ahead of the HTF phase-lag signal — caught earlier than the Angle-5 regime-onset triad would have triggered.

---

## (d) Macro / HTF context (as-of entry)

- **4H:** trend −1, RSI 44.5, pos 0.53, slope −0.87, **in fresh virgin demand** (dist_demand 0.38 ATR, in_demand 1). 4H bearish but flushed into a defended fresh 4H demand zone — the floor.
- **1H:** trend −1, RSI 45.2, pos 0.37, slope −0.56, h1_eff 0.39 (not chop). 1H still bearish but decelerating; price above its own demand (in_demand 0, dist 2.4).
- **Daily:** trend 0 (flat/neutral), RSI 48.8, pos 0.23, slope −2.09 — daily in the lower-third, neutral bias.
- **Read:** a multi-day grind-down into a *fresh virgin 4H demand* during the quiet Asia session, in a compressed-vol regime. No NAS, no bubbles, no SMC BOS at entry — this bottom is carried almost entirely by **order-flow absorption + the quiet/off-killzone/non-headline-low structure**, launching before the HTF trend confirmed. A "leading absorption" MONSTRO.

---

**1-line summary:** MONSTRO — absorption bottom (3 huge effort bars, V7–8k, no net result → green close → volume drain) at an off-killzone local higher-low in fresh virgin 4H demand; entry = EMA21 reclaim on bar +4 (~2381.3) after the micro higher-low, ahead of any HTF turn.
