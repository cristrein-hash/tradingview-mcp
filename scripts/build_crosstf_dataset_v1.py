#!/usr/bin/env python3
"""build_crosstf_dataset_v1.py — cross-timeframe analytical layer (v1).

Joins the slim feature datasets (from extract_replay_features_v1) into ONE
1-row-per-15M-bar analytical table: 15M base + 30M/1H context via backward as-of
join. Reads slims from the external drive, writes a JSONL + .report.json there.
RAW and slim sources are NEVER modified.

Approved design (2026-05-26):
  - base = 15M (prefix m15_); context = 30M (m30_), 1H (h1_). Keys ts/symbol unprefixed.
  - dedup keep-last per ts per TF (replay-stall artifact); slim untouched, provenance recorded.
  - as-of backward join: for each base ts, attach latest context row with ctx.ts <= base.ts
    (no future leak; ts = end-of-bar, lexicographic ISO == chronological).
  - JSONL first (Parquet later). v1 covers only where 15M exists (2025-05-25 -> 2026-05-25).
  - NOT including 4H/1D yet; schema allows appending more context TFs later.

Usage:
  python3 scripts/build_crosstf_dataset_v1.py            # build + validate + write
  python3 scripts/build_crosstf_dataset_v1.py --dry-run  # validate + print, no write
Read-only on slims; writes only under TradingData/slim_features/XAUUSD/cross_tf/.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime
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
TF_DIR = {"15M": "15M", "30M": "30M", "1H": "1H"}
TF_FILE = {"15M": "15m", "30M": "30m", "1H": "1h"}  # matches extractor's args.timeframe.lower()
STALE_THRESH_S = {"m30": 35 * 60, "h1": 70 * 60}


def epoch(ts: str) -> float:
    return datetime.fromisoformat(ts).timestamp()


def load_tf(reg: dict, ext_parent: Path, tf: str) -> list:
    slim_dir = ext_parent / "TradingData" / "slim_features" / "XAUUSD" / TF_DIR[tf]
    rows = []
    blocks = sorted([e for e in reg["datasets"] if e["timeframe"] == tf and e["status"] == "active"],
                    key=lambda e: e["start_date"])
    for e in blocks:
        f = slim_dir / f"XAUUSD_{TF_FILE[tf]}_features_{e['start_date']}_to_{e['end_date']}.jsonl"
        if not f.is_file():
            raise SystemExit(f"ERROR: slim missing: {f}")
        with f.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def dedup_keep_last(rows: list):
    """Keep the last capture per ts (max bar_index). Annotate dup_collapsed/dropped."""
    rows_sorted = sorted(rows, key=lambda r: (r["ts"], r["bar_index"]))
    by_ts = {}
    members = {}
    for r in rows_sorted:
        members.setdefault(r["ts"], []).append(r["bar_index"])
        by_ts[r["ts"]] = r  # last wins (sorted by bar_index asc)
    out = []
    extra_dropped = 0
    for ts in sorted(by_ts):
        r = dict(by_ts[ts])
        bidx = members[ts]
        if len(bidx) > 1:
            kept = r["bar_index"]
            r["_dup_collapsed"] = len(bidx)
            r["_dropped_bar_indexes"] = [b for b in bidx if b != kept]
            extra_dropped += len(bidx) - 1
        else:
            r["_dup_collapsed"] = 1
            r["_dropped_bar_indexes"] = []
        out.append(r)
    return out, extra_dropped


def asof(base_rows: list, ctx_rows: list) -> list:
    """For each base row (ts asc), return latest ctx row with ctx.ts <= base.ts (or None)."""
    res = []
    j = 0
    n = len(ctx_rows)
    last = None
    for b in base_rows:
        while j < n and ctx_rows[j]["ts"] <= b["ts"]:
            last = ctx_rows[j]
            j += 1
        res.append(last)
    return res


def prefixed(row: dict, prefix: str) -> dict:
    """Prefix all keys except none (symbol/ts handled at top level by caller)."""
    out = {}
    for k, v in row.items():
        out[f"{prefix}{k}"] = v
    return out


def build_context_cols(base_ts: str, ctx, prefix: str) -> dict:
    if ctx is None:
        return {f"{prefix}_present": False, f"{prefix}_ts": None, f"{prefix}_staleness_s": None}
    cols = {f"{prefix}_{k}": v for k, v in ctx.items()}
    cols[f"{prefix}_present"] = True
    cols[f"{prefix}_ts"] = ctx["ts"]
    cols[f"{prefix}_staleness_s"] = int(epoch(base_ts) - epoch(ctx["ts"]))
    return cols


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-TF analytical dataset v1 (15M base + 30M/1H context)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text())
    ext_parent = Path(os.path.dirname(reg["_meta"]["external_root"]))
    if not ext_parent.is_dir():
        print(f"ERROR: external drive not mounted: {ext_parent}", file=sys.stderr)
        return 1

    raw15 = load_tf(reg, ext_parent, "15M")
    raw30 = load_tf(reg, ext_parent, "30M")
    raw1h = load_tf(reg, ext_parent, "1H")

    base, drop15 = dedup_keep_last(raw15)
    ctx30, drop30 = dedup_keep_last(raw30)
    ctx1h, drop1h = dedup_keep_last(raw1h)

    m30_match = asof(base, ctx30)
    h1_match = asof(base, ctx1h)

    out_rows = []
    for i, b in enumerate(base):
        row = {"symbol": b.get("symbol"), "ts": b["ts"]}
        # base m15_ (prefix everything from the base slim row)
        m15 = {f"m15_{k}": v for k, v in b.items() if k not in ("_dup_collapsed", "_dropped_bar_indexes")}
        m15["m15_dup_collapsed"] = b["_dup_collapsed"]
        m15["m15_dropped_bar_indexes"] = b["_dropped_bar_indexes"]
        row.update(m15)
        # context (strip the internal dedup keys before prefixing, keep them as *_dup_collapsed)
        def clean(c):
            if c is None:
                return None
            d = {k: v for k, v in c.items() if k not in ("_dup_collapsed", "_dropped_bar_indexes")}
            d["dup_collapsed"] = c["_dup_collapsed"]
            return d
        row.update(build_context_cols(b["ts"], clean(m30_match[i]), "m30"))
        row.update(build_context_cols(b["ts"], clean(h1_match[i]), "h1"))
        out_rows.append(row)

    # ---------------- validations ----------------
    n = len(out_rows)
    ts_list = [r["ts"] for r in out_rows]
    ts_sorted = all(ts_list[i] <= ts_list[i + 1] for i in range(n - 1))
    dup_ts = n - len(set(ts_list))
    # no-future-leak
    leak_m30 = sum(1 for r in out_rows if r["m30_present"] and r["m30_ts"] > r["ts"])
    leak_h1 = sum(1 for r in out_rows if r["h1_present"] and r["h1_ts"] > r["ts"])
    # context coverage
    m30_absent = sum(1 for r in out_rows if not r["m30_present"])
    h1_absent = sum(1 for r in out_rows if not r["h1_present"])
    # staleness
    def stale_stats(prefix):
        vals = [r[f"{prefix}_staleness_s"] for r in out_rows if r[f"{prefix}_present"]]
        if not vals:
            return {}
        vals.sort()
        over = sum(1 for v in vals if v > STALE_THRESH_S[prefix])
        return {"max_s": vals[-1], "p95_s": vals[int(0.95 * (len(vals) - 1))], "median_s": vals[len(vals) // 2],
                "over_threshold": over, "threshold_s": STALE_THRESH_S[prefix]}

    # spot-check: independent as-of for 10 base ts
    import bisect
    ctx30_ts = [c["ts"] for c in ctx30]
    ctx1h_ts = [c["ts"] for c in ctx1h]
    targets = sorted(set(int(i * (n - 1) / 9) for i in range(10))) if n >= 10 else list(range(n))
    spot = []
    for idx in targets:
        r = out_rows[idx]
        bt = r["ts"]
        p = bisect.bisect_right(ctx30_ts, bt) - 1
        exp30 = ctx30_ts[p] if p >= 0 else None
        q = bisect.bisect_right(ctx1h_ts, bt) - 1
        exp1h = ctx1h_ts[q] if q >= 0 else None
        spot.append({"i": idx, "ts": bt,
                     "m30_ok": exp30 == r["m30_ts"], "h1_ok": exp1h == r["h1_ts"]})
    spot_pass = all(s["m30_ok"] and s["h1_ok"] for s in spot)

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": "crosstf_v1",
        "base_tf": "15M", "context_tfs": ["30M", "1H"],
        "base_range": {"min": ts_list[0] if ts_list else None, "max": ts_list[-1] if ts_list else None},
        "rows": n,
        "dedup": {"m15_extra_dropped": drop15, "m30_extra_dropped": drop30, "h1_extra_dropped": drop1h,
                  "policy": "keep-last per ts"},
        "ts_monotonic": ts_sorted, "duplicate_ts": dup_ts,
        "future_leak": {"m30": leak_m30, "h1": leak_h1},
        "context_absent": {"m30": m30_absent, "h1": h1_absent},
        "staleness": {"m30": stale_stats("m30"), "h1": stale_stats("h1")},
        "spot_check": {"all_pass": spot_pass, "targets": targets, "details": spot},
        "notes": [
            "Covers only where 15M exists (2025-05-25 -> 2026-05-25); 30M/1H extra year (2024-05->2025-05) unused by this 15M-keyed join.",
            "4H/1D NOT included (pending collection); schema allows appending m4h_/d1_ later.",
            "staleness > threshold usually = weekend/session gap (soft, not an error).",
        ],
        "warnings": [],
    }
    if leak_m30 or leak_h1:
        report["warnings"].append(f"FUTURE LEAK: m30={leak_m30} h1={leak_h1}")
    if not ts_sorted or dup_ts:
        report["warnings"].append(f"base not clean: monotonic={ts_sorted} dup_ts={dup_ts}")
    if not spot_pass:
        report["warnings"].append("spot-check FAILED")

    print(f"rows={n} | base {report['base_range']['min']} -> {report['base_range']['max']}")
    print(f"dedup dropped: m15={drop15} m30={drop30} h1={drop1h}")
    print(f"future_leak: m30={leak_m30} h1={leak_h1} | ctx_absent: m30={m30_absent} h1={h1_absent}")
    print(f"staleness m30={report['staleness']['m30']} h1={report['staleness']['h1']}")
    print(f"spot_check all_pass={spot_pass} | warnings={report['warnings']}")

    if args.dry_run:
        print("[dry-run] not writing")
        return 0

    out_dir = ext_parent / "TradingData" / "slim_features" / "XAUUSD" / "cross_tf"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"XAUUSD_crosstf_15m_base_{ts_list[0][:10]}_to_{ts_list[-1][:10]}"
    slim_path = out_dir / f"{base_name}.jsonl"
    report_path = out_dir / f"{base_name}.report.json"
    with slim_path.open("w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    report["slim_path"] = str(slim_path)
    report["slim_size_bytes"] = slim_path.stat().st_size
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {slim_path} ({report['slim_size_bytes']} bytes)")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
