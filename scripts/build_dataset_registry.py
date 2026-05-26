#!/usr/bin/env python3
"""build_dataset_registry.py — generate docs/data/dataset_registry.json from the
external cold-storage manifests + RAW gzipped replay datasets.

The registry is a CATALOG / rollup for the extractor/analyzer. The per-file
manifests under TradingData/manifests/ (and superseded/) remain the PRIMARY source
of integrity; this script reads them, confirms each .jsonl.gz exists, validates
`gzip -t` and sha256(gz) against the manifest, and records any divergence as a
WARNING (never hidden). It NEVER modifies anything on the external drive.

Scope: TradingData/raw_replay/XAUUSD/ (15M/30M/1H + superseded/). Datasets outside
raw_replay (e.g. backtests/) are not included.

Per-bar feature_availability is NOT deep-scanned here (would require decompressing
every dataset); it is derived from manifest notes only. Integrity (gzip+sha) IS
validated. A future --deep pass could compute exact per-source counts.

Usage:
  python3 scripts/build_dataset_registry.py            # generate + validate + write
  python3 scripts/build_dataset_registry.py --dry-run  # print, don't write
Read-only against the external drive. Output: docs/data/dataset_registry.json (repo).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
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


EXTERNAL_ROOT = Path(os.environ.get("TRADINGDATA_ROOT", "/Volumes/GUTS_ LACIE/TradingData"))
RAW_ROOT = EXTERNAL_ROOT / "raw_replay" / "XAUUSD"
MANIFEST_DIR = EXTERNAL_ROOT / "manifests"
OUT_PATH = repo_root() / "docs" / "data" / "dataset_registry.json"

TF_LABEL = {"15": "15M", "30": "30M", "60": "1H"}
TF_MINUTES = {"15M": 15, "30M": 30, "1H": 60}
COLLECTOR = "run_xau_replay_feature_collect.py"
WINDOW_MODE = "replay-collect"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gzip_ok(path: Path) -> bool:
    try:
        return subprocess.run(["gzip", "-t", str(path)], capture_output=True).returncode == 0
    except Exception:
        return False


def parse_manifest(path: Path) -> dict:
    """Parse `key: value` manifest lines into a dict (first colon splits)."""
    d = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("===") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip()] = v.strip()
    return d


def find_manifest(gz: Path) -> Path | None:
    base = gz.name[:-len(".jsonl.gz")] if gz.name.endswith(".jsonl.gz") else gz.stem
    mname = f"{base}_manifest.txt"
    for cand in (MANIFEST_DIR / mname, gz.parent / mname):
        if cand.is_file():
            return cand
    return None


def build_entry(gz: Path, warnings: list) -> dict:
    rel_gz = str(gz.relative_to(EXTERNAL_ROOT.parent)) if EXTERNAL_ROOT.parent in gz.parents else str(gz)
    rel_gz = str(gz).replace(str(EXTERNAL_ROOT.parent) + "/", "")
    status = "superseded" if "/superseded/" in str(gz) else "active"

    m_path = find_manifest(gz)
    man = parse_manifest(m_path) if m_path else {}
    if not m_path:
        warnings.append(f"{gz.name}: manifest NOT FOUND")

    # timeframe from filename (15m/30m/60m)
    mm = re.search(r"_(\d+)m_replay", gz.name)
    tf_res = mm.group(1) if mm else None
    tf_label = TF_LABEL.get(tf_res, tf_res)

    # nominal window from filename
    wm = re.search(r"_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})", gz.name)
    start_date, end_date = (wm.group(1), wm.group(2)) if wm else (None, None)

    # bars + real replay range from manifest dataset: line
    bars = None
    replay_range_real = None
    ds = man.get("dataset", "")
    dm = re.search(r"([\d,]+)\s*bars,\s*(.+?)\s*->\s*(.+?)\s*$", ds)
    if dm:
        bars = int(dm.group(1).replace(",", ""))
        replay_range_real = {"start": dm.group(2).strip(), "end": dm.group(3).strip()}

    # integrity validation against manifest
    integ = {"exists": gz.is_file(), "gzip_t": None, "sha256_match": None}
    man_gz_sha = man.get("archived_sha256")
    if gz.is_file():
        integ["gzip_t"] = gzip_ok(gz)
        if not integ["gzip_t"]:
            warnings.append(f"{gz.name}: gzip -t FAILED")
        actual_sha = sha256_file(gz)
        if man_gz_sha:
            integ["sha256_match"] = (actual_sha == man_gz_sha)
            if not integ["sha256_match"]:
                warnings.append(f"{gz.name}: sha256(gz) {actual_sha[:12]} != manifest {man_gz_sha[:12]}")
        else:
            warnings.append(f"{gz.name}: manifest has no archived_sha256")
        actual_sz = gz.stat().st_size
        man_sz = man.get("archived_size_bytes")
        if man_sz and str(actual_sz) != man_sz:
            warnings.append(f"{gz.name}: gz size {actual_sz} != manifest {man_sz}")
    else:
        warnings.append(f"{gz.name}: .gz MISSING on disk")

    feature_baseline = man.get("indicators")
    if not feature_baseline:
        feature_baseline = None
        if status == "active":
            warnings.append(f"{gz.name}: manifest has no `indicators:` (feature_baseline null)")

    known_gaps = []
    if man.get("note_bar0"):
        known_gaps.append("bar_index 0: pine_boxes/pine_lines empty (legit first replay bar)")
    feature_availability = {
        "per_bar_deep_scanned": False,
        "source": "manifest" if m_path else "none",
        "summary": man.get("note_bar0", "not recorded in manifest (integrity validated via gzip+sha)"),
    }

    notes = man.get("note", "")
    if "rerun_customOBbaseline" in gz.name:
        notes = "source of truth for 2026-02-25->2026-05-25 (re-collected with validated Custom OB v11 baseline); supersedes the pre-baseline block in superseded/."
    elif status == "superseded":
        notes = "superseded by the rerun_customOBbaseline block (pre-baseline collection); preserved for audit. NOTE: manifest archived_file path predates the move into superseded/."

    collector = COLLECTOR
    if status == "superseded":
        collector += " (collected pre-rename as run_xau_15m_replay_backtest.py, pre-baseline)"

    return {
        "symbol": "XAUUSD",
        "timeframe": tf_label,
        "start_date": start_date,
        "end_date": end_date,
        "replay_range_real": replay_range_real,
        "bars": bars,
        "raw_gz_path": rel_gz,
        "manifest_path": (str(m_path).replace(str(EXTERNAL_ROOT.parent) + "/", "") if m_path else None),
        "sha256_original": man.get("original_sha256"),
        "sha256_gz": man_gz_sha,
        "original_size_bytes": int(man["original_size_bytes"]) if man.get("original_size_bytes", "").isdigit() else None,
        "gz_size_bytes": int(man["archived_size_bytes"]) if man.get("archived_size_bytes", "").isdigit() else None,
        "collected_at": man.get("created_at"),
        "feature_baseline": feature_baseline,
        "feature_availability": feature_availability,
        "known_gaps": known_gaps,
        "collector": collector,
        "window_mode": WINDOW_MODE,
        "series_group": f"XAUUSD_{tf_label}" if tf_label else None,
        "series_order": None,  # assigned after sort (active only)
        "status": status,
        "notes": notes,
        "_integrity": integ,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate dataset_registry.json from external manifests")
    ap.add_argument("--dry-run", action="store_true", help="print, do not write")
    args = ap.parse_args()

    if not EXTERNAL_ROOT.is_dir():
        print(f"ERROR: external drive not mounted: {EXTERNAL_ROOT}", file=sys.stderr)
        return 1
    if not RAW_ROOT.is_dir():
        print(f"ERROR: raw_replay root not found: {RAW_ROOT}", file=sys.stderr)
        return 1

    warnings: list = []
    gz_files = sorted(RAW_ROOT.rglob("*.jsonl.gz"))
    entries = [build_entry(gz, warnings) for gz in gz_files]

    # assign series_order within each group (active only), by start_date
    groups = {}
    for e in entries:
        if e["status"] == "active":
            groups.setdefault(e["series_group"], []).append(e)
    for g, lst in groups.items():
        for i, e in enumerate(sorted(lst, key=lambda x: x["start_date"] or ""), start=1):
            e["series_order"] = i

    entries.sort(key=lambda e: (
        e["symbol"],
        TF_MINUTES.get(e["timeframe"], 999),
        e["series_group"] or "",
        e["series_order"] if e["series_order"] is not None else 999,
        e["start_date"] or "",
    ))

    counts = {}
    for e in entries:
        key = f"{e['timeframe']}_{e['status']}"
        counts[key] = counts.get(key, 0) + 1

    registry = {
        "_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "scripts/build_dataset_registry.py",
            "external_root": str(EXTERNAL_ROOT),
            "primary_integrity_source": "per-file manifests under TradingData/manifests (and superseded/)",
            "integrity_validated": "gzip -t + sha256(gz)==manifest, per entry",
            "feature_availability_note": "per-bar availability NOT deep-scanned; derived from manifest notes only",
            "dataset_count": len(entries),
            "counts_by_tf_status": counts,
            "warnings": warnings,
        },
        "datasets": entries,
    }

    text = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    print(f"datasets: {len(entries)} | counts: {counts}")
    print(f"warnings: {len(warnings)}")
    for w in warnings:
        print(f"  WARN: {w}")
    if args.dry_run:
        print("[dry-run] not writing")
        return 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
