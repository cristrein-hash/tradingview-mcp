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
| `com.cristrein.external-factors-heartbeat` | `alert-bridge/external_factors_heartbeat.py --daemon --sleep 900` | RunAtLoad + **KeepAlive** | External-factors heartbeat (created 2026-05-25). ⚠️ **CANCELLED 2026-06-14 — bootout + plist archived; see §12 (2026-06-14 entry). Now unloaded, do not reactivate.** |
| `com.cristrein.xau-4h-monitor-daemon` | `alert-bridge/monitor_xau_4h_strategies.py --mode daemon` | RunAtLoad (resident) | XAU 4H strategy monitor (event-driven). ⚠️ **DORMANT PERSISTENTE (2026-06-14) — unloaded, sem processo; plist ARQUIVADO (movido p/ backups/launchagents_archive). DO_NOT_LOAD sem autorização (controla chart via MCP/CDP). See §12 (2026-06-14 entry).** |
| `com.cristrein.enrich-indicator-outcomes` | `alert-bridge/enrich_indicator_outcomes.py` | daily 03:00 | Pipeline: enrich indicator outcomes |
| `com.cristrein.d2r-daily` | `alert-bridge/auto_d2r_daily.py` | daily 04:00 | Pipeline: D2R daily. ⚠️ **PAUSED/MORATORIUM 2026-06-14 — re-bootout + plist archived; see §12 (2026-06-14 entry) + §13. Now unloaded, do not reactivate até Outcome Engine limpo.** |
| `com.cristrein.archive-weekly` | `alert-bridge/scripts/archive_old_files.py` | Sun 04:00 | Maintenance: archive old files |
| `com.cristrein.weekly-review` | `alert-bridge/weekly_review.py` | Sun 09:00 | Monitoring: weekly review/health |

### Unloaded
| Label | Script | Note |
|---|---|---|
| `com.cristrein.claude-monitor` | `run_claude_monitor.sh` → `claude_monitor.py` | Legacy. Script archived (4B.1a, `afbbd63`); **plist file ARCHIVED** (Camada 4B.1b) — moved out of `~/Library/LaunchAgents/` to `backups/launchagents_archive/` (gitignored). |
| `com.cristrein.claude-intraday-monitor` | `run_claude_intraday_monitor.sh` → `claude_intraday_monitor.py` | Legacy. Script archived (`afbbd63`); **plist file ARCHIVED** (4B.1b) to `backups/launchagents_archive/`. |
| `com.cristrein.xau-4h-monitor-cron` | `monitor_xau_4h_strategies.py` (cron variant) | Unloaded. **Decision: KEEP** (Camada 4B.1c) — kept in `~/Library/LaunchAgents/` as a fallback/reference for the cron mode of the XAU 4H monitor. It points to the **live** `monitor_xau_4h_strategies.py`, which must NOT be touched. ⚠️ **ARCHIVED 2026-06-14 — dormant persistente (plist movido p/ backups/launchagents_archive); see §12 (2026-06-14 entry).** |

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
  `normalization_method` / `validation_status` / `validation_reason` /
  `_normalize_warning` fields. Operational whitelist:
  `XAUUSD, XAGUSD, ETHUSD, US500, EURUSD, USOUSD` (BTCUSD/XPTUSD/USDJPY removed).
  **HARD WHITELIST GATE**: symbols whose `base_symbol` is outside the whitelist
  (or empty payload) are REJECTED with `validation_status='rejected_unauthorized_symbol'`
  (or `'rejected_empty_symbol'`); `write_indicator_signal` diverts them to
  `alert-bridge/logs/indicator_signals_quarantined.jsonl` (with full `raw_event`
  preserved for audit) and they **never enter** the operational
  `indicator_signals.jsonl` nor pollute the dedup index. Unauthorized providers
  (OANDA/VANTAGE/FOREXCOM/etc.) are accepted only if their base is in the
  whitelist (normalized to `PEPPERSTONE:<BASE>` + warning); otherwise the entire
  signal is rejected.
- **Replacement**: future "Signal Outcome Lab" — batch/manual (no scheduled
  LaunchAgent initially), PEPPERSTONE hard gate, unified chart lock with
  monitor/draws/replay/visual-audit, canonical-slim-first read path, live chart
  fallback only inside explicit safe windows, output manifest/provenance. Not
  scheduled.
- **Rollback** (if ever needed): `cp backups/launchagents_archive/com.cristrein.enrich-indicator-outcomes.plist.deprecated_2026-05-28 ~/Library/LaunchAgents/com.cristrein.enrich-indicator-outcomes.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.enrich-indicator-outcomes.plist` — but this restores the buggy behaviour and is not recommended.

