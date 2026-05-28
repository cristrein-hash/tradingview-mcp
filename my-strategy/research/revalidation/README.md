# Strategy Revalidation Lab

Clean, canonical area for **revalidating legacy strategies against the new
canonical data base** before deciding what survives, what becomes production,
what is downgraded, and what is removed from the core system.

## Why this exists

The old `my-strategy/research/` tree (`backtests/`, `experimental/`, `proposals/`)
mixed exploratory work, dead fronts, and partial/close-only backtests. Decisions
about production were being made on top of that noise. This lab is a **separate,
disciplined space** with one job: produce **traceable, reproducible revalidation
evidence** using only the canonical data layer.

## Place in the architecture

```
DATA           RAW replay · manifests · dataset_registry.json        (source of truth, immutable)
FEATURES       extract_replay_features.py · slim_features/ (schema 2) (canonical features)
ANALYTICS      build_crosstf_dataset.py · slim_features/.../cross_tf/ (cross-TF, no future leak)
STRATEGY TRUTH my-strategy/strategies/catalog.json                    (single source of status/evidence)
REVALIDATION   my-strategy/research/revalidation/  <-- THIS LAB       (read-only experiments -> recommendations)
PRODUCTION     strategy_rules.json · monitor · recheck · receiver     (live; changed only AFTER revalidation)
```

## The one rule

**The lab is READ-ONLY on data and RECOMMENDATION-ONLY on decisions.**

- It NEVER edits RAW / manifests / registry / extractor / cross-TF.
- It NEVER writes `catalog.json` or `strategy_rules.json`.
- It NEVER touches production (monitor / recheck / receiver / LaunchAgents).
- It produces a `report.json` whose `decision.result_status` is a **recommendation**.
  A human reads `summary.md` + `report.json` and *manually* applies any catalog
  transition, recording `revalidation_ref` back to the report.

## Layout

```
revalidation/
  README.md                 # this charter
  .gitignore                # ignores **/trades.jsonl (bulk, regenerable)
  _schema/
    config.schema.json      # contract for every config.json
    report.schema.json      # shared report contract (cross-strategy comparable)
    STATUS_TAXONOMY.md       # 6 result statuses + map to catalog.validation_status
    DECISION_FLOW.md         # 2-stage decision flow (technical validity, then merit)
  <STRATEGY_ID>/<version>/
    methodology.md           # thesis + data lineage + criteria (prose; references config)
    config.json              # the ONLY source of parameters the script reads
    trades.jsonl             # per-trade output (gitignored)
    report.json              # aggregate EVIDENCE (tracked)
    summary.md               # human TL;DR + recommendation (tracked)
```

## What is tracked vs ignored

- **Tracked (git):** `README.md`, `_schema/*`, `methodology.md`, `config.json`,
  `report.json`, `summary.md` — the design and the evidence are part of the
  auditable record.
- **Ignored (git):** `**/trades.jsonl` — bulk, deterministically regenerable from
  `config.json` + canonical data + the recorded code commit. `report.json` records
  the commit hashes and data paths so any result is reproducible without it.

## Source-of-truth boundaries

- `config.json` is the **single** source of parameters. `methodology.md` explains
  the *why* and *references* config — it must never become a second, divergent
  source of parameter values.
- Each `<version>/` directory is **immutable once a result is published**. A
  re-run with changed parameters becomes a new version directory.

## Current revalidations

| Strategy | Version | Status |
|---|---|---|
| `XAU_4H_REVERSAL_CAPITULATION` | v2 | scaffolded (methodology + config); backtest not yet run |
