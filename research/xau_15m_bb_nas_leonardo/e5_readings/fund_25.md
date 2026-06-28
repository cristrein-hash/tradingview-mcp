# Fund 25 — DEEP READING (XAU 15M MON+FORTE bottom)

- **Date:** 2025-06-12 22:30 UTC · block 2025-05-25
- **Tier:** FORTE · power_score 7.1 · leg_atr 30.21 · year 2025
- **Outcome (exit-side, not used for entry):** mfe12 = 21.55 ATR, mae12 = 0.76 ATR — near-zero heat, monster clean run.

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

**Archetype: quiet pullback-into-aligned-demand reclaim, NOT a capitulation reversal.** There is NO sweep here (`sweep_depth_atr = 0.0`, `swept_prior_low = 0`), NO CHoCH after (`choch_15m_after = 0`), NO NAS-long (`nas_long_after = 0`), and RSI never went oversold (`rsi_low = 45.8`). So the trigger is NOT sweep+reclaim and NOT a structural break. It is a **shallow controlled dip that taps fresh 4H demand and immediately reclaims EMA21 with a climbing floor.**

Reaction sequence (post-low, ATR units):

| bar | c_atr | l_atr | green | note |
|---|---|---|---|---|
| 1 | 1.60 | 0.76 | 1 | thrust off low, first higher-low already (HL bar = 1) |
| 2 | 2.07 | 1.18 | 1 | floor climbs |
| 3 | 1.64 | 1.51 | 0 | red but **low still rises** (no look-back) |
| 4 | 3.19 | 1.41 | 1 | EMA21 reclaimed here (`reclaim_ema_bars = 4`) |
| 5 | 6.72 | 3.01 | 1 | displacement begins |
| 6 | 9.48 | 5.10 | 1 | acceleration |
| 7+ | →21.5 | →18.9 | mostly green | monotone staircase to +21.5 ATR |

**My entry: bar 4 close, on the EMA21 reclaim.** Rationale: bars 1–3 give a confirmed higher-low with a *climbing floor* (l_atr 0.76 → 1.18 → 1.51, never revisits the low even on the red bar 3) — that is the "no-look-back" signature (Angle 4 L1). Bar 4 closes back above EMA21 (`reclaim_ema_bars = 4`) and prints +3.19 ATR — the front-loaded thrust confirming initiative. Stop goes just below the low (mae after entry is essentially zero, so this is a tight, high-R entry). An aggressive variant enters bar 1 on the engulfing thrust off the 0.76 low while holding a stop under the low, but bar 4's EMA reclaim is the highest-conviction, fully-causal trigger consistent with the demand-tap + reclaim read.

**Why not wait for sweep/CHoCH:** they never come. This bottom is mechanically a pullback that holds; demanding a sweep or CHoCH would skip the trade entirely. The causal trigger is: **price dips into fresh/virgin 4H demand → does not sweep → reclaims EMA21 within 4 bars with a monotone-rising floor.**

---

## (b) LENSES PRESENT / STRONG here

### Old features_E1 / HTF (PRESENT)
- **In fresh, virgin 4H demand:** `in_demand=1`, `dist_demand_atr=-0.09`, `demand_fresh=1`, `demand_virgin=1`, `htf4_native.in_demand=1`, `htf4 dist_demand_atr=-0.07`. The flush lands *exactly* on an untested 4H demand floor. STRONG.
- **Calm/coiled regime:** `atr_regime=0.35` (extremely low), `atr_compression_pre=1.71` (very high), `vol_climax=0.45` (tiny). Textbook drained-and-coiled. STRONG.
- **Grindy, inefficient down-leg:** `downleg_eff=0.25`, `flush_v_ratio=0.4`, `consec_down=3`, `drop20_atr=4.93` (moderate, not a cascade). Two-sided fighting / absorption, not a clean crash. PRESENT.
- **Not oversold:** `rsi_low = rsi_min8 = 45.8` (way above the 31–37 typical floor). The non-oversold-bottom signature. STRONG/distinctive.
- **Low holds & is bought:** `low_closepos=0.6`, `lower_wick_ratio=0.6`, `low_revisit=1`. Strong-close + rejection wick. PRESENT.
- **Off-killzone, Asia/LATE:** `session=LATE`, `killzone=0`. The off-killzone quiet-reversal profile. PRESENT.

