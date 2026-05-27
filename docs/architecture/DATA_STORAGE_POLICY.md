# Data Storage Policy — hot (MacBook) vs cold (external)

> As-of **2026-05-26**. Companion to [OPERATIONAL_INVENTORY.md](./OPERATIONAL_INVENTORY.md).
> No secrets here. Paths/checksums only.

## Principle
- **MacBook = live system + files needed for immediate operation** (HOT).
- **External drive `GUTS_ LACIE` (exFAT) = cold storage**: complete RAW datasets, historical
  backtests, cold backups, and manifests. Root: `/Volumes/GUTS_ LACIE/TradingData/`.
- **If the external drive is disconnected, production must NOT break.** Nothing live depends on it.
- **Preserve RAW datasets complete** — do **not** reduce payload / drop features. `gzip` is allowed
  because it is **lossless** (the file returns identical via `gunzip`, verified by roundtrip SHA256).

## Cold-archive procedure (mandatory before any local deletion)
A local file may be deleted **only after** ALL of:
1. copy/`gzip -c` to the external drive;
2. SHA256 of the original recorded;
3. SHA256 of the `.gz` recorded;
4. `gzip -t` (integrity) passes;
5. **roundtrip** `gunzip -c <.gz> | sha256` == original SHA256;
6. manifest written under `…/TradingData/manifests/`;
7. **explicit per-batch deletion approval** from the operator.

## External layout
```
/Volumes/GUTS_ LACIE/TradingData/
  raw_replay/XAUUSD/{15M,30M,1H,4H,1D}/  # gzipped raw replay feature dumps
  backtests/XAUUSD/{15M,30M,1H,4H}/ # gzipped historical backtest dumps
  slim_features/...  legacy_logs/  legacy_archives/  backups/
  manifests/                        # one manifest per archived file/batch
  README.md
```

## Current external contents (cold, validated)

**The authoritative inventory is the Dataset Registry** → [`docs/data/dataset_registry.json`](../data/dataset_registry.json),
generated/validated by `scripts/build_dataset_registry.py` (scans `manifests/` + `raw_replay/XAUUSD/`,
confirms each `.gz` + `gzip -t` + sha256==manifest, records divergences as warnings). **Do not
re-list the detailed inventory here** — query the registry. The per-file manifests under `manifests/`
(and `superseded/`) remain the primary integrity source; the registry is the rollup.

Snapshot (as of 2026-05-27 — see registry for the source of truth; 20 datasets, 0 warnings, all integrity-validated):
- **XAU 15M** — 2 years, 8 active blocks (3-month each) + 1 superseded (the pre-baseline `2026-02-25→05-25`, kept in `raw_replay/XAUUSD/15M/superseded/`; source of truth for that window is `..._rerun_customOBbaseline.jsonl.gz`).
- **XAU 30M** — 2 years, 4 active blocks (6-month each).
- **XAU 1H** — 2 years, 3 active blocks (year 1 = 2 semesters, year 2 = 1 annual block).
- **XAU 4H** — ~10 years deep (macro/regime context), 3 active blocks: `2016-05-25→2020-01-01` · `2020-01-01→2023-01-01` · `2023-01-03→2026-05-25`.
- **XAU 1D** — ~14 years deep (macro/regime context), 1 active block: `2012-06-19→2026-05-25`.
- Slim features (1-row-per-bar, derived/regenerable) extracted to `slim_features/XAUUSD/{15M,4H,1D}/` via `scripts/extract_replay_features_v1.py`. Derived layer — RAW `.gz` + manifests remain the source of truth.
- 5× 4H pre-v6 unversioned dumps in `backtests/XAUUSD/4H/` (outside `raw_replay/`, not in the registry).
- All RAW locals removed; baseline = Custom OB v11 + LuxAlgo SMC + NAS Top Bottom + Market Order Bubbles + RSI.

## Current local state (`alert-bridge/logs/backtests/`, ~1.3 GB)
**Kept on MacBook (HOT or live dependency):**
- Active logs / active jsonl (`tradingview_alerts.jsonl`, `indicator_signals.jsonl`,
  `indicator_signals_dedup_index.json`, `setup_research_log.jsonl`, `setup_watch_log.jsonl`,
  `setup_watch_state.json`, active launchd logs), receiver, LaunchAgents, scripts, `src/`, `my-strategy/`.
- **8× `XAUUSD_240_*_v6.jsonl` (4H, ~1.35 GB)** — kept local because **`find_dream_demands.py`**
  references all 8 by name (manual research tool).
- **`XAUUSD_240_2025-11-19_to_2026-05-19.jsonl` (13 MB)** — kept local because
  **`draw_xau_4h_trades.py`** hardcodes it.

