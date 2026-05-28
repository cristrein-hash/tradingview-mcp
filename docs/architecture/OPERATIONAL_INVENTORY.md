# Operational Inventory

> Snapshot as-of **2026-05-25** (updated after Camada 6A.4 — path foundation rollout complete; only physical restructure remains).
> Verified by live inspection (`launchctl`, import/spawn graph, path references).
> This is a **map**, not a change plan — see [Next Phases](#11-next-phases).
> No secrets are recorded here.

Primary host: **MacBook** (receiver, cloudflared, TradingView, MCP, monitors, all LaunchAgents).
The **iMac** runs only the External Factors bridge. See [README.md](./README.md).
Cold storage (external HD) hot/cold split + archive procedure: see [DATA_STORAGE_POLICY.md](./DATA_STORAGE_POLICY.md).

---

## 1. LaunchAgents

All plists live in `~/Library/LaunchAgents/com.cristrein.*.plist` and reference **absolute paths**
under `/Users/cristrein/tradingview-mcp/`.

### Loaded (8)
| Label | Script | Trigger | Role |
|---|---|---|---|
| `com.cristrein.tv-webhook-receiver` | `alert-bridge/start_receiver.sh` (→ `tv_webhook_receiver.py`) | RunAtLoad (resident) | Webhook receiver; `/health`, `/webhook/<secret>` |
| `com.cristrein.cloudflared-tunnel` | `/opt/homebrew/bin/cloudflared tunnel run tradingview-webhook` | RunAtLoad + **KeepAlive** | Public ingress tunnel (created 2026-05-25) |
| `com.cristrein.external-factors-heartbeat` | `alert-bridge/external_factors_heartbeat.py --daemon --sleep 900` | RunAtLoad + **KeepAlive** | External-factors heartbeat (created 2026-05-25; was an unsupervised manual daemon, down since 10:30Z) |
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
- `alert-bridge/run_xau_replay_feature_collect.py` — **TF-agnostic** per-bar feature collector via Replay (`--symbol`/`--timeframe 15|30|60`); renamed from `run_xau_15m_replay_backtest.py` (2026-05-25). Run only through `safe_backtest_window.sh --replay-smoke|--replay-collect`. Drives the multi-TF historical plan — see [DATA_STORAGE_POLICY.md](./DATA_STORAGE_POLICY.md).
- `scripts/build_dataset_registry.py` — generates/validates the **Dataset Registry** [`docs/data/dataset_registry.json`](../data/dataset_registry.json) (catalog/rollup of external RAW datasets; reads manifests, validates gzip+sha, read-only on the HD). The registry is the authoritative inventory consumed by the future extractor/analyzer.
- `alert-bridge/run_xau_15m_pullback_ohlcv.py` — OHLCV collector (stabilized 2026-05-25; deprecated for deep history — Replay collector supersedes it).
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
- ✅ **Backtest retention cleanup** — removed superseded backtest dumps `XAUUSD_240_*_v2/v3/v4/v5.jsonl` (32 files) + 4 empty orphan launchd logs (`launchd_[intraday_]stdout/stderr.log`). **~1.72 GB freed**; `logs/backtests/` 3.1 GB → 1.4 GB. **v6 (8 files) kept as the current base**; unversioned dumps preserved (incl. `XAUUSD_240_2025-11-19_to_2026-05-19.jsonl`, hardcoded in `draw_xau_4h_trades.py`). All deleted files were gitignored/untracked → no commit. Active jsonl / dedup_index / active launchd logs / `backups/` untouched.
- ✅ **Camada 5B — v6 retention policy: KEEP ALL 8** (uncompressed).
  - The earlier "longest window is a superset of the other 7" premise was **REJECTED after inspecting the actual data**: every v6 has exactly **540 bars** (`bar_index 0→539`); the filename's `_to_2026-05-21` is misleading.
  - **No single canonical window exists.** Each v6 is a distinct ~90-day historical sample (real coverage, by `replay_current_date`): 2023-01→05 · 2023-07→11 · 2024-01→05 · 2024-07→11 · 2025-05→09 · 2025-09→2026-01 · 2025-11→2026-03 · 2026-03→(incomplete). Gaps + minor overlaps; none fully contains another.
  - All 8 classified **KEEP_FOR_REASON** — useful for cross-regime comparison/future backtests; deleting any loses unique data. None referenced by live code; no open handles.
  - ⚠️ **Quality flag:** `XAUUSD_240_2026-03-19_..._v6.jsonl` has an **incomplete last record** (`replay_current_date=None`).
  - **Future option (not now):** reversible `gzip` of the 8 v6 (~1.35 GB → est. ~150–270 MB) if space becomes a problem again.
- ✅ **Camada 5C — small legacy orphan logs archived** — moved 7 frozen, gitignored, orphan logs (no writer, no live consumer) from `alert-bridge/logs/` to `backups/legacy_logs/` (~8.3 MB): `claude_monitor_events.jsonl`, `claude_intraday_monitor_events.jsonl`, `claude_monitor_last.json`, `claude_intraday_monitor_last.json`, `launchd_monitor.log`, `launchd_intraday_monitor.log`, `watch_manager.out`. Move only (reversible); `backups/` is gitignored → no commit for the move. Active receiver/pipeline jsonl, dedup_index, active launchd logs untouched; receiver `/health` OK. Note: `watch_manager.out` was a stale stdout of the still-present `setup_watch_manager.py` (which now writes to `setup_watch_log.jsonl`/`setup_watch_state.json`, not `.out`).
- ✅ **Camada 5D — retention automation** (commit `194ada6`). `scripts/archive_old_files.py` gained three opt-in modes, **dry-run by default (act only with `--apply`)**, **not** part of `all` so the `archive-weekly` LaunchAgent is unchanged:
  - `backtests` — per-window keep top `BACKTEST_KEEP_VERSIONS` (=1, the max); prune superseded `_vN.jsonl` + orphaned `*.checkpoint.json`. Unversioned dumps always protected.
  - `launchd` — copytruncate `launchd_*.log` above `LAUNCHD_CAP_MB` (=5), inode-preserving; never deletes.
  - `bak-prune` — delete `backups/bak_archive/` entries older than `BAK_RETENTION_DAYS` (=90).
  - Hard protections (all new modes): only gitignored files (`git check-ignore`), skip open handles (`lsof`), never the max version per window or unversioned files.
  - **First safe `--apply`**: removed **32 orphan `.checkpoint.json`** (v2/v3/v4/v5 of already-deleted dumps). **v6 (8 .jsonl + 8 checkpoints) and 7 unversioned `.jsonl` preserved**; 0 `.jsonl` deleted; receiver `/health` OK. All removed files were gitignored → no commit for the deletion.
- ✅ **Camada 6A.1 — path foundation (backtest/manual scripts)** (commit `a1f4a79`). Replaced fragile `Path(__file__).parent.parent` with an inline `repo_root()` helper in the 4 manual/backtest scripts: `run_xau_15m_pullback_ohlcv.py`, `run_xau_4h_backtest.py`, `draw_xau_4h_trades.py`, `find_dream_demands.py`.
  - `repo_root()` prefers `TVMCP_ROOT`, else walks up for markers (`.git` / `src/server.js` / `alert-bridge`+`my-strategy`), else raises a clear error. `BASE_DIR`/`BACKTESTS_DIR` now anchor to it → these 4 **survive a future physical move** (resolves the coupling-(B) problem for them).
  - On the current layout the helper is a functional no-op (resolves to the repo root, same as before). Validated: `repo_root()` → `/Users/cristrein/tradingview-mcp`; smoke `safe_backtest_window.sh --smoke` PASS; production restored (receiver OK, pause flag absent, zero orphan server.js).
  - ⚠️ **Scripts with a LaunchAgent are NOT yet migrated** to `repo_root()` (still use `__file__`-relative or `Path.home()`): `monitor_xau_4h_strategies.py`, `weekly_review.py`, and the Family-B `Path.home()/...` scripts. Moving any of those physically still requires a code edit first.
- ✅ **Camada 6A.2 — `external_factors_heartbeat.py` path foundation + supervision** (code commit `c5ebcc1`).
  - **Path:** `repo_root()` helper applied; `BASE_DIR = repo_root() / "alert-bridge"` (preserves the original `__file__.parent` semantics — logs/.env/state stay under `alert-bridge/`, now move-safe). Validated via `--once` (status=ok); `.env` not modified.
  - **Supervision fix:** this was an **unsupervised manual `--daemon`** that had been **down since 10:30Z** (same event that killed the cloudflared tunnel). Put under new LaunchAgent **`com.cristrein.external-factors-heartbeat`** (RunAtLoad + KeepAlive, `--daemon --sleep 900`, logs in `alert-bridge/logs/launchd_external_factors_heartbeat_*`). Now `state=running`, first check `status=ok`, stderr clean. The plist is in `~/Library/LaunchAgents/` (not versioned). Receiver + public `/health` unaffected.
- ✅ **Camada 6A.3 — `weekly_review.py` path foundation** (commit `8025f8a`). `repo_root()` helper applied: `BASE_DIR = repo_root()`, `LOG_DIR = repo_root() / "alert-bridge" / "logs"` (same semantics today, now move-safe). The `weekly-review` LaunchAgent (Sun 09:00, `--mode cron`) was **not touched or restarted** — it picks up the change on its next scheduled run. Validated: py_compile OK; BASE_DIR/LOG_DIR resolve correctly; `--mode once` exit 0, no traceback, **no Telegram sent**; `.env` not modified.
- ✅ **External cold storage** (HD `GUTS_ LACIE`, `/Volumes/GUTS_ LACIE/TradingData/`) — see [DATA_STORAGE_POLICY.md](./DATA_STORAGE_POLICY.md). Cold archive of RAW XAU 15M 3-month replay (~130 MB `.gz`, gzip+roundtrip validated) + 5× 4H unversioned `_to_2026-05-20` dumps (~1.9 MB `.gz`) + checkpoints + manifests. Locals removed **only after** SHA256(orig)+SHA256(gz)+`gzip -t`+roundtrip+manifest+explicit approval (~65 MB + 1.06 GB freed). 15M smoke artifacts removed (not archived). **Production must not break if the HD is disconnected** — nothing live depends on it. **Kept local by live dependency:** 8× v6 4H (`find_dream_demands.py`), `XAUUSD_240_2025-11-19_to_2026-05-19.jsonl` (`draw_xau_4h_trades.py`). **Policy: never reduce RAW payload; gzip OK (lossless).**
- ✅ **Camada 6A.4 — `monitor_xau_4h_strategies.py` path foundation** (commit `a29239c`). `repo_root()` helper applied: `BASE_DIR = repo_root()`, `LOG_DIR = repo_root() / "alert-bridge" / "logs"` (`MCP_SERVER_PATH`/`env_path` follow; `CHART_LOCK_PATH` absolute, unchanged). **No-op on current layout**, now move-safe. The **live `xau-4h-monitor-daemon` (pid 58236) was NOT restarted** — keeps old code in memory, converges on next natural restart; no behavioral divergence (no-op). Plists untouched (script path unchanged). Validated **non-invasively** (py_compile + path resolution only; no MCP spawn, no chart, no daemon touch). **Path-foundation rollout for `__file__`-relative scripts is now complete.**
- ✅ **Historical XAU data foundation complete** (2026-05-27): 15M/30M/1H/4H/1D collected via Replay, archived externally (gzip + SHA256 + `gzip -t` + roundtrip + manifest, all integrity-validated), locals clean. Dataset Registry updated → 20 datasets, 0 warnings (15M 8 active +1 superseded, 30M 4, 1H 3, 4H 3, 1D 1). Slim features extracted for 4H (3 blocks) + 1D (1 block) to `slim_features/XAUUSD/{4H,1D}/`. 4H ~10y (2016→2026) and 1D ~14y (2012→2026) serve as macro/regime context. See [DATA_STORAGE_POLICY.md](./DATA_STORAGE_POLICY.md) + [`dataset_registry.json`](../data/dataset_registry.json). Next: `Strategy System Reset & Canonical Workflow`.

## 11. Next Phases

**Done:** ~~Version `my-strategy/strategies/`~~ (Camada 3, `c6b355a`) · ~~Archive one-offs~~ (Camada 4A, `9810bf2`) · ~~Archive legacy monitor **scripts**~~ (Camada 4B.1a, `afbbd63`) · ~~Archive legacy monitor **configs** + state/gitignore cleanup~~ (Camada 4B.3) · ~~Archive the 2 `claude-*` **plists**~~ (Camada 4B.1b) · ~~Decide `xau-4h-monitor-cron`~~ → KEEP (Camada 4B.1c).

> Legacy Claude-monitor bundle is now **fully archived** (scripts + configs + plists). `xau-4h-monitor-cron` is intentionally KEPT. The live `monitor_xau_4h` ecosystem is untouched.

Remaining — require explicit authorization:
1. ✅ **Path foundation rollout (6A) — COMPLETE** for `__file__`-relative scripts: 6A.1 (4 backtest/manual, `a1f4a79`), 6A.2 (`external_factors_heartbeat`, `c5ebcc1` + supervision), 6A.3 (`weekly_review`, `8025f8a`), 6A.4 (`monitor_xau_4h_strategies`, `a29239c`).
   - **Optional, deferred:** functional `--mode once` test of `monitor_xau_4h` inside a maintenance window (bootout daemon → run → bootstrap) — not required (patch is a no-op).
   - **Optional:** Family-B (`Path.home()/...`) scripts → `repo_root()` for portability; does not block moves.
2. **Physical restructure** — the big one, only after path foundation: move LaunchAgent-referenced scripts/configs into a cleaner layout in a maintenance window, editing each plist's absolute paths in lockstep (`bootout` → move → edit `<string>` → `bootstrap` → validate), one agent at a time, with rollback.

> Retention automation exists (Camada 5D); future `--apply` of `launchd`/`bak-prune` is wired but currently no-op (nothing over the thresholds). Optionally wire the new modes into a schedule later (would touch a LaunchAgent → separate authorization).

> v6 backtest window policy is **decided** (Camada 5B): keep all 8 uncompressed; gzip is a reversible future option only.

## 12. Decommissioned Components

### 2026-05-28 — `com.cristrein.enrich-indicator-outcomes` (DEPRECATED / CANCELLED)
- **LaunchAgent removed** from `~/Library/LaunchAgents/`; plist archived to
  `backups/launchagents_archive/com.cristrein.enrich-indicator-outcomes.plist.deprecated_2026-05-28`
  (SHA256 verified against source before removal).
- **Script** `alert-bridge/enrich_indicator_outcomes.py` marked DEPRECATED in
  docstring banner (preserved for reference only; code below banner kept intact
  for potential reuse by the future Signal Outcome Lab design — DO NOT execute).
- **Reason**: it invoked `chart_set_symbol` with bare tickers (no provider
  prefix). TradingView resolved bare tickers to OANDA (default provider) instead
  of PEPPERSTONE → outcomes silently contaminated. Compounding: a single batch
  held `/tmp/tradingview_chart.lock` for hours due to Claude headless timeouts,
  interfering with visual audits and other chart consumers.
- **State of outputs**: `indicator_signals_outcomes.jsonl` (330 entries
  pre-decommission) is **preserved** and flagged as `contaminated_pre_pepperstone_fix`.
  Not deleted. Not used for strong decisions. Will be audited and selectively
  regenerated by the redesigned outcome layer.
- **Receiver fix (paired patch)**: `tv_webhook_receiver.py::_normalize_indicator_parsed`
  was inverted on the same date — now ADDS `PEPPERSTONE:` prefix (instead of
  removing it) and emits `raw_symbol` / `base_symbol` / `symbol` / `provider` /
  `normalization_method` / `_normalize_warning` fields. Operational whitelist:
  `XAUUSD, XAGUSD, ETHUSD, US500, EURUSD, USOUSD` (BTCUSD/XPTUSD/USDJPY removed).
- **Replacement**: future "Signal Outcome Lab" — batch/manual (no scheduled
  LaunchAgent initially), PEPPERSTONE hard gate, unified chart lock with
  monitor/draws/replay/visual-audit, canonical-slim-first read path, live chart
  fallback only inside explicit safe windows, output manifest/provenance. Not
  scheduled.
- **Rollback** (if ever needed): `cp backups/launchagents_archive/com.cristrein.enrich-indicator-outcomes.plist.deprecated_2026-05-28 ~/Library/LaunchAgents/com.cristrein.enrich-indicator-outcomes.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.enrich-indicator-outcomes.plist` — but this restores the buggy behaviour and is not recommended.
