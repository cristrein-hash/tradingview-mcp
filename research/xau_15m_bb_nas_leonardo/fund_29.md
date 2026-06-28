# Fund 29 — DEEP READING — XAU 15M MON+FORTE bottom

**Block 2026-02-25 | low bar = 2026-02-25 20:45 UTC (t=1772052300) | tier FORTE | leg_atr 26.84 | power 5.9**

Raw bars confirmed from `primitives/XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.primitives.json`, low = series idx 88. Everything below is as-of the entry bar (post-low bars used only for the reclaim/entry trigger, which prints a few bars after the minimum — legal because the leg is large).

---

## (a) THE ENTRY MECHANIC — where I actually get in

This is a **sweep + reclaim → CHoCH-confirmed** entry, NOT a "buy the absorption coil" entry.

Bar-by-bar at the turn (o/h/l/c, ATR≈10):
- **bar 88 (the low, 20:45)** = 5181.5 / 5181.6 / **5145.9** / 5152.0 — a **wide capitulation candle**, range 35.7 ≈ 3.5×ATR, close in lower ~17% of the bar, vol 6524 (peak of the leg), RSI 36.5. It takes out the entire near base (the two live 15M demand zones 5172.8/5155.1 and 5166.4/5155.1 are both consumed exactly on this bar — last_t = the low bar) and undercuts the prior-50 low (5155.1). This is a genuine **lowest-of-50 stop-run**.
- **bar 89 (21:00)** = closes **green +9.6 → 5161.6**, reclaiming back above the swept zone tops; **15M bullish CHoCH prints here** (smc_event t=1772053200, price 5159.21). RSI bottoms at 24.6 on THIS bar (one bar after the price low → momentum low lags price low = classic bullish RSI hook).
- **bar 90 (21:15)** = **NAS LONG fires** (nas_event t=1772054100, price 5148.06), closes 5168.8.

**Entry trigger I would take:** the **reclaim-of-the-swept-level + CHoCH on bar 89's close (~5161.6)**, sized up on the bar-90 NAS-LONG confirmation. Stop under the flush low 5145.9 (mae from entry ≈ 1 ATR — entry_mechanics.mae12 = 0.45 ATR confirms the low held). The cleaner, lower-risk version waits for bar 90 NAS-LONG (entry ~5165) and trails the climbing reaction floor.

This is a **"shallow-sweep-into-HTF-demand → instant reclaim"** entry (Angle 0 L7 / Angle 1 Lens 2 archetype), confirmed by structure (CHoCH) and a directional NAS handoff (SHORT cluster → LONG). entry_mechanics agrees: `swept_prior_low=1`, `first_higher_low_bar=1`, `choch_15m_after=1`, `nas_long_after=1`, `reclaim_ema_bars=10` (EMA reclaim is slow because the flush was deep — EMA is not the trigger here; the swept-level reclaim + CHoCH is).

## (b) Lenses PRESENT/STRONG vs ABSENT (honest)

