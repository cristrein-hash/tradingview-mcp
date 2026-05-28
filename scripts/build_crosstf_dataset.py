#!/usr/bin/env python3
"""build_crosstf_dataset.py — canonical cross-timeframe analytical layer (schema crosstf_v2).

Joins the canonical slim feature datasets (schema_version=2, from
scripts/extract_replay_features.py) into ONE 1-row-per-15M-bar analytical table:
15M base + 30M/1H/4H/1D context via a backward as-of join. Reads slims from the
external drive, writes a gzipped JSONL + .report.json there. RAW, manifests,
registry and slim sources are NEVER modified.

Canonical design (crosstf_v2, 2026-05-28):
  - base = 15M (prefix m15_); context = 30M (m30_), 1H (h1_), 4H (h4_), 1D (d1_).
  - TIME KEY = bar_close_time (epoch; = open of the last CLOSED bar). The ISO `ts`
    field is the replay cursor (replay_current_dt) and is offset/unreliable per TF —
    it is NEVER used for join/dedup/ordering, only preserved as *_replay_cursor_ts.
  - close_epoch(bar) = open_epoch of the NEXT bar of the same TF (real boundary,
    handles weekend/session gaps); nominal interval fallback for the last bar.
  - dedup keep-last per bar_close_time (replay-stall artifact); last capture
    (max bar_index) wins; provenance recorded.
  - as-of backward join: for each base bar (open-epoch asc), attach the latest
    context bar with ctx.close_epoch <= base.close_epoch. HARD FAIL on any leak.
  - column hygiene: drop do_not_use (bubble_event_price) and redundant identity
    (schema_version, raw_gz_path, registry_entry, symbol, timeframe, bar_close_time)
    from per-row output; summarize them in the report instead.
  - output .jsonl.gz; field_classes propagated in the report for downstream filtering.

Usage:
  python3 scripts/build_crosstf_dataset.py            # build + validate + write
  python3 scripts/build_crosstf_dataset.py --dry-run  # validate + print, no write
Read-only on slims; writes only under TradingData/slim_features/XAUUSD/cross_tf/.
"""
from __future__ import annotations
import argparse
import bisect
import gzip
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def repo_root() -> Path:
    env = os.environ.get("TVMCP_ROOT")
    if env and Path(env).expanduser().is_dir():
        return Path(env).expanduser().resolve()
    cur = Path(__file__).resolve().parent
    for d in (cur, *cur.parents):
        if (d / ".git").exists() or (d / "src" / "server.js").exists() \
           or ((d / "alert-bridge").is_dir() and (d / "my-strategy").is_dir()):
            return d
    raise RuntimeError("TVMCP repo root not found; set TVMCP_ROOT")


REGISTRY = repo_root() / "docs" / "data" / "dataset_registry.json"

BASE_TF = "15M"
CONTEXT_TFS = ["30M", "1H", "4H", "1D"]
ALL_TFS = [BASE_TF] + CONTEXT_TFS

TF_DIR = {"15M": "15M", "30M": "30M", "1H": "1H", "4H": "4H", "1D": "1D"}
TF_FILE = {"15M": "15m", "30M": "30m", "1H": "1h", "4H": "4h", "1D": "1d"}
PREFIX = {"15M": "m15", "30M": "m30", "1H": "h1", "4H": "h4", "1D": "d1"}
NOMINAL_INTERVAL_S = {"15M": 900, "30M": 1800, "1H": 3600, "4H": 14400, "1D": 86400}
# soft staleness thresholds (close-to-close); over = weekend/session gap, not an error
STALE_THRESH_S = {"m30": 35 * 60, "h1": 70 * 60, "h4": 260 * 60, "d1": 26 * 3600}

# column hygiene: dropped from every per-row block (kept/summarized in report)
DROP_DO_NOT_USE = {"bubble_event_price"}
DROP_IDENTITY = {"schema_version", "raw_gz_path", "registry_entry", "symbol",
                 "timeframe", "bar_close_time"}
DROP_FIELDS = DROP_DO_NOT_USE | DROP_IDENTITY


def iso(epoch) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()


