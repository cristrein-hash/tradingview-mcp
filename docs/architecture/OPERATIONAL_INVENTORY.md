# Operational Inventory

> Snapshot as-of **2026-05-25** (updated after Camada 4A — XAU one-offs archived).
> Verified by live inspection (`launchctl`, import/spawn graph, path references).
> This is a **map**, not a change plan — see [Next Phases](#11-next-phases).
> No secrets are recorded here.

Primary host: **MacBook** (receiver, cloudflared, TradingView, MCP, monitors, all LaunchAgents).
The **iMac** runs only the External Factors bridge. See [README.md](./README.md).

---

## 1. LaunchAgents

All plists live in `~/Library/LaunchAgents/com.cristrein.*.plist` and reference **absolute paths**
under `/Users/cristrein/tradingview-mcp/`.

### Loaded (7)
| Label | Script | Trigger | Role |
|---|---|---|---|
| `com.cristrein.tv-webhook-receiver` | `alert-bridge/start_receiver.sh` (→ `tv_webhook_receiver.py`) | RunAtLoad (resident) | Webhook receiver; `/health`, `/webhook/<secret>` |
| `com.cristrein.cloudflared-tunnel` | `/opt/homebrew/bin/cloudflared tunnel run tradingview-webhook` | RunAtLoad + **KeepAlive** | Public ingress tunnel (created 2026-05-25) |
| `com.cristrein.xau-4h-monitor-daemon` | `alert-bridge/monitor_xau_4h_strategies.py --mode daemon` | RunAtLoad (resident) | XAU 4H strategy monitor (event-driven) |
| `com.cristrein.enrich-indicator-outcomes` | `alert-bridge/enrich_indicator_outcomes.py` | daily 03:00 | Pipeline: enrich indicator outcomes |
| `com.cristrein.d2r-daily` | `alert-bridge/auto_d2r_daily.py` | daily 04:00 | Pipeline: D2R daily |
| `com.cristrein.archive-weekly` | `alert-bridge/scripts/archive_old_files.py` | Sun 04:00 | Maintenance: archive old files |
| `com.cristrein.weekly-review` | `alert-bridge/weekly_review.py` | Sun 09:00 | Monitoring: weekly review/health |

### Unloaded (3 — plist present, NOT in `launchctl list`)
| Label | Script | Note |
|---|---|---|
| `com.cristrein.claude-monitor` | `run_claude_monitor.sh` → `claude_monitor.py` | Legacy, superseded by `monitor_xau_4h` |
| `com.cristrein.claude-intraday-monitor` | `run_claude_intraday_monitor.sh` → `claude_intraday_monitor.py` | Legacy |
| `com.cristrein.xau-4h-monitor-cron` | `monitor_xau_4h_strategies.py` (cron variant) | Disabled; daemon variant runs instead. **Same live script** — only the cron plist is unloaded. |

---

## 2. PRODUCTION_ACTIVE scripts
Breaking these breaks live ingestion/monitoring.
- `alert-bridge/tv_webhook_receiver.py` — receiver (LaunchAgent).
- `alert-bridge/start_receiver.sh` / `stop_receiver.sh` — receiver lifecycle (loads `.env`).
- `alert-bridge/claude_recheck.py` — **spawned by the receiver** (`subprocess`), not a LaunchAgent. Shares a mirrored alert-type list with the receiver (keep in sync).
- `alert-bridge/monitor_xau_4h_strategies.py` — XAU 4H daemon (LaunchAgent).

## 3. PIPELINE_ACTIVE scripts
Scheduled or indirectly invoked data pipeline.
- `alert-bridge/enrich_indicator_outcomes.py` — LaunchAgent, daily 03:00.
- `alert-bridge/auto_d2r_daily.py` — LaunchAgent, daily 04:00.
- `alert-bridge/evaluate_r_outcomes.py`, `evaluate_setup_outcomes.py`, `generate_d2r_summary.py`, `setup_watch_manager.py` — **invoked indirectly** (by `auto_d2r_daily.py` / the receiver). Invocation chain not 100% traced — verify before moving.

## 4. MONITORING_ACTIVE scripts
- `alert-bridge/weekly_review.py` — LaunchAgent, Sun 09:00.
- `alert-bridge/scripts/archive_old_files.py` — LaunchAgent, Sun 04:00 (maintenance/retention).
- Receiver `/health` endpoint (inside `tv_webhook_receiver.py`).

## 5. RESEARCH / BACKTEST scripts (manual tools — safe to move)
- `alert-bridge/run_xau_15m_pullback_ohlcv.py` — OHLCV collector (stabilized 2026-05-25).
- `alert-bridge/run_xau_4h_backtest.py`, `poc_scan_xau_4h.py`, `draw_xau_4h_trades.py`, `find_dream_demands.py`, `run_d2r_backfill.py`.
- `alert-bridge/report_indicator_edge.py`, `run_research_cycle.py`, `research_status.py` — research/reporting; ad-hoc (not scheduled) — confirm before final classification.

## 6. ONE-OFF scripts (completed research — 35 files) — ARCHIVED
- **Archived 2026-05-25 (Camada 4A, commit `9810bf2`)** via `git mv` to
  `alert-bridge/research/archive/analyze_xau/` — 35 `analyze_xau_*.py` scripts, content unchanged.
- No longer in the `alert-bridge/` root. None were referenced by any LaunchAgent or live code
  (only a docstring comment naming a non-existent file); scripts are self-contained (stdlib-only).

## 7. LEGACY_UNLOADED scripts
- `alert-bridge/claude_monitor.py`, `claude_intraday_monitor.py`.
- `alert-bridge/run_claude_monitor.sh`, `run_claude_intraday_monitor.sh` (their wrappers).
- `alert-bridge/monitor_state_helpers.py` — **legacy-adjacent**: imported **only** by the two legacy monitors above; NOT used by the live `monitor_xau_4h`. (Correction to an earlier audit pass.)

---

## 8. Files that MUST NOT be moved now
All LaunchAgent-referenced scripts + **their log paths** + production config:
- `tv_webhook_receiver.py`, `start_receiver.sh`, `monitor_xau_4h_strategies.py`
- `enrich_indicator_outcomes.py`, `auto_d2r_daily.py`, `weekly_review.py`, `scripts/archive_old_files.py`
- `claude_recheck.py` (spawned by receiver)
- `my-strategy/strategy_rules.json`, `my-strategy/operational_prompt.md` (production config, read by ~8 scripts)
- `src/server.js` (spawned by the monitor/backtest and by Claude's MCP)
- `alert-bridge/.env` (secrets — never touched)
- everything under `alert-bridge/logs/launchd_*` (plist `StandardOut/ErrorPath`)

## 9. Absolute-path risks
- **All 10 plists** hardcode `/Users/cristrein/tradingview-mcp/...` — moving any referenced file/log **silently** breaks the agent.
- Scripts that hardcode the repo path: `auto_d2r_daily.py`, `safe_backtest_window.sh` (and the now-archived `research/archive/analyze_xau/analyze_xau_4h_backtest.py`).
- `ops/start_trading_stack.sh` uses `$HOME/tradingview-mcp`.
- **Rule:** any physical move of a referenced file requires editing the plist in lockstep (`bootout` → move → edit `<string>` → `bootstrap` → validate), one agent at a time, with rollback.

## 10. Resolved points (2026-05-25)
- ✅ **cloudflared LaunchAgent** `com.cristrein.cloudflared-tunnel` (RunAtLoad + KeepAlive) — public ingress now auto-restarts; fixed the ~2h outage caused by an unsupervised manual tunnel.
- ✅ **`ops/start_trading_stack.sh` safe** — rewritten as `--check` (read-only) / `--start` (supervised `launchctl kickstart`); removed the `local-test` secret and direct-python receiver start; asserts public `/health`=200 and legacy `/webhook/local-test`=403.
- ✅ **`alert-bridge/safe_backtest_window.sh`** — official maintenance runbook for backtests (pause → bootout daemon → restart TV → smoke → always restore via `trap EXIT`).
- ✅ **receiver LaunchAgent** `com.cristrein.tv-webhook-receiver` — canonical receiver path via `start_receiver.sh` (loads `.env`, real secret).
- ✅ **`/webhook/local-test` blocked** — legacy endpoint returns **403** (`legacy_endpoint_enabled:false`).
- ✅ **MCP hardening** — `connection.js` CDP timeouts; `tv_launch` real hard restart; `chart_scroll_to_date` fixed; backtest restore timeout widened to 30s.
- ✅ **Camada 3** — strategy candidate packets versioned (`my-strategy/strategies/candidates/`, commit `c6b355a`).
- ✅ **Camada 4A** — 35 XAU one-off research scripts archived to `alert-bridge/research/archive/analyze_xau/` (commit `9810bf2`).

## 11. Next Phases

**Done:** ~~Version `my-strategy/strategies/`~~ (Camada 3, `c6b355a`) · ~~Archive one-offs~~ (Camada 4A, `9810bf2`).

Remaining — require explicit authorization:
1. **Catalog legacy** — formally decide the fate of `claude_monitor*` / `claude_intraday_monitor*` / `monitor_state_helpers.py` + their unloaded plists (keep as reference vs archive). Confirm no intent to reactivate before archiving.
2. **Review unloaded plists** — `claude-monitor`, `claude-intraday-monitor`, `xau-4h-monitor-cron` (present but unloaded): keep, archive, or remove.
3. **Decide backups / log retention** — `backups/` (~6.9 MB) and `alert-bridge/logs/` (~3.1 GB): define retention policy (`archive-weekly` agent may already cover part of this).
4. **Physical restructure** — only after the above, and only in a maintenance window with lockstep plist edits.