### 2026-06-14 — `com.cristrein.external-factors-heartbeat` (CANCELLED / DO_NOT_REACTIVATE)
- **External Factors = CANCELLED / DO_NOT_REACTIVATE.** Decisão do operador: External Factors está cancelado e não deve ser reativado. (O bridge iMac já estava decommissionado — §05 `05_SYSTEM_ARCHITECTURE` — e o heartbeat MacBook agora também foi cancelado; antes havia divergência live↔doc, agora reconciliada.)
- **Heartbeat MacBook parado** via `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.external-factors-heartbeat.plist` (2026-06-14). KeepAlive não ressuscita após bootout.
- **Plist arquivado** (move, NÃO deletado) para `backups/launchagents_archive/com.cristrein.external-factors-heartbeat.plist.cancelled_2026-06-14`.
  - SHA256 (origem=destino, verificado): `7950421ead2f9e5804163bf1917d9ea30fbfb6d89ccb367c625119f5b7ab72b0`.
- **Estado pós-ação:** `launchctl list` ausente; processo `external_factors_heartbeat` ausente. Não recarrega em login/reboot (plist fora de `~/Library/LaunchAgents/`).
- **Código/logs NÃO deletados:** `alert-bridge/external_factors_heartbeat.py` + `alert-bridge/logs/external_factors_heartbeat_state.json` + `logs/launchd_external_factors_heartbeat_*` permanecem intactos (preservados; ainda não inventariados para delete).
- **Próxima etapa para delete completo:** inventariar refs/código/logs `external_factors` (grep imports / LaunchAgents / scripts) e montar lista explícita de delete, com backup/checksum + aprovação explícita.
- **Rollback** (se necessário, NÃO recomendado): `mv backups/launchagents_archive/com.cristrein.external-factors-heartbeat.plist.cancelled_2026-06-14 ~/Library/LaunchAgents/com.cristrein.external-factors-heartbeat.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.external-factors-heartbeat.plist`.

### 2026-06-14 — `com.cristrein.d2r-daily` (re-PAUSED / MORATORIUM / DO_NOT_REACTIVATE até Outcome Engine limpo)
- **d2r-daily = PAUSED / MORATORIUM / DO_NOT_REACTIVATE** até existir um Outcome Engine limpo. A camada atual de outcomes/reporting não é confiável para o novo core (lê outcomes contaminados/quarantined — ver §13).
- **Contexto (drift):** o moratório original (§13, 2026-05-28) fez bootout, mas o agente foi encontrado **re-carregado** (divergência live↔doc) na reconciliação de 2026-06-14. Re-pausado persistentemente nesta data.
- **Ação 2026-06-14:** `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.d2r-daily.plist` + plist movido (não deletado) para `backups/launchagents_archive/com.cristrein.d2r-daily.plist.paused_moratorium_2026-06-14`.
  - SHA256 (origem=destino, verificado): `a68e67eb40f29b650d406b6a26cce31137cda1074e67021bc1aceb8a9a86151d`.
- **Estado pós-ação:** `launchctl list` ausente; plist fora de `~/Library/LaunchAgents/` (não recarrega em login/reboot). Código `auto_d2r_daily.py` + logs **NÃO deletados** (preservados). Backup do moratório original (`...paused_moratorium_2026-05-28`) também preservado.
- **Rollback** (só quando Outcome Engine limpo + autorização explícita): `mv backups/launchagents_archive/com.cristrein.d2r-daily.plist.paused_moratorium_2026-06-14 ~/Library/LaunchAgents/com.cristrein.d2r-daily.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.d2r-daily.plist`.

### 2026-06-14 — `com.cristrein.xau-4h-monitor-daemon` + cron (DORMANT PERSISTENTE / DO_NOT_LOAD)
- **Estado real (verificado 2026-06-14):** ambos **UNLOADED / DORMANT** — ausentes do `launchctl list`, **sem processo** `monitor_xau_4h_strategies` vivo. (Reconciliou divergência: §1 antes dizia "Loaded (resident)".)
- **Tornado persistente (2026-06-14):** os 2 plists foram **arquivados** (move, NÃO deletados) de `~/Library/LaunchAgents/` para `backups/launchagents_archive/` — impede recarga automática em login/reboot (antes, com `RunAtLoad`, voltariam). NÃO é cancelamento definitivo nem delete de código.
  - `com.cristrein.xau-4h-monitor-daemon.plist.dormant_2026-06-14` · SHA256 `483769f020c761ef74137481fc7bfddfcfd46057f526fb842b4e233383aec0b2`.
  - `com.cristrein.xau-4h-monitor-cron.plist.dormant_2026-06-14` · SHA256 `419c1631c92f6d5c291761cd3f21846c2ff3786d3c1296958a9dd69b814a8510`.
