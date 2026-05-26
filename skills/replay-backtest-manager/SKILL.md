---
name: replay-backtest-manager
description: Operates the TradingView Replay data-collection workflow for XAUUSD multi-timeframe research, including safe maintenance windows, feature capture, external cold storage, checksums, manifests, and production-restore discipline.
---

# Replay Backtest Manager

## Purpose

Operate and protect the TradingView Replay-based historical data collection workflow for the trading system.

This skill manages:

- TradingView Replay collection for XAUUSD 15M / 30M / 1H.
- `safe_backtest_window.sh`.
- Maintenance windows.
- TradingView/MCP/CDP preflight.
- External RAW archival to `/Volumes/GUTS_ LACIE/TradingData/`.
- gzip + SHA256 + manifest validation.
- Production restore checks.
- Avoiding orphan `server.js` processes.
- Preventing accidental production disruption.

The priority is reliability, consistency, and safe data collection. Speed is secondary.

---

## Core Context

The system runs primarily on the MacBook.

The iMac is only for External Factors / bridge operations.

Production components on the MacBook include:

- TradingView Desktop
- tv webhook receiver
- cloudflared tunnel
- external factors heartbeat
- XAU 4H monitor daemon
- Claude recheck
- TradingView MCP / CDP tooling
- replay-based backtest/data collection

External OHLCV sources are out of scope unless explicitly approved by the user.

TradingView Replay is the canonical mechanism for deep historical TradingView/MCP backtests.

---

## Non-Negotiable Principles

1. Do not use external OHLCV data unless the user explicitly approves.
2. Do not run replay collection outside `safe_backtest_window.sh`.
3. Do not reduce RAW payload unless the user explicitly approves.
4. Do not assume the chart has the correct indicators loaded.
5. Do not run another block without explicit user authorization.
6. Do not delete local RAW before external gzip + checksum + roundtrip + manifest validation and explicit user approval.
7. Do not alter receiver, LaunchAgents, secrets, or live alert logic during data collection.
8. If a run fails, restore production, stop, and report. Do not loop.
9. Separate mechanical success from data-quality success.
10. Preserve full RAW data; create derived/slim datasets only later if explicitly approved.

---

## Canonical Tools

Canonical collector:

```bash
alert-bridge/run_xau_replay_feature_collect.py
```

Canonical maintenance wrapper:

```bash
alert-bridge/safe_backtest_window.sh
```

Do not use `run_xau_15m_pullback_ohlcv.py` for deep historical collection. It uses scroll + OHLCV and does not reliably load deep history.

---

## Approved Symbol and Timeframes

Default symbol:

```text
PEPPERSTONE:XAUUSD
```

Timeframe mapping:

```text
15M = --timeframe 15
30M = --timeframe 30
1H  = --timeframe 60
```

---

## Indicator Baseline

Before any real collection block, the user must manually confirm the chart has:

- Custom OB baseline correct.
- Smart Money Concepts [LuxAlgo].
- NAS TOP BOTTOM DETECTOR.
- Market Order Bubbles - By Leviathan.
- Relative Strength Index.

Important nuance:

The Custom OB indicator may appear in JSON output as `Custom OB Detector v11 — Alert`; this is accepted as the correct baseline if the user confirms it is the current saved/updated indicator. TradingView can keep an older displayed Pine name even when the saved script/alert baseline is current.

The collector must capture full RAW payload:

- `ohlcv`
- `study_values`
- `pine_boxes`
- `pine_labels`
- `pine_shapes_bubbles`
- `pine_lines`

Do not reduce `pine_labels`, `pine_lines`, features, labels, or drawings unless the user explicitly approves.

---

## Current Data Collection Status

### XAU 15M

Target: 1 year.

Status:

- `2025-05-25 → 2025-08-25`: collected, gzip-archived externally, local raw pending/removed status must be checked from the latest session state.
- `2025-08-25 → 2025-11-25`: collected, gzip-archived externally, local removed.
- `2025-11-25 → 2026-02-25`: collected, gzip-archived externally, local removed.
- `2026-02-25 → 2026-05-25`: re-collected with confirmed Custom OB baseline, gzip-archived externally, local removed. Previous pre-baseline version is preserved in `superseded/`.

Current source of truth for `2026-02-25 → 2026-05-25` is:

```text
/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz
```