**STRONG / PRESENT — this bottom's real signature is HTF-demand + structural reclaim, not quiet-absorption:**
- **Angle 5 L5.6 Multi-TF Demand Stack (the headline lens here):** htf4_native in_demand=1, **dist_demand_atr=0.05** (price flushed to land EXACTLY on 4H demand), 4H trend=+1, clean_sky_atr=0.84 (room above). The 15M flush bottomed precisely on a 4H demand floor inside a 4H uptrend — nested floor + clear-ish sky.
- **Angle 5 L5.1/L5.2 1H regime already bullish:** htf1_native trend=+1, rsi 57.6, dist_demand_atr 1.54, in_demand=0, clean_sky 2.54. The 1H had already lifted off its own demand and is bullish while the 15M flushed = the cross-TF spring (1H up, 15M deep-flushed onto 4H floor). (Note: here 4H is ALSO already +1, so it's a full HTF-up alignment, not the "1H-leads-bearish-4H phase-lag" variant.)
- **Angle 0 L7 / Angle 1 Lens 2 liquidity-grab-no-followthrough:** swept the prior-50 low AND the two live demand zones, then reclaimed within 1 bar (close 89 back above zone tops). Shallow follow-through, instant reclaim.
- **Angle 3 L4 overnight/cross-session sweep clock & off-Asia timing:** 20:45 UTC NY-late — the flush takes out the day's intraday pools then reverses into the Asia handover.
- **Structural confirmation stack:** 15M CHoCH-up (bar 89) + NAS SHORT→LONG flip (1771999200/1772040600 SHORT → 1772054100 LONG) = Angle 5 L5.7 NAS hand-off / L5.9 CHoCH confirmation, and `rsi_low/min8` momentum hook (RSI low lags the price low).
- **Held higher-low base (Angle 4 L1/L8, partial):** reaction lows 5150→5160→5166 climb for 3 bars, then a shallow dip to 5162/5165/5163 — the first pullback holds well above 5145.9 (shallow retest, no re-test of the low). mfe12 = 4.52 ATR, mae12 = 0.45 ATR = no-look-back launch.

**ABSENT / INVERTED vs the catalog's "typical MONFORTE = quiet absorption" thesis:**
- **Angle 0 L2 quiet_climax / Angle 2 L1 atr_decel / vol_drain — ALL ABSENT.** ATR is RISING into the low (7.78→10.18, +31%), volume is RISING into the low (4583→5450→5239→5632→5472→**6524** peak ON the low bar), the low bar is a wide 3.5×ATR capitulation candle, lowest-of-50=TRUE, RSI dumps to 24.6. This is a **loud, climactic flush**, the opposite of the catalog's "calm/coiled/drained" MONFORTE prototype.
- **Angle 1 Lens 1 off-killzone/non-headline-low — ABSENT** (it IS the headline lowest-of-50, in NY hours).
- **Angle 2 L8 flush_then_freeze** — the flush is real but it does not "freeze"; it V-reverses immediately (snap, not freeze).

## (c) What is DISTINCTIVE about this bottom

It is the **climactic-flush exception** to the dossier's dominant "quiet absorption" archetype. The angle catalog repeatedly grounds MONFORTE on shallow sweeps / calm vol / drained volume; **this fund is the inverse** — a wide capitulation bar on peak volume that swept the obvious low AND the live demand zones. The reason it still produced a FORTE leg is **WHERE it flushed, not HOW**: it dumped to land **0.05 ATR onto a 4H demand zone inside a 4H+1H bullish regime**, swept the liquidity sitting just under that floor, and reclaimed in one bar with CHoCH + NAS-LONG. So the edge is **location (multi-TF demand stack) + structural reclaim**, which overrode the "loud" microstructure that would normally flag a continuation/control low. This is the case that proves the quiet-absorption lenses are a *subset*, not the whole — a violent flush ONTO stacked HTF demand in an uptrend is the other valid MONFORTE family.

## (d) Macro / HTF context

- **4H:** uptrend (trend=+1), RSI 61, sitting IN 4H demand (dist 0.05 ATR), clean_sky 0.84 ATR above — a defended 4H floor with modest overhead room.
- **1H:** uptrend (trend=+1), RSI 57.6, above its own demand (dist 1.54 ATR, in_demand=0), clean_sky 2.54 ATR — the slow frame had already turned and had air above.
- **Regime:** both HTFs aligned bullish; the 15M flush is a deep liquidity-grab pullback within an established HTF uptrend, not a counter-trend reversal. The leg that follows (leg_atr 26.84, mfe12 4.52 ATR) is the resumption of the HTF uptrend off a swept 4H demand floor.
- **Local structure:** prior 15M structure was choppy (CHoCH 1772018100, CHoCH 1772032500) but inside a higher base; the flush swept it, the bar-89 CHoCH flipped 15M back up in agreement with the intact HTF uptrend.
