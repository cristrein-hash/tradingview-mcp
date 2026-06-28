# Fund 19 — DEEP READING (XAU 15M MON+FORTE bottom)

- **Block:** 2025-02-25 · **Date/time:** 2025-03-14 20:00 UTC · **Tier:** MONSTRO · **Year:** 2025
- **leg_atr:** 31.6 · **power_score:** 4.8 · **mfe12_atr:** 5.19 · **mae12_atr:** 0.24

---

## TL;DR
A MONSTRO bottom that is the **purest counter-example to the "quiet-flush / capitulation"
groundings of all six angle catalogs.** There is **no sweep, no flush, no oversold** here.
This is a **shallow demand-pullback inside a powerful, already-bullish trend on BOTH HTFs**
(4H near top of range, h4_rsi 69.9, h1_trend up) that lands on a **fresh/virgin 4H-aligned
demand zone** and detonates. The entry is a **demand-retest + fast EMA reclaim + 15M CHoCH**,
NOT a sweep-and-reclaim. The leg's fuel is **trend continuation into clean sky**, not exhaustion.

---

## (a) THE ENTRY MECHANIC — where/when I actually enter

Reading the `reaction_seq` (bars w=1..12, ATR-normalised) bar-by-bar from the low:

| w | c_atr | h_atr | l_atr | green | read |
|---|------|------|------|-------|------|
| 1 | 0.48 | 0.84 | 0.24 | 0 | low printed, tiny red bounce, bar LOW only 0.24 ATR off the bottom |
| 2 | **2.52** | 2.63 | 0.28 | 1 | **explosive thrust +2.04 ATR close-to-close — the engulf/CHoCH bar** |
| 3 | 2.75 | 2.91 | **2.28** | 1 | floor jumps to 2.28 — price never looks back |
| 4 | 3.41 | 3.70 | 0.90 | 1 | continues |
| 5 | 2.74 | 3.59 | 2.43 | 0 | shallow pullback, low HOLDS at 2.43 (>> original low) |
| 6 | 3.50 | 3.57 | 2.21 | 1 | reload |
| 7 | 3.05 | — | 2.90 | 0 | |
| 8 | 3.79 | — | 2.68 | 1 | |
| 9 | **5.12** | 5.15 | 3.82 | 1 | second leg, prints the mfe |
| 10–12 | 4.29→2.81 | | | 0 | give-back / exit zone |

**Entry decision:** The low (w=0) is a tiny-range red/indecision bar (bar1 only travels 0.24 ATR
off the bottom — `mae12_atr=0.24` confirms the bottom is *the* low and is never threatened again).
I do **not** enter on the low bar — there is no sweep+reclaim trigger there (`swept_prior_low=0`,
`sweep_depth_atr=0.0`). The real, confirmable trigger is **bar w=2**: the +2.04 ATR thrust bar that
(i) reclaims the 15M EMA21 (`reclaim_ema_bars=2`), (ii) prints the **bullish 15M CHoCH**
(`choch_15m_after=1`), and (iii) sets the first higher-low structure (`first_higher_low_bar=1`).

> **Entry = on/at close of reaction bar w=2 — the EMA-reclaim + CHoCH thrust off fresh demand.**
> This is a **demand-retest-reclaim**, NOT a sweep-reclaim and NOT a micro-HL scalp. SL goes
> just under the w=0 low (the leg low, only ~0.24 ATR below entry-bar low → tight, structural).
> mfe from there is ~5.19 ATR with essentially zero adverse excursion = a clean staircase leg.

The post-entry trajectory is textbook **Angle-4 staircase**: `reclaim_low_monotone_k` ≈ full
(lows climb 0.28→2.28→… and the only dip, w5 at 2.43, holds far above the low → `reclaim_dip_depth`
shallow), `close_progression_R2` high (near-linear ramp w1→w9), `reclaim_jerk` strongly
**front-loaded** (the whole turn is bar 2). All the Angle-4 SHAPE lenses fire STRONG here even
though the Angle-4 down-leg/anatomy lenses do not (there was no climax flush to taper from).