**Removed locally (after external validation or as smoke artifacts):**
- All 4 RAW XAU 15M blocks (~4.4 GB total transient) — each archived+validated externally, then deleted.
- 5× 4H unversioned `_to_2026-05-20` + their checkpoints (~65 MB) — archived externally first.
- 15M smoke artifacts (`*_80bars*`, scroll-collector `15m_ohlcv_*`, ~15 MB) — test artifacts, not archived.
- 30M + 1H smoke artifacts (`XAUUSD_{30m,60m}_replay_2026-02-24_80bars.jsonl` + checkpoints, ~32 MB, 2026-05-26) — test artifacts, regenerable via `--replay-smoke`, not archived.

## Historical collection plan (multi-TF)
Build a robust per-timeframe historical base **before** validating XAU strategies. RAW kept
**complete** (no payload reduction). Replay only — **no external source**. One block at a time,
always via `safe_backtest_window.sh` (maintenance window). After each block: validate file →
`gzip` lossless to external → SHA256(orig) → SHA256(gz) → `gzip -t` → roundtrip SHA256 →
manifest → **explicit approval** → delete local. **A block does not start until the previous
one is validated and archived.**

| TF | Coverage | Block size | Blocks | Status |
|---|---|---|---|---|
| XAU 15M | 1 year | 3 months | 4: 2025-05-25→08-25 · 08-25→11-25 · 11-25→2026-02-25 · 2026-02-25→05-25 | ✅ **COMPLETE** (4/4 archived, locals clean) |
| XAU 30M | 2 years | **6 months** | 4: 2025-11-25→2026-05-25 · 2025-05-25→2025-11-25 · 2024-11-25→2025-05-25 · 2024-05-25→2024-11-25 | ⏳ pending (smoke ✓; block 1 authorized but **deferred** until enrich done) |
| XAU 1H | 2 years | **6 months** | 4: same 4 windows as 30M | ⏳ pending (smoke ✓) |

> **Plan revised 2026-05-26:** 30M/1H use **6-month blocks** (not 3) — fewer bars per TF make 6-month blocks efficient and still under the 8000-bar cap (30M 6-mo ≈ 6000-6200 bars, 1H 6-mo ≈ 3000). Both 30M and 1H target **2 years / 4 blocks**.

- Collector: **`alert-bridge/run_xau_replay_feature_collect.py`** (TF-agnostic; `--symbol`/`--timeframe 15|30|60`).
- Real block: `safe_backtest_window.sh --replay-collect --timeframe T --start-date S --end-date E`.
- ⚠️ Each block pauses the XAU 4H daemon for the whole run (~30 min for a 6-month 30M/1H block).

### 🚨 Mandatory preflight before any 30M/1H collection block
The daily enrich pipeline (`com.cristrein.enrich-indicator-outcomes` → `enrich_indicator_outcomes.py --batch-size 15`)
spawns `claude -p` "OUTCOME EVALUATOR" subprocesses that **use the chart via MCP** and **leak one orphan
`server.js` per batch**. A backlog can keep it running for hours. The window's `pkill -f server.js` would kill an
active evaluator's MCP server mid-run. **Before opening a collection window, ALL must hold:**
1. `pgrep -fl "OUTCOME EVALUATOR"` → empty.
2. `pgrep -fl enrich_indicator_outcomes` → empty.
3. Clean leftover orphan `server.js` (kill only `ppid=1` ones; preserve the daemon's child and any active evaluator child).
4. Read-only chart check (`node src/core/health.js` → sym/tf) + confirm XAU + correct TF + the 5 indicators loaded.

### Pending P1 (hardening, separate authorization)
- **Leak fix in `enrich_indicator_outcomes.py`** (`run_claude_batch`): `subprocess.run(["claude",…])` has no process
  group, so the grandchild `node server.js` is orphaned on timeout/exit. Proposed fix: spawn with `start_new_session=True`
  and `os.killpg` the whole group in `finally`. Apply+test only when enrich is idle (the test also uses the chart/MCP).

## Pending decisions
1. **Lote 2 — the 8 v6 4H (~1.35 GB):** move to external requires resolving the
   `find_dream_demands.py` dependency. Options: (a) keep local; (b) update `find_dream_demands.py`
   to read from external/gzip; (c) restore-on-demand mechanism. **Not decided.**
2. **`backups/` (~15 MB):** low-priority candidate for external (`legacy_logs`/`legacy_archives`/`backups`).
3. **Next practical step:** 15M is complete. Resume the 30M collection (block 1: 2025-11-25→2026-05-25)
   **once enrich is idle** (see mandatory preflight above), then 1H. Building an analysis/extractor for the
   accumulated external dataset is a parallel option — per operator decision.

## Reminders
- The replay feature collector is `alert-bridge/run_xau_replay_feature_collect.py`; windowed runs go
  through `safe_backtest_window.sh --replay-collect --timeframe T --start-date S --end-date E`
  (maintenance window). Default symbol/timeframe stays PEPPERSTONE:XAUUSD 15M.
- Restore a cold dataset when needed: `gunzip -c <external>.gz > <local>` (lossless; verify SHA256).
