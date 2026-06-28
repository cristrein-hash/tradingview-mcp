# Fund 12 — DEEP READING (MONSTRO bottom, 2025-12-09 06:00 UTC, block 2025-11-25)

**Tier:** MONSTRO · power_score 7.6 · leg_atr 38.68 · mfe12 7.5 ATR / mae12 0.87 ATR (clean, no give-back).
**Régua:** RAW-only, as-of bottom bar i / SHIFT1. Reaction bars (w1..12) are post-low, already-closed → entry a few bars after the low is causal (this leg is huge, plenty of R left).

---

## (a) THE ENTRY MECHANIC — where/when I actually take this

Raw bars confirm the structure precisely:

- **The low bar i (06:00 UTC):** o4179.9 h4180.0 **l4169.8** c4174.6, range 10.2 = **2.15 ATR**, vol 6294 (the volume PEAK of the leg), RSI 31.1. This is a **terminal capitulation/velocity-spike bar** — biggest range + biggest volume of the whole down-leg, printed in thin Asia liquidity, closing in the **upper ~47%** of its own range (`low_closepos` 0.47, `lower_wick_ratio` 0.47). So: one violent flush bar that immediately rejects half its range. It swept a prior fractal low (`swept_prior_low=1`, `sweep_depth_atr` 3.43 — note: deeper than the typical MONFORTE shallow-sweep prior, see "distinctive").
- **w1 (06:15):** green, c4178.4 — reclaims back above the flush bar's open, RSI momentum bottoms here (26.0) while *price* already made its higher low → first higher-low forms immediately (`first_higher_low_bar=1`).
- **w2–w4 (06:30–07:00):** lows climb 4176.4 → 4180.2 → 4180.4 — a **monotone climbing floor** (no-look-back; matches reaction_seq l_atr 1.39→2.19→2.24).
- **w5 (07:15):** the only real dip (l4176.0, red) — a shallow retest that holds well above the low (dip stays ~+6 pts above the 4169.8 low).
- **EMA21 reclaim happens at bar 8** (`reclaim_ema_bars=8`): bar 8 (08:00) closes 4188.3 vs ema 4184.9 — first close back above the 21-EMA. NAS-LONG confirms after the low (`nas_long_after=1`).
- **w12 (09:00):** the displacement bar — h4205.4, +13 pts, vol 6279, RSI 57.9. This is the leg igniting.

**Where I enter — two-tier:**
1. **Aggressive (preferred, captures the whole 7.5 ATR):** on the **w1/w2 micro-HL reclaim** — enter on the close of w2 (06:30, ~4181) once the flush bar's range is reclaimed AND the higher-low is confirmed against the i-low. Trigger = *shallow-sweep + instant intra-/next-bar reclaim of the swept level* (ANGLE 0 L7 / ANGLE 1 Lens 2). SL just under 4169.8 (the flush low); risk ≈ 1.0–1.3 ATR → mae12 only 0.87 ATR, so the w5 retest never threatens it.
2. **Confirmation (cleaner, gives up ~2 ATR):** on the **EMA21 reclaim at bar 8** (08:00, ~4188) plus the NAS-LONG print. This is the textbook "reclaim of demand + structure flip up" entry but enters with the leg already 4 ATR up.

I take **tier-1 (sweep+reclaim micro-HL at w1/w2)** because the mae of 0.87 ATR proves the low held and the climbing floor was real from bar 1. The trigger is **sweep-of-prior-low → reject (close upper-half) → next-bar green higher-low**, not a CHoCH (`choch_15m_after=0` — there is NO 15M CHoCH here, so anyone waiting for CHoCH misses this leg entirely).

---

## (b) Lenses PRESENT / STRONG here

**Cross-TF (ANGLE 5) — the strongest cluster for this fund:**
- **L5.1 HTF Phase-Lag Turn — STRONG.** `htf1_native.trend=+1` while `htf4_native.trend=−1`. The 1H is ALREADY bullish, the 4H still bearish → the canonical 1H-leads-4H regime-onset signature. This is the single cleanest cross-TF separator and it is textbook-present.
- **L5.2 1H Room-Above — STRONG.** `htf1_native.in_demand=0`, `htf1_native.dist_demand_atr=2.06` (well clear of its floor), `h1_pos` reading the 1H lifted off — while the 15M flushed INTO 4H demand (`htf4_native.in_demand=1`, `dist_demand_atr −0.06`). Exactly the "15M at the floor, 1H already reclaimed" multi-TF spring.
- **L5.3 HTF RSI Hook — PRESENT.** 15M RSI washed (rsi_low 31.1, dips to 26 at w1) while `htf1_native.rsi=58.8` (1H strong, non-oversold). The 1H refuses to confirm the 15M panic.
- **L5.6 Multi-TF Demand Stack — STRONG.** 15M inside demand (`in_demand=1`, `demand_virgin=1`) nested inside 4H demand (`htf4_native.in_demand=1`), with `htf1_native.clean_sky_atr 0.31` / `htf4_native.clean_sky 0.28` room above. Floor below + air above + virgin demand = launchpad.

**Liquidity / Auction (ANGLE 1):**
- **Lens 1 QUIET RECLAIM — PRESENT.** `killzone=0`, session=ASIA (06:00 UTC) → off-killzone, the 8.1×-lift profile. Bottom forms in thin Asia liquidity, not London/NY.
- **Lens 2/5 engineered raid — PARTIAL.** `swept_prior_low=1` with reclaim, but no EQH/EQL pair flagged in E1 (smc_bos=0); the sweep is real, the dual-pool cycle is not strongly marked.
- **Lens 3 Liquidity Asymmetry — PRESENT.** `dist_demand_atr −0.05` (floor right here) vs `dist_supply_atr 0.88` (supply close-ish) — but `n_supply_overhead=66` is heavy. Mixed: floor is defended/nearer but overhead is congested (a caution flag).
- **Lens 6 Discount-not-breakdown — INVERTED/CAUTION.** `dealing_range_pos −1.69` → price is BELOW the discount band (range *break*, not discount accumulation). This is the one auction lens that reads "continuation," not "reversal" — a genuine tension in this fund.

