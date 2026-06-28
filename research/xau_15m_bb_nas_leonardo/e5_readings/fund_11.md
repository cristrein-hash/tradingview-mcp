# Fund 11 — Deep Reading (MONSTRO, 2025-10-03 03:30 UTC, block 2025-08-25)

**Tier:** MONSTRO · power_score 8.5 · leg_atr 39.24 · year 2025
**Outcome:** mfe12 4.08 ATR / mae12 0.23 ATR — near-perfect MFAE asymmetry (price almost never traded below the entry floor after the turn).

---

## (a) THE ENTRY MECHANIC — where/when I actually enter

Raw bar-by-bar (confirmed from `series`):

```
03:00  l3845.1 c3847.8  rsi38   (grinding down)
03:15  l3839.8 c3839.9  rsi37   (down-bar, close-on-low)
03:30  l3838.0 c3841.0  rsi29   v5319  <<< LOW BAR — closes in UPPER HALF of its own range (c3841 of 3838-3842.4), RSI 29
03:45  l3839.3 c3842.9  rsi31   v4916  GREEN — first higher-low (l 3839.3 > 3838); NAS LONG fires @03:45 (price 3836.94)
04:00  l3841.7 c3845.3  rsi35   GREEN — second higher-low, lows climbing
...
05:15  l3850.4 c3853.9  rsi51         <<< EMA21 reclaim (c3853.9 > ema21 3849.7) = reclaim_ema_bars 6
06:10  CHoCH-up prints @3859.95         (structural confirmation, late)
```

**Entry decision — the trigger is a SWEEP-FAILURE + HIGHER-LOW + NAS-LONG hand-off, NOT a deep-flush capitulation:**

- The 03:30 low bar is itself the tell: it pierces the 03:15 down-bar low fractionally, RSI dumps to 29 (the lone washed print), yet it **closes in the upper half of its own range** (low_closepos 0.68) on the largest volume of the leg (v5319) = absorption-on-the-flush. That is the "one puke then strong close" footprint.
- **I enter on the +1 bar (03:45)** when (i) the first higher-low confirms (l 3839.3 > 3838, `first_higher_low_bar=1`) AND (ii) the **NAS-LONG prints at 03:45** (id 1593, dir LONG @3836.94). The NAS-LONG hand-off on the very next bar is the discrete, causal trigger — it converts the strong-close low into an actionable long.
- **SL** sits just under the 03:30 low / under the 3824.72-3819.08 demand zone (the prior-session-low demand born Thu 16:30). MAE was only 0.23 ATR, so the entry floor was never threatened.
- A more conservative entry exists at the **EMA21 reclaim (05:15, +6 bars)** or the CHoCH (06:10), but both give back ~12-15 pts of the leg; the leg is huge (39 ATR) so either still captures most of it. **Best causal entry = +1 bar NAS-LONG into the higher-low.**

---

## (b) Lenses PRESENT / STRONG here

**Order-flow (Angle 0):**
- **L2 quiet_climax = STRONG (3/3):** vol_climax 1.18 (<1.35), sweep_depth 1.65 (<1.8), lower_wick_ratio 0.45 (~boundary). Modest-everything low = the MON fingerprint.
- **L4 absorption_reload = PRESENT:** the 03:30 low bar is the volume peak of the leg (v5319) and closes in the upper half (close_pos 0.68) — high-volume strong-close = positive-delta proxy.
- **L9 buy_bubble_first_print = STRONG:** `buy_bub_w=2`, `sell_bub_w=0` — buy bubbles printing AND zero sell bubbles at the low. Sell-pressure footprint fully dried up (L3 exhaustion gap maxed).
- **L10 rsi_holds_above_floor = WEAK/borderline:** rsi_min8 29.3 (this one IS oversold, slightly below the MON-typical 35) — the only "loud" signature here.

**Liquidity / Auction (Angle 1):**
- **L1 QUIET RECLAIM = STRONG (the headline 8.1× lens):** `killzone=0`, session ASIA, and the low is **NOT the lowest of trailing 50** (3838 > the 3819 low set 44 bars prior). It undercuts only a local pool, then reclaims — exactly the off-killzone non-headline reversal.
- **L3 LIQUIDITY ASYMMETRY = PRESENT:** dist_demand 0.67 ATR (floor near, in_demand=1), supply 0.26 — but n_supply_overhead=30 is heavier overhead; floor is well-defended (demand_fresh=1, demand_virgin=1).
- **L6 DISCOUNT-NOT-BREAKDOWN = STRONG:** dealing_range_pos −0.738 (deep discount band, but NOT a range break beyond −1.0). Buy-the-discount, not chase-the-break.

