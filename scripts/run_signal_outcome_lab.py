#!/usr/bin/env python3
"""
Signal Outcome Lab — MVP (Patch 4: real outcome computation for XAU backfill).

References:
  docs/architecture/SIGNAL_OUTCOME_LAB.md
  docs/architecture/SIGNAL_OUTCOME_LAB_MVP.md
  docs/architecture/INDICATOR_SIGNAL_POLICY.md
  docs/architecture/LOG_MUTATION_POLICY.md

MVP scope (frozen 2026-05-28):
  - XAUUSD only.
  - Canonical slim only (no TradingView, no MCP, no chart, no chart lock).
  - Manual batch only (no LaunchAgent, no scheduler).
  - Two modes:
      fresh_from_signal_journal    — forward, read indicator_signals.jsonl.
      backfill_from_quarantine     — read-only over the 330 quarantined
                                     legacy outcomes; XAUUSD recoverable.

Patch 4 status:
  - compute_outcome() is now implemented (real computation from canonical slim).
  - In dry-run + backfill mode, the script selects demo records (1 per TF when
    max_signals <= 3) and includes computed outcomes inline in the report.
  - write_outputs() is implemented but only executes when --write is passed.
  - This patch authorizes only dry-run on the 3 hand-picked signals. Bulk runs
    and --write executions require separate explicit authorization.

Hard rules (always honored):
  - No TradingView / MCP / chart calls. Ever.
  - Inputs (Signal Journal, quarantine file) are read-only.
  - Output dir is created ONLY on --write. Never on dry-run.
"""

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants pinned by the MVP contract.
# ---------------------------------------------------------------------------

EVALUATOR_VERSION = "v0.1.0"
ALLOWED_PROVIDER = "PEPPERSTONE"
ALLOWED_SYMBOLS_MVP = {"XAUUSD"}
WHITELIST_FULL = {"XAUUSD", "XAGUSD", "ETHUSD", "US500", "EURUSD", "USOUSD"}
FORBIDDEN_PROVIDERS = {"OANDA", "VANTAGE", "FOREXCOM", "FX", "FX_IDC"}

DRIVE_ROOT = Path("/Volumes/GUTS_ LACIE")
SLIM_ROOT = DRIVE_ROOT / "TradingData" / "slim_features"

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO_ROOT / "alert-bridge" / "logs"
SIGNAL_JOURNAL = LOGS_DIR / "indicator_signals.jsonl"
QUARANTINE_FILE = (
    LOGS_DIR
    / "indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28"
)
DEFAULT_OUTPUT_DIR = LOGS_DIR / "signal_outcomes_lab"

# Primary horizon per timeframe; matches legacy bars_evaluated=20 for clean
# old-vs-new comparison in Mode B. Additional horizons land in a later patch.
HORIZONS = {
    "15": [{"bars": 20, "spec_id": "H20@15M"}],
    "30": [{"bars": 20, "spec_id": "H20@30M"}],
    "60": [{"bars": 20, "spec_id": "H20@1H"}],
}

TF_TO_SLIM_DIR = {"15": "15M", "30": "30M", "60": "1H"}

SLIM_FILENAME_RE = re.compile(
    r"XAUUSD_(?P<tfslug>15m|30m|1h|4h|1d)_features_"
    r"(?P<start>\d{4}-\d{2}-\d{2})_to_(?P<end>\d{4}-\d{2}-\d{2})"
    r"(?P<suffix>[_A-Za-z0-9]*)\.jsonl(?:\.gz)?$"
)

# Verdict tolerances per MVP §10.
CLOSE_AGREE_PCT = 0.005   # |diff_pct| < 0.5% of new_entry → AGREES
ENTRY_DIVERGE_RATIO = 0.10  # |entry_diff| / legacy_entry > 10% → SIGN (provider contamination)

# ---------------------------------------------------------------------------
# Small helpers.
# ---------------------------------------------------------------------------


def parse_iso(s):
    """Parse ISO8601 (with Z or +HH:MM) into aware datetime; None on failure."""
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def is_test_or_synthetic(rec):
    """True if record carries TEST_* or synthetic_* markers (top-level or payload_full)."""
    if not isinstance(rec, dict):
        return False
    pf = rec.get("payload_full")
    candidates = [rec]
    if isinstance(pf, dict):
        candidates.append(pf)
    for d in candidates:
        ind = d.get("indicator_name") or ""
        typ = d.get("signal_type") or ""
        src = d.get("source") or ""
        if isinstance(ind, str) and ind.startswith("TEST_"):
            return True
        if isinstance(typ, str) and typ.startswith("TEST_"):
            return True
        if isinstance(src, str) and src.startswith("synthetic_"):
            return True
    return False


