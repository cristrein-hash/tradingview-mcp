# XAU_4H_DEMAND_BREAKOUT — Revalidation v2 (methodology)

> Parameters are authoritative in `config.json` (same directory). This document
> explains the thesis, legacy evidence, reconstructed rule, caveats, and plans,
> and **references** config — it does not restate parameters as a second source.

## 1. Identity

- Catalog strategy id: `XAU_4H_DEMAND_BREAKOUT`
- Direction: long · Base timeframe: 4H · Context: none required by the legacy rule
- revalidation_version: **v2** (the legacy close-only exploration in
  `project_xau_4h_backtest_v1` is the "v1" era; this canonical R-real
  revalidation is v2, consistent with CAPITULATION v2).
- Status going in: catalog `validation_status = ACTIVE_CANDIDATE`,
  `current_deployment_status = LIVE` (dispatches Telegram). Must be revalidated on
  canonical data before any production decision.

## 2. Legacy evidence

- Rule: **V0 + V3'** (adopted 2026-05-20).
- Metric: **close-only, H=20** (some early exploration used H=10).
- Combined over 6 windows (2023–2026, ~3 years): **n ≈ 80, win ≈ 83.8%,
  avg_R close-only ≈ +2.43R, sum_R ≈ +194.57R**, 4/5 evaluated windows pass the
  70% gate. Sample gate: PRELIMINAR_FORTE (n ≥ 50).
- Source: TradingView Replay 4H. **The legacy RAW dumps are persisted**
  (`alert-bridge/logs/backtests/XAUUSD_240_*_v6.jsonl`, 5 files, 2026-05-21) — same
  raw-snapshot format as the canonical replay (pine_boxes/labels/study_values/
  replay_current_dt). Unlike CAPITULATION, legacy signals/timestamps are
  recoverable.
- **The exact analyzer that produced 83.8% / +194.57R is NOT in the repo**
  (`analyze_xau_4h_backtest.py` absent). The legacy SIGNAL conditions are fully
  documented; the legacy OUTCOME computation (fill, horizon, "R" definition) must
  be reconstructed and may differ subtly. Legacy "R" is close-only (no real stop)
  and is not directly comparable to R-real.

## 3. Reconstructed legacy rule (canonical fields)

Long signal at 4H bar `c` when ALL hold (values in `config.json`):
1. `inside_demand_zone[c] == true` — close inside a Custom OB v11 DEMAND box
   (legacy `IN_OB_ZONE`; presence only, no state filter).
2. `nas_dist_ema_atr[c] ∈ [1.0, 2.0]` — NAS distance from EMA in ATR units
   (legacy `NAS:1to2`; price stretched UP).
3. `dist_14d_pct[c] ∈ [-1.0, 0.0]` — practically at the 14-day high
   (legacy `V3'`; recomputed from 4H OHLC).

## 4. Conceptual explanation

- "DEMAND" = a Custom OB v11 DEMAND box (bullish order block zone).
- **Entry is INSIDE the demand zone**, not after breaking out above it.
- The "breakout" in the name is *active breakout* = price near the 14-day high
  **while still inside** the demand zone — momentum-at-top, not a zone-exit.
- It is **not** `close > high of the zone` and **not** `close > swing_high`
  (the latter is the Família B DECISIVE_BREAKOUT_CONTINUATION).
- The main legacy rule does **not** use Bubbles, RSI, or SMC (these were explored
  as V1/V2 and discarded).

## 5. Caveats (mandatory — resolve during reconciliation, before any strong verdict)

- **C1 — `nas_dist_ema_atr` is `diagnostic_only`** in the canonical field classes.
  It is used here for faithful reconstruction of the legacy rule, but a
  diagnostic-class field should not normally gate a backtest. Before any strong
  verdict, verify it is safe as a gate.
- **C2 — NAS_DIST lookahead/source.** Confirm the extractor's `nas_dist_ema_atr`
  comes from the **closed** bar, not the forming bar (study_values in replay can
  reflect the current/forming bar; v1 noted degenerate current-bar OHLCV). If
  forming → lookahead.
- **C3 — `dist_14d_pct` window must be defined and tested.** Confirm whether "14d"
  means **84 candles** (14 calendar days × 6 4H bars/day) or another window. The
  live monitor only had `ohlcv_last_40_bars` (~6.6 days), so the legacy "14d" may
  not be a true 14-day high. `config.json` lists window candidates to test.
- **C4 — demand-zone visibility / retro-draw.** Confirm `inside_demand_zone[c]`
  reflects a zone **visible at bar c**, not a box retro-drawn with pivot
  confirmation lag.
- **C5 — close-only is not final validation.** R-real may change the conclusion
  entirely (as it did for CAPITULATION).

## 6. Reconciliation plan

1. Reconstruct V0+V3' signals on the canonical 4H slim, restricted to the legacy
   window (2023–2026).
2. Reconstruct signals from the persisted v6 legacy dumps where possible.
3. Compare timestamps (n match? same bars?) — the unique advantage over CAPITULATION.
4. Compute close-only at H=10 and H=20 on canonical data; check whether n and win%
   approach the legacy (~80 / ~83.8%).
5. **Gate:** if the canonical close-only does NOT reproduce the legacy, STOP and
   audit (classify as signal/data mismatch) BEFORE running R-real.

## 7. R-real plan (future, not run here)

- Entry: open of the candle after the signal (never the signal close).
- Stop primary: below the DEMAND zone (`nearest_demand_low`); sensitivities:
  structural 3-bar low and `entry − 1.5 × atr14_sma_tr`.
- Targets: 1R / 2R / 3R; primary 2R. Time limit: H=20. Intrabar: stop-first.
- Costs: 0 / 0.20 / 0.50.
- Overlap: no-overlap; one trade per episode/zone (finalize episode definition in
  the script after observing in-zone clusters — `inside_demand_zone` is true for
  ~16.7% of bars, so consecutive in-zone bars cluster).

## 8. Future comparison (overlap / redundancy)

- vs **CAPITULATION**: opposite regimes (CAPITULATION = bottoms: NAS LONG label +
  RSI1D<50 + ATR>1.3; DEMAND = near highs: NAS_DIST +1..2 + dist_14d∈[-1,0]).
  Expected bar overlap ~0; does not replace CAPITULATION. Measure shared signal bars.
- vs **XAUUSD_4H_BREAKOUT_CONTINUATION** (Família B): high conceptual overlap (both
  long near highs/momentum; catalog flags this). Measure shared signal bars,
  timing correlation, and whether one subsumes the other (merge candidate).

## Reproduction

The backtest script (later, separately authorized) reads only this `config.json`,
processes canonical slims (and optionally the persisted v6 dumps for
reconciliation) read-only, and writes `trades.jsonl` / `report.json` / `summary.md`
into this directory. No script and no backtest exist yet.
