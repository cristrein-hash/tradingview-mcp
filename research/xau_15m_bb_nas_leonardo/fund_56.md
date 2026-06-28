# Fund 56 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2024-08-25 → 2024-11-25 | **Low bar:** 2024-10-10 12:30 UTC (NY open +0min) | **Tier:** FORTE | **leg_atr 17.0** | **power 4.7**
**Outcome geometry:** mfe12 7.38 ATR, mae12 3.64 ATR (post-low draw was the single low-bar wick, never revisited).

---

## (a) ENTRY MECHANIC — where/when I actually enter to capture this leg

This is a **single-bar selling-climax → instant V-reclaim** at the NY open. The mechanic is *sweep + reclaim on the climax bar itself*, then confirm.

Raw anatomy of the low bar (+0, 12:30):
- `o=2612.5  l=2601.8  h=2624.3  c=2621.2` — a ~22.5pt range bar where ATR pre-bar was ~2.3. It flushed **10.7pt below the open** then **closed 19.4pt off the low** (close in the top **87%** of the bar, `low_closepos 0.86`).
- Volume `7188` vs ~2500 baseline (**~3× session-relative spike**, `vol_climax 2.79`).
- The low 2601.8 swept **below the prior-200-bar minimum (2604.5)** and the prior-50 low (2605.9) by ~4pt — a true multi-day sell-side liquidity raid (range break, `dealing_range_pos −1.251`, `swept_prior_low=1`).
- A **medium BUY bubble (plot_2) printed on +1 (12:45)**, with plot_0 buy prints already at 10:30–10:45 → demand footprint emerging exactly at the turn (`buy_bub_w 4`).

**Entry decision tree (causal, only info ≤ entry bar):**
1. The cleanest aggressive entry is **on the close of the climax bar +0 (2621.2)**: a wide-range bar that swept the multi-day low and closed in its top 13% under a 3× volume spike = absorption-confirmed reclaim *within the bar*. Risk to below 2601.8.
2. The safer, still-early entry is **+1 close (2625.1)** — the first green continuation bar that *holds above the climax-bar close and never re-tests the low* (`first_higher_low_bar=1`, `choch_15m_after=1`). RSI snapped 43→64.
3. There is **no need to wait for an EMA reclaim** (`reclaim_ema_bars=0` — price closed back above EMA21 on the very low bar). The reaction floor then climbs monotonically (l_atr 4.83→5.82 over bars 1–6) — a no-look-back staircase that confirms the entry was structural, not a dead-cat.

