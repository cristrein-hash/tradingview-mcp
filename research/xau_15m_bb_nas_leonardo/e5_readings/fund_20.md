# FUND 20 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2025-02-25 → 2025-05-25 | **Low bar:** 2025-03-26 15:00 UTC | **Tier:** FORTE | **power_score 6.9** | **leg_atr 31.46** | **year 2025**
**Low geometry (RAW):** flush bar 15:00 → l 3012.0, c 3017.5 (closed +5.5 off its own low, `low_closepos 0.99`, `lower_wick_ratio 0.97` — a near-pin-bar rejection). MFE12 +2.02 ATR, MAE12 0.63 ATR (held). Demand zone id 5006 (3017.95–3014.85) was **born ON the low bar**.

---

## (a) ENTRY MECHANIC — where/when I actually enter

This is **NOT** a clean V-staircase launch (the canonical MONSTRO shape from Angle 4). It is a **slow grind-and-hold off fresh demand inside the NY killzone** — a *defended-floor accumulation base*, not an impulsive thrust. The reaction_seq grinds (c_atr 0.96→1.08→0.91→1.27 for bars 1–4, lows sagging back) and the EMA21 reclaim is LATE (bar +12). So the EMA reclaim is the WRONG trigger here — it pays too late.

The causal entry is a **micro-HL retest of the fresh demand zone that was created at the pre-low CHoCH**, executed in two legitimate windows:

- **Trigger A (the structural read, preferred): retest-of-demand-hold.** A 15M bullish **CHoCH printed at bar −4 (14:00, 3016.96)** — *before* the actual price low. Price then made its true low (3012.0) on the 15:00 flush, immediately closed back INSIDE the freshly-born demand zone 5006 (3014.85–3017.95), and **held that zone for ~11 bars (3014.8–3017.0)** without a single close back below 3014.8. Entry = on the **first higher-low confirmation that the demand floor holds** — bar +2/+3 (15:30–15:45), where price retests 3014.8–3015.9 and refuses to break the flush low. `entry_mechanics.first_higher_low_bar = 1`. Stop below the flush low 3012.0 (≈0.7–0.8 ATR), giving a tight structural risk into a leg that ran +2 ATR by bar 12.
- **Trigger B (momentum confirm, later/safer): EMA21 reclaim at bar +12** (18:00, c 3019.7 > ema 3018.8), corroborated by the **second 15M CHoCH at +14 (18:30, 3020.07)**. This is the dossier's `reclaim_ema_bars=12`. Costs ~5–6 pts of the move vs Trigger A but removes ambiguity.

**My call:** enter on Trigger A — the **sweep-of-flush-low + immediate reclaim-into-fresh-demand + micro-HL hold**, with stop under 3012.0. The thesis that makes A valid (not just hindsight) is the *pre-low CHoCH* + *NAS-short exhaustion* + *demand born at the low* converging before any close confirms the base.

## (b) Lenses PRESENT / STRONG here

**STRONG / present (causal, ≤ entry):**
- **Angle 1 L7 / Angle 3 L6 — stop-run / NAS-short exhaustion.** NAS SHORTs fired at −30b and −27b (07:30/08:15, 3027–3032) then went **completely stale** — zero fresh shorts into the low. The down-initiative dried up before the print. STRONG and distinctive.
- **Angle 1 L3 — liquidity asymmetry / defended floor.** `dist_demand_atr −0.11`, `in_demand 1`, `demand_fresh 1`, `demand_virgin 1` — price is sitting ON a fresh, virgin, untested demand. Floor is defended at the candle.
- **Angle 5 L5.6 (partial) — multi-TF demand stack.** `htf4_native.in_demand 1` (15M flush lands on 4H demand), AND a fresh 15M demand born at the low → nested floor. BUT `clean_sky` is thin: htf4 `clean_sky_atr 0.12`, htf1 0.24, `dist_supply_atr 0.08`, `n_supply_overhead 51` — overhead supply is CLOSE (supply zones 5005 at 3027 and 4991 at 3032–3036 directly above). So floor=strong, runway=capped → consistent with FORTE (good leg) rather than MONSTRO (no runway).
- **Angle 0 L4 — absorption_reload.** Low bar v=4566 (the largest volume of the whole down-leg cluster) with close in the upper 60%+ of its bar (`low_closepos 0.99`) = volume spike absorbed, buyers closed it strong. Present and clean.
- **Angle 0 L10 / E1 `rsi_bull_div 1` — RSI holds above floor.** `rsi_min8 34.2`, `rsi_low 40.1` — NOT deeply oversold; RSI refused to confirm the new price low. Bullish divergence flagged. Matches the "less-oversold strong bottom" fingerprint.
- **Angle 5 L5.4 — compressed regime / `atr_compression_pre 0.73`** elevated coil, `vol_climax 1.55` modest. Calm-coil precondition partially present.
- **Angle 1/2 shallow-sweep:** `sweep_depth_atr 0.65` — very shallow stop-run (much shallower than the control ~2.3). Quiet absorption, not deep capitulation.
- **E1 confluence:** `dealing_range_pos −0.187` (discount band, NOT broken — Angle 1 L6 ✓), `sell_decel 2`, `sell_bub_w 6` then faded (Angle 0 L3 exhaustion-gap consistent).

