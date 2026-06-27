#!/usr/bin/env python3
"""APROFUNDAMENTO 5 — Asia-blackout (validado year-robusto) na base AMPLA sweep (n728, 7/sem) p/ manter ≥1/sem segurando
o lift de WR. Mede WR/avgR/streak/DD/freq + por ANO + por bloco + leave-one-out. Causal. Verified 2026-06-26."""
import csv, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "candidates_sweep.csv")))
for r in rows:
    d=dt.datetime.utcfromtimestamp(int(r["t"])); r["hr"]=d.hour; r["yr"]=d.year; r["R"]=float(r["R"]); r["w"]=r["win"]=="True"; r["asia"]=0<=d.hour<7
def metr(sub,label):
    if not sub: print(f"  [{label}] vazio"); return
    n=len(sub);w=sum(1 for x in sub if x["w"]);sm=sum(x["R"] for x in sub)
    ts=sorted(sub,key=lambda x:int(x["t"]));eq=0;pk=0;dd=0;stk=0;mstk=0
    for x in ts:
        eq+=x["R"];pk=max(pk,eq);dd=min(dd,eq-pk)
        if x["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    span=(int(ts[-1]["t"])-int(ts[0]["t"]))/(7*86400) or 1
    print(f"  [{label:>20}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} DD={dd:.1f}R streakL={mstk} freq={n/span:.2f}/sem")
print(f"base sweep n={len(rows)} (7/sem). Asia-blackout (cortar 00-06):")
metr(rows,"BASE (todos)"); metr([r for r in rows if not r["asia"]],"sem Asia")
print("\n por ANO (sem Asia tem que segurar):")
for yr in (2024,2025,2026):
    sub=[r for r in rows if r["yr"]==yr]
    if sub: metr(sub,f"{yr} base"); metr([r for r in sub if not r["asia"]],f"{yr} sem-Asia")
print("\n por dir (sem Asia):"); metr([r for r in rows if not r["asia"] and r["dir"]=="LONG"],"LONG sem-Asia"); metr([r for r in rows if not r["asia"] and r["dir"]=="SHORT"],"SHORT sem-Asia")
print("\n + confluência NAS (sem Asia & nas_near):"); metr([r for r in rows if not r["asia"] and r["nas_near"]=="1"],"sem-Asia & NAS")
na=[r for r in rows if not r["asia"]]; byb={}
for x in na: byb.setdefault(x["block"][:16],[]).append(x)
cap=lambda x:max(-1.0,min(15.0,x["R"])); drop=set(sorted(byb,key=lambda b:sum(cap(x) for x in byb[b]),reverse=True)[:2])
rem=[x for x in na if x["block"][:16] not in drop]; pos=sum(1 for b in byb if sum(x['R'] for x in byb[b])>0)
print(f"\n leave-one-out (sem Asia): sumR {sum(cap(x) for x in na):+.0f} → −top2bloc {sum(cap(x) for x in rem):+.0f}(n{len(rem)},WR{100*sum(1 for x in rem if x['w'])/max(1,len(rem)):.0f}%) | blocos net+ {pos}/{len(byb)}")
