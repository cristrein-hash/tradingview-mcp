# Operational Inventory

> Snapshot as-of **2026-05-25** (updated after Camada 4B.1c — legacy bundle archived; `xau-4h-monitor-cron` KEPT).
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

### Unloaded
| Label | Script | Note |
|---|---|---|
| `com.cristrein.claude-monitor` | `run_claude_monitor.sh` → `claude_monitor.py` | Legacy. Script archived (4B.1a, `afbbd63`); **plist file ARCHIVED** (Camada 4B.1b) — moved out of `~/Library/LaunchAgents/` to `backups/launchagents_archive/` (gitignored). |
| `com.cristrein.claude-intraday-monitor` | `run_claude_intraday_monitor.sh` → `claude_intraday_monitor.py` | Legacy. Script archived (`afbbd63`); **plist file ARCHIVED** (4B.1b) to `backups/launchagents_archive/`. |
| `com.cristrein.xau-4h-monitor-cron` | `monitor_xau_4h_strategies.py` (cron variant) | Unloaded. **Decision: KEEP** (Camada 4B.1c) — kept in `~/Library/LaunchAgents/` as a fallback/reference for the cron mode of the XAU 4H monitor. It points to the **live** `monitor_xau_4h_strategies.py`, which must NOT be touched. Not archived. |

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

## 7. LEGACY_UNLOADED scripts — ARCHIVED
- **Archived 2026-05-25 (Camada 4B.1a, commit `afbbd63`)** via `git mv` to
  `alert-bridge/archive/legacy_monitors/` — content unchanged. Files:
  - `claude_monitor.py`, `claude_intraday_monitor.py` (superseded by `monitor_xau_4h`)
  - `run_claude_monitor.sh`, `run_claude_intraday_monitor.sh` (their wrappers)
  - `monitor_state_helpers.py` — legacy-adjacent: imported **only** by the two monitors above; moved with them to preserve the co-located import. NOT used by the live `monitor_xau_4h`.
- No live code imports any of these (two docstring mentions in `monitor_xau_4h_strategies.py` and `weekly_review.py` are descriptive only — `weekly_review` defines its own `send_telegram`).
- **Config bundle (Camada 4B.3, commit pending):** `monitor_targets.json` + `monitor_targets_intraday.json` `git mv`'d into the same archive dir; the gitignored runtime states (`monitor_targets[_intraday]_state.json`) were deleted and their `.gitignore` lines removed.
- ⚠️ **Reactivation note:** these scripts use an **absolute** path (`Path.home()/"tradingview-mcp"/"alert-bridge"/...`), not `__file__`-relative. Reactivating a monitor would require restoring its `monitor_targets*.json` to the original `alert-bridge/` root path — the archived copy will not be found in place.
- **Their plists remain unloaded and NOT yet moved** — see [Next Phases](#11-next-phases).

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
- ✅ **Camada 4B.1a** — 5 legacy Claude monitor scripts archived to `alert-bridge/archive/legacy_monitors/` (commit `afbbd63`). Plists not yet moved.
- ✅ **Camada 4B.3** — legacy monitor target configs (`monitor_targets[_intraday].json`) archived to the same dir; gitignored runtime states deleted; stale `.gitignore` lines removed. Bundle closed in-repo.
- ✅ **Camada 4B.1b** — the 2 unloaded `claude-*` plists moved from `~/Library/LaunchAgents/` to `backups/launchagents_archive/` (gitignored; not versioned). Active agents (`tv-webhook-receiver`, `cloudflared-tunnel`, `xau-4h-monitor-daemon`) unchanged; receiver + public `/health` OK.
- ✅ **Camada 4B.1c** — `xau-4h-monitor-cron` decision: **KEEP** (unloaded, not archived). Reason: fallback/reference for the XAU 4H monitor's cron mode; its target script `monitor_xau_4h_strategies.py` is live and must not be touched. Documentation-only decision; plist left in place.

## 11. Next Phases

**Done:** ~~Version `my-strategy/strategies/`~~ (Camada 3, `c6b355a`) · ~~Archive one-offs~~ (Camada 4A, `9810bf2`) · ~~Archive legacy monitor **scripts**~~ (Camada 4B.1a, `afbbd63`) · ~~Archive legacy monitor **configs** + state/gitignore cleanup~~ (Camada 4B.3) · ~~Archive the 2 `claude-*` **plists**~~ (Camada 4B.1b) · ~~Decide `xau-4h-monitor-cron`~~ → KEEP (Camada 4B.1c).

> Legacy Claude-monitor bundle is now **fully archived** (scripts + configs + plists). `xau-4h-monitor-cron` is intentionally KEPT. The live `monitor_xau_4h` ecosystem is untouched.

Remaining — require explicit authorization:
1. **Decide backups / log retention** — `backups/` (~6.9 MB) and `alert-bridge/logs/` (~3.1 GB): define retention policy (`archive-weekly` agent may already cover part of this).
2. **Physical restructure** — only after the above, and only in a maintenance window with lockstep plist edits.