### NEW angles (STRONG)
- **Angle 2 / Angle 0 — drained-and-coiled (L1 atr_decel, L4 vol_of_vol_collapse, L6 coiled_spring):** This is the cleanest fit. atr_regime 0.35 + compression_pre 1.71 = a deep coil; the bottom forms in stored, not spent, energy. The leg then released into a +21.5 ATR run — the spring fired. **PRESENT-STRONG.**
- **Angle 0 L2 quiet_climax / L8 vol_drain_into_low / L7 liquidity_grab inverted:** vol_climax 0.45 (modest), sweep_depth 0.0 (shallow — actually no sweep), lower_wick 0.6. The "strength via the absence of climax theatrics" thesis fits perfectly. The one mismatch: there is literally NO sweep, so L7 (shallow-grab+reclaim) does NOT fire — this bottom does not even need a stop-run. **PRESENT (anti-capitulation), L7 ABSENT.**
- **Angle 4 L1 reclaim_low_monotone_k / L5 close_progression_R2 / L8 reclaim_dip_depth:** The climbing-floor staircase (l_atr 0.76→1.18→1.51→1.41→3.01→5.10, run holds through the single red bar) + near-monotone rising closes = the no-look-back launch. `first_higher_low_bar=1` (immediate HL), shallow retest. **PRESENT-STRONG — this is the defining post-low signature here.**
- **Angle 3 L1/L3 Asia off-peak + first-session-hour:** 22:30 UTC = the Asia/LATE off-killzone window, ~early in the Asia ramp. Matches the 2.3×–4.7× Asia enrichment. **PRESENT.**
- **Angle 1 L3 liquidity asymmetry (floor nearer than ceiling):** `dist_demand_atr=-0.09` (on the floor) vs `dist_supply_atr=0.64` overhead — floor is right here, but note `n_supply_overhead=10` is high → overhead is NOT thin. So the *defended-floor* half is STRONG; the *clean-runway* half is WEAK on the raw count. **PARTIAL.**
- **Angle 5 L5.6 multi-TF demand stack:** 15M flush lands on 4H demand (`htf4_native.in_demand=1`), `htf4 clean_sky_atr=0.4`, `htf1 clean_sky_atr=0.27`. Nested floor PRESENT, but clean-sky is thin (small clean_sky values) so runway is modest on the snapshot. **PARTIAL.**

### NEW angles ABSENT (important for the read)
- **Angle 5 L5.1/L5.3/L5.8 phase-lag turn — ABSENT/INVERTED.** The grounding thesis is "1H turns up while 4H still −1". Here BOTH frames are ALREADY bullish: `h1_trend=+1, h4_trend=+1`, `h1_rsi=61, h4_rsi=63.7`, `h1_slope_atr=+2.61, h4_slope_atr=+6.36`. There is no phase-lag — this is a continuation pullback inside an established multi-TF uptrend, not a regime-onset reversal. **This is the biggest divergence from the "typical" MON+FORTE template and is what makes fund 25 distinctive.**
- **Order-flow bubbles / NAS — ABSENT.** `buy_bub_w/L=0`, `sell_bub_w/L=0`, `nas_long_16=0`, `nas_short_16=0`, `smc_bos=0`, `rsi_bull_div=0`. No bubble or NAS confluence at all. The edge here is purely structural (demand + reclaim + coil), not signal-driven.
- **No sweep, no CHoCH** (covered above).

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is a continuation pullback, not a reversal.** Unlike the canonical MON+FORTE template (1H-leads-4H, 4H still bearish, deep flush into a turn), here 4H AND 1H are both already trending up with strong RSI (61/64). The "bottom" is a shallow dip that retags fresh 4H demand inside a live uptrend. The big leg is the *resumption* of an existing trend, which is why it ran so cleanly (+21.5 ATR, mae 0.76).
2. **Extreme calm + deep coil with essentially no flush.** atr_regime 0.35 is among the lowest possible, vol_climax 0.45, sweep_depth 0.0, RSI 45.8. There is no capitulation event whatsoever — pure quiet absorption. This is the *purest* expression of the "anti-capitulation" thesis in the catalog: the bottom is invisible to any climax/sweep/oversold detector.
3. **Perfect climbing-floor reclaim with near-zero heat.** mae12 = 0.76 ATR — once the low printed, price barely retraced. The monotone l_atr staircase + bar-4 EMA reclaim made this one of the lowest-risk entries possible.
4. **Edge is entirely structural, zero signal-confluence.** No bubbles, no NAS, no divergence, no BOS/CHoCH. If a strategy required bubble/NAS/sweep confluence, it would MISS this monster. The only readable signals are: fresh-virgin-demand-tap + coiled-vol + EMA-reclaim-with-climbing-floor + aligned HTF trend.

---

## (d) MACRO / HTF CONTEXT

- **4H (native + E1):** uptrend (`h4_trend=+1`), rsi 63.7, `h4_pos=0.82` (high in range), `h4_slope_atr=+6.36`, dist_demand -0.07 (at 4H demand), clean_sky 0.4. → 4H is in a strong, established uptrend pulling back to a fresh demand floor. macro_bull=1, macro_bear=0.
- **1H (native + E1):** uptrend (`h1_trend=+1`), rsi 58–61, `h1_pos=0.72`, `h1_slope_atr=+2.61`, `h1_eff=0.12` (low — the recent 1H move is grindy/coiled, consistent with the compression). dist_demand 0.8 (1H sitting just above its own demand → room beneath intact).
- **Synthesis:** This is a **mid-uptrend, multi-TF-aligned, quiet pullback to fresh/virgin 4H demand in the Asia/off-killzone window**, forming inside a deeply compressed-vol coil. No sweep, no climax, no oversold, no signal confluence — the leg is the trend resuming off a defended fresh floor. The reversal mechanic is a 4-bar EMA21 reclaim with a monotone climbing floor (no-look-back). The only caution against over-stacking the "capitulation reversal" lenses: they do NOT fire here — this fund is detected by the *continuation-pullback-in-coil* family (demand-fresh-virgin + coiled atr_regime + aligned-HTF-trend + climbing-floor reclaim), which is a distinct sub-archetype within MON+FORTE.