def load_tf(reg: dict, ext_parent: Path, tf: str):
    """Load + concatenate all active blocks for a TF. Returns (rows, registry_entries, raw_paths)."""
    slim_dir = ext_parent / "TradingData" / "slim_features" / "XAUUSD" / TF_DIR[tf]
    rows = []
    reg_entries = []
    raw_paths = set()
    blocks = sorted([e for e in reg["datasets"] if e["timeframe"] == tf and e["status"] == "active"],
                    key=lambda e: e["start_date"])
    for e in blocks:
        f = slim_dir / f"XAUUSD_{TF_FILE[tf]}_features_{e['start_date']}_to_{e['end_date']}.jsonl"
        if not f.is_file():
            raise SystemExit(f"ERROR: canonical slim missing: {f}")
        cnt = 0
        with f.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("raw_gz_path"):
                    raw_paths.add(r["raw_gz_path"])
                rows.append(r)
                cnt += 1
        reg_entries.append({"registry_entry": e.get("name") or f"XAUUSD_{tf}_{e['start_date']}",
                            "start_date": e["start_date"], "end_date": e["end_date"],
                            "rows_in_file": cnt})
    return rows, reg_entries, sorted(raw_paths)


def dedup_keep_last(rows: list):
    """Keep last capture per bar_close_time (max bar_index). Returns (deduped sorted asc,
    extra_dropped, null_bct_dropped). Adds _dup_collapsed/_dropped_bar_indexes."""
    null_dropped = 0
    valid = []
    for r in rows:
        if r.get("bar_close_time") is None:
            null_dropped += 1
        else:
            valid.append(r)
    rows_sorted = sorted(valid, key=lambda r: (int(r["bar_close_time"]), r.get("bar_index", 0)))
    by_bct = {}
    members = {}
    for r in rows_sorted:
        bct = int(r["bar_close_time"])
        members.setdefault(bct, []).append(r.get("bar_index"))
        by_bct[bct] = r  # last wins (sorted by bar_index asc)
    out = []
    extra_dropped = 0
    for bct in sorted(by_bct):
        r = dict(by_bct[bct])
        bidx = members[bct]
        r["_dup_collapsed"] = len(bidx)
        if len(bidx) > 1:
            kept = r.get("bar_index")
            r["_dropped_bar_indexes"] = [b for b in bidx if b != kept]
            extra_dropped += len(bidx) - 1
        else:
            r["_dropped_bar_indexes"] = []
        out.append(r)
    return out, extra_dropped, null_dropped


def add_close_epochs(deduped: list, tf: str):
    """close_epoch = next bar's open epoch; nominal fallback for the last bar."""
    n = len(deduped)
    for i, r in enumerate(deduped):
        oe = int(r["bar_close_time"])
        if i + 1 < n:
            r["_close_epoch"] = int(deduped[i + 1]["bar_close_time"])
        else:
            r["_close_epoch"] = oe + NOMINAL_INTERVAL_S[tf]


def asof(base: list, ctx: list, key: str):
    """For each base row (open-epoch asc), latest ctx row with ctx[key] <= base['_close_epoch']."""
    res = []
    j = 0
    n = len(ctx)
    last = None
    for b in base:
        bc = b["_close_epoch"]
        while j < n and ctx[j][key] <= bc:
            last = ctx[j]
            j += 1
        res.append(last)
    return res


def feat_cols(rec: dict, prefix: str) -> dict:
    """Prefix all feature keys; drop identity/do_not_use; ts -> <p>_replay_cursor_ts."""
    out = {}
    for k, v in rec.items():
        if k.startswith("_") or k in DROP_FIELDS:
            continue
        if k == "ts":
            out[f"{prefix}_replay_cursor_ts"] = v
            continue
        out[f"{prefix}_{k}"] = v
    return out


