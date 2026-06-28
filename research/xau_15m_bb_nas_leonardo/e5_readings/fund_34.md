# Fund 34 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2024-11-25 · **Low bar:** 2024-12-06 01:00 UTC · **Tier:** FORTE · **leg_atr** 24.71 · **power** 5.6
**Outcome geometry:** mfe12 = +11.7 ATR, mae12 = +0.55 ATR → after the low the trade barely breathed against you (0.55 ATR worst-case) and ran ~11.7 ATR in 12 bars. This is a clean, no-look-back leg — a textbook MON/FORTE.

---

## (a) THE ENTRY MECHANIC — where/when I would actually get in

This is an **Asia-session cross-session sweep-and-reclaim**, and the reclaim is a **front-loaded staircase**. Reading the `reaction_seq` (ATR, post-low, all closed bars):

| w | l_atr (floor) | c_atr (close) | green |
|---|---|---|---|
| 1 | 0.55 | 2.13 | ✓ |
| 2 | 1.99 | 3.07 | ✓ |
| 3 | 1.33 | 1.76 | ✗  ← single shallow dip/retest |
| 4 | 1.47 | 2.88 | ✓ |
| 5 | 2.33 | 3.46 | ✓ |
| 6 | 3.23 | 4.47 | ✓ |
| 7 | 4.13 | 4.81 | ✓ |
| 8 | 4.64 | 6.14 | ✓ |
| 9 → 12 | 5.86 → 10.61 | 9.06 → 11.36 | ✓✓✓✓ (acceleration) |

What happened, causally:
- **Bar +1 is an engulfing thrust off the low**: low only sagged to 0.55 ATR, close ripped to +2.13 ATR — that is a +2.1 ATR initiative bar straight off the bottom (`first_higher_low_bar = 1`, `swept_prior_low = 1`). The low swept a prior pool and instantly reclaimed.
- **Bars +1/+2 do the heavy lifting** (+2.13 then +3.07 close) — front-loaded jerk, the spring releasing immediately.
- **Bar +3 is the only flinch**: close pulls back to +1.76, floor dips 1.99→1.33. This is the shallow retest — it holds *well above* the original low (dip retraces to ~1.3 ATR, never near 0). A `choch_15m_after = 1` prints around here and `nas_long_after` fires by bar +2.

**My actual entry: on the bar +4 close (or the +3 → +4 transition).** Rationale — bar +1 is the impulsive thrust, bar +3 is the higher-low retest that holds, and bar +4 reclaiming (+2.88 close, floor stepping back up to 1.47) is the confirmation that the retest held and structure is up (CHoCH already printed). Entering at +4 you take only the shallow retest as risk, sit at ~+2.9 ATR with the low's floor at ~+1.3 ATR, and still have ~+8.8 ATR of leg left (it tops at +11.7). The trigger is therefore: **sweep+reclaim on bar +1 → micro higher-low / CHoCH-up confirmed on bar +3–4 → enter the +4 reclaim.** SL goes just under the retest floor (~the bar +3 low), not under the absolute low — the leg never revisits it.

Note: `reclaim_ema_bars = 8` (it took 8 bars to formally reclaim the 15M EMA21) — so an EMA-reclaim entry would be late (bar +8, already +6 ATR up). The *structural* entry (sweep-reclaim + higher-low + CHoCH) at bar +4 is the superior, earlier mechanic here. The price was already well above EMA in ATR terms; the 8-bar EMA reclaim reflects EMA distance (`h1_dist -8.74`), not slowness of the turn.

---

## (b) LENSES PRESENT / STRONG here

**Angle 3 (Time/Session) — STRONGLY PRESENT, this is a canonical Asia off-killzone bottom:**
- `session = ASIA`, `killzone = 0` → the single strongest discriminator in the corpus (off-killzone S 39% vs C 5%). 01:00 UTC is exactly the 4.7×-enriched Asia-ramp hour (L3 `time_since_session_open` — first hours of Asia).
- L1 `asia_offpeak_flush` and L4 `overnight_low_sweep_clock`: low printed in thin Asia liquidity, `swept_prior_low = 1` → a stop-run into a vacuum that snapped back. This is the highest-conviction time lens and it is squarely PRESENT.

