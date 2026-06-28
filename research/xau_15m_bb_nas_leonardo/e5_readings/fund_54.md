# Fund 54 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block** 2025-11-25_to_2026-02-25 · **Low bar** 2026-01-02 18:30 UTC (t=1767378600) · **Tier** FORTE · **power 4.2** · **leg_atr 17.72** · **session LATE / killzone=0**
**Outcome geometry (causal-light):** mfe12 +2.06 ATR, mae12 0.22 ATR (post-low drawdown almost nil → the floor held immediately).

---

## (a) ENTRY MECHANIC — where/when I would actually enter

This is **NOT a snap-V reversal**. It is the textbook **quiet-absorption / climbing-floor (no-look-back staircase) bottom** the angle catalog says defines MON+FORTE. The raw tape:

```
bar  time     o      h      l      c      rsi   atr    note
-2  18:00   4322.5 4323.7 4312.5 4314.6  28.7  11.72  flush bar
-1  18:15   4314.7 4321.8 4310.6 4318.8  25.7  11.73  BOS-down prints @4314.87, rsi_min
 0  18:30   4318.9 4319.6 4309.7 4312.3  30.1  10.78  LOW (close-pos 0.26, weak close)
+1  18:45   4312.5 4315.8 4312.1 4315.1  27.6  10.15  first higher-low (l 4312.1>4309.7), green
+2  19:00   4315.7 4322.1 4315.7 4321.6  30.9   9.59  green, low climbs again, NAS-LONG re-prints
+3  19:15   4321.9 4323.3 4316.5 4318.6  36.9   9.12  rsi breaks 36, floor still climbing
```

**Entry decision — bar +2 close (≈4321.6), confirmation entry.** Trigger stack, all causal as-of +2:
1. **Bar +1 = first higher-low** (`first_higher_low_bar=1`): low 4312.1 > low-bar low 4309.7 — the floor stepped up the very next bar.
2. **Bar +2 confirms the higher-low and takes bar +1's high** (h 4322.1 > 4315.8) — a micro-HL → micro-HH = the earliest structural up-shift, while ATR is collapsing (10.78→9.59) = absorption confirmed not chop.
3. **NAS-LONG re-prints at the low and at +2** (id 1549 @ low, id 1551 @ 19:00) — the down-window NAS cluster (5 LONG prints 15:45→18:30, all firing INTO a falling market = absorption) keeps printing AFTER the low instead of going stale.

This is a **micro-HL + reclaim-of-prior-bar-high** entry, NOT a sweep-reclaim and NOT an EMA reclaim. The EMA21 reclaim is very late (`reclaim_ema_bars=9`, ~bar +9 at 20:45) — waiting for it would forfeit most of the +2 ATR. There is **no 15M CHoCH-up** after the low (`choch_15m_after=0`) and the swept-prior-low is only a shallow local sweep (`sweep_depth_atr=0.48`). So the only valid early trigger is the climbing-floor micro-structure, taken at bar +2. SL below the low (4309.7), ~1.0 ATR; mae of 0.22 ATR means it was never threatened.

## (b) Lenses PRESENT / STRONG here

**STRONGEST — quiet-absorption family (Angle 0 / Angle 2 — the central thesis):**
- **L2 quiet_climax (Angle 0): full 3/3.** vol_climax 1.19 (<1.35), sweep_depth 0.48 (<1.8, extremely shallow), lower_wick 0.26 (<0.45). This is a near-perfect anti-capitulation fingerprint — no climax theatrics at all.
- **ATR-decel / vol-drain (Angle 0 L8, Angle 2 L1/L2/L9): VERY STRONG.** ATR falls 14.85 (bar -8) → 10.78 (low) → 6.19 (+12). A textbook **vol-drain-into-and-through-the-low** and a multi-bar **regime halving** (Angle2 L9): vol regime collapsed ~40% across the base. atr_regime 1.73 here is elevated for the leg but the *direction* (draining hard) is the signal.
- **atr_compression_pre 1.23 + range_exp 0.88 (Angle 2 L3/L6, Angle 0 L6 coil):** compression elevated, the low bar is NOT a blow-off (range modest) → coiled-pocket low.
- **downleg_eff 0.53 + drop20 6.3:** grindier than a clean cascade (bars -7..-4 are a tight shelf), consistent with absorption rather than impulsive continuation.

