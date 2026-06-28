# Fund 41 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block** 2025-02-25_to_2025-05-25 · **Low bar** 2025-05-20 03:00 UTC (t=1747710000) · **Tier** FORTE · **Power** 5.9 · **leg_atr** 22.89 · **Year** 2025 · **Session** ASIA · raw idx 5449.

Low = 3204.6, close-of-low = 3211.3 (close_pos 0.85), ATR ≈ 6.15. mfe12 = 2.49 ATR, mae12 = 0.38 ATR (it barely went against you after the close-of-low). This is a **shallow-MAE, grind-base** bottom that lifts ~2 ATR over 12 bars — a FORTE, not a monster V.

---

## (a) ENTRY MECHANIC — where/when I actually enter

**This is NOT a sweep-and-snap. It is a quiet Asia grind-flush into a defended 4H/1H demand stack, that bases for ~7 bars then leans on its EMA.** Reading the raw reaction bar-by-bar:

- Down-leg: clean grind 01:15 (3230) → 03:00 low (3204.6), ~8 bars, no climax bar (low-bar vol 4133 ≈ prior bars 4250/4093, not a spike). RSI washes 53→27.
- **Bar +0 (the low, 03:00):** opens 3206.7, pokes 3204.6, **closes 3211.3 in the top 85% of its own range** — a same-bar absorption/rejection. `swept_prior_low=1`: it dipped under the local pool then closed back up. RSI 27 is the trough.
- **Bars +1..+6: a tight base** (3206.9–3215), lows holding ~3206–3211, never re-breaking 3204.6. This is the *retest-holds* phase, NOT a thrust. `first_higher_low_bar=1` but shallow.
- **Bar +7 (04:45):** close 3217.0 finally **reclaims EMA21 (3216.8)** — `reclaim_ema_bars=7`. This is the cleanest, most causal trigger this bottom offers.

**My entry:** the structural-low close (bar +0) already gives a strong-close + washed-RSI + swept-prior-low + landing inside stacked demand — an aggressive scale-in is defensible there because MAE is tiny (0.38 ATR). But the **decisive, rule-clean entry is bar +7, the EMA21 reclaim**, after the base held the low for 6 bars. SL goes just below 3204.6 (≈ −1.2 ATR of risk from the EMA reclaim). There is **no 15M CHoCH and no 15M NAS-LONG** after the low (`choch_15m_after=0`, `nas_long_after=0`), so the EMA reclaim + held base IS the trigger — do not wait for a CHoCH that never prints.

**Honest caveat:** entering at bar +7 you've given back ~6 of the ~12 ATR of post-low travel to confirmation; this bottom *pays the patient*, not the early-aggressive, unless you trust the close-of-low absorption.

## (b) Lenses PRESENT / STRONG here

**Strongly present (the spine of this read):**
- **Angle 5 — STACKED-FLOOR / phase-lag is the dominant signature.** `htf4_native.in_demand=1` AND `htf1_native.in_demand=1` with `htf1.dist_demand_atr=2.09` and **clean_sky 2.17 ATR on 1H / 0.27 ATR on 4H** → 15M flushed into a nested 4H+1H demand floor (L5.6). `h1_pos=0.11`, `h4_pos=0.69` — 4H already mid-range/lifting (`h4_slope_atr=+1.33`, the 4H is curling up) while 1H/1D still −1. This is exactly L5.1's **1H/4H phase-lag** geometry (slow frame turning, room above). `htf1.choch_rec=1` — a recent 1H CHoCH already armed the slow frame.
- **Angle 1 / Angle 0 — QUIET, off-headline auction.** `killzone=0`, **session=ASIA, 03:00 UTC** — squarely in Angle 3's 2.3×-enriched Asia/late window and Angle 1's off-killzone polarity (the single strongest discriminator, lift 8.1× in combo). `vol_climax=1.31` and `sweep_depth_atr=1.55` are both on the QUIET side → Angle 0 L2 `quiet_climax` and Angle 1 Lens 1 fire.
- **Angle 1 Lens 6 — discount-not-breakdown.** `dealing_range_pos=-0.511`: in the discount third but NOT range-broken (> −1) — accumulation band, not continuation.
- **Demand quality.** `in_demand=1`, `demand_fresh=1`, `demand_virgin=1`, `n_demand_near=65` — fresh, untouched, well-supported floor. `smc_bos=1`.
- **Sell-effort drying.** `sell_bub_w=2` (thin), `sell_decel=-2`, `buy_bub_w=0` → Angle 0 L3 `sell_bubble_exhaustion_gap` direction (supply fading, though no buy-bubble print yet).
- **Same-bar absorption.** `low_closepos=0.85` (strong close-in-range at the low) → Angle 0 L4 `absorption_reload` direction; `lower_wick_ratio=0.27` (modest wick, MONFORTE-typical).

