# Signal Outcome Lab — Architecture (Design)

**Status:** design only. **Not implemented.** No code, no LaunchAgent, no data
movement, no production effect from this document.

**Date:** 2026-05-28.
**Author:** post-incident redesign following decommission of
`com.cristrein.enrich-indicator-outcomes`.

This document defines the architecture of the **Signal Outcome Lab**, the clean
replacement for the decommissioned outcome enrichment layer. It is the source
of design intent until and unless explicitly amended.

## 1. Objective

The Signal Outcome Lab computes **R-multiple outcomes** for signals already
collected by the Signal Journal (`tv_webhook_receiver.py` →
`indicator_signals.jsonl`), producing a clean, provenance-rich outcomes dataset
that downstream consumers (D2R daily, weekly review, edge reports) can trust.

It **replaces** `enrich_indicator_outcomes.py`, which was decommissioned on
2026-05-28 (see `OPERATIONAL_INVENTORY.md` section 12) because it:
- called `chart_set_symbol` with bare tickers (no provider prefix), allowing
  TradingView to silently resolve to OANDA instead of PEPPERSTONE, contaminating
  the outcomes;
- ran as a background batch that held `/tmp/tradingview_chart.lock` for hours,
  interfering with other chart consumers;
- mixed signal collection assumptions with chart-bound evaluation in a way that
  did not respect provider policy nor lock discipline.

The Lab is the architectural reset: outcomes are produced **only** under
explicit provider hard gates, **only** within controlled chart windows (when
chart is needed at all), and **only** with manifest/provenance recorded for
every record.

## 2. Principles

Hard rules, in priority order:

1. **Batch/manual first.** No LaunchAgent or `StartCalendarInterval` initially.
   The Lab runs only when an operator invokes it (or an explicit orchestrator
   like `safe_backtest_window.sh` invokes it inside a window).
2. **Provider hard gate.** Every signal processed must satisfy
   `symbol == "PEPPERSTONE:<BASE>"` with `BASE` in the active whitelist.
   Anything else is **skipped + recorded** (`SKIPPED_PROVIDER_MISMATCH` /
   `SKIPPED_UNSUPPORTED_SYMBOL`). The gate **rejects** silently-resolving
   defaults like OANDA, VANTAGE, FOREXCOM, FX, FX_IDC.
3. **Active whitelist (frozen at design time, 2026-05-28):**
   `XAUUSD, XAGUSD, ETHUSD, US500, EURUSD, USOUSD`.
   Changes to this whitelist require updating
   `tv_webhook_receiver.py::KNOWN_BASE_SYMBOLS` AND this document AND
   strategy_rules.json AND explicit operator authorization. No silent expansion.
4. **No bare tickers anywhere.** Any code path that emits a `symbol` operationally
   (config field, MCP call arg, log record `symbol` field, alert payload
   downstream) must carry `PEPPERSTONE:<BASE>`. `base_symbol` (without
   provider) is internal-only.
5. **Canonical-slim-first.** When the asset/timeframe is covered by the
   canonical slim/features layer (`slim_features/`, produced by
   `scripts/extract_replay_features.py` from validated RAW), the Lab reads from
   there. It does **not** touch TradingView for those (asset, timeframe) pairs.
6. **TradingView chart only as controlled fallback.** When canonical data is
   not available for a given (asset, timeframe), the Lab may use the live
   TradingView chart **only** inside a chart-window-exclusive context (see
   section 8). Outside the window, the Lab does not touch the chart.
7. **Unified lock.** All chart access goes through a single, documented
   filesystem mutex (current: `/tmp/tradingview_chart.lock` via `flock`).
   Lock-busy → abort or timed wait, never override.
8. **Manifest/provenance on every output.** Each outcome record carries
   `evaluator_version`, `run_id`, `data_source`, `data_source_ref`, raw +
   normalized symbol, provider, evaluated_at, and the signal_hash it refers to.
   Every batch emits a separate `<batch>.manifest.json`.
9. **Append-only outputs; LOG_MUTATION_POLICY-compliant.** The Lab never
   rewrites or removes its own past outputs while a writer is running. Past
   contaminated outputs are quarantined (file rename) per the policy.