---

## (b) Lenses PRESENT / STRONG vs ABSENT

**STRONG (the signature of THIS bottom):**
- **Angle 1 / L1 QUIET RECLAIM** — `killzone=0`, session=LATE (20:00 UTC), and the low is NOT a
  headline lowest-of-50 flush. Off-killzone quiet reclaim: PRESENT and strong (matches the
  8.1× lift probe).
- **Angle 1 / L3 LIQUIDITY ASYMMETRY** — `dist_demand_atr=0.59` (floor very near) vs
  `dist_supply_atr=−0.08` … note: supply is essentially AT price on the 15M (`n_supply_overhead=9`),
  BUT the HTF picture overrides: `htf4_native.clean_sky_atr=99`, `htf1_native.clean_sky_atr=99`
  → **clean sky above on both HTFs**. The 15M overhead supply is local noise inside a 4H runway.
- **Angle 5 / L5.6 MULTI-TF DEMAND STACK** — the strongest single read here:
  `in_demand=1`, `demand_fresh=1`, `demand_virgin=1`, `vpnode_dist_atr=0.08` (right on the VP node),
  i.e. 15M flush lands ON a fresh, untested, value-backed demand WITH clean HTF sky above. This is
  the "floor below + air above" launchpad lens, fully PRESENT.
- **Angle 4 SHAPE TRIO** — `reclaim_low_monotone_k`, `close_progression_R2`, `reclaim_jerk`
  (front-loaded), `reclaim_dip_depth` (shallow retest at w5): ALL strong. The leg is a clean
  monotone staircase, not chop.
- **Angle 0 / L9 buy_bubble_first_print** — `buy_bub_w=3`, `sell_bub_w=0`, `sell_bub_L=0`,
  `buy_bub_L=0`: BUY bubbles present, **zero SELL bubbles** = no supply footprint at the low =
  demand stepping in quietly. The `sell_bubble_exhaustion_gap` is total (sells already at zero).
- **Macro alignment** — `macro_bull=1`, `macro_bear=0`, `h4_trend=+1`, `h1_trend=+1`,
  `h1_slope_atr=+0.2` (1H slope already POSITIVE, not just decelerating).

**WEAK / ABSENT (and WHY this matters):**
- **All capitulation / exhaustion lenses fail by design here** — Angle-0 L1/L2 quiet_climax,
  Angle-2 flush_then_freeze / vol_drain, Angle-4 downleg taper / climax flush: there is
  **nothing to detect** because there was no flush. `flush_v_ratio=0.27` (sharp), but
  `drop20_atr=3.64` and `downleg_eff=0.08` with `consec_down=1` → this is a *one-bar shallow dip*,
  not a multi-bar cascade. No `sweep_depth` (0.0), `low_revisit=4` but `lower_wick_ratio=0.69`
  (a healthy buy wick, not a long capitulation tail).
- **RSI is NOT washed** — `rsi_low=43.4`, `rsi_min8=40.7` → far above the oversold floor.
  Angle-0/L10 (`rsi_holds_above_floor`) technically PRESENT in the trivial sense, but the
  underlying reason is "this was never a panic," not "momentum absorbed a panic."
- **Angle-5 phase-lag turn (L5.1) does NOT apply** — the grounding assumed 4H bearish / 1H just
  flipping. Here **both HTFs are already bullish** (h4_trend +1, h4_rsi 69.9, h4_pos 0.78). This
  is NOT a regime-onset bottom; it is a continuation-pullback bottom. The Angle-5 thesis
  ("1H leads 4H out of a bear") is INVERTED for this fund.
- **NAS silent** — `nas_long_16=0`, `nas_short_16=0`, `smc_bos=0`, `htf*.nas_long_rec=0`.
  No NAS hand-off; this bottom did not need a NAS trigger.