**Angle 5 (Cross-TF momentum) — MIXED but the diagnostic onset signature is present:**
- `htf4_native.trend = -1` AND `htf1_native.trend = -1` → here BOTH HTF frames are still bearish. The 1H has NOT yet flipped +1, so L5.1 phase-lag turn is *partial/absent* (this is the one place fund 34 diverges from the median MON profile where h1 leads to +1).
- BUT L5.6 **Multi-TF Demand Stack is STRONG**: 15M `in_demand = 1`, `htf4_native.in_demand = 1`, `htf1_native.in_demand = 1` → the 15M flush lands inside a **nested 1H+4H+15M demand stack**. `htf4_native.dist_demand_atr = -0.26` (right on/just inside 4H demand), `htf1_native.dist_demand_atr = 1.05` (1H sits a clean ATR above its floor → room).
- L5.4/L5.6 clean-sky: `htf4_native.clean_sky_atr = 0.29`, `htf1_native.clean_sky_atr = 0.52`, 15M `dist_supply_atr = 2.76` — modest air immediately overhead on HTF but a clear 15M runway. `htf4_native.choch_rec = 1` (a 4H CHoCH already recent) is constructive.
- L5.3/L5.8 RSI hook: 15M `rsi_low 37.9` (NOT deeply washed — see Angle 0/L10), `h1_rsi 36.1`, `h4_rsi 40.2` — HTF RSI not strong yet, so the RSI-hook lens is weak here. The strength is structural (demand stack + sweep), not momentum-divergence.

**Angle 0 & 2 (Order-flow / Volatility — "quiet absorption, not climax") — PRESENT:**
- `atr_regime = 0.73` (well below 1.0 — calmer regime than the corpus median) and `atr_compression_pre = 0.89` → L2 `quiet_climax` / L5.4 compressed-regime onset PRESENT. The leg forms from stored, not spent, energy.
- `rsi_low / rsi_min8 = 37.9` (Angle 0 L10 `rsi_holds_above_floor`) — the bottom is NOT deeply oversold; momentum was absorbed rather than capitulated. Matches the MON fingerprint (less oversold than control).
- COUNTER-SIGNAL (honest): `sweep_depth_atr = 5.77` and `drop20_atr = 8.1` are DEEP and large — this is the one place fund 34 looks more like a *capitulation* than the "quiet, shallow sweep" MON archetype. `flush_v_ratio = 0.62` and `vol_climax = 2.07` (a genuine volume burst). So this bottom is a **deep flush into stacked demand that snapped back hard**, not the shallow-grind archetype. The quiet part is the *regime* (low atr_regime, compression); the loud part is the *terminal flush*. Angle 2 L8 `flush_then_freeze` fits: one large puke (drop20 8.1, vol_climax 2.07) immediately followed by the +2.1 ATR reversal bar.
- `low_closepos = 0.15`, `lower_wick_ratio = 0.15` → the LOW BAR itself closed weak with a small wick. The reversal did not come from a single hammer at the low; it came from the **next bar** (bar +1 engulf thrust). So Angle 4 L6 `pivot_engulf_thrust` is the right lens, not a single-bar rejection.