- **DO_NOT_LOAD sem autorização explícita:** carregar o daemon/cron **controla o chart via MCP/CDP** (spawna `server.js`, troca símbolo/TF, desenha) → conflita com pesquisa/visual audit/plotagens.
- **Status estratégico INALTERADO:** só o estado de carga mudou; nenhuma decisão de estratégia. Código `monitor_xau_4h_strategies.py` preservado (não tocado, não deletado).
- **Rollback** (exige mover plists de volta + autorização explícita): `mv backups/launchagents_archive/com.cristrein.xau-4h-monitor-daemon.plist.dormant_2026-06-14 ~/Library/LaunchAgents/com.cristrein.xau-4h-monitor-daemon.plist && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.xau-4h-monitor-daemon.plist` (idem para o cron).

### 2026-06-14 — Pause flag `/tmp/claude_recheck.paused` (INTENTIONAL_PAUSE / RESEARCH_CLEANUP_WINDOW)
- **Estado:** pause flag **presente** em `/tmp/claude_recheck.paused` (intencional, mantida durante a janela de pesquisa/cleanup BPT/XAU + re-arquitetura). `claude_recheck` está pausado.
- **DO_NOT_REMOVE sem autorização explícita:** não remover a flag nesta fase — removê-la reativa o caminho de recheck.
- **Retomar recheck = ação SEPARADA:** exige autorização explícita + checagem prévia (receiver `/health` OK, public `/health` 200, cloudflared vivo, zero orphan `server.js`).
- **Nota:** com o canal legacy de strategy-alert dormente desde 2026-05-24, a pausa não afeta fluxo operacional ativo hoje; é salvaguarda durante a re-arquitetura. Não criar/recriar a flag por automação — só o operador.

### 2026-06-14 — `alert-bridge/logs/` retention checkpoint (inventário + limpeza mínima)
- **Tamanho:** `alert-bridge/logs/` ≈ **1.4G**, dos quais ≈ **1.3G são `backtests/`** (8 dumps v6 + 1 unversioned). Os logs/journals reais somam ~50MB.
- **Journals ativos = KEEP:** `indicator_signals.jsonl`, `tradingview_alerts.jsonl`, `indicator_signals_dedup_index.json`, `claude_recheck_events.jsonl`, `launchd_tv_receiver_stdout.log` + logs modificados recentemente. Não tocar.
- **Limpeza mínima executada (2026-06-14):** removidos **4 `*.checkpoint.json` órfãos** (≤321B cada, sem `.jsonl` correspondente) via `archive_old_files.py --mode backtests --apply`. SHA256 pré-delete registrados na sessão. **Nenhum `.jsonl` foi tocado** (`.jsonl` em backtests 9→9). Arquivos eram untracked/gitignored → sem commit da deleção.
- **8 dumps v6 (`XAUUSD_240_*_v6.jsonl`) + unversioned `XAUUSD_240_2025-11-19_to_2026-05-19.jsonl`:** **KEEP / DO_NOT_GZIP_OR_DELETE sem bloco próprio.** O unversioned é hardcoded em `draw_xau_4h_trades.py` (protegido pelo tool). Cada v6 é janela única (§10, Camada 5B = KEEP ALL 8).
- **Opção futura (bloco próprio, com autorização):** gzip dos 8 v6 (reversível, ~1.1G recuperável) — exige checksums + `gunzip -t` + roundtrip + confirmar que nada vivo lê os v6 descomprimidos. NÃO executar fora de bloco dedicado.

### 2026-06-14 — Auditoria de exposição real recheck/Telegram (read-only)
- **Veredito: SEM LIVE_RISK imediato.** A segurança hoje é por **camadas dormentes** (pause flag + daemon dormant + canal de estratégia dormente desde 2026-05-24 + raw alerts suprimidos), **não** por arquitetura limpa.
- **DEMAND_BREAKOUT, CAPITULATION, `discr_sweep`/`discr_base`:** sem rota viva — computadas pelo monitor (agora dormant/arquivado) e bloqueadas por `NO_TELEGRAM_DISPATCH` (lista hardcoded em `monitor_xau_4h_strategies.py:52`). Se o monitor for reativado, Telegram **continua suprimido** por essa lista (precisaria também sair da lista para emitir). Risco: NO_LIVE_ROUTE.
- **BREAKOUT_CONTINUATION / `claude_recheck.py:931` (`Módulo ATIVO`):** **DORMANT_BUT_DANGEROUS_IF_REACTIVATED.** Produziria `SETUP_VALIDO` (= "always sent, no cap" ao Telegram, `tv_webhook_receiver.py:419`) **se** a pause flag fosse removida **E** chegasse um alerta no canal de estratégia. Hoje bloqueado pela pause flag (receiver pula o thread de recheck quando `/tmp/claude_recheck.paused` existe) + canal dormente + raw suprimido.
- **Antes de QUALQUER retomada operacional (ordem obrigatória):**
  1. neutralizar `recheck:931` / `BREAKOUT_CONTINUATION` ativo (emitiria SETUP_VALIDO sem promoção validada);
  2. reconciliar `catalog.json` `current_deployment_status` das REJECTED/RESEARCH ainda marcadas `LIVE` (DEMAND_BREAKOUT, CAPITULATION, DISCRETIONARY) → DISABLED/WATCH;
  3. substituir `NO_TELEGRAM_DISPATCH` hardcoded por **permissão central** no futuro Strategy Registry (rota só existe se o status autorizar).
