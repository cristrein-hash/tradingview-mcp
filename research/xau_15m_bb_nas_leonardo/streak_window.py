#!/usr/bin/env python3
"""Painel completo + streak da JANELA ago2025->01jan2026 (window_aug2025_jan2026.csv)."""
import csv,statistics as st
from pathlib import Path
rows=sorted(csv.DictReader(open(Path(__file__).parent/"window_aug2025_jan2026.csv")),key=lambda r:int(r["cj_t"]))
rs=[float(r["R"]) for r in rows]; n=len(rs); sm=sum(rs); w=sum(1 for x in rs if x>0)
eq=pk=dd=0
for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
mL=mW=cl=cw=0
for x in rs:
    if x>0: cw+=1; cl=0
    else: cl+=1; cw=0
    mW=max(mW,cw); mL=max(mL,cl)
top=sorted(rs,reverse=True)
print(f"N {n} | WR {100*w/n:.1f}% | sumR {sm:.1f} | avgR {sm/n:.3f} | medR {st.median(rs):.3f}")
print(f"DD {dd:.1f} | return/DD {abs(sm/dd):.2f} | maxR {max(rs):.1f} | top5 {sum(top[:5]):.1f}R ({100*sum(top[:5])/sm:.0f}%)")
print(f"streak: max perdas {mL} | max ganhos {mW}")
