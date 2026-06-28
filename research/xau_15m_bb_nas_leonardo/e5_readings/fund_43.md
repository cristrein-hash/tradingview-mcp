# Fund 43 — Deep Reading (XAU 15M MON+FORTE bottom)

**Identity:** 2025-01-20 01:00 UTC · block 2024-11-25→2025-02-25 · tier **FORTE** · leg_atr 21.89 · power_score 5.4
**Bottom bar:** idx 3465 · low **2689.36** · close 2690.0 · ATR 3.38 · ema21 2699.19 · v **4297** (~3.4× leg avg)
**Outcome:** mfe12 4.38 ATR / mae12 0.16 ATR — near-zero giveback, a true no-look-back launch.

This is the cleanest "Asia-ramp shallow-sweep + NAS-cluster + monotone staircase" bottom in the set. It is NOT the quiet-absorption archetype the angle catalog emphasizes; it is the *engineered cross-session liquidity grab* archetype — and it is textbook.

---

## (a) ENTRY MECHANIC — where/when I actually enter

**The low itself (bar 3465) is the climax flush, not a quiet print.** It is the single largest-volume bar of the entire leg (v=4297 vs ~1300 trailing avg), range 5.1 = 1.5 ATR, closing on its low (`low_closepos` 0.12, wick ratio 0.12 — a weak-close capitulation bar). Crucially it **swept** the trailing-50 low (prior min 2691.15) by ~1.8 pts (0.53 ATR — shallow, `sweep_depth_atr` 0.53). A **NAS LONG cluster** fired exactly here: ids 1573 (00:15), 1576 (00:45), **1578 at the low bar 01:00** — three LONG prints into the flush (`nas_long_16`=4).

**Trigger = sweep + reclaim, confirmed within 1 bar.** Bar +1 (3466, 01:15) trades down to 2689.9 (holds the low) and closes **2693.0 — back above the swept 2691.15 level**. That is the actionable reclaim: stop-run failed, price reclaimed the prior pool on the very next bar with no continuation.

**Where I enter:** at the close of reaction bar +1 (2693.0), or on the bar +2/+3 micro-higher-low retest (lows 2690.5 → 2691.5, each holding above the flush low). SL below the flush low 2689.36 (≈1.1 ATR of risk). The leg then never revisits — by bar +7 (03:00) close 2700.8 reclaims EMA21 (`reclaim_ema_bars`=7), confirming the trend flip. Waiting for the full EMA reclaim costs ~3 ATR of the move; the sweep-reclaim entry at bar +1 captures the whole leg with minimal risk.

`first_higher_low_bar`=1, `swept_prior_low`=1, `choch_15m_after`=0 (the leg ran clean enough that no 15M CHoCH was needed — the sweep-reclaim WAS the structure event).

---

## (b) Lenses PRESENT / STRONG here

**Strongest cross-TF (Angle 5 — the headline fit):**
- **L5.1 HTF Phase-Lag Turn — PRESENT/STRONG.** `htf1_native.trend = +1` while `htf4_native.trend = −1`. The classic 1H-leads-4H disagreement: fast frame already bullish, 4H still falling = room overhead. This is the single cleanest MON separator and it is unambiguously present.
- **L5.2 1H Room-Above — STRONG.** `htf1_native.in_demand = 0`, `dist_demand_atr = 1.24`, `h1_pos`=−0.05 (marginal) — 1H has lifted off its own floor while the 15M flushes INTO 4H demand (`htf4_native.in_demand = 1`, `dist_demand_atr` −0.17, `features_E1.in_demand`=1). Multi-TF spring: 15M at the floor, 1H already off it.
- **L5.4 Compressed-Regime Onset — PRESENT.** `atr_regime` 1.16 (moderate, slightly above the 0.94 MON median — not the cleanest), but `atr_compression_pre` 0.74 is sub-par. So compression is the WEAK leg of this bottom — this is NOT a coiled-spring low, it is an impulsive flush low. Honest flag: the volatility/quiet-absorption lenses (Angle 0/2) mostly do NOT fit here.

