#!/usr/bin/env python3
"""Exporta trades 5ATR re-otim A2 (h1_pos>=0.65 & disp4_atr>=0.78) + dedup uma-posição + SL=B(flush-0.5ATR) + let-run.
Preços entry/SL/saída + win + #N → strategy_5atr_a2_trades.csv. RAW-causal."""
import json,csv,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480
F={}
for l in (HERE/"dataset_5atr.jsonl").read_text().splitlines():
    r=json.loads(l); F[(r["block"],r["low_t"])]=r
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1); exi=end
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; exi=k; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return dict(entry=entry,sl=sl,exit=ex,R=max(-1.0,min(RCAP,(ex-entry)/risk)),exi=exi,entry_t=s[cj]["t"])
def A2(r): return r.get("h1_pos") is not None and r["h1_pos"]>=0.65 and r["disp4_atr"]>=0.78
rows=[]
for k,pr in PRIM.items():
    s=pr["series"]; tmap={b["t"]:idx for idx,b in enumerate(s)}
    anch=[]
    for (blk,lt),r in F.items():
        if blk!=k[:10]: continue
        i=tmap.get(lt)
        if i is None or not s[i]["atr"]: continue
        anch.append((i,r["cj"],s[i]["atr"],r))
    anch.sort(key=lambda a:a[1]); busy=-10**9
    for i,cj,atr,r in anch:
        if cj<=busy or not A2(r): continue
        flush=min(x["l"] for x in s[i:cj+1]); entry=s[cj]["c"]; sl=flush-0.5*atr  # SL=B
        t=letrun(s,cj,entry,sl,atr)
        if not t: continue
        busy=t["exi"]; t["yr"]=dt.datetime.utcfromtimestamp(t["entry_t"]).year; rows.append(t)
rows.sort(key=lambda r:r["entry_t"])
for n,r in enumerate(rows,1): r["num"]=n
with open(HERE/"strategy_5atr_a2_trades.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["num","entry_t","entry","sl","exit","R","win","yr"])
    for r in rows: w.writerow([r["num"],r["entry_t"],round(r["entry"],2),round(r["sl"],2),round(r["exit"],2),round(r["R"],2),int(r["R"]>0),r["yr"]])
n=len(rows); w=sum(1 for r in rows if r["R"]>0)
print(f"strategy_5atr_a2_trades.csv: N={n} WR={100*w/n:.1f}% sumR={sum(r['R'] for r in rows):+.0f} | winners={w} losers={n-w}")
