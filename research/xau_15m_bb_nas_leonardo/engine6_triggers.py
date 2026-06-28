#!/usr/bin/env python3
"""ENGINE 6 — survey de GATILHOS causais de entrada-fundo (Cris 2026-06-28). Objetivo: achar gatilho que dê 100-200
trades em 2 anos (não prever label). Reporta N/freq/WR/sumR/avgR/DD + MON+FORTE capturados, por gatilho. Régua let-run."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
HMAX=480; RCAP=20.0; WK=2*52
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
def metr(name,sel):
    n=len(sel)
    if n<20: return None
    rs=[r["R"] for r in sel]; sm=sum(rs); w=sum(1 for x in rs if x>0); mf=sum(r["is_monforte"] for r in sel)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(r["R"] for r in sel if r["yr"]==y),1) for y in (2024,2025,2026)}
    return dict(name=name,n=n,wk=round(n/WK,2),WR=round(100*w/n,1),sumR=round(sm,1),avgR=round(sm/n,3),DD=round(dd,1),
                mf=mf,recall=round(mf/MF,2),py=py)
# GATILHOS causais (mecanismos, não predição de label)
TRIG={
 "reclaim>=1.5": lambda r: f(r,"reclaim_atr",0)>=1.5,
 "reclaim>=2.0": lambda r: f(r,"reclaim_atr",0)>=2.0,
 "reclaim>=2.5": lambda r: f(r,"reclaim_atr",0)>=2.5,
 "reclaim>=3.0": lambda r: f(r,"reclaim_atr",0)>=3.0,
 "reclaim>=3.5": lambda r: f(r,"reclaim_atr",0)>=3.5,
 "reclaim>=4.0": lambda r: f(r,"reclaim_atr",0)>=4.0,
 "reclaim>=5.0": lambda r: f(r,"reclaim_atr",0)>=5.0,
 "reclaim>=3 & sweep": lambda r: f(r,"reclaim_atr",0)>=3.0 and f(r,"swept_prior_low",0)==1,
 "reclaim>=3 & microHL": lambda r: f(r,"reclaim_atr",0)>=3.0 and f(r,"micro_hl",0)==1,
 "reclaim>=2.5 & sweep": lambda r: f(r,"reclaim_atr",0)>=2.5 and f(r,"swept_prior_low",0)==1,
 "sweep+reclaim>=1": lambda r: f(r,"swept_prior_low",0)==1 and f(r,"reclaim_atr",0)>=1.0,
 "sweep+reclaim>=2": lambda r: f(r,"swept_prior_low",0)==1 and f(r,"reclaim_atr",0)>=2.0,
 "demand_reclaim": lambda r: f(r,"demand_reclaim",0)==1,
 "demand_reclaim+rec>=1.5": lambda r: f(r,"demand_reclaim",0)==1 and f(r,"reclaim_atr",0)>=1.5,
 "microHL+reclaim>=1.5": lambda r: f(r,"micro_hl",0)==1 and f(r,"reclaim_atr",0)>=1.5,
 "sweep+demand_reclaim": lambda r: f(r,"swept_prior_low",0)==1 and f(r,"demand_reclaim",0)==1,
 "reclaim>=2 & upcloses>=2": lambda r: f(r,"reclaim_atr",0)>=2.0 and f(r,"up_closes_pc",0)>=2,
 "sweep+reclaim>=1.5 & microHL": lambda r: f(r,"swept_prior_low",0)==1 and f(r,"reclaim_atr",0)>=1.5 and f(r,"micro_hl",0)==1,
}
print(f"universo R-ok={len(G)} | MON+FORTE={MF} | alvo: gatilho com N entre 100-200 em 2 anos\n")
print(f"{'gatilho':<28}{'N':>5}{'/sem':>6}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>8}{'MF':>4}{'recall':>7}  yr24/25/26")
res=[metr(k,[r for r in G if fn(r)]) for k,fn in TRIG.items()]
for m in sorted([x for x in res if x],key=lambda z:z["n"]):
    flag=" <==100-200" if 100<=m["n"]<=200 else (" <300" if 200<m["n"]<=300 else "")
    print(f"{m['name']:<28}{m['n']:>5}{m['wk']:>6}{m['WR']:>6}{m['sumR']:>8}{m['avgR']:>7}{m['DD']:>8}{m['mf']:>4}{m['recall']:>7}  {m['py'][2024]}/{m['py'][2025]}/{m['py'][2026]}{flag}")
