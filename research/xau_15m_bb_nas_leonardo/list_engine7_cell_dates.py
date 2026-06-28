#!/usr/bin/env python3
"""Lista datas dos 21 trades plotados (engine7_cell_trades.csv) — p/ localizar no chart (reprodutível)."""
import csv,datetime as dt
from collections import Counter
from pathlib import Path
rows=list(csv.DictReader(open(Path(__file__).parent/"engine7_cell_trades.csv")))
ds=[(r,dt.datetime.utcfromtimestamp(int(r["cj_t"])).strftime("%Y-%m-%d %H:%M")) for r in rows]
print(f"N={len(rows)} | {ds[0][1]} -> {ds[-1][1]} | por ano:",dict(Counter(d[:4] for _,d in ds)))
for r,d in ds: print(f"  #{r['num']:>2} {d}  entry {r['entry']} R {r['R']} {'W' if r['win']=='1' else 'L'}")
