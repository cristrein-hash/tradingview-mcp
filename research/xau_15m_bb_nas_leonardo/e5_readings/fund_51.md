# Fund 51 — DEEP READING (XAU 15M MON+FORTE bottom)

- **Date:** 2025-11-25 08:45 UTC (block 2025-11-25; first bars of the 2025-11-25→2026-02-25 primitives file, idx 40)
- **Tier:** FORTE · power_score 2.5 · leg_atr 19.08 · year 2025
- **Bottom bar i (raw):** o 4127.62 / h 4128.12 / **l 4109.49** / c 4116.16 · v 5763 · rsi 38.34 · atr 8.13 · ema21 4136.76 · nas_dist −0.53
- **Note:** `features_E1` is EMPTY for this fund → reading leans on raw `series`, smc/nas/zone events, htf_native, reaction_seq, entry_mechanics.

---

## (a) ENTRY MECHANIC — where/when I would actually enter

**Trigger = engineered sell-side liquidity raid + same-bar reversal-bar confirmation, then EMA reclaim.** Two viable entry tiers:

1. **Aggressive (bar i+1, ~09:00):** The bottom bar i (idx40) is a wide-range bearish flush (range 18.6 = 2.3 ATR) that **sweeps the resting EQL pool at 4140.26** (printed bar ~29) and the prior local lows, undercutting to 4109.49 — a clean stop-run below sell-side liquidity. The **very next bar (i+1, idx41) is a decisive bullish reversal bar**: o 4116.15 → c 4126.98 (+10.8, closes near its high 4128.46), instantly reclaiming back above the swept level. `entry_mechanics`: `swept_prior_low=1`, `first_higher_low_bar=1`. This is `flush_then_snap` / `liquidity_grab_no_followthrough`: shallow-ish sweep, immediate reclaim. Enter long on the close of i+1 with SL below 4109.49 (the swept low, ~1 ATR risk).

2. **Confirmation (bar i+5, idx45, ~11:00):** `reclaim_ema_bars=5` — close 4137.22 reclaims EMA21 (4134.0) for the first time after the flush. `reaction_seq` shows a **monotone climbing floor** (l_atr 0.55→1.63→1.51→2.02→2.20 — lows hold and rise from bar 2 on, almost no look-back) and a clean staircase of closes (c_atr 2.15→1.89→2.26→2.32→3.41). This is the safer "EMA reclaim of an intact higher-low base" entry.

I'd take **tier 1 (sweep+reclaim of the EQL at i+1)** as the primary trigger — it captures the most of the 19 ATR leg; tier 2 is the add/confirm. Note `choch_15m_after=0` and `nas_long_after=0`, so the trade is NOT confirmed by a textbook 15M CHoCH or a fresh NAS-LONG — it relies on the sweep-reclaim + climbing-floor structure, which is the distinctive read here.

## (b) Lenses PRESENT / STRONG

**Liquidity / Auction (angle_1) — strongest cluster:**
- **L2 Engineered double-bottom raid / EQL undercut+reclaim — PRESENT & STRONG.** EQL at 4140.26 swept (low 4109.49 << EQL) then reclaimed within 1 bar. Textbook sell-side raid.
- **L8 EQH magnet overhead — PRESENT.** EQH 4147.84 sits ~31 pts (~3.8 ATR) above close = untested buy-side liquidity acting as the leg's draw/target.
- **L5 Dual-sided raid context — PARTIAL.** EQH (4147.84) then EQL (4140.26) both printed in the prior swing before the low = a raid-both-pools cycle.
- **L1 Quiet reclaim (off-killzone) — PRESENT.** 08:45 UTC is the London pre/open edge, but htf shows the move is NOT a headline lowest-of-50 capitulation; reclaim is quiet and fast.

**Order-flow / Microstructure (angle_0):**
- **L7 liquidity_grab_no_followthrough — STRONG** (shallow stop-run + instant reclaim; the discriminator).
- **L5 delta_proxy_reversal_2bar / L4 absorption_reload — PARTIAL.** Bar i closes lower-mid (weak close), but bar i+1 prints volume 5549 with close in the top of its range (close_pos ≈ 0.9) = absorption visible one bar after the low, not on it.
- **L10 rsi_holds_above_floor — MODERATE.** rsi at the low bar = 38.3 (NOT deeply oversold); rsi only dips to ~30 on i+1 then hooks up. Matches the MONFORTE "less oversold" fingerprint.

**Inter-bar geometry (angle_4) — strong:**
- **L1 reclaim_low_monotone_k — STRONG** (climbing floor, lows rise every bar from w2).
- **L5 close_progression_R2 / L2 reclaim_jerk — PRESENT.** Front-loaded, clean staircase ramp; mfe12 3.6 ATR by bar 12, mae12 only 0.55 ATR (the low was never revisited → shallow-retest / no-look-back launch).

**Cross-TF / Regime (angle_5):**
- **L5.6 Multi-TF demand stack — STRONG.** 15M flush lands ON 4H demand (`htf4_native.in_demand=1`, `dist_demand_atr=−0.3` = 0.3 ATR into the 4H floor). A defended HTF floor.
- **L5.1 / phase alignment — UNUSUAL HERE:** both htf4 trend=+1 AND htf1 trend=+1 (this is NOT the usual "1H-leads-bearish-4H" lag; here BOTH HTFs are already bullish). htf4 rsi 64, htf1 rsi 57.7 — HTF momentum is firmly up. So this is a **pullback-into-demand inside an established HTF uptrend**, not a contrarian regime-onset reversal.
- **htf4 choch_rec=1** — a recent 4H bullish CHoCH had already printed = HTF structure flipped up before this dip.
- clean_sky thin on 4H (0.25) but 15M overhead supply 4145.86–4152.07 ~3.8 ATR away gives the immediate runway to the EQH magnet.

## (c) What is DISTINCTIVE about this bottom

1. **It is a buy-the-dip in a CONFIRMED dual-HTF uptrend**, not a counter-trend bottom-fish. Both 4H and 1D `trend=+1`, both RSI >57, 4H already in demand with a fresh bullish CHoCH. This is the rarer "strong-trend pullback flush" profile (vs the angle catalogs' modal "1H-leads-bearish-4H phase-lag" reversal).
2. **The entry is a pure liquidity event:** a single sharp flush bar sweeps the EQL pool and the local lows, then snaps back the next bar — the classic engineered stop-run. No CHoCH and no NAS-LONG confirmation (`choch_15m_after=0`, `nas_long_after=0`); the read is structural (sweep+reclaim+climbing floor), which makes geometry/liquidity lenses the load-bearing ones.
3. **No-look-back launch:** mae12 = 0.55 ATR vs mfe12 = 3.6 ATR. The original low was never retested — a very high-quality higher-low base. The down-leg into it was a grind (modest rsi 38, calm-ish) that capitulated on one wide bar = exhaustion, not a high-vol panic.

## (d) Macro / HTF context

Established XAU bull regime (late-2025 ~$4100 gold). 4H: uptrend, RSI 64, price pulled back exactly INTO 4H demand (−0.3 ATR), recent bullish CHoCH = trend intact and dip-buyable. 1D: uptrend, RSI 57.7, sitting 0.76 ATR above 1D demand with 0.87 ATR clean sky. The 15M flush is a London-pre liquidity grab below the EQL inside this bullish HTF structure — supply overhead at 4145–4152 / EQH 4147.84 is the first target (~3.8 ATR), and with HTF trend up the leg ran to ~19 ATR. The setup is **HTF-uptrend pullback → 15M sell-side raid → instant reclaim off stacked 4H demand → run to overhead liquidity.**
