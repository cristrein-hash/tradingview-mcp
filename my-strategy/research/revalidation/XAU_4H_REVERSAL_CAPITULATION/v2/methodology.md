# XAU_4H_REVERSAL_CAPITULATION — Revalidation v2 (methodology)

> Parameters are authoritative in `config.json` (same directory). This document
> explains the thesis, data lineage, and decision criteria, and **references**
> config — it does not restate parameter values as a second source.

## Identity

- Catalog strategy id: `XAU_4H_REVERSAL_CAPITULATION`
- Direction: long · Base timeframe: 4H · Context: 1D
- Status going in: legacy "validated" claim (83.7% win, ~86 trades) that was
  **never reproduced on canonical data**. This v2 is the first R-real
  revalidation on the canonical base.

## Thesis

After a capitulation down-move in XAUUSD, a NAS Top/Bottom **LONG** signal that
fires while volatility is expanded (ATR ratio > 1.3) and the daily trend is not
overbought (RSI-1D < 50) marks a high-probability mean-reversion long. Entry on
the next 4H open; risk defined by structure and ATR; targets in R multiples.

## Why v1 failed (and must not be repeated)

The v1 backtest engine read the wrong inputs:

1. **Signal**: it used `nas_long` (study-values derived), which is near-dead
   (`nas_signal_study_long` = 12 True in 10 years). The real signal lives in the
   pine-label fields (`nas_label_long_event` = 452 True). v1 found 1–3 signals.
2. **ATR**: it recomputed ATR with **Wilder** smoothing instead of the legacy SMA
   formula. The canonical slim already carries the legacy ATR
   (`atr14_sma_tr`, `atr14_sma30_ratio`).

v2 fixes both by reading the **canonical slim fields** (schema_version 2).

## Data lineage

- Source: canonical slims (`slim_features/XAUUSD/4H/` + `/1D/`), produced by
  `scripts/extract_replay_features.py` from cold-storage RAW replay.
- Registry: `docs/data/dataset_registry.json` (active blocks only).
- 1D RSI is attached to each 4H bar by an **as-of backward join on `close_epoch`**,
  reusing the verified join logic of `scripts/build_crosstf_dataset.py` (the same
  close_epoch semantics that give the cross-TF layer zero future leak). The ISO
  `ts` field (replay cursor) is never used for join/dedup/ordering.
- `report.json.provenance` records the exact registry entries, raw/slim paths, and
  code commit used, so any result is reproducible.

## Signal rule (authoritative values in config.json)

Two modes are run side by side:

- **Primary (official, legacy-faithful)** — `signal.modes.primary`. For each NAS
  LONG event `e` (`nas_label_long_event` true), open at most one trade at the
  **first 4H candle `c` in `[e, e+5]`** where the full conjunction holds:
  `nas_label_long_recent` true and `nas_label_recent_long_bars ≤ 5`, ATR ratio >
  threshold, RSI-1D < threshold. This honors the legacy monitor's recency window
  (the conjunction may align a few candles after the NAS event).
- **Sensitivity (event-only)** — `signal.modes.sensitivity`. The conjunction must
  hold at the NAS event candle `e` itself.

Empirical (pre no-overlap, full 2016–2026): raw NAS events = 452; primary signals
= 90; event-only signals = 57. Primary (90) closely approximates the legacy
reference (~86); the 33-signal gap is exactly the delayed-alignment captured by
the recency window. This reconciles the legacy count without changing the source.

## Trade construction (authoritative values in config.json)

- Entry: open of the candle after the signal (`entry.fill`). Never the signal close.
- Stop: `min(structural 3-bar low, entry − atr_mult × atr14_sma_tr)` (`stop`).
- Targets: R multiples `targets.r_multiples` (primary `targets.primary_r` = 2R).
- Time limit: `time_limit_bars` 4H candles; unresolved at horizon → exit at close.
- Intrabar: `intrabar` = stop_first (pessimistic; ties resolve to stop).
- Costs: `costs_usd_roundtrip` applied as net-R adjustment (cost / risk).
- Trade generation: `no_overlap` (one open trade at a time),
  `max_trades_per_nas_event` = 1, `cooldown_bars` = 0 (off by default; ON would
  diverge from legacy, which 90≈86 indicates did not use a cooldown).
- Right-censoring: trades unresolved at series end are flagged and counted
  (`right_censoring`).

## Regimes

Bucketed by entry year (`regimes.buckets`): pre-COVID (2016–2019), COVID (2020),
inflation/bear-macro (2021–2022), gold-bull/recent (2023–2026). Aggregate views:
total, ex-COVID, COVID-only, by-regime.

## Metrics

Per trade and aggregate per `_schema/report.schema.json`: R real, MFE_R, MAE_R,
win%, avg/median/sum R, profit factor, max losing streak, sum-R excluding top
5/10, MFE/MAE means, exit-reason mix, by-regime, by-cost, mode comparison.

## Decision criteria

Two-stage gate per `_schema/DECISION_FLOW.md` and thresholds in
`config.json.decision_gates`. Stage 1 = technical validity (no leak, entry next
open, stop>0). Stage 2 = merit (sample, expectancy, regime robustness, outlier
robustness). The result is a recommendation only; a human applies any catalog
transition (see `_schema/STATUS_TAXONOMY.md`).

## Known limitations / risks

- Sample is modest (~90 pre no-overlap over 10 years; smaller after no-overlap and
  far smaller per regime bucket, e.g. 2024–2025). Per-regime stats are indicative,
  not conclusive.
- The legacy "83.7% win / 86 trades" claim's exact provenance (period, source) is
  not fully documented; v2 reports its own numbers honestly rather than targeting
  reproduction of the legacy figure.

## Reproduction

The backtest script (to be created in a later, separately authorized step,
`scripts/backtest_xau_4h_capitulation_v2.py`) reads only this `config.json`,
processes canonical slims read-only, and writes `trades.jsonl` / `report.json` /
`summary.md` into this directory. No backtest has been run yet.
