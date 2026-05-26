---
name: repo-governance-cleanup
description: Manages repository hygiene, archive decisions, retention, cold storage, git discipline, documentation updates, and safe cleanup. Use when cleaning files, archiving legacy code, moving cold data, updating inventory, or preparing commits.
---
# Repo Governance & Cleanup

Keep the repository and host clean without ever destroying live or irreplaceable data. Verify before you move or delete.

## Classify first
Tag every file before acting:
- **HOT / production** — breaking it breaks live ingestion/monitoring.
- **PIPELINE_ACTIVE** — scheduled/indirectly-invoked data pipeline.
- **MONITORING_ACTIVE** — health/review jobs.
- **RESEARCH** — manual analysis/backtest tools (safe to move with care).
- **ONE_OFF** — completed research scripts.
- **LEGACY** — superseded, kept for reference.
- **COLD_DATA** — RAW datasets / historical backtests for the external drive.
- **DELETE_CANDIDATE** — regenerable / cache / tmp / smoke.
- **UNKNOWN** — investigate before touching.

## Cleanup rules (hard)
- **Never delete before `git grep`** (and a reference search) for live usage.
- **Never move a LaunchAgent-bound file** (script or its log path) without a lockstep plan (`bootout` → move → edit plist `<string>` → `bootstrap` → validate).
- **Tracked files = caution** — deletion shows in git; confirm intent.
- **Safe delete candidate** = gitignored (`git check-ignore`) **AND** no open handle (`lsof`) **AND** no live reference.

## Archive vs delete
- **Archive** (move, reversible) — for anything with historical value.
- **Delete** — only for cache/tmp/smoke/regenerable artifacts.
- **Cold storage** — for RAW datasets and historical backtests.

## External cold storage — `/Volumes/GUTS_ LACIE/TradingData/`
Mandatory procedure before deleting a local file (ALL steps):
1. `gzip -c` to the external drive (lossless);
2. SHA256 of the original;
3. SHA256 of the `.gz`;
4. `gzip -t` (integrity);
5. **roundtrip**: `gunzip -c <.gz> | sha256` == original SHA256;
6. write a manifest under `…/TradingData/manifests/`;
7. **explicit per-batch deletion approval** from the operator — only then delete the local.

If the external drive is disconnected, **production must not break** — nothing live depends on it.

## logs/backtests policy
- RAW replay datasets → external (gzipped, validated).
- Local keeps only active/needed data.
- **Keep local: 8× v6 4H** dumps — `find_dream_demands.py` references them.
- **Keep local: `XAUUSD_240_2025-11-19_to_2026-05-19.jsonl`** — `draw_xau_4h_trades.py` hardcodes it.
- Never reduce RAW payload; `gzip` is allowed because it's lossless.

## Git discipline
- Small, focused commits.
- `git diff --check` (whitespace/conflict markers).
- Secret scan the staged diff before committing.
- Never mix docs / code / data in one commit.
- Leave the working tree clean; push only when asked.

## Docs to keep current (after real changes)
- `docs/architecture/OPERATIONAL_INVENTORY.md`
- `docs/architecture/DATA_STORAGE_POLICY.md`
- `docs/architecture/SESSION_STATE_*.md`
Update docs to reflect what actually changed — not aspirational state.
