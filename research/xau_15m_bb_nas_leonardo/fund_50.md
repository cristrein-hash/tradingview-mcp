# Fund 50 — DEEP READING (XAU 15M MON+FORTE bottom)

- **Block:** 2024-08-25 | **Date:** 2024-10-17 12:30 UTC | **Tier:** FORTE | **Year:** 2024
- **leg_atr:** 19.21 | **power_score:** 4.7
- **Bottom bar (raw):** o 2679.31 / h 2679.31 / l 2673.07 / c 2676.25 / v 6408 / atr 3.51
- **Entry-window outcome:** mfe12 6.75 ATR, mae12 0.84 ATR (clean — barely any heat after entry)

This bottom is a **NY-session pullback-in-uptrend that bottoms on a single climactic flush bar landing on a fresh same-day demand zone, then snaps up in a near-perfect monotone staircase.** It deliberately CONTRADICTS the "quiet absorption / Asia / off-killzone" FORTE archetype that several angle catalogs describe — and that contradiction is exactly what makes it instructive: it is the *flush-then-snap-V* face of FORTE, not the quiet-coil face.

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

**Sequence, bar by bar (causal, only info ≤ each bar):**

- Bars −3…−1 (11:45→12:15): controlled grind down off a local high ~2688, RSI sliding 55.6 → 46.8 → 44.0, volume building (3389 → 3464 → **4108**). Sellers pressing but `downleg_eff` is only **0.19** = grindy, two-sided, NOT a clean cascade.
- **Bar 0 (12:30) = the climax flush:** opens at its high (2679.31), pukes to **2673.07**, volume explodes to **6408** (biggest of the leg, vol_climax 2.21), atr ticks up to 3.51. This bar SWEEPS the prior local low (`swept_prior_low=1`, `sweep_depth_atr` 1.1 — shallow) and CLOSES off the low at 2676.25 (low_closepos 0.51, lower_wick_ratio 0.51 = half the bar is rejection wick). It lands directly inside a **demand zone born the SAME DAY (2674.41 / 2673.27, born 10-17)** — `in_demand=1`, `dist_demand_atr 0.12`, `demand_fresh=1`, `demand_virgin=1`.
- **Bar +1 (12:45) = the trigger.** Green engulfing reclaim: c 2680.6, takes back the entire bar-0 puke AND the −1/−2 down-bars in one bar. **A 15M bullish CHoCH prints here (smc id 4951 @ 2676.92)** = `choch_15m_after=1`. This bar is also the first higher-low (`first_higher_low_bar=1`) and price has reclaimed EMA21 within 2 bars (`reclaim_ema_bars=2`, ema ≈ 2681.9).

**My entry = the close of bar +1 (12:45), price ≈ 2680.6.** The trigger that I act on is the **sweep + instant single-bar reclaim + 15M CHoCH-up**, all confirmed by bar +1's close. I do NOT wait for the EMA-retest; the engulf-reclaim that simultaneously prints the CHoCH IS the confirmation. Trigger taxonomy: **sweep+reclaim → engulfing-thrust → CHoCH**, in that order, all inside one bar.

- **SL:** below the flush low 2673.07 (the demand-zone floor) — risk ≈ 7.5 pts ≈ 2.1 ATR from the +1 close. The leg then never looks back: bar-low climbs every bar (2676.02 → 2677.62 → 2681.67 → 2681.11…), so `mae12` after entry is only 0.84 ATR. The retest is shallow and holds (no re-test of 2673). Let-run target: the leg ran +6.75 ATR by bar 12 and the leg total is 19.21 ATR — a monster. Overhead is clean (a fresh 2686.83/2688.82 demand-flip zone is the only near structure; `n_supply_overhead=9` modest, `clean_sky_atr=99` on both HTF natives).

---

## (b) LENSES PRESENT/STRONG here

**STRONG / PRESENT (the ones that actually fire on this fund):**

- **Angle 4 — inter-bar geometry (this is the dominant signature):**
  - **L1 reclaim_low_monotone_k = MAX.** Bar-lows climb every single reaction bar (2676.02→2677.62→2681.67→2681.11→2685.73→2684.53…) — a textbook climbing-floor, no-look-back launch.
  - **L6 pivot_engulf_thrust = STRONG.** Bar +1 engulfs the prior down-bars and closes above bar-0's high → +1.4 ATR thrust off the low.
  - **L4 flush_then_snap = STRONG.** Sharp flush in (flush_v_ratio 0.24), up-velocity matches/exceeds it (c reaches +2.61 ATR by bar 2).
  - **L7 downleg_gap_velocity_spike + flush_reversed_next = STRONG.** Bar 0 is the biggest-range/biggest-volume bar of the leg and the very next bar reverses green.
  - **L5 close_progression_R2 = STRONG.** c_atr 2.14→2.61→2.88→3.83→4.43→4.81 is a near-straight monotone ramp (high R²).
  - **L9 velocity_regime_flip = STRONG.** Steep down-slope inverts hard into a steep up-slope.