**STRONG — momentum / divergence:**
- **rsi_bull_div=1, rsi_head=1.0, rsi_min8 24.3, rsi_low 30.1 (Angle 0 L10).** RSI made its true low at bar -1 (25.7) and at the price-low bar RSI is HIGHER (30.1) = regular bullish divergence at the print. Not deeply washed.
- **nas_long_16 = 5, nas_short_16 = 0 (Angle 1 L7 / Angle 3 L6 / Angle 5 L5.7).** A dense one-sided NAS-LONG cluster firing INTO the decline and continuing after the low = sell-side exhaustion / down-initiative refusing to confirm. This is the single most distinctive footprint here.

**STRONG — time/session (Angle 3):**
- **session LATE, killzone=0** — off-killzone bottom, exactly the enriched MON+FORTE profile (Angle 3: off-KZ 80% strong vs 47% control). 18:30 UTC = post-NY-fade / late window, thin liquidity.
- **2026-01-02 = Friday** — Angle 3 flags Friday-late as depleted in strong, so this is a *mild* off-profile note (not week-open noise though).

**STRONG — liquidity / structure (Angle 1):**
- **in_demand=1, demand_fresh=1, demand_virgin=1, dist_demand_atr -0.28** — flushed INTO a fresh, virgin 4H/15M demand zone (Angle 5 L5.6 stacked-demand floor). `htf4_native.in_demand=1` confirms the 15M low sits inside 4H demand.
- **A downside BOS prints at bar -1** (smc id 4151 @4314.87) — the final structural break that engineers the low; price undercuts it and immediately reclaims (close +1 = 4315.1 > 4314.87).

**STRONG — cross-TF regime onset (Angle 5):**
- **htf1_native.in_demand=0, dist_demand_atr 1.04, h1_pos 0.05 / 0.19** — 1H sits ABOVE its own demand (room overhead) while 15M is at the floor = the **multi-TF position divergence** (L5.2 room-above).
- **hd_trend = +1 (Daily bullish), hd_rsi 52.1, hd_slope +0.3** — the Daily frame is already constructive (Angle 5 phase-lag: fast/Daily up while 4H/1H still −1). h1_rsi 37.7 hooking, h4 still −1.

## (c) What is DISTINCTIVE about this bottom

1. **The NAS-LONG cluster fires DURING the decline (5 LONGs 15:45→18:30) and continues at the low** — the down-leg's own trigger engine is screaming LONG while price still falls. That is absorption made visible on the signal layer, not just the tape. Rare and clean.
2. **ATR collapse is the dominant signature** — not a sweep, not a wick, not a volume climax. The bottom is *defined by volatility draining* (14.85→6.19). The entry quality comes from the floor stepping up while energy bleeds out, then re-coiling.
3. **No theatrics at all:** sweep only 0.48 ATR, wick only 0.26, weak close (0.26). This is the *purest* "strength via the absence of capitulation" example — a detector that requires oversold/deep-sweep/strong-close would MISS this entirely, and that is exactly the catalog's central reframe.
4. **macro_bear=1 yet hd_trend=+1** — the bottom forms with the labelled macro context bearish but the Daily already turning, the 1H above demand. Classic phase-lag spring inside a higher-TF that has stopped breaking down.

## (d) Macro / HTF context

- **Daily (hd):** trend +1, pos 0.35, rsi 52.1, slope +0.3 — constructive, the slow frame supports the turn (room to a discount, not a breakdown).
- **4H (h4 / htf4_native):** trend −1, rsi 42→52.8, h4_pos 0.18, **in_demand=1, clean_sky 0.2 ATR** — flushed into 4H demand but with little clean sky immediately overhead (some overhead supply: n_supply_overhead 109). The leg has a defended floor but a moderately congested ceiling on the 4H.
- **1H (h1 / htf1_native):** trend −1, rsi 37.7→52.1 hooking, **above its own demand (dist 1.04, in_demand=0)** = room-above divergence vs the 15M floor.
- **Net read:** a late-Friday, off-killzone flush into stacked fresh 4H/15M demand, where selling effort is exhausting (ATR draining, NAS-LONG cluster, RSI divergence) inside a Daily that has already turned up. The reversal is administered by a climbing-floor staircase, not a snap — enter on the micro-HL confirmation (bar +2), SL below the low, expect a grind-up leg (mfe +2.06 ATR in 12 bars). Caveat: leg_atr 17.72 is large but mfe12 is only ~2 ATR within the dossier window — most of the FORTE leg extends beyond bar +12, consistent with a slow no-look-back grind rather than an instant impulse.