**Present but WEAK / mixed (be honest):**
- **RSI is genuinely washed here (`rsi_low=rsi_min8=27.2`).** This *contradicts* the MONFORTE "not-deeply-oversold" prior (Angle 0/5 expect rsi_min8 ~35). So Angle 0 L10 `rsi_holds_above_floor` does NOT fire — this bottom is more oversold than the archetype.
- **ATR is EXPANDING into the low (raw atr 4.26→6.15), not contracting.** So Angle 2 L1 `atr_decel_into_low` and Angle 5 L5.4 `compressed_regime_onset` are only half-true: `atr_regime=1.26` is on the HIGH side and `atr_compression_pre=0.54` is LOW — the coil/compression thesis is WEAK here. This bottom formed on still-elevated vol, not a drained coil.
- **Reclaim is a GRIND, not a staircase.** Angle 4's monotone-floor / front-loaded-jerk / hard-flip lenses are WEAK: lows dip back (bar +2 = 3206.9, bar +10 = 3210.3), reclaim takes 7 bars, no engulfing thrust bar. The shape is a rounded base, not a sharp V (consistent with FORTE-not-MON).
- **No NAS at all** (`nas_long_16=0`, `nas_short_16=0`, htf nas_long_rec=0) → Angle 5 L5.7 NAS hand-off absent.

## (c) What is DISTINCTIVE about this bottom

1. **It is a HTF-structure bottom, not a microstructure bottom.** The edge is almost entirely cross-TF positional (Angle 5): a 15M flush landing inside a *nested 4H+1H demand* with the 4H already slope-up (+1.33) and clean sky above — while the 15M reaction itself is unremarkable (grindy, no thrust, no CHoCH/NAS). If you read only the candle anatomy you would underrate it.
2. **Quiet timing + washed RSI is an unusual combo.** It nails the Asia/off-killzone/quiet-auction profile (Angle 1/3) yet is *deeply* oversold (RSI 27) — most MONFORTE are quiet AND not-very-oversold. So it sits at the intersection: quiet liquidity event + real momentum capitulation. The deep RSI + tiny MAE (0.38) says the capitulation was absorbed instantly.
3. **The base holds the low to the tick for 6 bars (low_revisit=1, mae12=0.38).** Defended-floor reading: this is a level actively held across the Asia base, the durable-floor pattern (Angle 3 L8 low-revisit-clock) — the launch comes off a tested floor, not a one-touch wick.
4. **It REJECTS the coil/compression archetype.** Vol was still expanding into the low (rising ATR), so this is the exhaustion-by-absorption (loud-then-held) variant, not the drained-coil variant. Worth flagging because a compression-gate would FILTER THIS BOTTOM OUT.

## (d) Macro / HTF context

- **1D and 1H are bearish, 4H is turning** (`hd_trend=-1`, `h1_trend=0`/native −1, `h4_trend=0` but `h4_slope_atr=+1.33`, `h4_pos=0.69`). Classic phase-lag: fast/mid frame curling up first into a still-bearish daily. `hd_dist=-7.56`, `hd_slope_atr=-4.25` — daily well below its anchor and still sloping down → the 15M long here is a **counter-daily mean-reversion bounce into a nested demand**, which fits FORTE (good leg) rather than MON (regime turn). Expect the leg to run toward 1H/4H value, not a full trend reversal.
- **No macro flag** (`macro_bull=0`, `macro_bear=0`) — neutral macro regime, neither tailwind nor headwind; the trade lives on local demand + phase-lag, so manage as a defined-risk bounce (target the overhead 1H magnet / clean_sky 2.17 ATR), not a let-it-ride monster.

---

### Convergence verdict
Strong on: **nested HTF demand + phase-lag (Angle 5 L5.1/L5.2/L5.6)**, **quiet Asia off-killzone auction (Angle 1/3)**, **discount-not-broken + fresh/virgin demand**, **same-bar absorption (close_pos 0.85)**. Weak/absent on: **compression-coil (Angle 2)**, **monotone-staircase reclaim (Angle 4)**, **not-oversold-RSI**, **CHoCH/NAS confirmation**. Net: a *positional* FORTE bottom whose edge is HTF location + quiet timing, captured cleanly at the **bar +7 EMA21 reclaim** off a 6-bar held base.