def slim_coverage(symbol, tf):
    """Probe canonical slim files by filename metadata (no file read)."""
    if symbol != "XAUUSD":
        return {"ok": False, "reason": f"symbol {symbol} not in MVP scope"}
    slim_tf = TF_TO_SLIM_DIR.get(str(tf))
    if slim_tf is None:
        return {"ok": False, "reason": f"timeframe {tf} not mapped to slim dir"}
    d = SLIM_ROOT / "XAUUSD" / slim_tf
    if not d.exists():
        return {"ok": False, "reason": f"dir missing: {d}"}
    files = []
    for f in sorted(d.iterdir()):
        m = SLIM_FILENAME_RE.match(f.name)
        if not m:
            continue
        files.append(
            {"name": f.name, "path": str(f),
             "start": m.group("start"), "end": m.group("end")}
        )
    if not files:
        return {"ok": False, "reason": f"no slim files in {d}"}
    return {
        "ok": True,
        "dir": str(d),
        "files": files,
        "overall_start": min(x["start"] for x in files),
        "overall_end": max(x["end"] for x in files),
    }


def locate_slim_file_for(tf, ts_signal):
    """Return Path of the slim file whose date range covers ts_signal, else None."""
    if ts_signal is None:
        return None
    cov = slim_coverage("XAUUSD", tf)
    if not cov.get("ok"):
        return None
    sig_date = ts_signal.date().isoformat()
    for fmeta in cov["files"]:
        if fmeta["start"] <= sig_date <= fmeta["end"]:
            return Path(fmeta["path"])
    return None