**Volatility-structure (Angle 2):**
- **L1 atr_decel / calm regime = PRESENT:** atr_regime 0.98-1.1 (calm), atr_compression_pre 0.63 (moderate). Forms in a controlled, not panic, vol state.
- **L5 inefficient drop = STRONG:** downleg_eff 0.38, flush_v_ratio 0.30 — grindy, vol-churning descent (two-sided fighting → buyers already present).

**Time / Session (Angle 3) — VERY STRONG, the standout dimension:**
- **L1 asia_offpeak_flush + L3 first-session-hour:** Friday **03:30 UTC, ASIA session, off-killzone** — the precise 2.3×-enriched MON+FORTE window. Mid-week-to-Friday (not week-open). This is the single most on-profile lens for this fund.

**Inter-bar geometry (Angle 4) — VERY STRONG:**
- **L1 reclaim_low_monotone = STRONG:** post-low bar lows climb monotonically (3839.3 → 3841.7 → 3843.2 ...) — no-look-back staircase, lows never revisit the 3838 floor.
- **L5 close_progression_R2 / L8 shallow_retest = STRONG:** clean rising reclaim; the first pullback (04:45 dip to 3843.4) holds far above the low (shallow retest). MAE 0.23 ATR confirms.
- **L6 pivot_engulf_thrust = PRESENT:** 03:45 green bar reclaims above the prior down-bar.

**Cross-TF momentum / regime-onset (Angle 5) — DEFINING:**
- **L5.1 HTF Phase-Lag Turn = STRONG:** `htf1_native.trend=+1` (1H already turned bullish) WHILE `htf4_native.trend=−1` (4H still bearish) — the canonical 1H-leads-4H phase lag. h4_trend=1 in E1 (resample) but native-4H reads −1: the slow frame still has room/no overhead 4H supply mitigated.
- **L5.4 Compressed-Regime Onset = PRESENT:** atr_regime ~0.98 (sub-1.0).
- **htf1 RSI / hd_trend context:** Daily strongly bullish (hd_trend=1, hd_rsi 84.5, hd_slope +12.6) — the higher-TF macro is in a powerful uptrend; this 15M flush is a pullback INTO a daily bull, the highest-quality long context.

---

## (c) What is DISTINCTIVE about this bottom

1. **It is a HIGHER-LOW retest of fresh prior-session demand, not a fresh capitulation low.** The deeper low (3819.08) was set 44 bars earlier (Thu 15:30); this 3838 low holds ABOVE it, on top of the 3824.72-3819.08 demand zone born at the prior-session low (Thu 16:30). Structurally this is "second test holds higher" = accumulation, the strongest reversal geometry.
2. **NAS-LONG hand-off on the immediate next bar** is the clean discrete trigger — rare and time-aligned (Angle 3 L6: recent + off-killzone NAS).
3. **Daily-bull pullback.** Unlike a counter-trend bottom, this is a pullback inside a roaring daily uptrend (hd_rsi 84.5) — the leg has macro tailwind. That is why it ran 39 ATR with MAE 0.23.
4. **Quiet on every loud axis** (volume, sweep, wick all modest) but **loud on RSI** (29.3) — the one slightly off-profile feature. The grindy 0.38 downleg_eff + strong-close flush bar reconcile it: oversold by RSI, but absorbed by price.

---

## (d) Macro / HTF context

- **Daily:** strong bull (trend +1, RSI 84.5, slope +12.6, pos 0.80, dist +19.2 ATR above demand) — extended but powerfully trending. This flush is a pullback within it.
- **4H:** native trend −1 (still-bearish micro-pullback) / E1 resample +1 with h4_eff only 0.12 (flat/choppy 4H) — i.e. 4H is mid-pullback with room overhead, no 4H supply yet mitigated → the leg has air.
- **1H:** trend +1 ALREADY turned bullish (the phase-lead), rsi 43.4 recovering, sitting above its demand → the fast frame has reclaimed while 15M flushed.
- **Confluence stack:** Daily-bull + 1H-turned-up + 15M flushed into fresh defended demand + Asia off-killzone + NAS-LONG trigger + monotone staircase reclaim = the convergent MON+FORTE template.
