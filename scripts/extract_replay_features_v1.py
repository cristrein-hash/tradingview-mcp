#!/usr/bin/env python3
"""extract_replay_features_v1.py — slim feature extractor (v1) for ONE XAU 15M block.

Reads docs/data/dataset_registry.json, locates the external RAW .jsonl.gz for the
target block, streams it bar-by-bar, and writes a SLIM 1-row-per-bar JSONL plus a
.report.json — both on the external drive (slim is derived/regenerable, NOT versioned).

The RAW is NEVER modified; this is read-only on the RAW and writes only under
TradingData/slim_features/. Schema v1 approved 2026-05-26. Decisions baked in:
  - decision bar = ohlcv[-2] (last CLOSED bar); ohlcv[-1] is forming -> forming_close only.
  - Custom OB demand/supply via the box `text` field ("DEMAND"/"SUPPLY").
  - smc_last_structure_event = SMC label with max x among the structure vocabulary.
  - numeric strings normalized for unicode minus (U+2212) and thousands separators.
  - missing/unparseable -> null (+ parse_errors counted); never faked.

Usage:
  python3 scripts/extract_replay_features_v1.py            # extract + validate + write
  python3 scripts/extract_replay_features_v1.py --dry-run  # process, print report, don't write
Default target: XAU 15M 2025-11-25 -> 2026-02-25 (override with --start-date).
"""
from __future__ import annotations
import argparse
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
SMC_STRUCT_VOCAB = {"CHoCH", "BOS", "EQH", "EQL", "Strong High", "Strong Low"}


