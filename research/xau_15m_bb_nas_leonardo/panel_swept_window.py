#!/usr/bin/env python3
"""Painel completo da janela plotada (swept_keep_window.csv) + corte na sua data de BEAR (2026-01-29)."""
import csv,datetime as dt
from pathlib import Path
rows=sorted(csv.DictReader(open(Path(__file__).parent/"swept_keep_window.csv")),key=lambda r:int(r["cj_t"]))
def panel(rs,tag):
    R=[float(r["R"]) for r in rs]; n=len(R); sm=sum(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    py={}
    for r in rs:
        y=r["date"][:4]; py[y]=py.get(y,0)+float(r["R"])
    print(f"{tag}: N{n} WR{100*w/n:.1f}% sumR{sm:.1f} avgR{sm/n:.3f} DD{dd:.1f} r/DD{abs(sm/dd) if dd<0 else 99:.2f} streak-{mL}/+{mW} | "+" ".join(f"{k}:{v:.0f}" for k,v in sorted(py.items())))
panel(rows,"PLOTADO (ago2025->mar2026)")
cut=dt.datetime(2026,1,29).timestamp()
panel([r for r in rows if int(r["cj_t"])<cut],"CORTE no seu BEAR (<2026-01-29)")