- **NÃO remover a pause flag nem reativar recheck/daemon** antes dos 3 itens acima. As três condições dormentes não devem ser revertidas sem neutralizar recheck:931 primeiro.

### 2026-06-15 — Inventário reconciliado (read-only) — comparação vs 2026-06-14

Inventário read-only de produção + peso, comparado entrada-a-entrada com as entradas de 2026-06-14 acima. **Veredito: ALINHADO, sem drift, sem regressão.** Nenhuma alteração operacional executada. Esta entrada **persiste a reconciliação e corrige rótulos perigosos**.

**1. Produção — alinhada (idêntica a 2026-06-14):**
- receiver **VIVO** PID 841 (LaunchAgent `com.cristrein.tv-webhook-receiver`, único plist ativo em `~/Library/LaunchAgents/`).
- cloudflared **VIVO** PID 1033 (`tradingview-webhook`).
- `external-factors-heartbeat` = **CANCELLED** (ausente do `launchctl`).
- `d2r-daily` = **PAUSED / MORATORIUM** (ausente).
- `xau-4h-monitor-daemon` + cron = **DORMANT PERSISTENTE** (sem processo `monitor_xau_4h_strategies` vivo; confirmado `pgrep` vazio).
- pause flag `/tmp/claude_recheck.paused` = **PRESENTE / INTENTIONAL** (mtime 2026-06-14 00:31).
- `recheck:931` / BREAKOUT_CONTINUATION = **exposure ainda PENDENTE / DORMANT_BUT_DANGEROUS_IF_REACTIVATED** (inalterado; fix em 3 itens da entrada de exposição acima continua válido).
- **Sem drift:** diferente de 2026-06-14 (que encontrou `d2r-daily` re-carregado divergindo do doc), em 2026-06-15 daemon/d2r/external estão todos confirmados dormant. Estado live↔doc estável.

**2. Correções de classificação (rótulos perigosos corrigidos):**
- **`node src/server.js` PID 7043** (uptime ~5d11h) = **MCP de uma sessão Claude paralela** (filho do PID 7033 `claude --model claude-fable-5`). **NÃO é orphan perigoso** — instância única, alinhado com §8 ("`src/server.js` spawned by Claude's MCP"); não é o caminho do daemon dormant. (Nota: há uma sessão Claude fable-5 ativa há ~5d segurando o MCP; não tocada.)
- **8 dumps v6 (`alert-bridge/logs/backtests/XAUUSD_240_*_v6.jsonl`)** = **KEEP / DO_NOT_GZIP_OR_DELETE por enquanto.** Corrige um rótulo intermediário "ARCHIVE_CANDIDATE" que era frouxo demais. Canônico (§10 Camada 5B + §12 retention): cada v6 é janela única de 540 bars **com dependência de código vivo** (`find_dream_demands.py` lê os 8; `draw_xau_4h_trades.py` lê o unversioned `XAUUSD_240_2025-11-19_to_2026-05-19.jsonl`). gzip (~1.1G recuperável) é **opção futura gated** (checksums + `gunzip -t` + roundtrip + aprovação), nunca archive casual.
- **`alert-bridge/logs/indicator_signals.jsonl`** (~16M) = **SOURCE_OF_TRUTH** (event journal FUTURE_CORE).
- **`alert-bridge/logs/indicator_signals.jsonl.before_synthetic_cleanup_2026-05-28`** (~2.9M) = **UNKNOWN — NÃO DELETAR.** Ainda não inventariado (refs/consumidores não checados); status pendente, não é DELETE_CANDIDATE confirmado.
- **RAW externo** (`/Volumes/GUTS_ LACIE/TradingData/`) = **SOURCE_OF_TRUTH** (cold storage; produção não depende dele).

