#!/usr/bin/env python3
"""
Signal Outcome Lab — MVP skeleton (Patch 3).

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

This is a skeleton:
  - --dry-run is the default (and the only allowed mode in this patch).
  - --write is intentionally REJECTED here. Real writes land in a later
    authorized patch.
  - compute_outcome_skeleton() is defined but NOT called in dry-run.
  - No directory is created. No file is written. No log is mutated.
  - The Signal Journal and the quarantine file are read-only inputs.
"""

import argparse
import collections
import datetime as dt
import hashlib
import json
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
    """
    Probe canonical slim files for (symbol, timeframe) using filename metadata.

    Reads NO file content; only the directory listing. Returns:
        {"ok": True, "dir": str, "files": [...], "overall_start": str, "overall_end": str}
        {"ok": False, "reason": str}
    """
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
        files.append({"name": f.name, "start": m.group("start"), "end": m.group("end")})
    if not files:
        return {"ok": False, "reason": f"no slim files in {d}"}
    return {
        "ok": True,
        "dir": str(d),
        "files": files,
        "overall_start": min(x["start"] for x in files),
        "overall_end": max(x["end"] for x in files),
    }


def outcome_id(signal_hash, evaluator_version, horizon_spec_id, data_source_resolution):
    """Idempotency id per MVP §12."""
    payload = (
        f"{signal_hash}|{evaluator_version}|{horizon_spec_id}|{data_source_resolution}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Pre-flight gates (MVP §13).
# ---------------------------------------------------------------------------


def preflight(args):
    """Return (ok, errors). Aborts the run on any failure."""
    errs = []
    # Gate 1: drive mounted.
    if not DRIVE_ROOT.exists():
        errs.append(f"drive not mounted: {DRIVE_ROOT}")
    # Gate 2: slim XAU exists.
    if not (SLIM_ROOT / "XAUUSD").exists():
        errs.append(f"slim_features/XAUUSD missing: {SLIM_ROOT / 'XAUUSD'}")
    # Gates 6/7: symbol restriction.
    if args.symbol != "XAUUSD":
        errs.append(f"symbol {args.symbol} not in MVP scope (allowed: XAUUSD)")
    # Gate 5: input file by mode.
    if args.mode == "fresh_from_signal_journal":
        if not SIGNAL_JOURNAL.exists():
            errs.append(f"signal journal missing: {SIGNAL_JOURNAL}")
    elif args.mode == "backfill_from_quarantine":
        if not QUARANTINE_FILE.exists():
            errs.append(f"quarantine file missing: {QUARANTINE_FILE}")
    # Gates 4/8/9: structural — this skeleton makes ZERO chart/MCP calls.
    return (len(errs) == 0, errs)


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
        "maturity_summary": {
            f"{tf}/{status}": n for (tf, status), n in mature.items()
        },
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
# Outcome computation — DEFINED but NOT called in skeleton.
# ---------------------------------------------------------------------------


def compute_outcome_skeleton(signal, slim_bars, horizon_bars, direction):
    """
    Skeleton outcome computation. NOT called in dry-run.

    Future patches (under explicit authorization) will implement:
      - locate entry bar by ts_signal
      - take `horizon_bars` closed bars after
      - compute close_after_horizon, MFE, MAE, return_pct, directional_result
      - attach data_source_sha256, data_window, provenance
      - emit per the MVP §11 schema
    """
    raise NotImplementedError(
        "compute_outcome_skeleton is intentionally not implemented in this "
        "skeleton patch (Patch 3). Real outcome computation lands in a later "
        "authorized patch."
    )


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def build_argparser():
    p = argparse.ArgumentParser(
        prog="run_signal_outcome_lab",
        description=(
            "Signal Outcome Lab — MVP skeleton "
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
                   help="Required when --write is implemented; ignored in dry-run if omitted.")
    p.add_argument("--max-signals", type=int, default=None)
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR),
                   help="Where outputs would land if --write were implemented.")
    p.add_argument("--signals-from", default=None, help="ISO8601; reserved.")
    p.add_argument("--signals-to", default=None, help="ISO8601; reserved.")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--dry-run", action="store_true", default=False,
                   help="(default) Plan-only; no writes. Explicit alias for clarity.")
    p.add_argument("--write", action="store_true", default=False,
                   help="(NOT IMPLEMENTED in skeleton; the run will exit non-zero.)")
    p.add_argument("--i-understand-this-is-not-implemented",
                   action="store_true", default=False,
                   help="Acknowledgment placeholder; still rejected in this patch.")
    return p


def main(argv=None):
    parser = build_argparser()
    args = parser.parse_args(argv)

    # Skeleton: always dry-run; reject --write unconditionally.
    args.dry_run = not args.write
    if not args.dry_run:
        print(
            "ERROR: --write is not implemented in this skeleton (Patch 3). "
            "Run with --dry-run (default).",
            file=sys.stderr,
        )
        return 2

    ok, errs = preflight(args)
    base_summary = {
        "lab_version": EVALUATOR_VERSION,
        "mode": args.mode,
        "symbol": args.symbol,
        "evaluator_version": args.evaluator_version,
        "run_id": args.run_id,
        "dry_run": True,
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
    else:
        plan = plan_backfill(args)

    run_id = args.run_id or (
        f"{args.mode.split('_')[0]}-DRYRUN-"
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

    report = {
        "summary": base_summary,
        "plan": plan,
        "output_paths_planned": output_paths_planned,
        "files_written_this_run": 0,
        "note": (
            "Dry-run only. No files were created; no log was modified; "
            "no chart was touched. compute_outcome_skeleton() is defined "
            "but intentionally not called in this skeleton."
        ),
    }
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