def outcome_id(signal_hash, evaluator_version, horizon_spec_id, data_source_resolution):
    """Idempotency id per MVP §12."""
    payload = (
        f"{signal_hash}|{evaluator_version}|{horizon_spec_id}|{data_source_resolution}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Slim file IO — read-only with per-run caching.
# ---------------------------------------------------------------------------

_FILE_CACHE = {}
_SHA_CACHE = {}


def load_slim_file_cached(path):
    """Load and parse all bars; sort by bar_close_time ascending. Cached per run."""
    sp = str(path)
    if sp in _FILE_CACHE:
        return _FILE_CACHE[sp]
    bars = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if "bar_close_time" not in d:
                continue
            bars.append(d)
    bars.sort(key=lambda b: b["bar_close_time"])
    _FILE_CACHE[sp] = bars
    return bars


def sha256_file_cached(path):
    """SHA256 of file content. Cached per run."""
    sp = str(path)
    if sp in _SHA_CACHE:
        return _SHA_CACHE[sp]
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    _SHA_CACHE[sp] = h.hexdigest()
    return _SHA_CACHE[sp]


def find_entry_bar_index(bars, ts_signal, tf_min):
    """
    Locate the index of the SIGNAL BAR — the bar whose close coincides with or
    just precedes ts_signal.

    Convention (matches the legacy enrich, see enrichment_notes "TV close used
    per rule"): when a signal arrives at ts_signal, the relevant signal bar is
    the one that JUST closed at or before ts_signal. The entry price is that
    bar's close. The "horizon" bars are taken strictly AFTER (so close_plus_1
    = close of the next bar, etc.).

    Formula: target_close = floor(ts_signal / tf_sec) * tf_sec
    (the largest bar_close_time <= sig_epoch).
    """
    if ts_signal is None or not bars:
        return None
    tf_sec = tf_min * 60
    sig_epoch = int(ts_signal.timestamp())
    target_close = (sig_epoch // tf_sec) * tf_sec
    lo, hi = 0, len(bars) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        bct = bars[mid].get("bar_close_time")
        if bct == target_close:
            return mid
        elif bct < target_close:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


# ---------------------------------------------------------------------------
# Pre-flight gates (MVP §13).
# ---------------------------------------------------------------------------


def preflight(args):
    """Return (ok, errors). Aborts the run on any failure."""
    errs = []
    if not DRIVE_ROOT.exists():
        errs.append(f"drive not mounted: {DRIVE_ROOT}")
    if not (SLIM_ROOT / "XAUUSD").exists():
        errs.append(f"slim_features/XAUUSD missing: {SLIM_ROOT / 'XAUUSD'}")
    if args.symbol != "XAUUSD":
        errs.append(f"symbol {args.symbol} not in MVP scope (allowed: XAUUSD)")
    if args.mode == "fresh_from_signal_journal":
        if not SIGNAL_JOURNAL.exists():
            errs.append(f"signal journal missing: {SIGNAL_JOURNAL}")
    elif args.mode == "backfill_from_quarantine":
        if not QUARANTINE_FILE.exists():
            errs.append(f"quarantine file missing: {QUARANTINE_FILE}")
    return (len(errs) == 0, errs)


# ---------------------------------------------------------------------------
# Outcome computation (real).
# ---------------------------------------------------------------------------


def compute_outcome(quarantine_record, direction, horizon_spec, run_id=None):
    """
    Compute one outcome record for a (quarantine_record, direction, horizon_spec).

    Real computation from canonical slim only. No chart, no MCP.
    """
    tf = str(quarantine_record.get("timeframe"))
    ts = parse_iso(quarantine_record.get("ts_signal"))
    horizon_bars = horizon_spec["bars"]
    spec_id = horizon_spec["spec_id"]
    signal_hash = quarantine_record.get("signal_hash", "")
    base = quarantine_record.get("base_symbol")

    base_record = _outcome_skeleton(
        quarantine_record, direction, horizon_spec, spec_id, run_id
    )

    if base != "XAUUSD":
        base_record["outcome_status"] = "SKIPPED_UNSUPPORTED_SYMBOL"
        base_record["errors"].append(f"base_symbol {base} not in MVP scope")
        return base_record

    if direction not in ("long", "short"):
        base_record["outcome_status"] = "UNKNOWN"
        base_record["errors"].append(f"invalid direction: {direction}")
        return base_record

    slim_path = locate_slim_file_for(tf, ts)
    if slim_path is None:
        base_record["outcome_status"] = "UNKNOWN"
        base_record["errors"].append("no canonical slim file covers ts_signal date")
        return base_record

    bars = load_slim_file_cached(slim_path)
    sha = sha256_file_cached(slim_path)

    try:
        tf_min = int(tf)
    except Exception:
        base_record["outcome_status"] = "UNKNOWN"
        base_record["errors"].append(f"unparseable timeframe: {tf}")
        return base_record

    entry_idx = find_entry_bar_index(bars, ts, tf_min)
    if entry_idx is None:
        base_record["outcome_status"] = "UNKNOWN"
        base_record["errors"].append("entry bar not found in slim file")
        return base_record

    if entry_idx + horizon_bars >= len(bars):
        base_record["outcome_status"] = "UNKNOWN"
        base_record["errors"].append(
            f"insufficient future bars after entry: have "
            f"{len(bars) - entry_idx - 1}, need {horizon_bars}"
        )
        return base_record

    entry_bar = bars[entry_idx]
    future_bars = bars[entry_idx + 1 : entry_idx + 1 + horizon_bars]

    entry_price = float(entry_bar["close"])
    close_after_horizon = float(future_bars[-1]["close"])

    highs = [float(b["high"]) for b in future_bars]
    lows = [float(b["low"]) for b in future_bars]

    if direction == "long":
        mfe_price = max(highs)
        mfe_abs = mfe_price - entry_price
        mae_price = min(lows)
        mae_abs = mae_price - entry_price  # negative
        if close_after_horizon > entry_price:
            directional = "long_close_above_entry"
        elif close_after_horizon < entry_price:
            directional = "long_close_below_entry"
        else:
            directional = "long_close_equal_entry"
    else:  # short
        mfe_price = min(lows)
        mfe_abs = entry_price - mfe_price
        mae_price = max(highs)
        mae_abs = entry_price - mae_price  # negative
        if close_after_horizon < entry_price:
            directional = "short_close_below_entry"
        elif close_after_horizon > entry_price:
            directional = "short_close_above_entry"
        else:
            directional = "short_close_equal_entry"

    return_pct = (close_after_horizon - entry_price) / entry_price if entry_price else 0.0
    mfe_pct = mfe_abs / entry_price if entry_price else 0.0
    mae_pct = mae_abs / entry_price if entry_price else 0.0

    data_resolution = f"canonical_slim_v2|{sha}"
    oid = outcome_id(signal_hash, EVALUATOR_VERSION, spec_id, data_resolution)

    legacy_ref, diff = compare_legacy_vs_new(
        quarantine_record, direction, entry_price, close_after_horizon, future_bars
    )

    base_record.update({
        "outcome_id": oid,
        "outcome_status": "CLEAN",
        "data_source": "canonical_slim_v2",
        "data_source_ref": f"{slim_path.name}:rows[{entry_idx}..{entry_idx + horizon_bars}]",
        "data_source_sha256": sha,
        "entry_price": entry_price,
        "close_after_horizon": close_after_horizon,
        "mfe": {"price": mfe_price, "abs": mfe_abs, "pct": mfe_pct, "R": None},
        "mae": {"price": mae_price, "abs": mae_abs, "pct": mae_pct, "R": None},
        "return_pct": return_pct,
        "directional_result": directional,
        "hit_result": "not_applicable",
        "legacy_outcome_ref": legacy_ref,
        "old_vs_new_diff": diff,
    })
    base_record["provenance"].update({
        "data_window_from": entry_bar.get("ts"),
        "data_window_to": future_bars[-1].get("ts"),
        "data_bars_observed": len(future_bars),
        "data_bars_expected": horizon_bars,
        "entry_bar_index": entry_idx,
        "entry_bar_close_time_epoch": entry_bar.get("bar_close_time"),
    })
    return base_record


def _outcome_skeleton(qrec, direction, horizon_spec, spec_id, run_id):
    """Bare outcome record template; populated with defaults; modified per status."""
    return {
        "outcome_id": None,
        "signal_hash": qrec.get("signal_hash"),
        "signal_provenance": "quarantine_legacy_2026-05-28",
        "run_id": run_id,
        "evaluator_version": EVALUATOR_VERSION,
        "evaluated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_symbol": qrec.get("base_symbol"),
        "symbol": f"{ALLOWED_PROVIDER}:{qrec.get('base_symbol')}",
        "provider": ALLOWED_PROVIDER,
        "timeframe": str(qrec.get("timeframe")),
        "ts_signal": qrec.get("ts_signal"),
        "indicator_name": qrec.get("indicator_name"),
        "signal_type": qrec.get("signal_type"),
        "direction": direction,
        "horizon": {"bars": horizon_spec["bars"],
                    "tf": str(qrec.get("timeframe")),
                    "spec_id": spec_id},
        "data_source": "none",
        "data_source_ref": None,
        "data_source_sha256": None,
        "provider_status": "ok",
        "legacy_provider_status": "contaminated_pre_pepperstone_fix",
        "outcome_status": "UNKNOWN",
        "entry_price": None,
        "stop_price": None,
        "target_price": None,
        "close_after_horizon": None,
        "mfe": None,
        "mae": None,
        "return_pct": None,
        "directional_result": None,
        "hit_result": "not_applicable",
        "legacy_outcome_ref": None,
        "old_vs_new_diff": None,
        "errors": [],
        "warnings": [],
        "provenance": {
            "signal_source_path": str(QUARANTINE_FILE),
            "raw_symbol_observed": qrec.get("base_symbol"),
            "horizon_bars_used": horizon_spec["bars"],
            "data_window_from": None,
            "data_window_to": None,
            "data_bars_observed": 0,
            "data_bars_expected": horizon_spec["bars"],
            "atr_source": "legacy_quarantine" if qrec.get("atr_at_signal") is not None else "unavailable",
            "chart_lock_holder": None,
        },
    }


def compare_legacy_vs_new(qrec, direction, new_entry, new_close_20, future_bars):
    """Build legacy_outcome_ref and old_vs_new_diff per MVP §10."""
    legacy_entry = qrec.get("entry_price")
    legacy_snapshots = qrec.get("snapshots") or {}
    legacy_close_20 = legacy_snapshots.get("close_plus_20")

    # Canonical snapshots aligned with legacy convention.
    canonical_snaps = {
        "close_plus_1":  float(future_bars[0]["close"])  if len(future_bars) > 0  else None,
        "close_plus_5":  float(future_bars[4]["close"])  if len(future_bars) > 4  else None,
        "close_plus_10": float(future_bars[9]["close"])  if len(future_bars) > 9  else None,
        "close_plus_20": float(future_bars[19]["close"]) if len(future_bars) > 19 else None,
    }

    legacy_ref = {
        "file": QUARANTINE_FILE.name,
        "enriched_at": qrec.get("enriched_at"),
        "bars_evaluated": qrec.get("bars_evaluated"),
        "snapshots_legacy": legacy_snapshots,
        "outcome_for_direction": qrec.get(f"{direction}_outcome"),
    }

    diff = {
        "legacy_entry":            legacy_entry,
        "new_entry":               new_entry,
        "entry_diff_abs":          None,
        "entry_diff_ratio":        None,
        "legacy_close_plus_20":    legacy_close_20,
        "new_close_plus_20":       canonical_snaps["close_plus_20"],
        "close_plus_20_diff_abs":  None,
        "close_plus_20_diff_pct_of_new_entry": None,
        "canonical_snapshots":     canonical_snaps,
        "verdict":                 "NEW_INCOMPLETE",
    }

    if canonical_snaps["close_plus_20"] is None:
        diff["verdict"] = "NEW_INCOMPLETE"
        return legacy_ref, diff

    legacy_outcome = legacy_ref["outcome_for_direction"]
    if not isinstance(legacy_outcome, dict):
        diff["verdict"] = "LEGACY_INCOMPLETE"
        return legacy_ref, diff

    if legacy_entry is None or legacy_close_20 is None:
        diff["verdict"] = "LEGACY_INCOMPLETE"
        return legacy_ref, diff

    # Entry contamination check.
    diff["entry_diff_abs"] = new_entry - legacy_entry
    diff["entry_diff_ratio"] = (new_entry - legacy_entry) / max(abs(legacy_entry), 1e-12)
    if abs(diff["entry_diff_ratio"]) > ENTRY_DIVERGE_RATIO:
        diff["verdict"] = "OUTCOME_DIVERGES_SIGN"
        diff["close_plus_20_diff_abs"] = canonical_snaps["close_plus_20"] - legacy_close_20
        diff["close_plus_20_diff_pct_of_new_entry"] = (
            diff["close_plus_20_diff_abs"] / max(abs(new_entry), 1e-12)
        )
        diff["reason"] = "entry_price_provider_divergence_above_threshold"
        return legacy_ref, diff

    diff["close_plus_20_diff_abs"] = canonical_snaps["close_plus_20"] - legacy_close_20
    diff["close_plus_20_diff_pct_of_new_entry"] = (
        diff["close_plus_20_diff_abs"] / max(abs(new_entry), 1e-12)
    )

    if abs(diff["close_plus_20_diff_pct_of_new_entry"]) < CLOSE_AGREE_PCT:
        diff["verdict"] = "OUTCOME_AGREES"
        return legacy_ref, diff

    legacy_move = legacy_close_20 - legacy_entry
    new_move = new_close_20 - new_entry
    if (legacy_move > 0) != (new_move > 0):
        diff["verdict"] = "OUTCOME_DIVERGES_SIGN"
    else:
        diff["verdict"] = "OUTCOME_DIVERGES_MAGNITUDE"
    return legacy_ref, diff


# ---------------------------------------------------------------------------
# Demo selection — used in dry-run reporting for small batches.
# ---------------------------------------------------------------------------


def select_demo_records(xau_records, target_n):
    """
    Pick demo records for inline computation in dry-run.

    For target_n <= 3: prefer 1 per TF (15, 30, 60) in that order.
    For target_n > 3:  take first target_n records as found.

    Within each TF, prefer non-ambiguous direction + atr present.
    """
    if target_n is None or target_n > 3:
        return xau_records[: (target_n or len(xau_records))]
    picks = []
    seen_tfs = set()
    for tf_pref in ("15", "30", "60"):
        if len(picks) >= target_n:
            break
        # Prefer non-ambiguous with ATR.
        best = None
        for r in xau_records:
            if str(r.get("timeframe")) != tf_pref:
                continue
            if r.get("atr_at_signal") is None:
                continue
            d = r.get("direction_classified")
            if d in ("long", "short"):
                best = r
                break
            if best is None and d == "ambiguous":
                best = r
        if best is not None and tf_pref not in seen_tfs:
            picks.append(best)
            seen_tfs.add(tf_pref)
    return picks[:target_n]


def expand_for_directions(record):
    """For a quarantine record, yield (record, direction) pairs.

    Ambiguous splits into two yields (long + short), per MVP §5.
    """
    d = record.get("direction_classified")
    if d == "ambiguous":
        yield (record, "long")
        yield (record, "short")
    elif d in ("long", "short"):
        yield (record, d)
    else:
        yield (record, None)  # will be UNKNOWN


# ---------------------------------------------------------------------------
# Mode A — fresh_from_signal_journal (MVP §2).
# ---------------------------------------------------------------------------


def plan_fresh(args):
    total = 0
    valid_xau = []
    skipped = collections.Counter()

    with open(SIGNAL_JOURNAL, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                rec = json.loads(line)
            except Exception:
                skipped["json_error"] += 1
                continue
            pf = rec.get("payload_full") if isinstance(rec.get("payload_full"), dict) else {}
            vstat = pf.get("validation_status")
            if vstat != "valid":
                skipped[f"validation_status={vstat}"] += 1
                continue
            sym = pf.get("symbol") or rec.get("symbol") or ""
            if not sym.startswith(f"{ALLOWED_PROVIDER}:"):
                skipped["provider_mismatch"] += 1
                continue
            base = pf.get("base_symbol") or rec.get("base_symbol")
            if base != "XAUUSD":
                skipped[f"non_xau_base={base}"] += 1
                continue
            if is_test_or_synthetic(rec):
                skipped["test_or_synthetic"] += 1
                continue
            valid_xau.append(rec)

    by_tf = collections.Counter(
        str((r.get("payload_full") or {}).get("timeframe") or r.get("timeframe") or "?")
        for r in valid_xau
    )

    coverage = {tf: slim_coverage("XAUUSD", tf) for tf in sorted(by_tf)}

    mature = collections.Counter()
    for r in valid_xau:
        tf = str((r.get("payload_full") or {}).get("timeframe") or r.get("timeframe") or "")
        cov = coverage.get(tf, {})
        if not cov.get("ok"):
            mature[(tf, "no_coverage")] += 1
            continue
        ts = parse_iso(r.get("ts_signal") or (r.get("payload_full") or {}).get("ts_signal"))
        if ts is None:
            mature[(tf, "ts_unparseable")] += 1
            continue
        try:
            tf_min = int(tf)
        except Exception:
            mature[(tf, "tf_unknown")] += 1
            continue
        end_dt = dt.datetime.fromisoformat(cov["overall_end"] + "T00:00:00+00:00")
        needed = ts + dt.timedelta(minutes=tf_min * 20)
        mature[(tf, "mature" if needed < end_dt else "immature")] += 1

    valid_capped = (
        valid_xau[: args.max_signals] if args.max_signals is not None else valid_xau
    )

    return {
        "mode": "fresh_from_signal_journal",
        "input_path": str(SIGNAL_JOURNAL),
        "total_records_scanned": total,
        "valid_xau_after_filter": len(valid_xau),
        "valid_xau_capped_by_max_signals": len(valid_capped),
        "skipped_reasons": dict(skipped),
        "by_timeframe": dict(by_tf),
        "canonical_coverage": _cov_summary(coverage),
        "maturity_summary": {f"{tf}/{status}": n for (tf, status), n in mature.items()},
    }


# ---------------------------------------------------------------------------
# Mode B — backfill_from_quarantine (MVP §3).
# ---------------------------------------------------------------------------


def plan_backfill(args):
    total = 0
    by_base = collections.Counter()
    xau_records = []
    non_xau = collections.Counter()
    directions = collections.Counter()
    tfs = collections.Counter()
    has_atr = 0
    no_atr = 0

    with open(QUARANTINE_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                rec = json.loads(line)
            except Exception:
                continue
            base = rec.get("base_symbol", "?")
            by_base[base] += 1
            if base == "XAUUSD":
                xau_records.append(rec)
                tfs[str(rec.get("timeframe", "?"))] += 1
                directions[rec.get("direction_classified", "?")] += 1
                if rec.get("atr_at_signal") is not None:
                    has_atr += 1
                else:
                    no_atr += 1
            else:
                non_xau[base] += 1

    coverage = {tf: slim_coverage("XAUUSD", tf) for tf in sorted(tfs)}

    n_long = directions.get("long", 0)
    n_short = directions.get("short", 0)
    n_amb = directions.get("ambiguous", 0)
    planned_outcomes = n_long + n_short + 2 * n_amb  # ambiguous splits into 2

    sj_hashes = set()
    if SIGNAL_JOURNAL.exists():
        with open(SIGNAL_JOURNAL, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                h = d.get("signal_hash")
                if h:
                    sj_hashes.add(h)

    q_hashes = {r.get("signal_hash") for r in xau_records if r.get("signal_hash")}
    matched = q_hashes & sj_hashes

    xau_capped = (
        xau_records[: args.max_signals] if args.max_signals is not None else xau_records
    )

    return {
        "mode": "backfill_from_quarantine",
        "input_path": str(QUARANTINE_FILE),
        "input_classification": "QUARANTINED_LEGACY_REFERENCE",
        "total_legacy_outcomes": total,
        "by_base": dict(by_base),
        "xau_recoverable_total": len(xau_records),
        "xau_capped_by_max_signals": len(xau_capped),
        "non_xau_pending": dict(non_xau),
        "xau_timeframe_distribution": dict(tfs),
        "xau_direction_distribution": dict(directions),
        "xau_atr_status": {"has_atr": has_atr, "no_atr": no_atr},
        "planned_outcomes_count_with_ambiguous_split": planned_outcomes,
        "signal_hash_matched_in_signal_journal": len(matched),
        "canonical_coverage": _cov_summary(coverage),
        # demo selection used downstream for inline outcome computation
        "_xau_records_for_demo": xau_records,
    }


def _cov_summary(coverage):
    out = {}
    for tf, c in coverage.items():
        if c.get("ok"):
            out[tf] = {
                "ok": True,
                "start": c["overall_start"],
                "end": c["overall_end"],
                "files": len(c["files"]),
            }
        else:
            out[tf] = {"ok": False, "reason": c.get("reason")}
    return out


# ---------------------------------------------------------------------------
# Write path — fully implemented; only fires when --write is passed.
# ---------------------------------------------------------------------------


def write_outputs(report, computed_outcomes, output_dir, run_id, mode, args):
    """
    Persist outcomes + manifest + log to disk. Caller has guaranteed --write.

    Writes ONLY under output_dir/<run_id>/ and the shared
    output_dir/outcomes_current.jsonl. Never modifies inputs.
    """
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    outcomes_path = run_dir / f"outcomes_{run_id}.jsonl"
    manifest_path = run_dir / f"outcomes_{run_id}.manifest.json"
    log_path = run_dir / f"outcomes_{run_id}.log"
    current_path = Path(output_dir) / "outcomes_current.jsonl"

    # outcomes_<run_id>.jsonl (one record per line, atomic via append).
    with open(outcomes_path, "w", encoding="utf-8") as fh:
        for o in computed_outcomes:
            fh.write(json.dumps(o, default=str) + "\n")

    # Manifest.
    status_counts = collections.Counter(o.get("outcome_status") for o in computed_outcomes)
    verdict_counts = collections.Counter(
        (o.get("old_vs_new_diff") or {}).get("verdict") for o in computed_outcomes
    )
    manifest = {
        "run_id": run_id,
        "mode": mode,
        "symbol": args.symbol,
        "evaluator_version": EVALUATOR_VERSION,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": os.uname().nodename,
        "max_signals": args.max_signals,
        "outcomes_count": len(computed_outcomes),
        "status_counts": dict(status_counts),
        "verdict_counts": dict(verdict_counts),
        "output_paths": {
            "outcomes_jsonl": str(outcomes_path),
            "manifest_json": str(manifest_path),
            "run_log": str(log_path),
            "outcomes_current": str(current_path),
        },
        "input_summary": report.get("plan"),
    }
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)

    # Run log (forensic).
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(report, indent=2, default=str))

    # Atomic rollup of outcomes_current.jsonl (CLEAN only, dedup by outcome_id).
    existing = {}
    if current_path.exists():
        with open(current_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                oid = d.get("outcome_id")
                if oid:
                    existing[oid] = d
    for o in computed_outcomes:
        if o.get("outcome_status") == "CLEAN" and o.get("outcome_id"):
            existing[o["outcome_id"]] = o
    tmp = current_path.with_suffix(current_path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for o in existing.values():
            fh.write(json.dumps(o, default=str) + "\n")
    tmp.replace(current_path)

    # Mode B extras.
    written = {
        "outcomes_jsonl": str(outcomes_path),
        "manifest_json": str(manifest_path),
        "run_log": str(log_path),
        "outcomes_current": str(current_path),
    }

    if mode == "backfill_from_quarantine":
        report_md = run_dir / "legacy_comparison_report.md"
        with open(report_md, "w", encoding="utf-8") as fh:
            fh.write(_render_legacy_comparison_md(computed_outcomes, run_id, manifest))
        skipped_path = run_dir / "skipped_signals.jsonl"
        with open(skipped_path, "w", encoding="utf-8") as fh:
            # Non-XAU pending are recorded as skipped at file-level.
            for base, n in (report.get("plan") or {}).get("non_xau_pending", {}).items():
                fh.write(json.dumps({
                    "base_symbol": base,
                    "count_pending": n,
                    "outcome_status": "PENDING_NO_CANONICAL_DATA",
                    "reason": "no canonical slim for base outside XAUUSD in MVP",
                }) + "\n")
        written["legacy_comparison_report"] = str(report_md)
        written["skipped_signals"] = str(skipped_path)

    return written


def _render_legacy_comparison_md(computed_outcomes, run_id, manifest):
    lines = []
    lines.append(f"# Legacy Comparison Report — {run_id}")
    lines.append("")
    lines.append(f"Generated: {manifest.get('created_at')}")
    lines.append(f"Outcomes computed: {manifest.get('outcomes_count')}")
    lines.append("")
    lines.append("## Verdict distribution")
    lines.append("")
    for v, n in (manifest.get("verdict_counts") or {}).items():
        lines.append(f"- `{v}`: {n}")
    lines.append("")
    lines.append("## Per-record details")
    lines.append("")
    for o in computed_outcomes:
        diff = o.get("old_vs_new_diff") or {}
        lines.append(
            f"- `{o.get('signal_hash')}` "
            f"TF={o.get('timeframe')} dir={o.get('direction')} "
            f"verdict=**{diff.get('verdict')}**  "
            f"legacy_entry={diff.get('legacy_entry')} "
            f"new_entry={o.get('entry_price')} "
            f"legacy_close+20={diff.get('legacy_close_plus_20')} "
            f"new_close+20={diff.get('new_close_plus_20')}"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def build_argparser():
    p = argparse.ArgumentParser(
        prog="run_signal_outcome_lab",
        description=(
            "Signal Outcome Lab — MVP "
            "(XAU-only, canonical-slim-only, no chart, dry-run default)."
        ),
    )
    p.add_argument(
        "--mode",
        required=True,
        choices=["fresh_from_signal_journal", "backfill_from_quarantine"],
    )
    p.add_argument("--symbol", default="XAUUSD",
                   help="MVP allows only XAUUSD; other values rejected by pre-flight.")
    p.add_argument("--evaluator-version", default=EVALUATOR_VERSION)
    p.add_argument("--run-id", default=None,
                   help="Required when --write is used; auto-generated in dry-run.")
    p.add_argument("--max-signals", type=int, default=None)
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR),
                   help="Where outputs land when --write is set.")
    p.add_argument("--signals-from", default=None, help="ISO8601; reserved.")
    p.add_argument("--signals-to", default=None, help="ISO8601; reserved.")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--dry-run", action="store_true", default=False,
                   help="(default) Plan-only; no writes. Explicit alias for clarity.")
    p.add_argument("--write", action="store_true", default=False,
                   help="Enable real writes. Outputs land under --output-dir/<run-id>/.")
    return p


def main(argv=None):
    parser = build_argparser()
    args = parser.parse_args(argv)

    args.dry_run = not args.write

    ok, errs = preflight(args)
    base_summary = {
        "lab_version": EVALUATOR_VERSION,
        "mode": args.mode,
        "symbol": args.symbol,
        "evaluator_version": args.evaluator_version,
        "run_id": args.run_id,
        "dry_run": args.dry_run,
        "max_signals": args.max_signals,
        "output_dir_planned": args.output_dir,
        "preflight_ok": ok,
        "preflight_errors": errs,
    }
    if not ok:
        print(json.dumps({"summary": base_summary, "aborted": True},
                         indent=2, default=str))
        return 1

    if args.mode == "fresh_from_signal_journal":
        plan = plan_fresh(args)
        xau_records = []  # fresh inline outcome computation deferred to a later patch
    else:
        plan = plan_backfill(args)
        xau_records = plan.pop("_xau_records_for_demo", [])

    # Compute outcomes when in backfill + max-signals is small (demo path).
    computed_outcomes = []
    if args.mode == "backfill_from_quarantine":
        demo_records = select_demo_records(xau_records, args.max_signals)
        run_id = args.run_id or (
            f"{args.mode.split('_')[0]}-"
            f"{'WRITE' if args.write else 'DRYRUN'}-"
            f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')}"
        )
        for rec in demo_records:
            tf = str(rec.get("timeframe"))
            specs = HORIZONS.get(tf, [])
            for record, direction in expand_for_directions(rec):
                if direction is None:
                    continue
                for spec in specs:
                    computed_outcomes.append(
                        compute_outcome(record, direction, spec, run_id=run_id)
                    )
    else:
        run_id = args.run_id or (
            f"{args.mode.split('_')[0]}-"
            f"{'WRITE' if args.write else 'DRYRUN'}-"
            f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')}"
        )

    output_paths_planned = {
        "outcomes_jsonl":   f"{args.output_dir}/{run_id}/outcomes_{run_id}.jsonl",
        "manifest_json":    f"{args.output_dir}/{run_id}/outcomes_{run_id}.manifest.json",
        "run_log":          f"{args.output_dir}/{run_id}/outcomes_{run_id}.log",
        "outcomes_current": f"{args.output_dir}/outcomes_current.jsonl",
    }
    if args.mode == "backfill_from_quarantine":
        output_paths_planned["legacy_comparison_report"] = (
            f"{args.output_dir}/{run_id}/legacy_comparison_report.md"
        )
        output_paths_planned["skipped_signals"] = (
            f"{args.output_dir}/{run_id}/skipped_signals.jsonl"
        )

    # Brief view of computed outcomes for non-verbose mode.
    def _outcome_brief(o):
        diff = o.get("old_vs_new_diff") or {}
        return {
            "outcome_id": o.get("outcome_id"),
            "signal_hash": o.get("signal_hash"),
            "timeframe": o.get("timeframe"),
            "direction": o.get("direction"),
            "outcome_status": o.get("outcome_status"),
            "entry_price_new": o.get("entry_price"),
            "close_after_horizon": o.get("close_after_horizon"),
            "return_pct": o.get("return_pct"),
            "mfe_abs": (o.get("mfe") or {}).get("abs"),
            "mae_abs": (o.get("mae") or {}).get("abs"),
            "directional_result": o.get("directional_result"),
            "data_source_ref": o.get("data_source_ref"),
            "data_source_sha256_prefix": (o.get("data_source_sha256") or "")[:16],
            "old_vs_new_diff_verdict": diff.get("verdict"),
            "entry_diff_ratio": diff.get("entry_diff_ratio"),
            "close_plus_20_diff_abs": diff.get("close_plus_20_diff_abs"),
            "errors": o.get("errors"),
        }

    report = {
        "summary": base_summary,
        "plan": plan,
        "output_paths_planned": output_paths_planned,
        "computed_outcomes_count": len(computed_outcomes),
        "computed_outcomes_brief": [_outcome_brief(o) for o in computed_outcomes],
        "computed_outcomes_full": computed_outcomes if args.verbose else None,
        "files_written_this_run": 0,
        "note": (
            "Dry-run only. No files were created; no log was modified; "
            "no chart was touched." if args.dry_run else
            "Real-write run. Files written under output-dir/<run-id>/."
        ),
    }

    if args.write:
        written = write_outputs(report, computed_outcomes,
                                args.output_dir, run_id, args.mode, args)
        report["files_written_this_run"] = len(written)
        report["files_written"] = written

    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
