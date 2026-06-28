#!/usr/bin/env python3
"""Streaks (máx perdas/ganhos consecutivos) da BASE FIXA 3120+h4_up&h1d_up (fixed_base_h4h1.csv). Cronológico por cj_t."""
import csv
from pathlib import Path
rows=sorted(csv.DictReader(open(Path(__file__).parent/"fixed_base_h4h1.csv")),key=lambda r:int(r["cj_t"]))
def streaks(rs):
    mL=mW=cl=cw=0
    for r in rs:
        if float(r["R"])>0: cw+=1; cl=0
        else: cl+=1; cw=0
        mW=max(mW,cw); mL=max(mL,cl)
    return mL,mW
mL,mW=streaks(rows)
print(f"GERAL N{len(rows)} | max losing streak {mL} | max winning streak {mW}")
for y in ("2024","2025","2026"):
    yr=[r for r in rows if r["yr"]==y]
    if not yr: continue
    l,w=streaks(yr); print(f"{y}  N{len(yr)} | maxLossStreak {l} | maxWinStreak {w}")