**3. Peso do sistema:**
- **Repo enxuto:** `.git` ≈ 3.3M; conteúdo tracked é pequeno (maiores tracked ~88K: `tv_webhook_receiver.py`, `claude_recheck.py`, `strategy_rules.json` 80K).
- **Peso grande está em gitignored / local / external:** `alert-bridge/logs/` ≈ 1.4G (≈ 1.34G = 8 dumps v6, **gitignored**); `backups/` 29M; RAW no HD externo. Nada disso polui o repositório.
- **Nada grande deve ser movido/deletado agora.** Os candidatos a peso têm dependência viva (v6) ou status pendente (snapshot). Liberar espaço exige bloco dedicado com aprovação por item.

**4. Próxima menor ação segura:**
- **Nenhuma alteração operacional.** Esta entrada é o registro read-only; produção segue intocada.
- Decisão seguinte (quando autorizada): escolher entre **(B) cleanup explícito por item** (gzip gated dos v6 / inventariar o snapshot `before_synthetic_cleanup` para delete, com protocolo checksum+roundtrip+manifest+aprovação) **ou (C) desenho do Production v2** — esta bloqueada até a exposure do `recheck:931` ser neutralizada (3 itens da entrada de exposição). Produção só depois do terreno limpo e compreendido.

### 2026-06-15 — `recheck:931` / BREAKOUT_CONTINUATION NEUTRALIZADO (item 1/3 da exposição)

- **Ação:** patch mínimo reversível em `alert-bridge/claude_recheck.py` (1 arquivo, 4+/12−). O bloco do prompt operacional `XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED` (recheck:931) foi marcado **NEUTRALIZADO**: header "Módulo ATIVO" → "Módulo NEUTRALIZADO 2026-06-15"; instrução de emissão `Classificação: SETUP_VALIDO` / `Promotion status: PROMOTE_TO_SETUP_VALIDO` substituída por **"NÃO emitir SETUP_VALIDO; no máximo SETUP_CANDIDATO_FORTE para revisão humana, ou NO_TRADE"**. Trigger/filtros/backtest preservados só para referência (Production v2).
- **Por quê:** era o único ponto de emissão de SETUP_VALIDO desse módulo legacy (`DORMANT_BUT_DANGEROUS_IF_REACTIVATED`). Agora, mesmo se a pause flag fosse removida e chegasse um alerta no canal, o módulo **não pode mais promover SETUP_VALIDO** (= "always sent" ao Telegram via `tv_webhook_receiver.py:419`).
- **Sem efeito em runtime:** `claude_recheck` é **spawn on-demand** (sem processo resident) → próximo spawn usa o código novo, **sem restart do receiver**. Pause flag continua presente; canal de estratégia dormente. A mudança só **RESTRINGE** (remove uma rota de emissão), nunca habilita.
- **Validação:** `py_compile` PASS · grep confirma 0 emissão de SETUP_VALIDO no bloco · diff só em `claude_recheck.py` · health read-only: receiver ok (PID 841), cloudflared vivo (PID 1033), pause flag PRESENTE, XAU daemon/cron dormant. Não tocado: receiver, monitor, strategy_rules, catalog, Telegram, LaunchAgents, v6, logs vivos.
- **Reversível:** `git revert` do commit restaura o bloco "Módulo ATIVO".
- **Exposição restante (itens 2 e 3, NÃO feitos aqui):** (2) reconciliar `catalog.json` REJECTED/RESEARCH ainda `LIVE`; (3) substituir `NO_TELEGRAM_DISPATCH` hardcoded por permissão central no Strategy Registry. Continuam pendentes; **não remover pause flag / reativar** antes deles.

### 2026-06-15 — `catalog.json` reconciliado (item 2/3 da exposição)

- **Ação:** patch mínimo em `my-strategy/strategies/catalog.json` (4+/4−, só `current_deployment_status`). Alinhado `current` → `recommended` (alvo já decidido no catalog) nas 4 divergências live-like claras:
  - `XAU_4H_DEMAND_BREAKOUT` (REJECTED): **LIVE → DISABLED**.
  - `XAU_4H_REVERSAL_CAPITULATION` (REJECTED): **LIVE → DISABLED**.
  - `XAU_4H_REVERSAL_DISCRETIONARY` (RESEARCH): **LIVE → WATCH_ONLY**.
  - `XAUUSD_INTRADAY_BB_CONFLUENCE` (RESEARCH, forward test parado ~2026-04-30): **SHADOW → NOT_DEPLOYED**.