def context_cols(base_close_epoch: int, ctx, prefix: str) -> dict:
    if ctx is None:
        return {f"{prefix}_present": False, f"{prefix}_open_epoch": None,
                f"{prefix}_close_epoch": None, f"{prefix}_close_iso": None,
                f"{prefix}_staleness_s": None, f"{prefix}_dup_collapsed": None}
    cols = feat_cols(ctx, prefix)
    cols[f"{prefix}_present"] = True
    cols[f"{prefix}_open_epoch"] = int(ctx["bar_close_time"])
    cols[f"{prefix}_close_epoch"] = ctx["_close_epoch"]
    cols[f"{prefix}_close_iso"] = iso(ctx["_close_epoch"])
    cols[f"{prefix}_staleness_s"] = int(base_close_epoch - ctx["_close_epoch"])
    cols[f"{prefix}_dup_collapsed"] = ctx["_dup_collapsed"]
    return cols


def build_row(b: dict, matches: dict) -> dict:
    row = {"symbol": b.get("symbol")}
    row["bar_open_epoch"] = int(b["bar_close_time"])
    row["bar_close_epoch"] = b["_close_epoch"]
    row["bar_open_iso"] = iso(b["bar_close_time"])
    row["bar_close_iso"] = iso(b["_close_epoch"])
    m15 = feat_cols(b, "m15")
    m15["m15_dup_collapsed"] = b["_dup_collapsed"]
    m15["m15_dropped_bar_indexes"] = b["_dropped_bar_indexes"]
    row.update(m15)
    for tf in CONTEXT_TFS:
        p = PREFIX[tf]
        row.update(context_cols(b["_close_epoch"], matches[p], p))
    return row