def norm_num(v, pe: list | None = None, label: str = ""):
    """Normalize a possibly-string number: unicode minus, thousands sep. None on missing;
    appends to `pe` only when a NON-EMPTY value fails to parse."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("−", "-").replace(",", "").strip()
    if s == "" or s.upper() in ("N/A", "NULL", "NONE"):
        return None
    try:
        return float(s)
    except ValueError:
        if pe is not None:
            pe.append(f"{label}={v!r}")
        return None


def flag(f):
    if f is None:
        return None
    return 1 if f != 0 else 0


def _zone_dist(close, high, low):
    if close is None or high is None or low is None:
        return None
    if low <= close <= high:
        return 0.0
    return round(min(abs(close - high), abs(close - low)), 5)


def extract_bar(rec: dict, prov: dict) -> dict:
    pe: list = []
    av = rec.get("_feature_availability") or {}

    # --- OHLCV: last CLOSED bar = ohlcv[-2]; forming = ohlcv[-1] ---
    obars = sorted((rec.get("ohlcv") or []), key=lambda b: b.get("time", 0))
    closed = obars[-2] if len(obars) >= 2 else None
    forming = obars[-1] if obars else None
    close = closed.get("close") if closed else None

    # --- study_values lookup ---
    sv = {st.get("name"): (st.get("values") or {}) for st in (rec.get("study_values") or []) if isinstance(st, dict)}
    rsi_v = sv.get("Relative Strength Index", {})
    nas_v = sv.get("NAS TOP BOTTOM DETECTOR", {})

    rsi_div_raw = rsi_v.get("Regular Bearish")  # SEMANTICS UNCERTAIN (see report)

    # --- pine_boxes: Custom OB + SMC ---
    boxes = rec.get("pine_boxes") or []
    cob = next((s for s in boxes if "OB Detector" in (s.get("name") or "")), None)
    smc_box = next((s for s in boxes if "LuxAlgo" in (s.get("name") or "")), None)

    def nearest(all_boxes, predicate=lambda b: True):
        best = None
        for b in all_boxes:
            if not predicate(b):
                continue
            d = _zone_dist(close, b.get("high"), b.get("low"))
            if d is None:
                continue
            if best is None or d < best[0]:
                best = (d, b)
        return best  # (dist, box) or None

    cob_boxes = (cob.get("all_boxes") or []) if cob else []
    cob_inside = any(_zone_dist(close, b.get("high"), b.get("low")) == 0.0 for b in cob_boxes) if close is not None else None
    nd = nearest(cob_boxes, lambda b: (b.get("text") or "").upper() == "DEMAND")
    ns = nearest(cob_boxes, lambda b: (b.get("text") or "").upper() == "SUPPLY")
    nz = nearest(cob_boxes)

    smc_boxes = (smc_box.get("all_boxes") or []) if smc_box else []
    smc_nz = nearest(smc_boxes)

    # --- pine_labels: SMC structure ---
    labels_studies = rec.get("pine_labels") or []
    smc_lbl = next((s for s in labels_studies if "LuxAlgo" in (s.get("name") or "")), None)
    smc_labels = (smc_lbl.get("labels") or []) if smc_lbl else []
    struct = [l for l in smc_labels if l.get("text") in SMC_STRUCT_VOCAB]
    last_struct = max(struct, key=lambda l: l.get("x", -1)) if struct else None
    smc_texts = {l.get("text") for l in smc_labels}
    labels_capped = any((s.get("showing") or 0) < (s.get("total_labels") or 0) for s in labels_studies)

    # --- pine_shapes_bubbles: activation at the closed bar's time ---
    bar_close_time = closed.get("time") if closed else None
    acts = []
    for st in (rec.get("pine_shapes_bubbles") or []):
        acts += st.get("activations") or []
    match = [a for a in acts if a.get("time") == bar_close_time] if bar_close_time is not None else []
    bubble_plots = sorted({k for a in match for k in (a.get("shapes") or {}).keys()})

    row = {
        # provenance
        "symbol": rec.get("symbol"),
        "timeframe": rec.get("timeframe"),
        "ts": rec.get("replay_current_dt"),
        "bar_index": rec.get("bar_index"),
        "bar_close_time": bar_close_time,
        "raw_gz_path": prov["raw_gz_path"],
        "source_start_date": prov["source_start_date"],
        "source_end_date": prov["source_end_date"],
        # ohlcv (last closed)
        "open": closed.get("open") if closed else None,
        "high": closed.get("high") if closed else None,
        "low": closed.get("low") if closed else None,
        "close": close,
        "volume": closed.get("volume") if closed else None,
        "forming_close": forming.get("close") if forming else None,
        # rsi
        "rsi": norm_num(rsi_v.get("RSI"), pe, "RSI"),
        "rsi_ma": norm_num(rsi_v.get("RSI-based MA"), pe, "RSI-based MA"),
        "rsi_div_bearish": norm_num(rsi_div_raw, pe, "Regular Bearish"),
        "rsi_div_bearish_present": rsi_div_raw is not None,
        # nas
        "nas_long": flag(norm_num(nas_v.get("NAS_LONG_SIGNAL"), pe, "NAS_LONG_SIGNAL")),
        "nas_short": flag(norm_num(nas_v.get("NAS_SHORT_SIGNAL"), pe, "NAS_SHORT_SIGNAL")),
        "nas_bottom": flag(norm_num(nas_v.get("NAS_BOTTOM_SIGNAL"), pe, "NAS_BOTTOM_SIGNAL")),
        "nas_top": flag(norm_num(nas_v.get("NAS_TOP_SIGNAL"), pe, "NAS_TOP_SIGNAL")),
        "nas_dist_ema_atr": norm_num(nas_v.get("NAS_DISTANCE_FROM_EMA_ATR"), pe, "NAS_DISTANCE_FROM_EMA_ATR"),
        "nas_rsi": norm_num(nas_v.get("NAS_RSI"), pe, "NAS_RSI"),
        # bubbles
        "bubble_active": bool(match),
        "bubble_plots": bubble_plots,
        "poc_flag": "plot_12" in bubble_plots,
        # custom ob
        "custom_ob_n_zones": (cob.get("total_boxes") if cob else 0),
        "custom_ob_inside_zone": cob_inside,
        "custom_ob_nearest_demand_dist": (nd[0] if nd else None),
        "custom_ob_nearest_supply_dist": (ns[0] if ns else None),
        "custom_ob_nearest_zone_high": (nz[1].get("high") if nz else None),
        "custom_ob_nearest_zone_low": (nz[1].get("low") if nz else None),
        # smc
        "smc_n_boxes": (smc_box.get("total_boxes") if smc_box else 0),
        "smc_nearest_zone_dist": (smc_nz[0] if smc_nz else None),
        "smc_nearest_zone_high": (smc_nz[1].get("high") if smc_nz else None),
        "smc_nearest_zone_low": (smc_nz[1].get("low") if smc_nz else None),
        "smc_last_structure_event": (last_struct.get("text") if last_struct else None),
        "smc_last_structure_price": (norm_num(last_struct.get("price"), pe, "smc_struct_price") if last_struct else None),
        "smc_has_bos": "BOS" in smc_texts,
        "smc_has_choch": "CHoCH" in smc_texts,
        "smc_has_eqh": "EQH" in smc_texts,
        "smc_has_eql": "EQL" in smc_texts,
        # quality
        "feature_quality": {
            "boxes_empty": not av.get("pine_boxes", True),
            "labels_capped": bool(labels_capped),
            "parse_errors": len(pe),
            "sources_missing": [k for k, v in av.items() if not v],
            "ohlcv_short": len(obars) < 2,
        },
    }
    return row, pe


def find_block(reg: dict, tf: str, start_date: str) -> dict:
    for e in reg["datasets"]:
        if e["timeframe"] == tf and e["start_date"] == start_date and e["status"] == "active":
            return e
    raise SystemExit(f"ERROR: block not found in registry: {tf} {start_date} active")


def main() -> int:
    ap = argparse.ArgumentParser(description="Slim feature extractor v1 (single 15M block)")
    ap.add_argument("--timeframe", default="15M")
    ap.add_argument("--start-date", default="2025-11-25")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text())
    ext_parent = Path(os.path.dirname(reg["_meta"]["external_root"]))
    if not ext_parent.is_dir():
        print(f"ERROR: external drive not mounted: {ext_parent}", file=sys.stderr)
        return 1

    entry = find_block(reg, args.timeframe, args.start_date)
    gz = ext_parent / entry["raw_gz_path"]
    if not gz.is_file():
        print(f"ERROR: RAW .gz not found: {gz}", file=sys.stderr)
        return 1

    prov = {
        "raw_gz_path": entry["raw_gz_path"],
        "source_start_date": entry["start_date"],
        "source_end_date": entry["end_date"],
    }
    out_dir = ext_parent / reg["_meta"]["external_root"].split(os.sep)[-1] / "slim_features" / "XAUUSD" / args.timeframe
    sym = "XAUUSD"
    base = f"{sym}_{args.timeframe.lower()}_features_{entry['start_date']}_to_{entry['end_date']}"
    slim_path = out_dir / f"{base}.jsonl"
    report_path = out_dir / f"{base}.report.json"

    rows = []
    total_pe = 0
    pe_samples: list = []
    error_bars = 0
    print(f"reading {gz}")
    with gzip.open(gz, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                error_bars += 1
                continue
            if rec.get("_error"):
                error_bars += 1
                continue
            row, pe = extract_bar(rec, prov)
            rows.append(row)
            total_pe += len(pe)
            for p in pe:
                if len(pe_samples) < 20:
                    pe_samples.append({"bar_index": row["bar_index"], "field": p})

    # ---------------- duplicate-ts marking (RAW replay-stall artifact, kept 1:1) ----------------
    ts_counts = {}
    for r in rows:
        ts_counts[r["ts"]] = ts_counts.get(r["ts"], 0) + 1
    dup_detail = {}
    for r in rows:
        is_dup = ts_counts.get(r["ts"], 0) > 1
        r["feature_quality"]["ts_duplicate"] = is_dup
        if is_dup:
            dup_detail.setdefault(r["ts"], []).append(r["bar_index"])

    # ---------------- validations ----------------
    n = len(rows)
    expected = entry["bars"]
    ts_list = [r["ts"] for r in rows]
    ts_sorted = all(ts_list[i] <= ts_list[i + 1] for i in range(len(ts_list) - 1))
    dup_ts = len(ts_list) - len(set(ts_list))
    ohlcv_violations = 0
    rsi_violations = 0
    neg_dist = 0
    for r in rows:
        o, h, l, c = r["open"], r["high"], r["low"], r["close"]
        if None not in (o, h, l, c):
            if not (l <= o <= h and l <= c <= h and l <= h):
                ohlcv_violations += 1
        if r["rsi"] is not None and not (0 <= r["rsi"] <= 100):
            rsi_violations += 1
        for k in ("custom_ob_nearest_demand_dist", "custom_ob_nearest_supply_dist", "smc_nearest_zone_dist"):
            if r[k] is not None and r[k] < 0:
                neg_dist += 1

    feature_keys = [k for k in rows[0].keys() if k not in ("feature_quality",)] if rows else []
    null_rate = {}
    for k in feature_keys:
        nonnull = sum(1 for r in rows if r[k] not in (None, [], ""))
        null_rate[k] = round(100 * (1 - nonnull / n), 2) if n else None

    # ---------------- spot-check 10 lines vs RAW (independent re-read) ----------------
    targets = sorted(set(int(i * (n - 1) / 9) for i in range(10))) if n >= 10 else list(range(n))
    slim_by_idx = {r["bar_index"]: r for r in rows}
    spot = []
    with gzip.open(gz, "rt", encoding="utf-8") as f:
        idx = -1
        want = set(targets)
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("_error"):
                continue
            idx += 1
            if idx not in want:
                continue
            obars = sorted((rec.get("ohlcv") or []), key=lambda b: b.get("time", 0))
            raw_close = obars[-2].get("close") if len(obars) >= 2 else None
            sv = {st.get("name"): (st.get("values") or {}) for st in (rec.get("study_values") or []) if isinstance(st, dict)}
            raw_rsi = norm_num(sv.get("Relative Strength Index", {}).get("RSI"))
            bi = rec.get("bar_index")
            sr = slim_by_idx.get(bi, {})
            spot.append({
                "bar_index": bi,
                "close_match": raw_close == sr.get("close"),
                "rsi_match": raw_rsi == sr.get("rsi"),
                "ts_match": rec.get("replay_current_dt") == sr.get("ts"),
            })
    spot_pass = all(s["close_match"] and s["rsi_match"] and s["ts_match"] for s in spot)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "v1",
        "source": {
            "raw_gz_path": entry["raw_gz_path"],
            "registry_bars": expected,
            "raw_gz_size_bytes": entry.get("gz_size_bytes"),
            "raw_original_size_bytes": entry.get("original_size_bytes"),
        },
        "rows_extracted": n,
        "expected_bars": expected,
        "rows_match_registry": n == expected,
        "error_bars_skipped": error_bars,
        "ts_range": {"min": ts_list[0] if ts_list else None, "max": ts_list[-1] if ts_list else None},
        "ts_monotonic": ts_sorted,
        "duplicate_ts": dup_ts,
        "duplicate_ts_detail": dup_detail,
        "duplicate_ts_note": "RAW artifact: replay_step did not advance the clock at these bars (identical closed_time/close); rows kept 1:1 with RAW (provenance), marked feature_quality.ts_duplicate=true. Dedup-by-ts (keep last) belongs in the analysis/join step, NOT the extractor.",
        "ohlcv_violations": ohlcv_violations,
        "rsi_out_of_range": rsi_violations,
        "negative_distances": neg_dist,
        "parse_errors_total": total_pe,
        "parse_error_samples": pe_samples,
        "null_rate_pct_by_feature": null_rate,
        "spot_check": {"targets": targets, "all_pass": spot_pass, "details": spot},
        "uncertainty_notes": [
            "rsi_div_bearish: semantics UNCERTAIN (value of 'Regular Bearish' plot; not a confirmed flag). Captured raw + presence only.",
            "smc_has_*: window-level (labels showing up to 500, often capped) -> low per-bar discriminative value; prefer smc_last_structure_event.",
            "distances are absolute price (no ATR/% normalization in v1).",
        ],
        "warnings": [],
    }
    if not report["rows_match_registry"]:
        report["warnings"].append(f"row count {n} != registry bars {expected}")
    if not ts_sorted:
        report["warnings"].append("timestamps not monotonic")
    if dup_ts:
        report["warnings"].append(f"{dup_ts} duplicate ts (RAW replay-stall artifact; rows kept 1:1 + marked; see duplicate_ts_detail)")
    if ohlcv_violations or rsi_violations or neg_dist:
        report["warnings"].append("value-range violations present")
    if not spot_pass:
        report["warnings"].append("spot-check FAILED")

    print(f"rows={n} expected={expected} match={report['rows_match_registry']} | ts_monotonic={ts_sorted} dup={dup_ts}")
    print(f"ohlcv_viol={ohlcv_violations} rsi_oor={rsi_violations} neg_dist={neg_dist} parse_errors={total_pe}")
    print(f"spot_check all_pass={spot_pass} | warnings={report['warnings']}")

    if args.dry_run:
        print("[dry-run] not writing slim/report")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    with slim_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    slim_size = slim_path.stat().st_size
    report["slim_path"] = str(slim_path)
    report["slim_size_bytes"] = slim_size
    raw_orig = entry.get("original_size_bytes") or 0
    report["size_vs_raw"] = {
        "slim_bytes": slim_size,
        "raw_original_bytes": raw_orig,
        "slim_pct_of_raw": round(100 * slim_size / raw_orig, 4) if raw_orig else None,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote slim:   {slim_path} ({slim_size} bytes)")
    print(f"wrote report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