### XAU 30M

Target: 2 years, 4 blocks of 6 months.

Planned/current blocks:

- `2025-11-25 → 2026-05-25`: collected, gzip-archived externally, local removed.
- `2025-05-25 → 2025-11-25`: pending.
- `2024-11-25 → 2025-05-25`: pending.
- `2024-05-25 → 2024-11-25`: pending.

### XAU 1H

Target: 2 years, 4 blocks of 6 months.

Planned blocks:

- `2025-11-25 → 2026-05-25`: pending.
- `2025-05-25 → 2025-11-25`: pending.
- `2024-11-25 → 2025-05-25`: pending.
- `2024-05-25 → 2024-11-25`: pending.

---

## Mandatory Preflight Before Replay Collection

Before opening a maintenance window, verify:

### 1. Enrich/evaluator must be stopped or absent

```bash
pgrep -fl "OUTCOME EVALUATOR" || true
pgrep -fl enrich_indicator_outcomes || true
```

Both should be empty unless the user explicitly authorizes stopping them.

Reason:

- Enrich/evaluator uses Claude/MCP/chart.
- It competes with replay collection.
- It can leak orphan `server.js`.
- It does not respect the replay maintenance window by default.

### 2. Check orphan MCP processes

```bash
pgrep -fl "server.js" || true
```

Only legitimate `server.js` children are allowed. Orphans should be cleaned before collection.

### 3. Confirm receiver and public ingress

```bash
curl -s http://localhost:8787/health
curl -s -o /dev/null -w "%{http_code}\n" https://webhook.tdwclaudestrategy.org/health
```

Expected:

- local receiver OK
- public health returns `200`
- pause flag absent
- `claude_recheck:true`
- `secret_configured:true`

### 4. Confirm XAU monitor daemon is loaded before the window

```bash
launchctl list | grep xau-4h-monitor-daemon || true
```

### 5. Confirm chart manually

The user must confirm:

- symbol
- timeframe
- indicator layout

Never assume chart state.

---

## Maintenance Window Rules

All replay collection must go through:

```bash
alert-bridge/safe_backtest_window.sh
```

The wrapper is responsible for:

- pause flag
- bootout of XAU monitor daemon
- MCP cleanup
- conditional TradingView restart
- CDP/API validation
- collection command
- trap-based production restore
- post-checks

Never bypass the maintenance window without explicit approval.

---

## Smoke Commands

30M smoke:

```bash
alert-bridge/safe_backtest_window.sh --replay-smoke --timeframe 30
```

1H smoke:

```bash
alert-bridge/safe_backtest_window.sh --replay-smoke --timeframe 60
```

15M smoke does not need repeating unless code/layout changed, because 15M already has smoke and real collection validation.

---

## Real Collection Commands

30M example:

```bash
alert-bridge/safe_backtest_window.sh --replay-collect --timeframe 30 --start-date 2025-05-25 --end-date 2025-11-25
```

1H example:

```bash
alert-bridge/safe_backtest_window.sh --replay-collect --timeframe 60 --start-date 2025-11-25 --end-date 2026-05-25
```

Run only one block per explicit user authorization.

Do not auto-start the next block.

---

## Post-Collection Report

After each block, report:

- PASS/FAIL
- local file path
- number of bars
- real timestamp range
- local file size
- invalid JSON count
- `_error` count
- feature availability
- indicator presence
- production restore status:
  - receiver OK
  - public health 200
  - pause flag absent
  - XAU monitor running
  - zero orphan `server.js`
  - enrich/evaluator absent if relevant
- working tree status

Use honest labels:

- Mechanical PASS: script exited without crash.
- Data-quality PASS: correct range, bars, sources, indicators.
- Production-restore PASS: production state restored.

Never claim the objective was met if only the process succeeded.

---

## External Storage Policy

External drive:

```text
/Volumes/GUTS_ LACIE/TradingData/
```

Cold storage layout:

```text
TradingData/
  raw_replay/
    XAUUSD/
      15M/
      30M/
      1H/
  backtests/
    XAUUSD/
      4H/
  manifests/
  backups/
  slim_features/
```

The external drive is cold storage only. Production must not depend on it.

If the external drive disconnects, receiver/alerts/production must continue functioning.

---

## Archival Procedure After Each Block

For each successful local RAW JSONL:

