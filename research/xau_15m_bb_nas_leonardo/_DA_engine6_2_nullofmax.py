#!/usr/bin/env python3
"""DA ENGINE6 ATTACK #2 — NULL-OF-MAX over thresholds.
19 triggers were scanned in engine6. Shuffle R across the universe K times, re-run the FULL
trigger search each shuffle, record max avgR across triggers (with N>=100 floor, the deployable
band). Where do reclaim>=4 / reclaim>=3.5 fall in the null-max distribution? p-value + Bonferroni.
Uses the SAME 19 trigger defs as engine6_triggers.py. R precomputed via _DA_engine6_1 cache
recomputed inline (base let-run, close fill)."""
import json,random,statistics as st
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
G=[r for r in ROWS if r["R"] is not None]

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
# precompute membership masks (fixed across shuffles)
MASK={name:[fn(r) for r in G] for name,fn in TRIG.items()}
Rall=[r["R"] for r in G]
N=len(G)

def avgR_for(mask,rvals):
    s=cnt=0
    for i,m in enumerate(mask):
        if m: s+=rvals[i]; cnt+=1
    return (s/cnt,cnt) if cnt else (None,0)

# observed
obs={name:avgR_for(MASK[name],Rall) for name in TRIG}
print("="*78); print("ATTACK #2 — NULL-OF-MAX over thresholds (K shuffles of R)"); print("="*78)
print(f"19 triggers scanned. Null-max taken over triggers with N>=100 (deployable band).\n")

K=2000; random.seed(42)
NFLOOR=100
# distribution of MAX avgR across triggers (N>=NFLOOR) under shuffled R
nullmax=[]
nullmax_all=[]   # no N floor (max over all 19 incl tiny n)
idx=list(range(N))
for _ in range(K):
    random.shuffle(idx)
    rsh=[Rall[i] for i in idx]
    best=best_all=-9
    for name in TRIG:
        a,c=avgR_for(MASK[name],rsh)
        if a is None: continue
        if a>best_all: best_all=a
        if c>=NFLOOR and a>best: best=a
    nullmax.append(best); nullmax_all.append(best_all)

def pval(obs_a,null): return sum(1 for x in null if x>=obs_a)/len(null)

for name in ("reclaim>=4.0","reclaim>=3.5","reclaim>=3.0","reclaim>=2.5"):
    a,c=obs[name]
    p_floor=pval(a,nullmax)
    p_all=pval(a,nullmax_all)
    print(f"{name:<18} obs avgR={a:.3f} (N={c})")
    print(f"   p(null-max, N>=100 band) = {p_floor:.4f}   [Bonferroni-protected by max]")
    print(f"   p(null-max, all 19 trig) = {p_all:.4f}")
print()
print(f"null-max (N>=100 band): mean={st.mean(nullmax):.3f} p95={sorted(nullmax)[int(.95*K)]:.3f} max={max(nullmax):.3f}")
print(f"null-max (all 19)     : mean={st.mean(nullmax_all):.3f} p95={sorted(nullmax_all)[int(.95*K)]:.3f} max={max(nullmax_all):.3f}")
print(f"\nbase avgR of full universe = {st.mean(Rall):.3f}")
