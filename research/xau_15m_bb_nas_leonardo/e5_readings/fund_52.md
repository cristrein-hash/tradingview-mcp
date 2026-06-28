# Fund 52 — DEEP READING (XAU 15M MON+FORTE bottom)

**Identity:** block 2025-02-25 · date **2025-05-15 06:00 UTC** · tier **FORTE** · leg_atr **18.6** · power_score **10.8** · session **ASIA** · killzone **0** (off-KZ).

---

## (a) THE ENTRY MECHANIC — where/when I actually enter

This is a **fast, front-loaded V-snap**, not a slow grind base. The reaction_seq is decisive:

| bar | c_atr | l_atr | green |
|---|---|---|---|
| 1 | 2.85 | 0.66 | ✓ |
| 2 | 3.87 | 2.47 | ✓ |
| 3 | 4.13 | 3.56 | ✓ |
| 4 | 4.20 | 3.33 | ✓ |
| 5 | 3.48 | 2.99 | ✗ |
| 6 | 1.67 | 1.55 | ✗ (pullback) |
| 7→12 | 3.07→**6.39** | climbs to 5.47 | ✓ run to MFE 6.74 |

The low bar already snaps **+2.85 ATR close** on bar 1 — bar 1 is itself the engulfing-thrust / pivot bar. The leg never re-tests the low (`mae12 = 0.66 ATR` — price effectively never came back). `first_higher_low_bar = 1`, `swept_prior_low = 1`, `choch_15m_after = 1`, `reclaim_ema_bars = 3`.

**Entry decision (causal, info ≤ entry bar):**
- The trigger is **sweep + instant reclaim**. `swept_prior_low=1` + low_closepos 0.54 + lower_wick 0.54 at the low bar = stops taken under a prior low, price closes back in the upper half on a wide-range bar (`range_exp 1.82`, `vol_climax 1.65`).
- **Cleanest fill = close of reaction bar 1** (the +2.85 ATR reclaim bar that closes back above the swept level and prints the first higher-low). Waiting for the formal 15M CHoCH (`choch_15m_after=1`, EMA21 reclaim at bar 3) costs ~1.3 ATR of the leg but is the more conservative confirmed entry. Given `mae12=0.66`, a stop just under the sweep low (≈ −1 ATR) is never threatened.
- Note the **bar-6 pullback to l_atr 1.55** (c_atr drops 4.20→1.67): a real retracement ~halfway back. If entered on the bar-1 thrust this is held comfortably; it is also a clean **shallow-retest re-entry** (ANGLE4 L8) for anyone who missed the first thrust — the higher-low at bar 6/7 launches the second, larger leg to MFE 6.74 by bar 12.

So: **sweep-prior-low → close-back-above (reclaim) on a wide thrust bar = entry at bar-1 close; managed with a stop below the sweep; optional add on the bar-6 shallow-retest higher-low.**

## (b) Lenses PRESENT / STRONG here

**Inter-bar geometry (ANGLE 4) — STRONGEST cluster:**
- **L1 monotone climbing floor** — l_atr 0.66→2.47→3.56 = run of 3 (bar4 dips trivially to 3.33). No-look-back launch present.
- **L2 reclaim_jerk / front-loaded** — d[1]=+2.85, d[2]=+1.02: the first bar does the bulk → strongly front-loaded thrust. PRESENT/STRONG.
- **L4 flush_then_snap** — up-velocity (≈4.2 ATR by bar 4) matches/exceeds the flush velocity. Mirror-V. PRESENT.
- **L6 pivot_engulf_thrust** — bar 1 is a +2.85 ATR green thrust off a 0.66 low = decisive engulf. STRONG.
- **L8 reclaim_dip_depth** — the bar-6 dip retraces but holds well above the low (l_atr 1.55 vs reaction high ~4.7); higher-low confirmed. PRESENT.
- **L9 velocity_regime_flip** — steep down-slope inverted into steep up-slope (hard flip). PRESENT.

**Cross-TF momentum / regime-onset (ANGLE 5) — STRONG, textbook phase-lag:**
- **L5.4 compressed-regime onset** — `atr_regime 1.25`, `atr_compression_pre 1.06`. ⚠️ atr_regime is ABOVE the MON median (0.94) — this bottom formed in a slightly ELEVATED-vol pocket, not the calm one. Compression-pre is present but regime is not the quiet archetype. PARTIAL.
- **L5.6 multi-TF demand stack** — 15M `in_demand=1`, `htf4_native.in_demand=1`, `htf1_native` 1.13 ATR above its demand. Nested 15M-inside-4H demand floor present. ⚠️ BUT `htf4 clean_sky_atr 0.27` and 15M `n_supply_overhead 271`, `dist_supply_atr −0.26` (price is AT/under supply) → overhead is NOT clean. The "air above" half is WEAK. So it bounced off a stacked floor straight into overhead supply — yet still ran (FORTE leg), driven by the thrust not by clean sky.
- **L5.2 1H room-above** — `htf1_native.in_demand=0`, `dist_demand_atr 1.13`, `h1_pos 0.03`. The 1H has lifted off its own demand (room present) but h1_pos is low. PARTIAL.
- **L5.1 / L5.8 phase-lag** — h4_trend −1, h1_trend −1 (both still bearish on E1), but `htf1_native.choch_rec=1` and `htf4_native.choch_rec=1` → a recent CHoCH on BOTH HTFs. The slow frames are already showing structural turns. The classic "1H-leads-4H +1" signature is NOT fully here (h1 native trend still −1), but the CHoCH-recent on both frames is the onset marker.

