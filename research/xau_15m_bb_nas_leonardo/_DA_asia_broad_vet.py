#!/usr/bin/env python3
"""DA VET: broad sweep universe (candidates_sweep.csv, n=728) — Asia 00-06 per-year
and per-session per-year, to check whether the proposed 'apply Asia-blackout to broad
sweep' next test rests on a year-robust signal. Verified 2026-06-26."""
import csv, datetime as dt, collections
from pathlib import Path
HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE/"candidates_sweep.csv")))
for r in rows:
    d = dt.datetime.utcfromtimestamp(int(r["t"]))
    r["hr"] = d.hour; r["yr"] = d.year; r["R"] = float(r["R"]); r["w"] = r["win"] == "True"
def sess(h):
    if 0 <= h < 7: return "Asia00-06"
    if 7 <= h < 13: return "Lon07-12"
    if 13 <= h < 19: return "NY13-18"
    return "PM19-23"
print("BROAD sweep n=728 — Asia 00-06 per-year:")
for yr in (2024, 2025, 2026):
    sub = [r for r in rows if r["yr"] == yr and sess(r["hr"]) == "Asia00-06"]
    if sub:
        n = len(sub); w = sum(1 for r in sub if r["w"]); sm = sum(r["R"] for r in sub)
        print(f"  {yr}: n={n} WR={100*w/n:.0f}% sumR={sm:+.1f} avgR={sm/n:+.2f}")
print("\nBROAD sweep — full session x year matrix (sumR):")
M = collections.defaultdict(lambda: [0, 0, 0.0])  # n,w,sumR
for r in rows:
    k = (r["yr"], sess(r["hr"])); M[k][0] += 1; M[k][1] += r["w"]; M[k][2] += r["R"]
for yr in (2024, 2025, 2026):
    line = f"  {yr}: "
    for s in ("Asia00-06", "Lon07-12", "NY13-18", "PM19-23"):
        n, w, sm = M[(yr, s)]
        if n: line += f"{s} n{n} WR{100*w/n:.0f}% sum{sm:+.0f} | "
    print(line)
print("\nWhat 'cut Asia' does to TOTAL sumR on broad sweep:")
allR = sum(r["R"] for r in rows); asiaR = sum(r["R"] for r in rows if sess(r["hr"]) == "Asia00-06")
print(f"  ALL sumR={allR:+.1f}  ->  cut-Asia sumR={allR-asiaR:+.1f}  (Asia contributed {asiaR:+.1f})")
