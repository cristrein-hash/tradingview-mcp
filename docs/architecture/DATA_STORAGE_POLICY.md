# Data Storage Policy — hot (MacBook) vs cold (external)

> As-of **2026-05-25**. Companion to [OPERATIONAL_INVENTORY.md](./OPERATIONAL_INVENTORY.md).
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
  raw_replay/XAUUSD/{15M,30M,1H}/   # gzipped raw replay feature dumps
  backtests/XAUUSD/{15M,30M,1H,4H}/ # gzipped historical backtest dumps
  slim_features/...  legacy_logs/  legacy_archives/  backups/
  manifests/                        # one manifest per archived file/batch
  README.md
```

## Current external contents (cold, validated)
| What | External path | Status |
|---|---|---|
| RAW XAU 15M 3-month replay (5710 bars) | `raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-02-25_to_2026-05-25.jsonl.gz` (~130 MB) | gzip+roundtrip ✓ · manifest ✓ · **local removed** |
| 5× 4H pre-v6 unversioned dumps (`_to_2026-05-20`) | `backtests/XAUUSD/4H/*.jsonl.gz` (~1.9 MB) + 5 checkpoints | gzip+roundtrip 5/5 ✓ · consolidated manifest ✓ · **locals removed** |
| Manifests | `manifests/` | per-file + consolidated (path/size/sha256 original+gz, roundtrip) |

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
- RAW XAU 15M 3-month replay (1.06 GB) — archived externally first.
- 5× 4H unversioned `_to_2026-05-20` + their checkpoints (~65 MB) — archived externally first.
- 15M smoke artifacts (`*_80bars*`, scroll-collector `15m_ohlcv_*`, ~15 MB) — test artifacts, not archived.

## Historical collection plan (multi-TF, in progress)
Build a robust per-timeframe historical base **before** validating XAU strategies. RAW kept
**complete** (no payload reduction). Replay only — **no external source**. Collected in
**3-month blocks, one at a time**, always via `safe_backtest_window.sh` (maintenance window).
After each block: validate file → `gzip` lossless to external → SHA256(orig) → SHA256(gz) →
`gzip -t` → roundtrip SHA256 → manifest → **explicit approval** → delete local. **A block does
not start until the previous one is validated and archived.**

| TF | Coverage | Blocks (3-mo each) | Status |
|---|---|---|---|
| XAU 15M | 1 year | 2025-05-25→08-25 · 08-25→11-25 · 11-25→2026-02-25 | pending (+ 2026-02-25→05-25 ✅ archived) |
| XAU 30M | 1 year | 4 blocks: 2025-05-25 → 2026-05-25 | pending |
| XAU 1H | 2 years | 8 blocks: 2024-05-25 → 2026-05-25 | pending |

- Collector: **`alert-bridge/run_xau_replay_feature_collect.py`** (TF-agnostic; `--symbol`/`--timeframe 15|30|60`).
- Per-TF **smoke first** (80 bars) and confirm all feature sources return data before any real block:
  `safe_backtest_window.sh --replay-smoke --timeframe 15|30|60`.
- Real block: `safe_backtest_window.sh --replay-collect --timeframe T --start-date S --end-date E`.
- Estimated cold size added: ~0.9 GB gz total (15M ~130 MB/block, 30M ~65 MB, 1H ~33 MB). Peak local
  transient is one block (~1 GB for 15M) — bounded by the serialized, archive-before-next rule.
- ⚠️ Each block pauses the XAU 4H daemon for the whole run (15M 3-mo ≈ 1.6–2.4 h); calibrate from the smoke.

## Pending decisions
1. **Lote 2 — the 8 v6 4H (~1.35 GB):** move to external requires resolving the
   `find_dream_demands.py` dependency. Options: (a) keep local; (b) update `find_dream_demands.py`
   to read from external/gzip; (c) restore-on-demand mechanism. **Not decided.**
2. **`backups/` (~15 MB):** low-priority candidate for external (`legacy_logs`/`legacy_archives`/`backups`).
3. **Next practical step:** run the multi-TF collection plan above (smokes → block 1), then build an
   analysis/extractor for the accumulated external dataset — per operator decision.

## Reminders
- The replay feature collector is `alert-bridge/run_xau_replay_feature_collect.py`; windowed runs go
  through `safe_backtest_window.sh --replay-collect --timeframe T --start-date S --end-date E`
  (maintenance window). Default symbol/timeframe stays PEPPERSTONE:XAUUSD 15M.
- Restore a cold dataset when needed: `gunzip -c <external>.gz > <local>` (lossless; verify SHA256).
