#!/usr/bin/env python3
"""PROVENANCE — varre results/*.csv + backbone por features de grau SEMANAL e DIARIO (demanda/origem-perna/range/
supply/clean-sky/dealing-range) com cobertura nos 276, p/ testar a hipotese macro-floor no GRAU CERTO + vozes
ortogonais a snap+sweep (room-above/clean-sky, range-pos D1/W). So inventario. Verified 2026-06-25."""
import csv, json, glob
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
KW = ("weekly", "wk", "_w_", "month", "dealing", "range_pos", "clean_sky", "supply", "demand", "d1_", "_1d",
      "origin_of_leg", "macro_reader_leg", "leg", "floor", "swing", "cascade", "polarity")
print("=== CSVs com features de grau D1/Weekly/range/supply (col : nrows) ===")
for f in sorted(glob.glob(str(V1 / "results/*.csv"))):
    try:
        rows = list(csv.DictReader(open(f)))
    except Exception:
        continue
    if not rows: continue
    cols = [c for c in rows[0] if c and any(k in c.lower() for k in KW)]
    has_bar = "bar_idx" in rows[0]
    if cols and has_bar and len(rows) >= 200:   # cobertura ~276
        hit = [c for c in cols if any(k in c.lower() for k in ("weekly", "month", "d1_", "_1d", "dealing", "clean_sky", "supply", "range_pos", "origin_of_leg", "cascade"))]
        if hit:
            print(f"\n[{Path(f).name}] n={len(rows)}")
            for c in hit: print(f"    {c}")
# backbone (jsonl)
print("\n=== backbone l2_bpt_raw_backbone_episodes.jsonl ===")
bk = [json.loads(l) for l in open(V1 / "results/l2_bpt_raw_backbone_episodes.jsonl")]
print(f"n={len(bk)}; regime keys:", list(bk[0].get("regime_raw_mapped", {}).keys()))
print("supply_demand keys:", list(bk[0].get("supply_demand_raw_mapped", {}).keys()))