- **`atr_regime=0.52`** — even calmer than the MON median (0.94). Deeply compressed vol regime;
  the dip is a small disturbance inside a quiet, trending tape (`atr_compression_pre=1.9`,
  `vol_climax=0.38` very low). Angle-2 "drained-and-coiled" preconditions PRESENT, but again
  via *low energy throughout*, not flush-then-freeze.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is a TREND-CONTINUATION pullback wearing a MONSTRO leg, not a reversal bottom.** Both
   HTFs are already up and strong (h4_rsi 69.9, h4_pos 0.78). The "bottom" is a shallow,
   one-bar, low-efficiency dip (`consec_down=1`, `downleg_eff=0.08`, `drop20_atr=3.64`) into a
   **fresh virgin demand zone** that immediately resumes the trend. This is the dossier's
   counter-example to the "monsters are born from quiet absorption of a flush" thesis — here
   there is no flush at all; the monster is born from **buying a fresh demand retest in an
   accelerating bull**.
2. **Zero supply footprint, full demand footprint at the low:** `sell_bub_w=0` / `buy_bub_w=3`,
   right on the VP node (`vpnode_dist_atr=0.08`), demand fresh+virgin. Supply simply isn't there.
3. **The turn is one explosive bar (w=2).** Almost the entire reclaim is front-loaded into a
   single +2.04 ATR thrust that simultaneously reclaims EMA21, prints CHoCH, and makes the HL.
   Near-perfect Angle-4 staircase afterward (`mae12=0.24`, mfe12=5.19).
4. **Off-killzone, LATE-session, mid-month** — quiet timing (Angle-1/3 enrichment) but for the
   "continuation" reason (institutions reloading in thin liquidity), not the "stop-run flush" one.
5. **Local 15M supply overhead (9 zones, dist_supply ≈ 0) is overridden by clean HTF sky.**
   The leg ran 5+ ATR straight through that local supply because the 4H/1D runway was empty —
   a reminder that overhead-supply lenses must be read multi-TF, not on the 15M alone.

---

## (d) MACRO / HTF CONTEXT

- **4H (native):** `trend=+1`, `rsi=69.9`(E1)/`71.0`(native), `pos=0.78`, `slope_atr=+8.19`,
  `dist=10.68 ATR above its demand`, `clean_sky_atr=99`. → A **strong, near-overbought 4H uptrend
  with clean air above.** The 4H is the driver; this 15M dip is a buy-the-pullback inside it.
- **1H (native):** `trend=+1`, `rsi=53.5`(E1)/`67.8`(native), `pos=0.19`, `slope_atr=+0.20`
  (already positive), `choch_rec=1` (recent 1H bullish CHoCH), `clean_sky_atr=99`. → 1H already
  turned/turning up with a fresh CHoCH and room above; 1H is in the lower part of its short-range
  (h1_pos 0.19) = the pullback is fresh, not extended.
- **Daily:** native daily fields null in the dossier (not resampled), but 4H rsi ~70 + macro_bull=1
  imply a higher-TF bull intact.
- **Regime:** compressed vol (`atr_regime=0.52`), bullish macro flags, fresh virgin 4H-aligned
  demand, clean HTF sky. The macro read is unambiguous: **continuation-up, buy the fresh demand
  retest.** The risk is the near 4H overbought (rsi ~70) — but here it converted to a +5 ATR leg
  because the demand was fresh/virgin and overhead HTF supply was absent.

---

## Convergence summary (causal, only info up to the w=2 entry bar)
Floor (fresh virgin 4H-aligned demand at VP node) + Air (clean HTF sky, both frames) +
Trend (4H/1D bull, 1H CHoCH up) + Quiet timing (off-killzone LATE) + No supply (sell_bub=0) +
Decisive trigger (one +2 ATR EMA-reclaim/CHoCH thrust). **This is a demand-retest continuation
MONSTRO, not a capitulation reversal — the cleanest "buy fresh demand in a bull" fund in the set.**