**Liquidity / Auction (Angle 1) — STRONG:**
- **Lens 1 QUIET RECLAIM — PRESENT.** `killzone = 0`, ASIA session, 01:00 UTC. Off-killzone Asia bottom = the 8.1× lift profile. (Note: it IS the lowest-of-50, so it's the headline-low variant of Lens 1, not the local-pool variant.)
- **Lens 7 STOP-RUN context / NAS — PRESENT but inverted to a fresh cluster.** Rather than stale shorts, here a fresh NAS **LONG** cluster (3 prints) fires at the low — the reversal trigger is time-aligned with the bottom (Angle 3 L6 `nas_off_killzone` + recent latency).
- **Lens 6 DISCOUNT-NOT-BREAKDOWN — PRESENT.** `dealing_range_pos` −0.145 (discount third, not broken beyond −1). `demand_virgin`=1 (fresh value floor), `rsi_bull_div`=1.

**Time/Session (Angle 3) — STRONG, the defining axis:**
- **L1 asia_offpeak_flush — STRONG.** Outsized candle (1.5 ATR, 3.4× volume) in the thin Asia 01:00 window — forced-liquidation-into-a-vacuum that snaps back. Hour-01-UTC is the 4.7× enriched bucket.
- **L3 time_since_session_open — PRESENT.** First ~3h of the Asia ramp.
- **L4 overnight_low_sweep_clock — PRESENT.** Sweeps the prior (Fri 01-17) session low region then reclaims.

**Inter-bar geometry (Angle 4) — STRONGEST single fit:**
- **L1 reclaim_low_monotone_k — MAXIMAL.** Reaction l_atr: 0.16→0.33→0.63→1.26→1.43→1.91→2.09→2.36→3.20→3.34→3.80→3.85. The bar LOW climbs **every single bar** (run = 12/12). Buyers defend every new bar — the textbook no-look-back launch.
- **L5 close_progression_R2 — STRONG.** c_atr 1.08→0.68→1.35→1.75→1.95→2.23→2.36→3.37→3.39→4.18 — a near-monotone clean ramp (one dip at bar 2, then straight up). High R², high slope.
- **L8 reclaim_dip_depth — STRONG (shallow retest).** The only pullback (bar 2, l 0.33) is microscopic; the first higher-low holds far above the bottom. `mae12` 0.16 ATR confirms essentially zero giveback.
- **L6 pivot_engulf_thrust / L7 climax_flush — PRESENT.** The low bar is the velocity+volume climax; reaction bar 1 is green and reverses it immediately (`flush_reversed_next`).

**Order-flow (Angle 0) — MIXED.** `vol_climax` 1.52 and the weak-close climax bar do NOT fit the quiet-absorption thesis (L2 quiet_climax FAILS: vol>1.35). BUT **L4 absorption_reload partial / L9 buy-bubble**: `buy_bub_w`=0 (no buy bubbles) and `sell_bub_w`=14 (heavy sell-bubble spray) — this bottom is the *climactic* variant, not the absorption variant. The sell-bubble count (14) is high vs the MON median (1), so Angle 0/3 sell-bubble-exhaustion lenses do NOT fire. **This bottom worked despite being a loud climax** — its edge is geometry + cross-TF + NAS, not quiet absorption.

---

## (c) What is DISTINCTIVE about this bottom

1. **Perfect monotone-floor reaction (12/12 climbing lows).** This is the rarest, highest-specificity Angle-4 signature and it is maximal here — the reaction is the discriminator, and it is flawless.
2. **It is the LOUD/climactic archetype, not the quiet one.** Unlike most of the MON set (quiet absorption: small sell bubbles, modest vol), this bottom is a high-volume (4297) climax flush with heavy sell-bubble spray (14) and a weak close. It proves the convergent thesis: the cross-TF phase-lag + monotone reclaim carry it even when the order-flow/volatility lenses point the wrong way. A pure "find the quiet absorption" detector would MISS this FORTE bottom.
3. **NAS-LONG cluster fires AT the flush low** (3 prints, last exactly on the low bar) — the trigger and the bottom are time-locked, not lagging.
4. **Asia 01:00 thin-liquidity stop-run** that reclaims the swept pool in 1 bar — the engineered-grab-in-a-vacuum profile.
5. **mae 0.16 ATR / mfe 4.38 ATR** — one of the cleanest risk profiles possible; entry risk is tiny, run is large.

---

## (d) Macro / HTF context

- **4H (native):** trend −1 (still bearish), `h4_pos` 0.37, `h4_rsi` 51, in_demand=1, `clean_sky_atr` 0.72 — price flushed into a 4H demand zone while the 4H is still technically down = the leg has room (no 4H supply mitigated overhead). The 4H is the "floor + air" frame.
- **1H (native):** trend **+1**, rsi ~59, off its demand (dist 1.24) — the fast frame has already turned. This 1H-up / 4H-down phase lag is the structural engine (Angle 5 L5.1).
- **Daily:** `hd_trend` +1, `hd_pos` 0.73, `hd_rsi` 58, `hd_slope_atr` +5.31 — Daily is firmly bullish and rising. So the larger-degree trend is UP; the 15M/4H flush is a pullback within a Daily uptrend buying the discount (`dealing_range_pos` −0.145, demand_virgin). `macro_bull`/`macro_bear` both 0 (neutral macro flag), but the Daily structure is constructive.
- **Net read:** Daily-up → 1H-already-turned → 4H-still-flushing-into-demand → 15M Asia stop-run sweeps the local pool, NAS-LONG cluster fires, price reclaims in 1 bar and staircases up. A discount pullback in a higher-degree uptrend, triggered by an off-killzone liquidity grab. The convergence is cross-TF momentum + geometry + NAS, NOT volatility-quiet.

**Honesty flags:** quiet_climax (Angle 0 L2), atr_compression_pre, vol-drain lenses, and sell-bubble-exhaustion all FAIL or are weak here — this is the climactic-flush variant. `atr_compression_pre` 0.74 and `vol_climax` 1.52 are the opposite of the MON-quiet median. The bottom is carried by the reaction-shape + cross-TF phase-lag + NAS cluster, which is the robust, convergent signature for this specific fund.
