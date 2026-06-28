#!/usr/bin/env python3
"""Exporta os trades SELECIONADOS pelo combo Engine 2 (reclaim_atr+h1_pos+killzone) p/ plotagem canônica + revisão visual.
Reproduz a MESMA seleção do engine_entry_discovery (AUC-dir + threshold quantil 0.60/0.40). entry=close de cj,
SL=min low s[p..cj]-0.1ATR, exit=let-run (régua 8ATR: cf_low trail, HMAX480, RCAP20). -> entry2_selected_trades.csv"""
import json,csv,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
COMBO=["reclaim_atr","h1_pos","killzone"]
def auc(feat):
    vv=[(r[feat],r["is_monforte"]) for r in ROWS if r.get(feat) is not None]
    pos=[v for v,y in vv if y]; neg=[v for v,y in vv if not y]
    if not pos or not neg: return .5
    sv=sorted(vv,key=lambda x:x[0]); vals=[v for v,_ in sv]; ranks=[0]*len(vals); j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        rr=(j+k)/2+1
        for m in range(j,k+1): ranks[m]=rr
        j=k+1
    rsp=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
    return (rsp-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
dirn={f:(1 if auc(f)>=.5 else -1) for f in COMBO}
def thr(f,q):
    vals=sorted(r[f] for r in ROWS if r.get(f) is not None); return vals[int(q*len(vals))]
TH={f:(thr(f,0.60) if dirn[f]>0 else thr(f,0.40)) for f in COMBO}
def passes(r):
    for f in COMBO:
        v=r.get(f)
        if v is None: return False
        if dirn[f]>0 and v<TH[f]: return False
        if dirn[f]<0 and v>TH[f]: return False
    return True
sel=[r for r in ROWS if passes(r)]
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1); exi=end
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; exi=k; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),ex
out=[]
for r in sel:
    pr=PRIMK[r["block"]]; s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr
    R,ex=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    out.append({"cj_t":r["cj_t"],"entry":round(entry,2),"sl":round(sl,2),"exit":round(ex,2),
                "R":round(R,2),"win":int(R>0),"label":r["label"],"yr":r["yr"]})
out.sort(key=lambda x:x["cj_t"])
for n,o in enumerate(out,1): o["num"]=n
with open(HERE/"entry2_selected_trades.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["num","cj_t","entry","sl","exit","R","win","label","yr"]); w.writeheader()
    for o in out: w.writerow(o)
from collections import Counter
print(f"selecionados: {len(out)} | sumR={sum(o['R'] for o in out):+.1f} WR={100*sum(o['win'] for o in out)/len(out):.0f}% avgR={sum(o['R'] for o in out)/len(out):+.3f}")
print("labels:",dict(Counter(o['label'] for o in out)))
print("R buckets:", {"<=0":sum(1 for o in out if o['R']<=0),"0-1.5R":sum(1 for o in out if 0<o['R']<=1.5),"1.5-3R":sum(1 for o in out if 1.5<o['R']<=3),">3R":sum(1 for o in out if o['R']>3)})
print("-> entry2_selected_trades.csv")