- **Zero impacto em runtime:** o `_meta` do catalog declara que ele é **PURELY DESCRIPTIVE — nenhum consumidor o lê; editar não muda comportamento do sistema**. Reconciliação documental. Monitor XAU está dormant (não despacha), Telegram suprimido por `NO_TELEGRAM_DISPATCH` — a verdade live deixou de ser `LIVE`.
- **Não tocado:** `validation_status`, nomes, métricas, histórico, `recommended_deployment_status`, e nenhum outro campo. Não tocado: strategy_rules, claude_recheck, receiver, monitor, Telegram, LaunchAgents, pause flag.
- **Residual NÃO patcheado (sem divergência interna current==recommended; exige decisão humana, não reconciliação):** `US500_1H_BREAKOUT_REGIME_FILTERED` (RESEARCH @ LIVE_DORMANT) e `ETHUSD_1H_PULLBACK_EMA50_REGIME` (RESEARCH @ LIVE_DORMANT) — a tensão está no próprio `recommended=LIVE_DORMANT`, não em current vs recommended. Flag para decisão futura (RESEARCH idealmente não fica em status live-like, mas é dormant: 0 ocorrências, recheck path neutralizado/pausado).
- **Validação:** JSON parse OK · todos `current_deployment_status` dentro do enum `deployment_enum` · diff só em `catalog.json` · health read-only: receiver ok (841), cloudflared vivo (1033), pause flag PRESENTE, XAU dormant.
- **Exposição restante:** item 3 (substituir `NO_TELEGRAM_DISPATCH` por permissão central no Strategy Registry) continua pendente. **Não remover pause flag / reativar** antes dele.

## 13. Outcome Automation Moratorium — 2026-05-28

**Status:** active. Lifted only by explicit operator authorization once the
**Signal Outcome Lab** (redesigned outcome layer) is built and a clean
replacement dataset is available.

### Rationale
- `enrich_indicator_outcomes.py` was decommissioned (section 12).
- `alert-bridge/logs/indicator_signals_outcomes.jsonl` was quarantined to
  `*.contaminated_pre_pepperstone_fix_2026-05-28` (manifest at
  `alert-bridge/logs/indicator_signals_outcomes.quarantine_manifest_2026-05-28.json`).
- Three downstream consumers (`auto_d2r_daily.py`, `report_indicator_edge.py`,
  `weekly_review.py::check_enrich_v2`) were patched (commit `d23b71d`) to detect
  the quarantined sibling and emit the structured marker
  `OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH` instead of misleading "no edge"
  / "still collecting" output.
- The moratorium goes one step further: **temporarily unload the LaunchAgent
  that runs the outcomes-dependent daily Telegram report**, so no automated
  message goes out claiming a meaningful state while the outcome layer is
  being redesigned.

### Per-LaunchAgent disposition (post-2026-05-28)

| LaunchAgent | Script | Outcomes dependency | Disposition | Notes |
|---|---|---|---|---|
| `com.cristrein.enrich-indicator-outcomes` | `enrich_indicator_outcomes.py` | writer (now decommissioned) | **REMOVED** (section 12) | plist archived; do not bootstrap |
| `com.cristrein.d2r-daily` | `auto_d2r_daily.py` | reads outcomes for Telegram appendix B.1 | **PAUSED (moratorium)** | unloaded via `launchctl bootout`; plist remains at `~/Library/LaunchAgents/` but inactive; backup at `backups/launchagents_archive/com.cristrein.d2r-daily.plist.paused_moratorium_2026-05-28` |
| `com.cristrein.weekly-review` | `weekly_review.py` | 1 check of N (`check_enrich_v2`) reads outcomes; other checks (receiver health, secret leak, schema warnings, module status) are independent | **KEPT (with patch)** | patch `d23b71d` makes `check_enrich_v2` report `OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH`; the other valuable health checks remain active |
| `com.cristrein.archive-weekly` | `archive_old_files.py --mode=all` | none | **KEPT** | log archival only; does not read outcomes |
| `com.cristrein.xau-4h-monitor-cron` | `monitor_xau_4h_strategies.py --mode cron` | none | **KEPT** | strategy monitor; does not read outcomes |
| `com.cristrein.xau-4h-monitor-daemon` | `monitor_xau_4h_strategies.py --mode daemon` | none | **KEPT** | strategy monitor; does not read outcomes |
| `com.cristrein.tv-webhook-receiver` | `start_receiver.sh` → `tv_webhook_receiver.py` | none | **KEPT** | signal journal; does not read outcomes |
| `com.cristrein.cloudflared-tunnel` | cloudflared | none | **KEPT** | public ingress |
| `com.cristrein.external-factors-heartbeat` | `external_factors_heartbeat.py` | none | **KEPT** | external data |

Manual scripts that consume outcomes (no LaunchAgent):
- `report_indicator_edge.py` — patched (`d23b71d`) to emit
  `OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH` report instead of "no matched
  pairs" when the outcomes file is quarantined. Safe to invoke manually; it
  will print the explanatory report rather than fake-empty results.

