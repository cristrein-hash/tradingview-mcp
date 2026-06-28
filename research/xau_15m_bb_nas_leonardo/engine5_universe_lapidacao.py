#!/usr/bin/env python3
"""LAPIDAÇÃO DO UNIVERSO — só corte anti-faca (Cris 2026-06-28): N/WR/R/DD do universo cru vs corte-de-faca.
Régua let-run oficial (SL=min low s[p..cj]-0.1ATR, entry=close cj, cf_low trail, HMAX480, RCAP20). Determinístico."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"]); r["R"]=None
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if atr:
        entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; r["R"]=letrun(s,cj,entry,sl,atr)
G=[r for r in ROWS if r["R"] is not None]; MF=sum(r["is_monforte"] for r in G)
def knife_audit(r): return f(r,"rsi_min8",50)<32 and f(r,"atr_regime",1)>1.05 and f(r,"downleg_decel",1)==0
def knife_m1(r): return f(r,"h4n_trend")==-1 and f(r,"h4n_in_demand")==0
def knife_v2(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
def metr(sel):
    n=len(sel); rs=[r["R"] for r in sel]; sm=sum(rs); w=sum(1 for x in rs if x>0); mf=sum(r["is_monforte"] for r in sel)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(r["R"] for r in sel if r["yr"]==y),1) for y in (2024,2025,2026)}
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),mf,py
print(f"{'cenario':<28}{'N':>6}{'MF':>4}{'recall':>7}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>8}  sumR yr24/25/26")
defs=[("UNIVERSO cru (take-all)",lambda r:False),
      ("- corta faca (AUDIT)",knife_audit),
      ("- corta faca (M1 macro)",knife_m1),
      ("- corta faca (KNIFEKILL_v2)",knife_v2)]
for name,kn in defs:
    sel=[r for r in G if not kn(r)]
    n,wr,sm,avg,dd,mf,py=metr(sel)
    cut=len(G)-n
    tag=name if cut==0 else f"{name} (-{cut})"
    print(f"{tag:<28}{n:>6}{mf:>4}{round(mf/MF,2):>7}{wr:>6}{sm:>8}{avg:>7}{dd:>8}  {py[2024]}/{py[2025]}/{py[2026]}")
