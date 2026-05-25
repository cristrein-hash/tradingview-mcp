# Session State — before XAU 15M backtest

> Operational consolidation as-of **2026-05-25**. Read-only snapshot; no secrets.
> Companion to [OPERATIONAL_INVENTORY.md](./OPERATIONAL_INVENTORY.md) and [README.md](./README.md).

## 1. Current system state (verified live, read-only)

**Hosts**
- **MacBook = primary host.** Receiver, cloudflared, TradingView Desktop + MCP, monitors, pipeline, all LaunchAgents.
- **iMac = External Factors bridge only.** Nothing else operational depends on it.

**LaunchAgents (verified `launchctl list`)**
| Label | State |
|---|---|
| `com.cristrein.tv-webhook-receiver` | running (resident) |
| `com.cristrein.cloudflared-tunnel` | running (RunAtLoad + KeepAlive) |
| `com.cristrein.external-factors-heartbeat` | running (RunAtLoad + KeepAlive) |
| `com.cristrein.xau-4h-monitor-daemon` | running (resident) |
| `com.cristrein.enrich-indicator-outcomes` | loaded (daily 03:00) |
| `com.cristrein.d2r-daily` | loaded (daily 04:00) |
| `com.cristrein.archive-weekly` | loaded (Sun 04:00) |
| `com.cristrein.weekly-review` | loaded (Sun 09:00) |
| `com.cristrein.xau-4h-monitor-cron` | **unloaded (KEEP)** — cron variant of the live script |

**Health (verified)**
- receiver `/health`: `ok:true`, `claude_recheck:true`, `secret_configured:true`, `legacy_endpoint_enabled:false`, `pause_flag_present:false`.
- public `/health` (via tunnel): **200**.
- `/webhook/local-test`: **403** (legacy disabled).
- **Schema enforcement: `shadow`** (logs warnings, does not block).
- pause flag `/tmp/claude_recheck.paused`: **absent**.
- XAU 4H monitor daemon: **running**.
- Orphan `server.js`: **0** (the one live instance is the daemon's child, not an orphan).
- git: branch `main`, in sync with `origin/main`, **working tree clean**.

## 2. What was fixed / stabilized this cycle
- Receiver security/health hardened; real secret in `.env`; `/webhook/local-test` blocked (403).
- **cloudflared tunnel supervised** (LaunchAgent, KeepAlive) — was an unsupervised manual daemon.
- **external_factors_heartbeat supervised** (LaunchAgent, KeepAlive) — was an unsupervised manual daemon.
- **MCP/backtest stabilized:** `src/connection.js` per-operation CDP timeouts (no infinite hangs); `tv_launch` real hard restart; `chart_scroll_to_date` fixed; backtest restore timeout widened.
- **`safe_backtest_window.sh` validated** as the official backtest runbook.
- Repo governance: XAU one-offs archived; legacy Claude-monitor bundle fully archived; log/backtest retention cleanup (~1.72 GB freed); retention automation installed (`archive_old_files.py` modes, dry-run default); **path foundation 6A complete** (`repo_root()` in all `__file__`-relative scripts).

## 3. What is supervised now
Resident + KeepAlive: receiver, cloudflared tunnel, external-factors heartbeat. Resident: XAU 4H monitor daemon. Scheduled: enrich, d2r-daily, archive-weekly, weekly-review.

## 4. Official backtest workflow (canonical)
Use **`alert-bridge/safe_backtest_window.sh`** — never run a manual backtest outside a maintenance window.
1. Preflight: confirm receiver `/health` ok, public `/health` 200, daemon running, working tree clean.
2. Enter maintenance: `touch /tmp/claude_recheck.paused` (interlock; also pauses claude_recheck dispatch).
3. Stop XAU monitor daemon (`launchctl bootout` — KeepAlive needs bootout, not stop).
4. Kill orphan MCP `server.js`.
5. Hard-restart TradingView if CDP is wedged (`launch()` kills the real instance, then relaunches + validates CDP command channel).
6. Validate CDP (`cdp_connected` + `api_available`).
7. Run smoke test.
8. Run incremental backtest (checkpointed).
9. Restore production ALWAYS via `trap EXIT` (remove pause flag, bootstrap daemon).
10. Confirm: receiver OK · public `/health` 200 · pause flag absent · XAU monitor running · zero orphan `server.js` · logs without critical error.

The script's default is `--check`/`--smoke`; **full backtest requires explicit approval** and is not wired into the script by default.

## 5. Safe commands (read-only / non-destructive)
- `curl -s http://127.0.0.1:8787/health` — receiver health (booleans only).
- `curl -s -o /dev/null -w '%{http_code}' https://<public-host>/health` — tunnel up (expect 200). *(no secret in path)*
- `launchctl print gui/$(id -u)/<label>` — agent state.
- `alert-bridge/safe_backtest_window.sh --check` — read-only stack health.
- `git status -sb` / `git diff --check` — repo hygiene.
- `python3 alert-bridge/weekly_review.py --mode once` — review without Telegram.

## 6. Known risks
- **Concurrency:** backtest MCP + live daemon both use the chart → coordinated by `flock /tmp/tradingview_chart.lock`; maintenance window pauses/bootouts the daemon to avoid contention.
- **CDP can wedge:** TradingView HTTP discovery may answer while the command channel is dead → `tv_launch` hard restart clears it; connection.js timeouts make it fail-fast.
- **`server.js` killed by the runbook:** `safe_backtest_window.sh` kills `server.js`, including Claude's own MCP connection → reconnect with `/mcp` afterwards.
- **Live daemon runs pre-6A.4 code** until its next restart (no-op divergence; harmless).
- **Chart resting timeframe** may differ (1H vs 4H) after a restart — cosmetic; daemon sets what it needs per evaluation.

## 7. What NOT to do
- ❌ Run the receiver with `python3 tv_webhook_receiver.py` / `nohup ...` directly (SECRET falls back to `local-test` → silent 403s).
- ❌ Run a manual backtest outside the maintenance window.
- ❌ Run a full (multi-month, non-dry-run) backtest without explicit approval.
- ❌ Touch LaunchAgents / receiver / `.env` / secrets / alerts as a side effect.
- ❌ Print `.env`, secrets, tokens, or full URLs containing the secret.
- ❌ Leave the pause flag set or the daemon stopped at the end.
- ❌ Mix infra changes with strategy/Pine changes in one commit.

## 8. Checklist before the XAU 15M backtest
- [ ] Working tree clean (`git status`).
- [ ] receiver `/health` ok + public `/health` 200 + `/webhook/local-test` 403.
- [ ] XAU 4H daemon running; pause flag absent; zero orphan `server.js`.
- [ ] Confirm exact backtest parameters (months, dry-run vs real write, target output jsonl).
- [ ] Run via `safe_backtest_window.sh` (maintenance window), NOT a bare `python3` call.
- [ ] Plan to restore production via the script's `trap` + verify the 6 post-conditions.
- [ ] If anything fails: stop, restore production, report — do not retry blindly.

## 9. Recommended next step
Confirm the **scope of the XAU 15M backtest** (it relates to candidate packet `my-strategy/strategies/candidates/xauusd_15m_long_pending.md`, whose section 3 needs a ≥6-month / n≥30 backtest):
- Is it an **OHLCV collection** run (`run_xau_15m_pullback_ohlcv.py`, N months, real write) or the existing **smoke** (`--months 1 --dry-run`)?
- Then run it inside `safe_backtest_window.sh` with explicit parameters.

**No backtest will run without explicit authorization and confirmed parameters.**