**ABSENT / against the usual MON profile (honesty):**
- **Angle 1 L1 / Angle 3 (off-killzone, Asia thesis) — ABSENT.** This is a **NY-session, killzone=1** bottom (14:00–15:00 UTC = NY open). The headline "monsters bottom off-killzone in Asia" lens does NOT apply here. This fund is a counter-example to that angle — a strong NY-killzone bottom.
- **Angle 4 staircase lenses (L1 monotone-floor, L2 jerk, L5 R²) — WEAK/ABSENT.** The reclaim grinds and chops (lows sag back at bars 3,6,7); it is not front-loaded and not a high-R² ramp. This is a *base-builder*, not a *spring-release*. `downleg_eff 0.02` (extremely grindy).
- **Angle 5 L5.1 phase-lag turn — MIXED.** `htf1_native.trend +1` (1H already bullish, good) but `htf4_native.trend −1` (4H still bearish) — the 1H-leads-4H structure IS present, but at the DAILY level it is firmly bullish (`hd_trend 1`, `hd_rsi 58.1`, `hd_dist 7.43`), so this is a pullback-in-uptrend, not a regime reversal from below.
- **NAS-LONG / buy bubbles — ABSENT** (`nas_long_16 0`, `buy_bub_w 0`). No bullish trigger printed; the bull case is purely structural (CHoCH + demand + exhaustion), not signal-confirmed.

## (c) What is DISTINCTIVE about this bottom

1. **Pre-low CHoCH.** The bullish CHoCH fired at bar −4, BEFORE the actual price low — structure called the turn while price made one more lower wick into fresh demand. The flush at +0 was the *sweep that ran the stops below the already-broken structure*, then reclaimed. Sweep-of-low under a confirmed CHoCH is the textbook engineered reversal.
2. **Demand born AT the low.** Zone 5006 was created on the low bar itself and immediately defended for 11 bars — a real participant base, not a passive level.
3. **Grind-base, not V-snap.** Despite FORTE tier, the reclaim is the *slowest, grindiest* archetype: tight 3-pt base held for 11 bars, EMA reclaim at +12. This is the "absorption-without-climax" profile (Angle 0 reframe), executed via a defended floor rather than an impulsive thrust. The edge is the FLOOR, not the launch velocity.
4. **Capped runway = FORTE not MONSTRO.** Strong defended floor + close overhead supply (clean_sky 0.12 ATR) → exactly the asymmetry that produces a good-but-bounded leg.

## (d) MACRO / HTF context

- **Daily: firmly bullish.** `hd_trend +1`, `hd_rsi 58.1`, `hd_slope_atr 5.77`, `hd_pos 0.80`, `hd_dist 7.43` — gold in a strong daily uptrend (this is the Mar-2025 leg toward the all-time-high run). This is a **pullback-buy inside a daily bull**, the highest-context tailwind a 15M long can have.
- **1H: turning up.** `h1_trend +1`, `h1_rsi 46.1`, `h1_pos 0.23`, above its demand (`htf1_native.dist_demand_atr 2.98`, `in_demand 0`) — 1H already lifted off its floor while the 15M flushed. Classic multi-TF spring (15M at floor, 1H reclaimed).
- **4H: still soft.** `htf4_native.trend −1` but in 4H demand (`in_demand 1`) — the 4H is mid-pullback, providing the demand the 15M bounced from. The 1H-bullish / 4H-bearish split = regime-onset phase-lag (Angle 5 L5.1), but here it is a *pullback-completion* read because the Daily anchors the bull.
- **Session/time:** NY open (14:00–15:00 UTC), killzone — a NY-driven pullback-buy, which is why the off-killzone/Asia angles do not fire. macro_bull/bear E1 flags both 0 (neutral macro tag), but the native daily clearly carries the bull.

**Net read:** a daily-uptrend pullback that flushed into fresh, virgin 4H+15M-nested demand inside the NY killzone, with the 1H already turned up and NAS-short initiative exhausted. The turn was pre-signaled by a 15M CHoCH; the actual low was a shallow sweep absorbed on the biggest down-leg volume (strong close). Entry = micro-HL hold of the freshly-born demand at bars +2/+3 (stop under 3012.0); the late EMA21 reclaim at +12 is the conservative backstop. FORTE-not-MONSTRO because overhead supply caps the runway (clean_sky 0.12 ATR).