**Chosen entry: +0 close (climax-bar reclaim), stop under 2601.8 (~1ATR risk on the post-climax ATR ≈ 3.8).** The leg ran +7.4 ATR mfe with the worst adverse excursion already behind us (the low bar's own wick).

## (b) Lenses PRESENT / STRONG here

This fund is the **CLIMACTIC / DRAMATIC archetype** — it sits on the *opposite* pole of the "quiet absorption" thesis that dominates the MONFORTE median (Angle 0/1/2). It is the rarer "loud" monster, and the *velocity/geometry* and *cross-TF* lenses are what light up, not the quiet-vol ones.

STRONG / PRESENT:
- **Angle 4 L7 `downleg_gap_velocity_spike`** + **L6 `pivot_engulf_thrust`**: the climax bar is the biggest bar of the leg AND it engulfs and reverses the prior down-bars in one print. Textbook terminal-spike-then-reverse. (PRESENT-STRONG)
- **Angle 4 L4 `flush_then_snap` / L9 `velocity_regime_flip`**: up-velocity ≥ down-velocity at the pivot — the V is symmetric/sharp. `flush_v_ratio 0.14` (very sharp V), `range_exp 10.3`. (STRONG)
- **Angle 4 L1 `reclaim_low_monotone_k` / L8 `reclaim_dip_depth`**: post-low floor climbs every bar (l_atr 4.83→5.82→5.59→5.51, only shallow dips), shallow retest holds far above the low. No-look-back launch. (STRONG)
- **Angle 1 L1 QUIET-RECLAIM polarity** — *partial*: it sweeps a **non-headline local + multi-day pool and reclaims**, but it is **INSIDE the NY killzone** (12:30, `killzone` flag 0 in E1 but session=NY). So the killzone-OFF discriminator does NOT hold here; this is the loud NY-open exception, not the Asia-quiet archetype.
- **Angle 1 L6 DISCOUNT — *inverted/break***: `dealing_range_pos −1.251` is a **range BREAK**, not the −1.0..−0.2 discount band. By Angle-1's logic this would read as continuation-risk — yet it reversed. The override is the *instant reclaim of the broken range* (the break was a stop-run, not acceptance).
- **Angle 5 L5.2 1H Room-Above**: `htf1_native.in_demand=0`, `dist_demand_atr 1.42`, `h1_pos 1.17`, `hd_trend +1` (daily up) — the 1H/Daily already lifted off the floor while the 15M flushed into 4H demand (`htf4_native.in_demand=1`, `dist_demand 0.32`). Multi-TF spring. (STRONG)
- **Angle 5 L5.6 Multi-TF Demand Stack**: 15M flush lands in 4H demand with clean sky (`htf4_native.clean_sky_atr 1.5`, daily `hd` up). Floor below + air above. (PRESENT)
- **Angle 0 L4 `absorption_reload`**: v-spike (7188) with strong close-in-range (0.86) = demand absorbed the climax supply. The delta-proxy flips positive on the low bar itself. (STRONG)

WEAK / ABSENT (and this is the distinctive part):
- **Angle 0/2 quiet-vol family is ABSENT/INVERTED**: `vol_climax 2.79` (loud, not quiet), `sweep_depth_atr 2.51` (deep, not shallow), `drop20_atr 5.92` (deep flush), `atr_regime 1.68` (EXPANDED, not compressed). Every "quiet absorption" lens fires the wrong way — this monster is a *loud capitulation*, the control-set signature that still produced a real leg.
- `rsi_low 42.6` — not deeply oversold, but not the quiet-base profile either.
- `nas_long_16=0`, `smc_bos=0`, `rsi_bull_div=0`, `macro_bull/bear=0` — no NAS/SMC/divergence confirmation; the read is pure price/volume climax geometry.

## (c) What is DISTINCTIVE about this bottom

It is the **anti-archetype**: a *loud, climactic, deep-sweep, expanded-vol* MONFORTE bottom — precisely the profile the quiet-absorption angles (0/1/2) say should be the *weak control set*. Yet it is FORTE with a 17-ATR leg. The reconciliation: it is a **NY-open multi-day liquidity raid that reclaimed inside a single bar**. The discriminator that saves it is not vol-quietness but **velocity symmetry + instant reclaim of a broken range** (Angle 4 family) layered on a **1H/Daily already turned up** (Angle 5 L5.1/L5.2 phase-lag). The bottom is made *against* an HTF that has already decided up — so the 15M climax flush is the last sweep before continuation, not a new downtrend. The single-bar engulf/reclaim makes the entry low-risk despite the deep wick (mae lives only in that one bar).

## (d) Macro / HTF context

- **Daily (`hd`): trend +1, slope +1.43 ATR, pos 0.54, RSI 48** — daily is in an uptrend, mid-range. This is a *pullback into an uptrend*, not a trend reversal — the highest-probability long context.
- **1H (`htf1_native`): trend +1, RSI 52.4, choch_rec=1, ABOVE demand (dist 1.42, in_demand=0)** — fast frame already bullish and structurally turned; the 15M flush is a discount entry beneath an already-up 1H.
- **4H (`htf4_native`): trend −1, RSI 40.5, IN demand (dist 0.32), clean_sky 1.5, nas_long_rec 2** — 4H still technically down BUT sitting in fresh 4H demand with clean overhead and two recent 4H NAS-LONG prints. This is the **1H-leads-4H phase-lag** (Angle 5 headline): fast up, slow catching up from a defended floor with room to run.
- **Session:** NY open (12:30) — the loud-window exception to the Asia-quiet MONFORTE tendency; the NY open swept the overnight/multi-day low and reversed.

---
**Honesty:** lens labels are calibration-grade (n=61/144), not validated edge. This fund is an *outlier within the study set* (climactic, not quiet) — useful as the boundary case proving the MONFORTE family has TWO modes: quiet-absorption (the median) and loud-sweep-reclaim-into-aligned-HTF (this one). Any combo that hard-gates on quiet-vol/off-killzone/shallow-sweep would MISS this winner — argues for soft 2-of-3 voting with the velocity-geometry + HTF-phase-lag stack as an alternate path.
