#!/usr/bin/env python3
"""SANITY_PROBE materializada (exigência do guard) — diagnósticos do SKIP FAMILY LEDGER:
base rates por macro, cobertura S4, S1 em BULL, valor incremental S3-only. Reproduzível."""
import csv, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE/"results/skip_family_discovery_ledger.csv")))
out = {}
for g in ("BULL", "BEAR", "RANGE"):
    sub = [r for r in rows if r["macro"] == g]
    L = sum(1 for r in sub if r["out"] == "0")
    out[g] = {"n": len(sub), "losers": L, "loser_rate": round(L/len(sub), 2)}
out["S4_covered"] = sum(1 for r in rows if r["s4_covered"] == "1")
s1b = [r for r in rows if r["F_S1"] == "1" and r["macro"] == "BULL"]
out["S1_in_BULL"] = {"marked": len(s1b), "losers": sum(1 for r in s1b if r["out"] == "0")}
s2a_t = {r["t"] for r in rows if r["F_S2a"] == "1"}
s3only = [r for r in rows if r["F_S3"] == "1" and r["t"] not in s2a_t]
out["S3_only_vs_S2a"] = {"n": len(s3only), "losers": sum(1 for r in s3only if r["out"] == "0")}
(HERE/"results/skip_family_diagnostics.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