**Liquidity / auction (ANGLE 1) + Time/session (ANGLE 3):**
- **L1 quiet reclaim / off-killzone (A1-L1, A3)** — killzone=0, **ASIA session**. This is the dominant strong-bottom timing profile (Asia/off-KZ enriched 2.3×–8×). STRONG and distinctive.
- **A3-L1 asia_offpeak_flush** — Asia-window AND large bar (`range_exp 1.82`, `vol_climax 1.65` is a real spike for Asia) = outsized candle in thin liquidity = forced-liquidation snap. PRESENT/STRONG.
- **A1-L6 discount-not-breakdown** — `dealing_range_pos −0.259` sits in the discount band (−1, −0.2), not a range break. PRESENT.
- **A0-L7 / sweep+reclaim** — `sweep_depth_atr 2.1` (a touch deeper than MON median 1.65) but `swept_prior_low=1` with fast reclaim. PRESENT.

**Volatility structure (ANGLE 2):** `atr_compression_pre 1.06` (coil present) but `atr_regime 1.25` and `vol_climax 1.65` lean toward the climactic/expanded side rather than the drained-quiet archetype → ANGLE2's "drained-and-coiled" thesis is only PARTIAL here.

**Order-flow (ANGLE 0):** `sell_bub_w 12` and `sell_decel −10` — sell-bubble effort was HIGH into the low (NOT the thin-sell-bubble MON fingerprint), but `buy_bub_w 0`. `nas_long_16 = 3` (a NAS-LONG cluster at the bottom — demand trigger present). `rsi_low/min8 = 19.7` (deeply oversold). So order-flow here is **capitulation-flavored** (loud sells, deep RSI), which is the CONTROL-leaning signature — yet the leg was FORTE.

## (c) What is DISTINCTIVE about this bottom

This is a **HYBRID bottom that contradicts the "quiet absorption" MON archetype on the order-flow axis but is textbook on the geometry/timing axis.** It is loud where the average monster is quiet (sell_bub_w 12, vol_climax 1.65, RSI 19.7, sweep 2.1, atr_regime 1.25 — all capitulation/control-leaning) yet it produced a clean FORTE leg because:
1. **The reclaim geometry is elite** — front-loaded +2.85 ATR thrust bar, monotone climbing floor, mae 0.66 (never looked back). The SHAPE-of-the-turn (ANGLE 4) carried it, not the quiet-flush precondition.
2. **Timing is the canonical Asia/off-killzone forced-liquidation snap** — deep RSI + range-expansion + sweep in thin Asia liquidity = stop-run into a vacuum that snapped violently. This is exactly ANGLE3-L1's "large candle in a thin window."
3. **Caveat / honest flag:** it bounced into overhead supply (clean_sky 0.27, dist_supply −0.26, 271 supply overhead) — no clean runway — and the leg still ran. The "air above" lens FAILED to predict here; the fuel was trapped-shorts + thrust, not a clear path. This is a useful counter-example: **a FORTE bottom can lack clean-sky and lack quiet-absorption, IF the V-snap geometry + Asia-liquidation-sweep are both maximal.**

## (d) Macro / HTF context (as-of, ≤ entry)

- **4H:** native trend −1, rsi 32.1, in_demand=1 (15M flushed into 4H demand), but clean_sky only 0.27 ATR and a **recent 4H CHoCH (choch_rec=1)** — 4H is bearish-but-turning, sitting on its demand floor with supply immediately overhead. E1 h4: dist −14.85, pos −0.15, slope −4.69, rsi 25.8 → still a falling 4H.
- **1H:** native trend −1, rsi 49.9 (NOT oversold on 1H while 15M RSI is 19.7 = cross-TF RSI divergence, ANGLE5-L5.3 partial), above its own demand (dist 1.13, in_demand=0), **recent 1H CHoCH (choch_rec=1)**. The 1H refused to confirm the 15M panic and is structurally turning.
- **Daily:** trend 0 (flat/neutral), rsi 42.8, pos −0.12, slope −2.07 → daily in balance, not trending down hard — supports a discount-accumulation read.
- **Net:** a 15M Asia capitulation flush into stacked 4H/15M demand, with the 1H already off its floor and recent CHoCHs on both HTFs marking regime onset. Daily neutral. The structure says "discount low inside a balancing daily, with the fast frames turning" — and the 15M execution was a violent off-killzone V-snap.

---
*Honesty: all lens groundings are calibration on 61/144 curated dossiers, NOT validated edge. This fund is notable precisely because it BREAKS the quiet/clean-sky archetype on several axes yet was FORTE — a data point for "geometry + Asia-liquidation can substitute for quiet-absorption." Treat as one case, not a rule.*