- **Angle 1 — liquidity/auction:** **Lens 1 QUIET-RECLAIM partial** — `killzone=0` (off the London/NY kill windows even though it is the NY session). **Lens 3 liquidity asymmetry STRONG** — floor is right under price (dist_demand 0.12) and overhead is thin (n_supply 9), so support ≪ supply distance. `swept_prior_low=1` shallow + reclaimed = the engineered-grab footprint.
- **Angle 5 — cross-TF momentum:** **L5.6 multi-TF demand stack PRESENT** (15M flush lands on fresh demand, clean sky above on both HTF natives, `clean_sky_atr=99`). **L5.9 CHoCH-in-constructive-structure STRONG** (15M CHoCH-up nested in fully bullish HTF). NOTE the phase-lag lenses (L5.1/L5.2) are INVERTED here vs the catalog: all HTF frames are ALREADY bullish (h1/h4/hd trend = +1), so this is not a "1H-leads-bearish-4H" turn — it is a continuation pullback with the whole stack already up.
- **features_E1 / entry_mechanics:** `buy_bub_w=5, sell_bub_w=0` (buy-bubble footprint present, sell desert → Angle 0 L3 sell_bubble_exhaustion_gap + L9 buy_bubble_first_print PRESENT). `macro_bull=1`. `consec_down=5`, `drop20_atr 4.49`.

**WEAK / ABSENT / INVERTED (honest contradictions):**

- **Angle 0 / 2 / 3 "quiet-absorption" thesis is INVERTED here.** This bottom is the LOUD, climactic kind those angles say marks the *control* set: `vol_climax 2.21` (high, not the MON-median 1.23), `atr_regime 1.23` (expanded, not <1.0), `range_exp 1.89`. So Angle-0 L2 quiet_climax and Angle-2's drained/coiled lenses would FAIL or fire weak. The fund is FORTE *despite* being climactic — the geometry (Angle 4) and the demand-stack (Angle 5) carry it, not the calm-vol lenses.
- **Angle 3 session lenses INVERTED:** it is NY session (the depleted-in-strong bucket), not Asia. Saved only by `killzone=0`.
- **No NAS support:** `nas_long_16=0`, `nas_short_16=0`, HTF `nas_long_rec=0` → Angle 5 L5.7 absent.
- **RSI not deeply oversold:** `rsi_min8=44` (no `rsi_bull_div`). The "non-oversold bottom" lens (Angle 0 L10) is satisfied trivially but for the wrong reason — it's a shallow pullback, not a washed-out reversal.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is the climactic-V exception to the FORTE rule.** Most catalogs frame FORTE as quiet/coiled/Asia/off-killzone. Fund 50 is the opposite: a high-volume NY climax flush. The lesson — **geometry (monotone climbing floor + clean R² ramp + engulf thrust) and the fresh-demand-stack can manufacture a FORTE leg even when the vol-regime/session lenses say "control."** A detector that REQUIRES quiet-absorption would miss this one.
2. **The demand zone was born the SAME DAY (10-17) and the flush hit it to the tick** (low 2673.07 vs zone 2673.27/2674.41). Fresh + virgin + first-touch defended floor = the launchpad.
3. **The reclaim is one of the cleanest possible:** single-bar engulf + CHoCH on bar +1, then 11 straight bars where the floor never sags. `mae12=0.84 ATR` — almost zero post-entry heat. This is a "no-look-back" leg.
4. **Everything is bullish-aligned across TF (h1/h4/hd all +1)** — so the trade is a *trend pullback*, the highest-confidence flavor, not a counter-trend reversal call.

---

## (d) MACRO / HTF CONTEXT

- **Daily (hd):** trend +1, rsi 64.0, slope +3.75 ATR, pos 0.89, dist +10.75 ATR — strong daily uptrend, price high in its daily range. (Oct 2024 gold parabolic run-up.)
- **4H (h4):** trend +1, rsi 65.5, slope +2.32 ATR, pos 0.75, eff 0.48 — clean, efficient 4H uptrend with momentum; not overhead-pinned (native `clean_sky_atr=99`, `in_demand=0`, `dist_demand 0.8`).
- **1H (h1):** trend +1, rsi 55.4, slope +0.67, pos 0.44, eff 0.05 — 1H cooling/consolidating mid-range (the pullback frame). A 1H CHoCH was recently set (`htf1_native.choch_rec=1`), price a clear ATR above 1H demand (dist 0.72) = room above.
- **Net read:** a strong multi-TF bull. The 15M flush at 12:30 NY is a liquidity grab into a fresh 15M demand inside an intact higher-TF uptrend, instantly reclaimed. The HTF gives the *fuel + clean runway*; the 15M sweep+CHoCH gives the *timed trigger*. Classic buy-the-dip in a trending market, with the entry precision-located by the same-day demand zone.

---

**1-line summary:** FORTE — entry on close of bar +1 (12:45, ~2680.6) on a **shallow sweep + single-bar engulfing reclaim + 15M CHoCH-up off a fresh same-day demand zone** inside a fully bullish HTF stack (climactic-V flavor, not the quiet-absorption archetype).