10. **Idempotence.** Re-running the Lab on the same set of signals with the
    same evaluator_version produces identical outcomes (same outcome_id, same
    fields), or it returns the existing outcome rather than duplicating.

Hard prohibitions (anti-rules):

- ❌ No background daemon controlling the chart.
- ❌ No `chart_set_symbol(bare_ticker)` from anywhere in this codepath.
- ❌ No fabrication of outcomes when data is missing — emit `SKIPPED_*` or
  `UNKNOWN`, never invent.
- ❌ No silent expansion of the whitelist to "unblock" a signal.
- ❌ No reading of `*.contaminated_pre_pepperstone_fix_*` files for operational
  outcomes (only for audit comparison; see section 10).
- ❌ No write to `indicator_signals.jsonl` (Signal Journal is read-only from the
  Lab's perspective).

## 3. Inputs

The Lab consumes (read-only):

| Input | Path / Owner | Purpose |
|---|---|---|
| Signal Journal | `alert-bridge/logs/indicator_signals.jsonl` (writer: `tv_webhook_receiver.py`) | the universe of signals to evaluate |
| Quarantine journal | `alert-bridge/logs/indicator_signals_quarantined.jsonl` | informational; audit of rejected signals; never produces operational outcomes |
| Watchlist rejections | `alert-bridge/logs/watchlist_rejections.jsonl` | informational; audit of signals dropped before quarantine |
| Canonical slim features | `slim_features/<SYMBOL>/<TF>/*.jsonl` (writer: `scripts/extract_replay_features.py`) | primary OHLCV/features source when available |
| Cross-TF analytics | `slim_features/<SYMBOL>/cross_tf/*.jsonl.gz` (writer: `scripts/build_crosstf_dataset.py`) | optional context for multi-timeframe outcomes |
| RAW replay (cold) | `/Volumes/GUTS_ LACIE/TradingData/raw_replay/...` | secondary; only via slim feature extraction, not direct |
| Quarantined legacy outcomes | `*.contaminated_pre_pepperstone_fix_2026-05-28` | audit-only (OANDA vs PEPPERSTONE comparison, section 10); never operational input |
| TradingView live chart (last resort) | via MCP `data_get_ohlcv` etc. | only inside chart-window-exclusive context |

The Signal Journal is the **only authoritative source of which signals exist**.
The Lab does not invent signals.

## 4. Outputs

Per batch, the Lab writes (append-only, manifest-tracked):

| Output | Path (proposed) | Notes |
|---|---|---|
| Clean outcomes | `alert-bridge/logs/signal_outcomes_lab/outcomes_<run_id>.jsonl` | one record per evaluated signal |
| Batch manifest | `alert-bridge/logs/signal_outcomes_lab/outcomes_<run_id>.manifest.json` | run_id, evaluator_version, input signal range, counts per outcome_status, lock holder, environment |
| Aggregated current outcomes | `alert-bridge/logs/signal_outcomes_lab/outcomes_current.jsonl` (symlink or rebuilt index) | a flat, dedup-by-outcome_id rollup of all clean outcomes across runs; consumers read this |
| Audit/debug log | `alert-bridge/logs/signal_outcomes_lab/run_<run_id>.log` | stdout/stderr of the batch run, for forensics |

Outcome status enum (every record has exactly one):

- `CLEAN` — outcome computed successfully under all gates; safe for operational
  use by downstream consumers.
- `NEEDS_REGENERATION` — outcome was once computed but the inputs were
  identified as contaminated (e.g. an earlier OANDA-based outcome); current
  record is a placeholder until a clean recomputation happens.
- `QUARANTINE_ONLY` — outcome exists in the quarantined legacy file but
  cannot be safely promoted (data integrity unresolved); informational.
- `UNKNOWN` — evaluator cannot decide due to missing prerequisites
  (e.g. canonical slim doesn't cover the range AND the chart window is closed);
  this signal will be re-attempted later.
- `SKIPPED_UNSUPPORTED_SYMBOL` — signal's `base_symbol` is outside the active
  whitelist; the Lab refuses to evaluate.
- `SKIPPED_PROVIDER_MISMATCH` — signal's `symbol` field does not start with
  `PEPPERSTONE:` (should not happen post-2026-05-28 due to receiver hard gate,
  but the Lab still checks defensively).

The aggregated `outcomes_current.jsonl` only contains records with
`outcome_status == CLEAN`. Other statuses live in their batch's
`outcomes_<run_id>.jsonl` for audit but never feed operational decisions.

## 5. Provider policy

Hard rules enforced by the Lab on every signal it considers:

1. `signal.symbol` MUST start with `PEPPERSTONE:`.
   - If absent or different prefix: outcome_status = `SKIPPED_PROVIDER_MISMATCH`;
     do not call `chart_set_symbol`; emit a warning in the audit log.
2. `signal.base_symbol` MUST be in the whitelist (frozen 2026-05-28:
   `XAUUSD, XAGUSD, ETHUSD, US500, EURUSD, USOUSD`).
   - Otherwise: outcome_status = `SKIPPED_UNSUPPORTED_SYMBOL`.
3. Any chart-touching MCP call MUST pass `PEPPERSTONE:<BASE>` explicitly.
   - Bare-ticker call sites are a code-review failure, not a runtime fallback.
4. Any new symbol that the operator wants the Lab to evaluate requires:
   - addition to `KNOWN_BASE_SYMBOLS` in `tv_webhook_receiver.py`;
   - addition to `allowed_symbols` in `strategy_rules.json`;
   - addition here;
   - explicit operator authorization.
   No silent expansion.

These rules are enforced in code (when implemented) by a single validation
function called at the start of every signal evaluation. The function never
"normalizes" a bad input upward — it rejects.

## 6. Data source policy

Priority order for OHLCV / context lookup (per signal × timeframe):

1. **Canonical slim** — `slim_features/<SYMBOL>/<TF>/` if available for the
   signal's timestamp range AND timeframe AND base_symbol. Use this. Record
   `data_source: "canonical_slim_v2"` and `data_source_ref` pointing to the
   slim file + record range used.
2. **Cross-TF** — when the outcome needs multi-timeframe context (e.g. 1D
   filter for a 4H signal), read from `slim_features/.../cross_tf/`. Record
   `data_source: "cross_tf_v2"`.
3. **TradingView live chart (FALLBACK ONLY)** — only when no canonical
   coverage exists for the (asset, timeframe, time window) needed. Subject to
   section 8 (chart lock + safe window). Record `data_source: "tv_chart_live"`
   AND the chart symbol/timeframe verified at evaluation time.
4. **Hard fail (no synthesis)** — if neither canonical nor chart can supply,
   outcome_status = `UNKNOWN` with `data_source: "none"`. Never invent data.

Per (base_symbol × timeframe), expected coverage as of 2026-05-28:
- `XAUUSD` 15M/30M/1H/4H/1D — canonical slim available (`slim_features/XAUUSD/`).
- `XAGUSD, ETHUSD, US500, EURUSD, USOUSD` — canonical slim **not** available
  yet; the Lab will fall back to TV chart (with all gates) until canonical
  coverage is extended. This is a known limitation, not a defect.

When `data_source == "tv_chart_live"`, the Lab additionally:
- verifies `chart_get_state` returns `symbol == "PEPPERSTONE:<expected>"` and
  the expected timeframe AFTER the `chart_set_symbol`/`chart_set_timeframe`
  calls;
- aborts the signal (UNKNOWN) on any mismatch — does not proceed with the
  wrong chart.

## 7. Execution model

The Lab is a **batch-mode tool**, manually invoked. There is no scheduler.

Invocation contract (proposed):

```
scripts/run_signal_outcome_lab.py \
  --evaluator-version <semver, e.g. "v0.1.0"> \
  --run-id <unique, e.g. "manual-2026-05-30T14:00Z"> \
  --signals-from <timestamp> --signals-to <timestamp> \
  [--symbol PEPPERSTONE:XAUUSD] \
  [--timeframe 4H] \
  [--allow-chart-fallback] \
  [--dry-run]
```

Per-batch flow (specification, not yet implemented):

1. **Acquire chart lock** if `--allow-chart-fallback` set (else skip).
   Lock-busy → abort with clear message; never override.
2. **Read signals** from the Signal Journal in the requested window.
   Filter: `validation_status == "valid"` AND `symbol` starts with
   `PEPPERSTONE:` AND `base_symbol` in whitelist.
3. **Maturity gate.** A signal is "mature" when enough bars have closed after
   `ts_signal` for the chosen horizon. Immature signals are simply not picked
   up by this batch; they will be on a later run.
4. **Idempotence check.** For each mature signal, compute `outcome_id` from
   `(signal_hash, evaluator_version, horizon, data_source_resolution)`. If a
   prior record with the same `outcome_id` exists in
   `outcomes_current.jsonl` with `outcome_status == CLEAN`, skip
   (already done).
5. **Resolve data source** per section 6.
6. **Evaluate outcome** (R-multiple, MFE, MAE, exit reason — exact metric
   schema in section 9).
7. **Emit record** to `outcomes_<run_id>.jsonl` (append-only).
8. **Update manifest** counts.
9. **Release chart lock** (if held).
10. **Rebuild `outcomes_current.jsonl`** by re-reading all
    `outcomes_<run_id>.jsonl` and emitting the latest `CLEAN` record per
    outcome_id (write to `outcomes_current.jsonl.tmp` then atomic mv; since
    nobody is writing to this file in parallel by design, this is safe).

The Lab **never** writes back to `indicator_signals.jsonl` or any input file.

## 8. Chart lock policy

Cross-references LOG_MUTATION_POLICY.md and OPERATIONAL_INVENTORY.md sections
on chart consumers. Specific rules for the Lab:

1. The Lab uses the **same** `/tmp/tradingview_chart.lock` mutex as the XAU
   monitor, the existing draw scripts, the replay collector. **Unified lock.**
2. Lab MUST acquire the lock with a documented timeout (e.g. 60s) before any
   `chart_set_symbol` / `chart_set_timeframe` / `data_get_ohlcv` call.
3. Lab MUST release the lock in a `finally:` (or equivalent) — never leak.
4. Lab MUST verify chart state after every set_symbol/set_timeframe call
   (`chart_get_state` returns expected symbol + timeframe). Mismatch → abort,
   do not retry, do not proceed with the wrong chart.
5. The Lab MUST NOT run during:
   - active visual audit window (an explicit pause flag like
     `/tmp/visual_audit_active.flag` will be honored — design pending);
   - replay collection (the existing pattern: replay collector takes the lock
     for the whole window);
   - any other chart-exclusive operation.

   Mechanism: in addition to the chart lock, the Lab honors an explicit
   "do not touch chart" flag list. If any flag is present, the Lab refuses to
   start (or finishes its current signal then stops, before touching chart
   again).
6. `safe_backtest_window.sh` (today already pauses the XAU monitor) MUST be
   extended (when the Lab is implemented) to ALSO pause the Lab and any future
   chart consumer.

The Lab never holds the lock for more than one signal at a time. If a batch
processes N chart-bound signals, it acquires/releases the lock N times — each
turn small enough to interleave with other consumers.

## 9. Schema preliminar — outcome record

Per outcome (one JSON-line per record):

```json
{
  "outcome_id":            "sha256(signal_hash | evaluator_version | horizon | data_source_resolution)[:16]",
  "signal_hash":           "<hash from indicator_signals.jsonl>",
  "run_id":                "<batch run id>",
  "evaluator_version":     "<semver>",
  "evaluated_at":          "<ISO8601 with timezone, microseconds>",

  "base_symbol":           "<e.g. XAUUSD>",
  "symbol":                "PEPPERSTONE:<base_symbol>",
  "provider":              "PEPPERSTONE",
  "timeframe":             "<e.g. 4H>",

  "ts_signal":             "<ISO8601 from the source signal>",
  "horizon":               {"bars": 20, "tf": "4H"},

  "data_source":           "canonical_slim_v2 | cross_tf_v2 | tv_chart_live | none",
  "data_source_ref":       "<path or chart snapshot identifier>",

  "provider_status":       "ok | mismatch_corrected | mismatch_skipped",
  "outcome_status":        "CLEAN | NEEDS_REGENERATION | QUARANTINE_ONLY | UNKNOWN | SKIPPED_UNSUPPORTED_SYMBOL | SKIPPED_PROVIDER_MISMATCH",

  "entry_price":           1234.56,
  "stop_price":             1200.00,
  "target_price":           1300.00,
  "horizon_close":          1290.45,

  "close_after_horizon":    1290.45,
  "mfe":                    {"price": 1305.10, "R": 1.83},
  "mae":                    {"price": 1219.30, "R": -0.42},

  "directional_result":     "long_close_above_entry | long_close_below_entry | short_close_below_entry | short_close_above_entry | none",
  "hit_result":             "stop | target | time_limit | not_applicable",

  "errors":                 [],
  "warnings":               [],

  "provenance": {
    "signal_source_path":  "alert-bridge/logs/indicator_signals.jsonl",
    "raw_symbol_observed": "<as seen in the source signal>",
    "horizon_bars_used":   20,
    "data_window_from":    "<ISO8601>",
    "data_window_to":      "<ISO8601>",
    "chart_lock_holder":   "signal-outcome-lab/<run_id> | null"
  }
}
```

Notes:
- All R-multiples are gross (no cost adjustments at this layer — cost models
  are a consumer's concern).
- `outcome_id` is deterministic: same signal + same evaluator + same horizon +
  same data source resolution = same outcome_id. Enables idempotence.
- `provider_status` records whether the provider was already correct on the
  input, was corrected upstream (receiver normalization), or was rejected
  (skip path).
- Fields can be `null` when not applicable (e.g. `target_price` for
  outcomes computed without an explicit target).

## 10. Relationship to quarantined legacy outcomes

`alert-bridge/logs/indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28`
(330 records) is **preserved** but treated as **not authoritative**.

Permitted use:
- **Audit comparison** (section 12 phase 2): a stratified sample is recomputed
  via the Lab once it exists; for each pair (legacy_outcome, lab_outcome) the
  classification (`SAFE_TO_USE_DIRECTIONAL` / `NEEDS_REGENERATION` /
  `QUARANTINE_ONLY` / `UNKNOWN`) informs a single `audit_report_2026-05-28.md`
  document (not a programmatic feedback into operational outcomes).
- **Historical reference** only. The quarantine file is `read` access; never
  modified, moved, or deleted by the Lab.

Forbidden use:
- ❌ Feeding directly into `outcomes_current.jsonl`.
- ❌ Being interpreted as evidence of edge in strategy decisions.
- ❌ Promotion to CLEAN without recomputation under the Lab's gates.
- ❌ Deletion (the file is the only existing record of those 330 evaluations).

## 11. Relationship to consumers

Until the Lab produces `outcomes_current.jsonl`:

- `alert-bridge/auto_d2r_daily.py` — invocation is **paused** by the
  moratorium (`com.cristrein.d2r-daily` unloaded). When the Lab produces
  clean outcomes AND `outcomes_current.jsonl` exists, operator may
  re-bootstrap the LaunchAgent. The script's outcomes appendix builder
  (`build_indicator_outcomes_summary`) currently emits
  `OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH` on the quarantine state; this
  branch should continue working as a safety net.
- `alert-bridge/weekly_review.py::check_enrich_v2` — kept active but reports
  `status: OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH` while no clean
  outcomes exist. When the Lab is live, this function (or its replacement)
  should read from `outcomes_current.jsonl` and report real counts.
- `alert-bridge/report_indicator_edge.py` — manual; currently emits the
  `OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH` report when run against the
  quarantine state. When the Lab is live, it should read
  `outcomes_current.jsonl` instead of the legacy path.

**No consumer is allowed to interpret "outcomes file missing" as "zero edge".**
This is hard-coded into the patched consumers and is reinforced by this
document. Future consumers added to the codebase must follow the same rule.

When `outcomes_current.jsonl` first appears with `CLEAN` records, consumers
**do not** automatically integrate the data — each consumer's reactivation is
an explicit operator decision (a separate authorized step, with verification
of the Lab's run manifest).

## 12. Phased roadmap

| Phase | Deliverable | Status |
|---|---|---|
| **0** | Design doc (this file) | **DONE** (2026-05-28) |
| **1** | `INDICATOR_SIGNAL_POLICY.md` — formalize PEPPERSTONE/whitelist policy, list of forbidden providers, expansion process | pending — must precede Phase 2 |
| **2** | Audit OANDA vs PEPPERSTONE on stratified sample of the 330 quarantined records — produce `audit_report_2026-05-28.md` with per-record classification + aggregate per-symbol divergence statistics. Audit runs **read-only** on quarantine file plus a small chart window (under all gates of section 8) | pending Phase 1 |
| **3** | Lab MVP — `scripts/run_signal_outcome_lab.py` manual batch only; canonical-slim-first; provider hard gate; lock-aware. No LaunchAgent. Validation against a few hand-picked signals before any bulk run | pending Phase 2 |
| **4** | Regenerate outcomes for the subset of legacy signals where the audit (Phase 2) says regeneration is meaningful; do **not** regenerate `SAFE_TO_USE_DIRECTIONAL` entries blindly; do **not** import from quarantine into operational outcomes | pending Phase 3 |
| **5** | Consumers read clean outcomes — point `auto_d2r_daily.py`, `report_indicator_edge.py`, and `weekly_review.py::check_enrich_v2` at `outcomes_current.jsonl`. Validate each in isolation before re-enabling | pending Phase 4 |
| **6** | Re-enable `com.cristrein.d2r-daily` — `launchctl bootstrap`; verify the daily Telegram now shows real outcome content (not the `OUTCOMES_UNAVAILABLE_*` banner) | pending Phase 5 |
| **7** | (Optional) Schedule the Lab — if and only if a sufficiently safe schedule + unified lock + window-exclusivity story exists. Default: stays manual | pending Phase 6 |

Each phase requires explicit operator authorization. No phase auto-starts the
next.

## 13. Out of scope

This document does **not** cover:

- Code implementation of any of the above (Phases 3+ produce code under
  separate authorization).
- Creation or restoration of any LaunchAgent for the Lab (Phase 7 only, if
  ever).
- Regeneration of outcomes (Phase 4 only, with its own authorization).
- Visual audit of strategies (separate workstream;
  `safe_backtest_window.sh` and the existing draw scripts).
- Changes to `strategy_rules.json` or `catalog.json` beyond what the
  PEPPERSTONE policy already mandates.
- TradingView alert definitions (alarmes) — unchanged; the receiver normalizes
  in-bridge.
- Cost models, slippage models, position sizing. Outcomes are gross R; consumers
  apply their own cost overlays.
- Real-time / streaming outcome computation. The Lab is post-hoc batch by design.

## 14. Cross-references

- `docs/architecture/OPERATIONAL_INVENTORY.md` — section 12 (enrich
  decommissioned), section 13 (outcome automation moratorium).
- `docs/architecture/LOG_MUTATION_POLICY.md` — append-only log discipline; the
  Lab's outputs are subject to this policy.
- `docs/architecture/DATA_STORAGE_POLICY.md` — cold storage rules for canonical
  inputs (RAW / manifests / slim_features).
- (future) `docs/architecture/INDICATOR_SIGNAL_POLICY.md` — Phase 1; will be
  the operator-facing reference for the PEPPERSTONE/whitelist policy.
- `alert-bridge/tv_webhook_receiver.py::_normalize_indicator_parsed` /
  `_write_indicator_quarantine` / `write_indicator_signal` — current Signal
  Journal behaviour the Lab depends on.
- `scripts/extract_replay_features.py` / `scripts/build_crosstf_dataset.py` —
  canonical data sources the Lab prefers.

## 15. Change control

This document is amended only by an explicit operator authorization, in the
same commit that records the architectural change. Material changes (whitelist
expansion, removal of a hard gate, new data source addition, scheduling) must
update `OPERATIONAL_INVENTORY.md` in the same commit.

End of design document.