def stale_stats(vals: list, threshold: int) -> dict:
    if not vals:
        return {}
    vals = sorted(vals)
    return {"median_s": vals[len(vals) // 2], "p95_s": vals[int(0.95 * (len(vals) - 1))],
            "max_s": vals[-1], "over_threshold": sum(1 for v in vals if v > threshold),
            "threshold_s": threshold}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Canonical cross-TF analytical dataset v2 (15M base + 30M/1H/4H/1D context)")
    ap.add_argument("--dry-run", action="store_true", help="validate + print, no write")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text())
    ext_parent = Path(os.path.dirname(reg["_meta"]["external_root"]))
    if not ext_parent.is_dir():
        print(f"ERROR: external drive not mounted: {ext_parent}", file=sys.stderr)
        return 1

    # ---- load + dedup + close epochs ----
    loaded = {}
    dedup_meta = {}
    provenance = {}
    for tf in ALL_TFS:
        raw, reg_entries, raw_paths = load_tf(reg, ext_parent, tf)
        deduped, extra_dropped, null_dropped = dedup_keep_last(raw)
        add_close_epochs(deduped, tf)
        loaded[tf] = deduped
        dedup_meta[tf] = {"raw_rows": len(raw), "unique_bars": len(deduped),
                          "extra_dropped": extra_dropped, "null_bar_close_time_dropped": null_dropped}
        provenance[tf] = {"registry_entries": reg_entries, "raw_paths": raw_paths}

    base = loaded[BASE_TF]
    n = len(base)
    matches = {PREFIX[tf]: asof(base, loaded[tf], "_close_epoch") for tf in CONTEXT_TFS}

    # ---- validations (computed from base + matches; no wide rows materialized) ----
    base_oe = [int(b["bar_close_time"]) for b in base]
    strictly_increasing = all(base_oe[i] < base_oe[i + 1] for i in range(n - 1))
    dup_open_epoch = n - len(set(base_oe))
    unique_base_bars = dedup_meta[BASE_TF]["unique_bars"]
    rows_match_base_dedup = (n == unique_base_bars)

    leaks = {}
    coverage = {}
    staleness = {}
    leak_demo_naive = {}
    for tf in CONTEXT_TFS:
        p = PREFIX[tf]
        mm = matches[p]
        leak = absent = 0
        stales = []
        for i in range(n):
            bc = base[i]["_close_epoch"]
            m = mm[i]
            if m is None:
                absent += 1
                continue
            if m["_close_epoch"] > bc:
                leak += 1
            stales.append(int(bc - m["_close_epoch"]))
        leaks[p] = leak
        coverage[p] = {"present": n - absent, "absent": absent,
                       "pct_present": round(100.0 * (n - absent) / n, 4) if n else 0.0}
        staleness[p] = stale_stats(stales, STALE_THRESH_S[p])

    # empirical demo: a NAIVE join on OPEN epoch (the v1-style ts/open mistake) would
    # attach context bars that have not yet closed -> count would-be leaks. close_epoch fixes it.
    for tf in CONTEXT_TFS:
        p = PREFIX[tf]
        ctx = loaded[tf]
        ctx_open = [int(c["bar_close_time"]) for c in ctx]
        would_leak = 0
        for b in base:
            bo = int(b["bar_close_time"])
            k = bisect.bisect_right(ctx_open, bo) - 1
            if k >= 0 and ctx[k]["_close_epoch"] > b["_close_epoch"]:
                would_leak += 1
        leak_demo_naive[p] = would_leak

    # spot-check: independent bisect as-of on close_epoch for 10 base rows
    spot = []
    spot_targets = sorted(set(int(i * (n - 1) / 9) for i in range(10))) if n >= 10 else list(range(n))
    for tf in CONTEXT_TFS:
        loaded[tf + "_ce"] = [c["_close_epoch"] for c in loaded[tf]]
    for idx in spot_targets:
        bc = base[idx]["_close_epoch"]
        rec = {"i": idx, "bar_close_iso": iso(bc)}
        ok = True
        for tf in CONTEXT_TFS:
            p = PREFIX[tf]
            ce = loaded[tf + "_ce"]
            q = bisect.bisect_right(ce, bc) - 1
            exp = ce[q] if q >= 0 else None
            got = matches[p][idx]["_close_epoch"] if matches[p][idx] else None
            rec[f"{p}_ok"] = (exp == got)
            ok = ok and (exp == got)
        rec["all_ok"] = ok
        spot.append(rec)
    spot_pass = all(s["all_ok"] for s in spot)

    no_future_leak = all(v == 0 for v in leaks.values())

    # ---- field classes (verbatim from a source report; identical across TFs) ----
    src_rep = sorted((ext_parent / "TradingData" / "slim_features" / "XAUUSD" / TF_DIR[BASE_TF]).glob("*.report.json"))
    source_field_classes = {}
    if src_rep:
        source_field_classes = json.loads(src_rep[0].read_text()).get("field_classes", {})

    base_range = {"open_min_epoch": base_oe[0] if base_oe else None,
                  "open_max_epoch": base_oe[-1] if base_oe else None,
                  "open_min_iso": iso(base_oe[0]) if base_oe else None,
                  "open_max_iso": iso(base_oe[-1]) if base_oe else None,
                  "close_max_iso": iso(base[-1]["_close_epoch"]) if base else None}

    warnings = []
    if not no_future_leak:
        warnings.append(f"FUTURE LEAK (close_epoch join): {leaks}")
    if not rows_match_base_dedup:
        warnings.append(f"rows({n}) != base dedup unique_bars({unique_base_bars})")
    if not strictly_increasing or dup_open_epoch:
        warnings.append(f"base not clean: strictly_increasing={strictly_increasing} dup_open_epoch={dup_open_epoch}")
    if not spot_pass:
        warnings.append("spot-check FAILED")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "crosstf_v2",
        "strategy_layer": "canonical_cross_tf",
        "base_tf": BASE_TF, "context_tfs": CONTEXT_TFS,
        "prefixes": PREFIX,
        "join": {"time_key": "bar_close_time (epoch; open of last closed bar)",
                 "close_epoch_method": "next bar open epoch; nominal interval fallback for last bar",
                 "inequality": "ctx_close_epoch <= base_close_epoch",
                 "ts_field": "NOT used for join/dedup/order; preserved as <prefix>_replay_cursor_ts (diagnostic)"},
        "base_range": base_range,
        "rows": n,
        "dedup": dedup_meta,
        "validations": {
            "rows_match_base_dedup": rows_match_base_dedup,
            "base_epoch_strictly_increasing": strictly_increasing,
            "duplicate_open_epoch": dup_open_epoch,
            "no_future_leak": no_future_leak,
            "future_leak_counts": leaks,
            "leak_demo_naive_open_join": leak_demo_naive,
            "spot_check_all_pass": spot_pass,
        },
        "context_coverage": coverage,
        "staleness": staleness,
        "spot_check": {"all_pass": spot_pass, "targets": spot_targets, "details": spot},
        "provenance": provenance,
        "dropped_fields": {"do_not_use": sorted(DROP_DO_NOT_USE),
                           "identity_redundant": sorted(DROP_IDENTITY)},
        "source_field_classes": source_field_classes,
        "field_class_note": "class of m15_<f> / <prefix>_<f> equals class of <f> in source_field_classes "
                            "(same schema_version=2 extractor for every TF); identity_redundant + do_not_use dropped.",
        "warnings": warnings,
    }

    # ---- console summary ----
    print(f"rows={n} | base open {base_range['open_min_iso']} -> {base_range['open_max_iso']}")
    print(f"rows_match_base_dedup={rows_match_base_dedup} | strictly_increasing={strictly_increasing} | dup_open_epoch={dup_open_epoch}")
    print(f"NO FUTURE LEAK (close_epoch): {no_future_leak} | leak_counts={leaks}")
    print(f"leak_demo_naive_open_join (would-be leaks if joined on open epoch): {leak_demo_naive}")
    print(f"coverage: " + " ".join(f"{p}={coverage[p]['pct_present']}%" for p in (PREFIX[t] for t in CONTEXT_TFS)))
    print(f"staleness: " + " ".join(f"{p}(max={staleness[p].get('max_s')}s,over={staleness[p].get('over_threshold')})" for p in (PREFIX[t] for t in CONTEXT_TFS)))
    print(f"dedup extra_dropped: " + " ".join(f"{tf}={dedup_meta[tf]['extra_dropped']}" for tf in ALL_TFS))
    print(f"spot_check all_pass={spot_pass} | warnings={warnings}")

    # HARD FAIL before writing
    if not no_future_leak:
        print("ABORT: future leak detected — refusing to write.", file=sys.stderr)
        return 2
    if not (rows_match_base_dedup and strictly_increasing and dup_open_epoch == 0 and spot_pass):
        print("ABORT: base integrity / spot-check failed — refusing to write.", file=sys.stderr)
        return 2

    if args.dry_run:
        print("[dry-run] not writing")
        return 0

    # ---- write (streamed gz) ----
    out_dir = ext_parent / "TradingData" / "slim_features" / "XAUUSD" / "cross_tf"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"XAUUSD_crosstf_15m_base_{base_range['open_min_iso'][:10]}_to_{base_range['open_max_iso'][:10]}"
    gz_path = out_dir / f"{base_name}.jsonl.gz"
    report_path = out_dir / f"{base_name}.report.json"
    written = 0
    with gzip.open(gz_path, "wt", encoding="utf-8") as f:
        for i in range(n):
            row = build_row(base[i], {PREFIX[tf]: matches[PREFIX[tf]][i] for tf in CONTEXT_TFS})
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1
    size = gz_path.stat().st_size
    report["output"] = {"jsonl_gz_path": str(gz_path), "size_bytes": size,
                        "report_path": str(report_path), "rows_written": written}

    # ---- reopen + validate written file (gate #10) ----
    seen = 0
    reopen_leak = 0
    prev_oe = None
    reopen_mono = True
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            seen += 1
            oe = r["bar_open_epoch"]
            if prev_oe is not None and oe <= prev_oe:
                reopen_mono = False
            prev_oe = oe
            for p in (PREFIX[t] for t in CONTEXT_TFS):
                if r.get(f"{p}_present") and r[f"{p}_close_epoch"] > r["bar_close_epoch"]:
                    reopen_leak += 1
    reopen_ok = (seen == written == n) and reopen_leak == 0 and reopen_mono
    report["output"]["reopen_validation"] = {"rows_read": seen, "leak": reopen_leak,
                                              "monotonic": reopen_mono, "ok": reopen_ok}
    if not reopen_ok:
        report["warnings"].append(f"REOPEN VALIDATION FAILED: rows={seen} leak={reopen_leak} mono={reopen_mono}")

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {gz_path} ({size} bytes, {written} rows)")
    print(f"reopen_validation ok={reopen_ok} (rows_read={seen} leak={reopen_leak} mono={reopen_mono})")
    print(f"wrote {report_path}")
    return 0 if reopen_ok else 2


if __name__ == "__main__":
    sys.exit(main())
