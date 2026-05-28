# Revalidation Status Taxonomy

A revalidation produces `report.json.decision.result_status`. This is a
**recommendation**, not a catalog status. A human reviews the evidence and
*manually* applies any transition to `catalog.json`, recording `revalidation_ref`.

## Two-stage gate (see DECISION_FLOW.md)

1. **Technical validity** — did the backtest run correctly? (no future leak,
   entry = next-bar open, every stop distance > 0, report generated). If this
   fails, the verdict is `inconclusive` **regardless of metrics** — the metrics
   from a broken run must never be interpreted. This is the direct guard against
   the 2026-05-18 class of mistake (acting on output of broken architecture).
2. **Merit** — only reached if technically valid. Judges expectancy, sample, and
   regime robustness.

## The six result statuses

| `result_status` | Meaning | Reached when |
|---|---|---|
| `inconclusive` | Cannot judge merit | Stage 1 failed (technical), OR moderate sample (`min_n_needs_more_data` ≤ n < `min_n_candidate`), OR mixed/ambiguous merit |
| `needs_more_data` | Too few trades to judge | n < `min_n_needs_more_data` |
| `fail` | Strategy does not work | avg_R ≤ 0, or PF < 1.0, or breaks badly |
| `reject_or_downgrade` | Should lose status/deployment | negative or fragile enough that current catalog status is unjustified |
| `pass` | Works, but not full VALIDATED bundle | positive expectancy but fragile (single regime, or depends on top trades, or n just above gate) |
| `candidate_for_VALIDATED` | Full evidence bundle, positive, robust | technically valid + R-real + MFE/MAE + regime coverage + traceable dataset + n ≥ `min_n_candidate` + avg_R>0 + PF ≥ `pf_min` + ex-COVID positive + ex-top5 positive |

Note: `candidate_for_VALIDATED` is only *possible* for an R-real backtest. A
close-only backtest can never exceed `pass` (ceiling = ACTIVE_CANDIDATE), per the
catalog rule "close-only never validates".

## Recommended catalog transition per status

Catalog axes: `validation_status` ∈ {VALIDATED, ACTIVE_CANDIDATE, RESEARCH,
REFERENCE_ONLY, REJECTED, LEGACY_ARCHIVE, UNKNOWN_NEEDS_DECISION};
`deployment_status` ∈ {LIVE, LIVE_CONTEXT, LIVE_DORMANT, SHADOW, WATCH_ONLY,
DISABLED, NOT_DEPLOYED}.

| `result_status` | recommended `validation_status` | deployment note |
|---|---|---|
| `candidate_for_VALIDATED` | propose **VALIDATED** (human confirms) | consider SHADOW → LIVE only after human sign-off |
| `pass` | **ACTIVE_CANDIDATE** | keep SHADOW / WATCH_ONLY |
| `inconclusive` | keep **RESEARCH** | unchanged |
| `needs_more_data` | keep **RESEARCH** / ACTIVE_CANDIDATE | flag: collect more data |
| `reject_or_downgrade` | **downgrade** (e.g. ACTIVE_CANDIDATE→RESEARCH) | downgrade deployment (e.g. LIVE→WATCH_ONLY) |
| `fail` | propose **REJECTED** or **LEGACY_ARCHIVE** | DISABLED / NOT_DEPLOYED |

## Applying a decision (human, manual)

1. Read `summary.md` + `report.json`.
2. If accepting the recommendation, edit `catalog.json` for the strategy:
   - set the new `validation_status` / `deployment_status`;
   - add `revalidation_ref` = path to the `report.json`;
   - add `revalidated_at` = date.
3. The lab does **not** perform step 2. Ever.
