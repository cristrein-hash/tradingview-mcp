# FUND 15 — DEEP READING (XAU 15M MON+FORTE bottom)

**Tier:** MONSTRO · power_score 8.1 · leg_atr 34.74 · block 2025-02-25 → 2025-05-25
**Low bar (i):** 2025-05-01 12:00 UTC · low 3201.67 · close 3206.77 (green) · RSI 27.3 · ATR 6.71
**Outcome:** mfe12 4.72 ATR, mae12 0.30 ATR (drawdown after entry essentially zero — a no-look-back launch)

---

## (a) ENTRY MECHANIC — where/when I would actually enter

This is a **two-bar capitulation flush → absorption-close → engulfing-thrust reclaim**. The cleanest, most causal entry is the **close of reaction bar +1 (12:15 UTC, c=3219.1)** — a sweep+reclaim + 15M micro-thrust confirmation. The raw bar-by-bar tells the whole story:

- **The flush (bars −2, −1):** two big-bodied red bars, body −1.29 then −1.31 ATR, on RISING volume (3912 → 5003). This is the terminal velocity spike / climax flush into the low — Angle 4 L7 `downleg_gap_velocity_spike` (last down-bar range 1.72 ATR ≥ 2× the quiet mid-leg bars at −5..−3 of ~0.5–0.7 ATR).
- **The low bar (+0, 12:00):** opens 3205.5, drops to 3201.67 (sweeps the −1 low at 3203.5 = **shallow stop-run, sweep_depth 1.76 ATR**), then **closes GREEN at 3206.77, close-position 0.62, lower-wick 0.47**. Volume 4486 — *lower* than the −1 flush bar (5003). This is absorption: max effort on the bar before, then the flush bar itself closes back up on declining volume = sellers spent, buyers stepped in (Angle 0 L4 `absorption_reload` / L8 `vol_drain_into_low`).
- **Bar +1 (12:15) = the trigger:** body **+1.84 ATR**, range 2.43 ATR, **closes 0.94 of its range (3219.1)** and reclaims back above the entire flush (above the −1 open 3214.3 and the demand zone). This is the **bullish engulfing thrust** (Angle 4 L6) and the **front-loaded reclaim jerk** (Angle 4 L2 — +1.84 then +1.11 in the first two bars do the bulk of the move).

So the actual mechanic: **shallow sweep of the immediate prior low (3203.5) → absorptive green close at the low → 15M reclaim/engulf thrust on bar +1.** `entry_mechanics` confirms it numerically: `swept_prior_low=1`, `first_higher_low_bar=1`, `reclaim_ema_bars=2`, `nas_long_after=1`. Entry at +1 close captures ~4 ATR of remaining run with the structural invalidation just below 3201.67 (mae after entry was only 0.30 ATR — the floor never gave back).

**Floor goes UP every bar (no-look-back):** lows 3201.7 → 3203.7 → 3218.4 → 3224.0 (reaction l_atr 0.30 → 2.50 → 3.32 → 2.91) = Angle 4 L1 `reclaim_low_monotone_k` run of 3–4. Angle 4 L5 `close_progression_R2`: c_atr 2.59→3.70→3.74→4.10 = a near-straight clean ramp, high R².

---

## (b) LENSES PRESENT / STRONG here