### Cross-references
- Active log mutation policy: `docs/architecture/LOG_MUTATION_POLICY.md`.
- Future: `INDICATOR_SIGNAL_POLICY.md` (provider/whitelist policy formalized;
  not yet authored at moratorium start).
- Future: Signal Outcome Lab design doc (architecture + provider hard gate +
  unified chart lock + canonical-slim-first + manifest/provenance — not yet
  authored).

### Rollback / re-enable

Lift the moratorium **only** when:
1. The Signal Outcome Lab is designed, built, and validated.
2. A clean outcomes dataset is produced (or stub policy is approved).
3. Operator explicitly authorizes re-enabling each paused LaunchAgent.

Re-enable command for `com.cristrein.d2r-daily` (when authorized):
```
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.d2r-daily.plist
launchctl list | grep d2r-daily      # confirm loaded
```

If the moratorium is escalated to also pause `weekly-review`, the same pattern
applies; the script is multi-purpose so reactivation may also be partial
(e.g. re-enable cron but keep `check_enrich_v2` returning the structured
marker until outcomes are real).

## 14. Current Signal Outcomes Rollup — 2026-05-28

**Status:** technical rollup only. Consumers **NOT reactivated**. The
moratorium of §13 remains in effect for all consumer LaunchAgents and
scripts.

This section documents the first clean outcomes dataset produced by the
Signal Outcome Lab MVP (see `SIGNAL_OUTCOME_LAB.md` and
`SIGNAL_OUTCOME_LAB_MVP.md`).

### Artifact paths

| Path | Content |
|---|---|
| `alert-bridge/logs/signal_outcomes_lab/outcomes_current.jsonl` | rollup of 72 CLEAN XAUUSD outcomes (deduped by `outcome_id`) |
| `alert-bridge/logs/signal_outcomes_lab/outcomes_current.manifest.json` | provenance manifest (source run, SHAs, scope, consumer status) |

### Provenance

| Field | Value |
|---|---|
| `source_run` | `backfill_2026-05-28_xau_full_v2` (Patch 8) |
| `source_outcomes_path` | `alert-bridge/logs/signal_outcomes_lab/backfill_2026-05-28_xau_full_v2/outcomes_backfill_2026-05-28_xau_full_v2.jsonl` |
| `source_outcomes_sha256` | `76db3fd4c92d5ab3b932a47c7c4648a54c8907c93c34ba7ddb7397a9ae8a2f4c` |
| `current_outcomes_sha256` | `76db3fd4c92d5ab3b932a47c7c4648a54c8907c93c34ba7ddb7397a9ae8a2f4c` |
| `evaluator_version` | `v0.1.0` |
| `created_at` | 2026-05-28T15:20:57+00:00 |

Source and current SHAs are identical because all 72 source records were
already CLEAN with distinct `outcome_id`s; the rollup is a byte-identical
copy. Future rollup updates (additional runs landing) may differ.

### Scope

| Field | Value |
|---|---|
| `scope` | `XAUUSD_ONLY` |
| `symbol` | `PEPPERSTONE:XAUUSD` only |
| `provider` | `PEPPERSTONE` only |
| `outcomes_count` | 72 |
| `distinct_outcome_ids` | 72 |
| `status_counts` | `{CLEAN: 72}` (100%) |

### Verdict counts (inherited from source run)

| Verdict | Count | % |
|---|---|---|
| `OUTCOME_AGREES` | 53 | 74% |
| `LEGACY_INCOMPLETE` | 16 | 22% |
| `OUTCOME_DIVERGES_SIGN` | 2 | 3% |
| `OUTCOME_DIVERGES_MAGNITUDE` | 1 | 1% |

### Non-XAU population (NOT in `outcomes_current.jsonl`)

| `base_symbol` | Count | Status |
|---|---|---|
| ETHUSD | 94 | `PENDING_NO_CANONICAL_DATA` |
| EURUSD | 62 | `PENDING_NO_CANONICAL_DATA` |
| US500 | 61 | `PENDING_NO_CANONICAL_DATA` |
| XAGUSD | 59 | `PENDING_NO_CANONICAL_DATA` |
| **Total non-XAU** | **276** | |

These 276 non-XAU records from the quarantine file are NOT part of
`outcomes_current.jsonl`. They remain dormant until canonical slim data
exists for their bases. The dormant population is recorded in the source
run's `skipped_signals.jsonl`.

### Consumer status (still per moratorium §13 — NOT reactivated)