1. Confirm local file exists.
2. Confirm file is gitignored/untracked.
3. Confirm no open handle.
4. Generate SHA256 of original.
5. gzip to external drive.
6. Generate SHA256 of `.gz`.
7. Validate:

```bash
gzip -t <file>.gz
gunzip -c <file>.gz | shasum -a 256
```

8. Roundtrip SHA256 must match the original.
9. Create manifest in:

```text
/Volumes/GUTS_ LACIE/TradingData/manifests/
```

10. Only after validation, ask user before deleting local.

Never delete local RAW before:

- gzip exists externally
- gzip integrity passes
- roundtrip hash matches
- manifest exists
- user explicitly authorizes local deletion

---

## Local Deletion Rules

Allowed only with explicit approval:

- local RAW already validated externally
- smoke artifacts
- gitignored temporary files

Never delete:

- `.env`
- active logs
- receiver files
- LaunchAgents
- `src/server.js`
- strategy configs
- files referenced by active scripts
- external `.gz` source-of-truth
- manifests

---

## Known Operational Risks

### Enrich/evaluator conflict

Do not collect replay data while `enrich_indicator_outcomes.py` or `OUTCOME EVALUATOR` is running unless the user explicitly authorizes stopping them.

If they are active, recommend stopping only when data collection/backtest is priority and the user approves.

### Enrich server.js leak

Known issue:

- `enrich_indicator_outcomes.py` can leave orphan `server.js` per evaluator batch.
- Future patch should run Claude subprocess in its own process group and kill the process group in `finally`.

Do not patch while enrich is actively running.

### TradingView/MCP instability

If collection fails:

1. restore production
2. stop
3. report
4. do not loop

### Chart state and indicator baseline

The collector depends on the chart layout.

Before each new timeframe or block, the user must confirm the chart has the correct indicator baseline.

---

## Data Quality Expectations

Each successful block should have:

- correct real timestamp range
- no duplicate timestamps
- no out-of-order timestamps
- no invalid JSON records
- no `_error` records
- all six feature sources present
- expected indicators present
- production restored

Expected sources:

- `ohlcv`
- `study_values`
- `pine_boxes`
- `pine_labels`
- `pine_shapes_bubbles`
- `pine_lines`

Indicator presence should be verified by name/source where possible:

- Custom OB baseline: usually `pine_boxes`
- LuxAlgo SMC: `study_values`, `pine_boxes`, `pine_labels`, `pine_lines`
- NAS Top Bottom: `study_values`, `pine_labels`
- Market Order Bubbles: `study_values`, `pine_shapes_bubbles`
- RSI: `study_values`

Do not claim that an indicator is captured if only the source is present but the indicator name was not confirmed.

---

## Communication Rules

Use concise operational reporting.

Prefer tables for status summaries.

Always separate:

- what was run
- what changed
- what was validated
- what remains pending
- what requires user approval

Never execute the next step without explicit approval.

---

## Commit Discipline

Use small commits by theme.

Examples:

```text
Generalize replay feature collector to any timeframe
Document multi-timeframe replay collection plan
Document external data storage policy
```

Do not mix:

- code + data movement
- docs + runtime changes
- LaunchAgent changes + collector changes

Run:

- syntax checks
- `git diff --check`
- secret scan
- status clean

---

## Never Do

- Never use external OHLCV source unless explicitly approved.
- Never run replay collection outside `safe_backtest_window.sh`.
- Never run another block without explicit user approval.
- Never reduce RAW payload unless explicitly approved.
- Never assume chart indicators are loaded.
- Never delete local RAW before external validation + user approval.
- Never touch receiver or secrets during collection.
- Never continue after repeated failure without a new diagnosis.
- Never erase source-of-truth external `.gz` datasets.
- Never overwrite an existing external dataset without explicit approval.

---

## Next Recommended Operational Step

At the current state, continue with XAU 30M only after:

1. `enrich_indicator_outcomes.py` and `OUTCOME EVALUATOR` are stopped/empty or user authorizes stopping them.
2. orphan `server.js` processes are cleaned.
3. user confirms chart is XAUUSD 30M with required indicators.
4. user authorizes one block.

Likely next block:

```bash
alert-bridge/safe_backtest_window.sh --replay-collect --timeframe 30 --start-date 2025-05-25 --end-date 2025-11-25
```