**STRONG (core of the read):**
- **Angle 4 L1 monotone climbing floor + L2 front-loaded jerk + L6 engulf thrust + L5 clean-ramp R²** — the bar-by-bar reclaim is the textbook staircase, the strongest single signature of this fund.
- **Angle 0 L7 liquidity_grab_no_followthrough** — shallow sweep (1.76 ATR) of 3203.5, reclaimed within 1 bar.
- **Angle 0 L4 absorption_reload / L10 rsi_holds** — low bar closes upper-half on volume; RSI 27.3 is washed but *not* extreme-extreme (rsi_min8 27.3), and immediately hooks up (29.2 at +1).
- **Angle 5 L5.6 multi-TF demand stack** — `in_demand=1` on both 15M (E1) and 4H (`htf4_native.in_demand=1`, dist −0.16); `demand_virgin=1`; flush lands exactly ON aligned 4H demand.
- **Angle 5 L5.1 / L5.8 phase-lag**: 1D trend is already +1 (`hd_trend=1`, hd_slope +4.45, hd_rsi 54.3) while 4H/1H still −1 — the **Daily has turned bullish, the lower frames are flushing into it**. This is the constructive HTF backdrop (a slightly different flavor than the canonical 1H-leads-4H, here it's 1D-leads).
- **NAS confluence:** `nas_long_16=1`, `nas_short_16=0`, low-bar nas_dist −5.0, `nas_long_after=1` — a fresh NAS-LONG arms exactly at the reclaim.
- **Sell-bubble exhaustion (Angle 0 L3):** `sell_bub_w=21` with `sell_decel=-15` — heavy sell-bubble effort that is DECELERATING into the low (the −15 decel is the drop-off signal, not the level).

**PRESENT but mixed / against the textbook profile:**
- **Capitulation, NOT the "quiet absorption" archetype.** The angle-catalog headline (Angles 0/1/2) says MON bottoms are *quiet, shallow, off-killzone, calm-vol*. This fund is the OTHER kind: it bottoms with `vol_climax=1.40`, `range_exp=1.37`, `drop20_atr=5.24` (deep), session=**NY at 12:00 UTC (NY open / killzone)**, on a real two-bar flush. So Angle 1 L1 (off-killzone) and the "quiet_climax" lens are ABSENT/INVERTED here. This is a **NY-open capitulation-and-reclaim monster**, not an Asia-grind monster.
- `atr_regime=0.97` and `atr_compression_pre=0.86` are middling — the coil/drain lenses (Angle 2) are weak-to-neutral.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is the archetype the catalog UNDER-weights:** a clean MONSTER born from a genuine NY-open capitulation flush + instant absorptive reclaim — the opposite of the "quiet Asia absorption" thesis that dominates the 61-vs-144 grounding. The edge here is NOT timing/quietness; it is the **velocity asymmetry at the pivot** (sharp flush down → sharper engulf up, Angle 4 L4 `flush_then_snap`).
2. **HTF is led by the DAILY, not the 1H.** Most MON funds show 1H-leads-4H; here the 1D is already trending up (+1, rsi 54, slope +4.45) while 1H/4H are still bearish and oversold. The 15M flush is a deep retrace INTO an intact daily uptrend — a higher-timeframe dip-buy, not a counter-trend bottom.
3. **Demand-on-demand with a defended floor:** 15M in-demand ∧ 4H in-demand ∧ demand_virgin ∧ shallow-sweep-reclaim. The overhead is congested (`n_supply_overhead=141`, `dist_supply_atr` only 0.17, `clean_sky` 0.43 ATR on 4H) — yet it still ran 4.72 ATR, because the DAILY draw (54 RSI, rising) pulled it through the near supply. The runway came from the HTF magnet, not from a clean local sky.
4. **MAE ≈ 0 post-entry:** entering at the +1 reclaim, price never came back to threaten — a true no-look-back launch (monotone climbing floor run of 3+).

---

## (d) MACRO / HTF CONTEXT (as-of, causal)

- **Daily:** UPTREND (`hd_trend=+1`), RSI 54.3, slope +4.45 ATR, position 0.46 in range, price −8.2 ATR below the daily reference but daily structure intact and rising. **This is a dip inside a daily bull.**
- **4H:** still bearish (`h4_trend=−1`, RSI 30.5, slope −4.07), price flushed −11.6 ATR / pos 0.02 — i.e. 4H is washed and oversold and IN its demand zone (native dist −0.16, in_demand=1). 4H clean_sky only 0.43 ATR (near supply overhead).
- **1H:** bearish (`h1_trend=−1`, RSI 24.7, slope −2.62), pos 0.03, in-demand — fully oversold/flushed.
- **Macro flags:** `macro_bear=1`, `macro_bull=0` on the lower frames — the lower-TF tape is bearish/oversold, which is exactly why this is a *flush into daily demand*, not a fresh-trend continuation. The convergence that makes it a MONSTER: **daily-bull pulling up + 4H/1H washed-out at aligned virgin demand + NAS-LONG firing + a shallow-sweep absorptive reclaim with engulf thrust.**

---

**One-line:** MONSTRO — NY-open two-bar capitulation flush that sweeps the prior low (3203.5) and closes green in absorption, then the bar +1 bullish-engulf thrust (+1.84 ATR, close 0.94 of range) reclaims it — ENTER at the +1 reclaim close (~3219), into an intact daily uptrend with NAS-LONG confirming; no-look-back monotone-floor launch (mae≈0, mfe 4.7 ATR).