**Geometry / Velocity (ANGLE 4):**
- **L1 reclaim_low_monotone — STRONG.** l_atr 0.87→1.39→2.19→2.24 over w1–w4 (climbing floor, run≈4).
- **L7 downleg_gap_velocity_spike + L6 pivot_engulf_thrust — STRONG.** The i-bar is the biggest-range/biggest-volume bar of the leg (2.15 ATR, vol peak) and reverses the very next bar (w1 green). Classic climax-flush-then-snap.
- **L8 reclaim_dip_depth (shallow retest) — STRONG.** w5 is the only dip and it holds far above the low; mae12 0.87 ATR confirms.
- **L5 close_progression_R2 — MODERATE.** c_atr ramps 1.82→2.34→2.56→2.74 (clean early) then chops mildly w5–w7 before the w8–w12 expansion; R² good early, two-stage launch.

**Volatility (ANGLE 2):**
- **L8 flush_then_freeze — PARTIAL/INVERTED.** Here it's flush-then-grind-then-expand, not flush-then-freeze; ATR actually rises post-low (4.75→5.98). The freeze model does NOT fit this fund.
- **atr_regime 1.11 / atr_compression_pre 0.87** — NOT the calm-coiled MONFORTE median (0.94/1.07). This bottom is in a slightly *elevated*, NOT compressed, regime.

**Order-flow (ANGLE 0):**
- **L4 absorption_reload — STRONG.** i-bar = volume peak (6294) closing in upper ~47% of range = supply spent, buyers absorbed at the low.
- **L3 sell_bubble_exhaustion_gap — PRESENT.** `sell_bub_w=3`, `sell_decel=−3` (sell-bubble effort decelerating into the low).
- **L2 quiet_climax — FAILS.** vol_climax 1.33 OK but `sweep_depth 3.43` is DEEP and the i-bar is a big 2.15-ATR range → this is a LOUD capitulation low, the *opposite* of the quiet-absorption MONFORTE thesis.

**RSI:** `rsi_low 31.1`, `rsi_min8 31.1`, `rsi_head 0.97`, `rsi_bull_div=0` — moderately oversold, no formal divergence; momentum capitulated WITH price (no L10 hidden-div).

---

## (c) What is DISTINCTIVE about this bottom

This MONSTRO is a **counter-example to the "quiet absorption" MONFORTE prototype** that ANGLEs 0/1/2 built their thesis on. It is a **LOUD, climactic, deep-sweep capitulation low** that still produced a 7.5-ATR clean leg:
- **Deep sweep (3.43 ATR) + big climax bar (2.15 ATR range, volume PEAK) + dealing_range_pos −1.69 (range BREAK below discount)** — all three are the *control/weak-bottom* signatures per the discovery angles, yet this is a verified MONSTRO.
- **What rescues it is purely cross-TF:** the 1H had already turned (`h1_trend=+1`, 1H RSI 58.8, 1H 2 ATR above its demand) while the 15M did the violent flush into nested 4H+15M virgin demand. So the edge here is **NOT the local flush character — it's the HTF phase-lag context** (ANGLE 5 L5.1/L5.2/L5.6). The 15M panic was a stop-run *inside* an already-turned 1H uptrend.
- **No CHoCH, no RSI divergence, no quiet-coil** — the standard 15M confirmation tools are all ABSENT/inverted. The only valid 15M trigger is the sweep+instant-reclaim micro-HL. A detector requiring quiet_climax, compressed regime, discount-not-break, or 15M CHoCH would REJECT this monster.

**Lesson for the engine:** this fund proves a second, orthogonal MONFORTE family — **"violent 15M flush rescued by a turned 1H"** — distinct from the "quiet-absorption-in-compressed-vol" family. The discriminator that survives here is the **cross-TF phase-lag + nested-demand**, plus the **micro-HL sweep-reclaim** as the entry trigger.

---

## (d) Macro / HTF context

- **4H:** still bearish (`h4_trend 0/native −1`), price 5.93 ATR below 4H reference, 4H RSI 46.8 — the higher frame had NOT confirmed; this is a low *inside* a 4H pullback/down-phase. Leg has room (no 4H supply mitigated overhead).
- **1H:** already turned bullish (`h1_trend −1` in E1 snapshot but **native +1**), 1H RSI 58.8, 1H sitting 2.06 ATR above its own demand — the fast frame leads the reversal.
- **Daily:** null in E1 (not resampled for this block).
- **Macro flags:** `macro_bull=0`, `macro_bear=0` — neutral macro regime; no NAS cluster pre-low (`nas_long_16=0`, `nas_short_16=0`), `smc_bos=0`.
- **Session/time:** ASIA, 06:00 UTC, off-killzone (`killzone=0`) — the off-peak, thin-liquidity reversal window that ANGLE 3 flags as 2.3× enriched for MONFORTE.
- **Caution flags carried to the entry:** `n_supply_overhead=66` (congested ceiling) and `dealing_range_pos −1.69` (range-break) are the two reads that argue "continuation"; they are overridden here only by the 1H having already turned + nested virgin demand + clean_sky ~0.3.
