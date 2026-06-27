#!/usr/bin/env python3
"""APROFUNDAMENTO 2 — condicionamento por SESSÃO/HORA (a única separação winner/loser achada). v2 trades por bucket de
hora UTC: WR/n/avgR/freq. Testa se restringir à sessão NY eleva WR mantendo frequência. Diagnóstico, não-gate-final.
Verified 2026-06-26."""
import csv, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
rows = [r for r in csv.DictReader(open(HERE / "candidates_v2_final.csv")) if r["t"] != "t"]
for r in rows: r["hr"] = dt.datetime.utcfromtimestamp(int(r["t"])).hour
span = (max(int(r["t"]) for r in rows) - min(int(r["t"]) for r in rows)) / (7*86400)
def agg(sub, label):
    if not sub: print(f"  [{label}] vazio"); return
    n=len(sub); w=sum(1 for r in sub if r["win"]=="True"); sm=sum(float(r["R"]) for r in sub)
    print(f"  [{label:>16}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} freq={n/span:.2f}/sem")
print("v2 por bucket de hora UTC:")
agg([r for r in rows if 0<=r["hr"]<7], "Asia 00-06")
agg([r for r in rows if 7<=r["hr"]<13], "Londres 07-12")
agg([r for r in rows if 13<=r["hr"]<19], "NY 13-18")
agg([r for r in rows if 19<=r["hr"]<24], "Tarde 19-23")
print("\ncombos:")
agg([r for r in rows if 13<=r["hr"]<19], "NY only")
agg([r for r in rows if 12<=r["hr"]<20], "NY amplo 12-19")
agg(rows, "TODOS (base)")
# por bloco dentro de NY (robustez)
print("\nNY-only por bloco (estacionariedade):")
ny=[r for r in rows if 13<=r["hr"]<19]
import collections
byb=collections.defaultdict(list)
for r in ny: byb[r["block"][:16]].append(r)
for b in sorted(byb):
    sub=byb[b]; w=sum(1 for r in sub if r["win"]=="True"); print(f"  {b}: n={len(sub)} WR={100*w/len(sub):.0f}% sumR={sum(float(r['R']) for r in sub):+.1f}")
