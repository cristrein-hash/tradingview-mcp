---
name: incident-response
description: Handles failures, outages, hangs, bad states, and unsafe automation loops. Use when something breaks, a process hangs, alerts stop, MCP fails, secrets may be exposed, or production needs safe restoration.
---
# Incident Response

When something is wrong, your job is to stabilize safely — not to "try things fast."

## First principle: STOP THE LOOP
Before anything else, stop any repeating/automated action. A wedged loop or a retry storm makes incidents worse. One careful diagnosis beats ten blind retries.

## Frame the incident (always, in this order)
1. **Symptom** — what is observably wrong (error, hang, 530, silence).
2. **Probable cause** — best current hypothesis (state it as a hypothesis, not fact).
3. **Production impact** — is ingestion/monitoring affected? data loss?
4. **Restore state** — is production currently up/down/degraded?
5. **Next safe step** — the single smallest action that reduces risk.

## Covered incidents
- **Secret leak** — a secret may be printed/committed/logged. Highest priority.
- **Receiver down** — `/health` fails or alerts stop arriving.
- **cloudflared 530 / public webhook down** — tunnel not routing.
- **MCP / TradingView CDP wedge** — HTTP discovery answers but the command channel is dead (`tv_health_check` hangs/fails).
- **Orphan `server.js`** — leaked MCP servers (ppid=1) accumulating.
- **`safe_backtest_window.sh` failure** — window aborted mid-run.
- **Chart symbol/timeframe mismatch** — collection/eval reading the wrong instrument.
- **enrich/evaluator running during a collection** — chart contention + the window's `pkill` would kill the evaluator's MCP server.
- **Terminal/shell wedged** — a foreground command hung.

## Rules (hard)
- **Do not expose secrets.** Never `cat`/`tail`/`grep` a log or file in a way that could print a secret. Read only booleans from `/health`; redact paths/URLs.
- **Do not loop.** No repeating the same command hoping for a different result.
- **Do not run backtest/collect after a failure without a diagnosis** — you may be operating on a broken state or dead infrastructure.
- **Always restore production first**, then investigate the root cause.
- For a CDP wedge: a hard restart (`tv_launch` / `launch()` that kills the real instance) clears it; connection timeouts make it fail-fast.
- For enrich-during-collection: never open a window while an evaluator/enrich is active; stopping enrich (kill the process, not the LaunchAgent) is safe and idempotent (resumes from already-enriched hashes).

## Diagnostic checklist
- receiver `/health` (booleans only);
- public `/health` (expect 200);
- pause flag present/absent;
- LaunchAgents loaded;
- `server.js` processes (daemon child vs orphans);
- stderr logs (without exposing secrets);
- `git status` / working tree.

## Report template
- **PASS/FAIL** of the current state;
- **Impact** (production, data);
- **Production restored?** (yes/no + evidence);
- **Data lost?** (what, how much, recoverable?);
- **Cause** (root cause, or best hypothesis if unconfirmed);
- **Recommended fix**;
- **What NOT to do** (to avoid repeating the incident).