**Angle 4 (Inter-bar geometry) — STRONGLY PRESENT (this is the cleanest dimension here):**
- L1 `reclaim_low_monotone_k`: floor climbs 0.55→1.99, dips once (bar 3), then 1.47→1.99... monotone for the rest. Run is broken once at bar 3 but resumes hard — near no-look-back.
- L2 `reclaim_jerk` / front-loaded: +2.13, +3.07 in the first two bars = strongly front-loaded thrust.
- L5 `close_progression_R2`: after the bar-3 dip the close ramp is very clean and *accelerates* (4.47→6.14→9.06→10.38→10.85→11.36) — high-R² rising launch, with second-half acceleration.
- L8 `reclaim_dip_depth`: the bar-3 dip is shallow (retraces to ~1.3 ATR off an already +3 ATR reaction high) → `shallow_retest` holds. L9 `velocity_regime_flip`: hard down-slope → hard up-slope, a sharp V.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is a DEEP-flush MON in a CALM regime** — it breaks the "shallow-sweep" MON archetype on sweep_depth (5.77) and drop20 (8.1), yet sits in a low atr_regime (0.73) with pre-compression (0.89). The distinctiveness: a big stop-run *inside* an otherwise compressed market that lands precisely on a **triple-nested demand floor** and snaps. The depth is the liquidity grab; the calm regime + nested demand is why it held.
2. **The floor is the star, not momentum.** All three HTF frames are still trend −1 and RSI is unremarkable (36–46), so the usual "1H leads +1 / RSI hook" cross-TF MON tells are ABSENT. What carries this bottom is the **15M-in-1H-in-4H demand stack + 4H CHoCH already printed + clean-ish HTF sky** — a structural launchpad, not a momentum turn.
3. **The reversal lives in bar +1, not the low bar.** The low bar closed weak (closepos 0.15, wick 0.15); the engulfing thrust is the very next bar. Entry must read the *post-low* bar, not the low candle's anatomy.
4. **Extreme run-quality:** mae12 = 0.55 ATR. Once the +1 thrust prints, the trade essentially never goes against you — the rare combination that makes a few-bars-late structural entry (bar +4) virtually risk-free relative to the 11.7 ATR upside.
5. **Bubble/NAS footprint is sparse:** `buy_bub_w/L = 0`, `sell_bub_w = 0`, `nas_long_16 = 0`, `smc_bos = 0` at the low — no loud order-flow signature. `nas_long_after = 2` confirms the trigger comes 2 bars AFTER the low, consistent with the bar-+1/+2 reclaim being where the signal materializes.

---

## (d) MACRO / HTF CONTEXT

- **4H:** trend −1, rsi 40.2, sitting on/just inside 4H demand (`dist_demand_atr -0.26`, in_demand 1), a recent 4H CHoCH (`choch_rec 1`), clean_sky 0.29 ATR. So on the slow frame this is a flush into a defended 4H demand zone at the end of a down-leg, with a structural turn (CHoCH) already hinted — but the 4H trend has not yet flipped.
- **1H:** trend −1, rsi 46.4, `dist_demand_atr 1.05` (above its own demand → room), clean_sky 0.52, no recent 1H CHoCH. The 1H is the higher-RSI, room-above frame — constructive but not yet turned.
- **Dealing range:** `dealing_range_pos = -2.479` → price is BELOW the dealing range (a range *break to the downside*, not the discount band). Per Angle 1 L6 this is technically the "break" zone, usually continuation — but here it resolved as a sweep-and-reverse because it landed on the nested HTF demand. This is the tension that makes the deep flush work: a range-break overshoot that gets absorbed by a real multi-TF floor.
- **Supply overhead:** `n_supply_overhead = 89` (heavy) but `dist_supply_atr = 2.76` — congestion exists but is 2.76 ATR away, leaving a near-term runway. `demand_virgin = 1` (fresh demand being tested).
- **Time macro:** Friday Dec 6 2024, 01:00 UTC, Asia ramp — a thin-liquidity overnight sweep of the prior session's excess, the classic stop-hunt-then-reverse window for these legs.

**Net read:** a deep Asia-overnight liquidity sweep that overshot the dealing range to the downside, flushed into a **nested 15M+1H+4H demand stack inside a calm/compressed vol regime**, and snapped back on a front-loaded engulfing staircase. Entry = bar +4 reclaim after the sweep+reclaim (+1), micro higher-low/CHoCH-up (+3), SL under the shallow retest floor. The edge is structural (demand stack + off-killzone Asia sweep), not momentum (HTF still bearish) — a FORTE that is carried by the floor it lands on.