| Consumer | Status | Behaviour today |
|---|---|---|
| `auto_d2r_daily.py` | `NOT_REPOINTED` | still emits `OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH` |
| `weekly_review.py::check_enrich_v2` | `NOT_REPOINTED` | still emits the same marker |
| `report_indicator_edge.py` | `NOT_REPOINTED` | manual; still emits the same marker against quarantine state |
| `com.cristrein.d2r-daily` LaunchAgent | `PAUSED` (moratorium) | unloaded; will not run until reactivation |
| `com.cristrein.enrich-indicator-outcomes` LaunchAgent | `DECOMMISSIONED` (§12) | plist archived; permanent |

### Important interpretation

1. **`outcomes_current.jsonl` is a TECHNICAL rollup only**, not yet an
   operational source for automated reports. Reactivation of any consumer
   requires an explicit separate patch with its own authorization,
   validation, and rollback plan.
2. **Scope coverage is partial by design.** Only XAUUSD has canonical slim
   data; ~84% of the legacy signal universe (non-XAU) is intentionally not
   represented. Consumers MUST NOT interpret "smaller dataset than legacy"
   as "less edge"; they MUST filter by `base_symbol == "XAUUSD"` or
   otherwise honor the `coverage_scope` marker before drawing conclusions.
3. **Three records have non-AGREES verdicts.** Specifically:
   - 1 `OUTCOME_DIVERGES_SIGN` from chart cross-instrument contamination
     (`signal_hash=2c37af21a28c7b67`, entry_diff_ratio ~5859%). Canonical
     computation is the source of truth; the legacy outcome was wrong.
   - 1 `OUTCOME_DIVERGES_SIGN` from genuine provider quote divergence with
     sign flip (`signal_hash=a314f98760171eff`). Directional conclusion is
     debatable between providers; documented as known edge case.
   - 1 `OUTCOME_DIVERGES_MAGNITUDE` from genuine provider quote divergence
     (`signal_hash=79bdd947bcf6f797`). Direction agrees, magnitude differs.
4. **16 records are `LEGACY_INCOMPLETE`** — canonical has data, legacy did
   not compute `close_plus_20` snapshots. These records are CLEAN and
   usable; the verdict reflects only the absence of a legacy comparison.

### How to read `outcomes_current.jsonl`

- Line-delimited JSON, one outcome per line.
- All records have `outcome_status == "CLEAN"`.
- Schema follows `SIGNAL_OUTCOME_LAB_MVP.md` §11.
- Source identification: `signal_provenance` field. All 72 records carry
  `quarantine_legacy_2026-05-28` (backfill source). Future fresh-mode
  rollups would add `signal_journal_v2`.
- Audit trail per record: `data_source_ref` (slim file + row range) +
  `data_source_sha256` (slim file hash).
- Each outcome carries `legacy_outcome_ref` (legacy snapshot reference for
  audit only) and `old_vs_new_diff` (comparison metadata).

### Update policy

`outcomes_current.jsonl` is updated by either:

1. **Re-running the Lab with `--write` (without `--no-current-rollup`).**
   This atomically replaces the file with the dedup-by-`outcome_id` union
   of all CLEAN outcomes from the run plus prior CLEAN outcomes from the
   existing rollup.
2. **A dedicated promotion of an approved run** (as done in Patch 9):
   read a specific approved run, filter CLEAN, dedup by `outcome_id`,
   atomic-mv into `outcomes_current.jsonl`, update
   `outcomes_current.manifest.json`.

Both pathways update `outcomes_current.manifest.json` to record source
provenance. The file follows `LOG_MUTATION_POLICY.md` discipline:
the Lab is the sole writer; atomic-mv is used (no concurrent writer
exists by design).

### Cross-references

- `SIGNAL_OUTCOME_LAB.md` — parent architecture.
- `SIGNAL_OUTCOME_LAB_MVP.md` — MVP contract (§9 outcomes_current policy,
  §11 outcome schema, §10 verdict enum).
- `INDICATOR_SIGNAL_POLICY.md` — provider whitelist enforced at Signal
  Journal write time.
- `LOG_MUTATION_POLICY.md` — atomic-mv pattern for outcomes_current.
- §12 — enrich decommission.
- §13 — outcome automation moratorium (still in effect).

### Rollback

`outcomes_current.jsonl` can be removed without affecting source run
directories (which retain their immutable artifacts). To roll back:

```bash
ts=$(date -u +%Y%m%dT%H%M%SZ)
mv alert-bridge/logs/signal_outcomes_lab/outcomes_current.jsonl \
   alert-bridge/logs/signal_outcomes_lab/outcomes_current.jsonl.rolled_back_${ts}
mv alert-bridge/logs/signal_outcomes_lab/outcomes_current.manifest.json \
   alert-bridge/logs/signal_outcomes_lab/outcomes_current.manifest.json.rolled_back_${ts}
```

The Patch 6 source run (with the historical `outcome_id` collision bug)
and the Patch 8 v2 source run (with the bug fix) remain immutable for
audit.
