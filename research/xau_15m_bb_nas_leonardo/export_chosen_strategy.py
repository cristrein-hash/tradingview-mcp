#!/usr/bin/env python3
"""Exporta os trades da config ESCOLHIDA: 8ATR+R2+R_B, dedup=uma-posição-por-vez, SL=B(flush-0.5ATR), EXIT=let-run.
Preços entry/SL/saída + win + #N cronológico → strategy_chosen_trades.csv (p/ plotagem canônica). RAW-causal."""
import json,bisect,datetime as dt,csv
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480
def R_B(r): return (r["absorption"]==1 and r["sell_decel"]==0) or (r["buy_sell_ratio4"]>7 and r["low_vol_rel"]>1.37) or (r["regime_age_h"]<=25.2 and r["sell_skew_mig"]>0)
FINAL=set()
for l in (HERE/"dataset_r2refine.jsonl").read_text().splitlines():
    r=json.loads(l)
    if r["r2_keep"]==1 and not R_B(r): FINAL.add((r["block"],r["low_t"]))
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def trade(s,i,cj,atr):
    entry=s[cj]["c"]; flush=min(x["l"] for x in s[i:cj+1]); sl=flush-0.5*atr  # SL=B
    risk=entry-sl
    if risk<=0: return None
    end=min(cj+HMAX,len(s)-1); trail=sl; r1=False; ex=None; exi=end
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; exi=k; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]; exi=end
    R=max(-1.0,min(RCAP,(ex-entry)/risk))
    return dict(entry=entry,sl=sl,exit=ex,R=R,exi=exi,entry_t=s[cj]["t"])
rows=[]
for k,pr in PRIM.items():
    s=pr["series"]; nn=len(s); L=[x["l"] for x in s]; tmap={b["t"]:idx for idx,b in enumerate(s)}
    anch=[]
    for (blk,lt) in [x for x in FINAL if x[0]==k[:10]]:
        i=tmap.get(lt)
        if i is None or not s[i]["atr"]: continue
        atr=s[i]["atr"]; cj=None
        for q in range(i+1,min(i+HMAX,nn-2)):
            if s[q]["h"]>=s[i]["l"]+8*atr: cj=q; break
        if cj is None or cj+2>=nn: continue
        anch.append((i,cj,atr))
    anch.sort(key=lambda a:a[1]); busy=-10**9
    for i,cj,atr in anch:
        if cj<=busy: continue  # uma-posição-por-vez
        t=trade(s,i,cj,atr)
        if not t: continue
        busy=t["exi"]; t["yr"]=dt.datetime.utcfromtimestamp(t["entry_t"]).year; rows.append(t)
rows.sort(key=lambda r:r["entry_t"])
for n,r in enumerate(rows,1): r["num"]=n
with open(HERE/"strategy_chosen_trades.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["num","entry_t","entry","sl","exit","R","win","yr"])
    for r in rows: w.writerow([r["num"],r["entry_t"],round(r["entry"],2),round(r["sl"],2),round(r["exit"],2),round(r["R"],2),int(r["R"]>0),r["yr"]])
n=len(rows); w=sum(1 for r in rows if r["R"]>0)
print(f"strategy_chosen_trades.csv: N={n} WR={100*w/n:.1f}% sumR={sum(r['R'] for r in rows):+.0f} | winners={w} losers={n-w}")
