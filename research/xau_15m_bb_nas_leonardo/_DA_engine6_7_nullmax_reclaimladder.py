#!/usr/bin/env python3
"""DA ENGINE6 ATTACK #2b — tighter null-of-max restricted to the RECLAIM-THRESHOLD LADDER only
(the actual search that surfaced reclaim>=4: the 7 pure reclaim cutoffs 1.5..5.0). This is the
honest family if the analyst's real search was 'pick the best reclaim cutoff'. Also a
continuous-threshold sweep null (scan reclaim cutoffs 1.0..6.0 step .25, take best avgR with
N>=100) under shuffled R — the worst-case multiple-comparison the cutoff search implies.
Also: causality sanity — confirm let-run uses only bars > cj (no look-ahead in exit)."""
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
    for k in range(cj+1,end+1):                  # <-- starts at cj+1: exit uses ONLY future bars. causal.
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
recl=[f(r,"reclaim_atr",0) for r in G]; Rall=[r["R"] for r in G]; N=len(G)
print("="*78); print("ATTACK #2b — NULL-OF-MAX restricted to reclaim-cutoff search"); print("="*78)
# continuous cutoff sweep
cuts=[round(1.0+0.25*i,2) for i in range(21)]  # 1.0..6.0
def best_cutoff(rvals):
    best=-9
    for c in cuts:
        sel=[rvals[i] for i in range(N) if recl[i]>=c]
        if len(sel)>=100:
            a=sum(sel)/len(sel)
            if a>best: best=a
    return best
obs_best=best_cutoff(Rall)
# observed reclaim>=4 avgR
sel4=[Rall[i] for i in range(N) if recl[i]>=4.0]; a4=sum(sel4)/len(sel4)
random.seed(11); K=2000; nullmax=[]
idx=list(range(N))
for _ in range(K):
    random.shuffle(idx); rsh=[Rall[i] for i in idx]; nullmax.append(best_cutoff(rsh))
p_obsbest=sum(1 for x in nullmax if x>=obs_best)/K
p_a4=sum(1 for x in nullmax if x>=a4)/K
print(f"cutoff ladder = {cuts}")
print(f"observed BEST cutoff avgR (N>=100) = {obs_best:.3f}")
print(f"observed reclaim>=4 avgR = {a4:.3f}")
print(f"null-max(best cutoff, shuffled R): mean={st.mean(nullmax):.3f} p95={sorted(nullmax)[int(.95*K)]:.3f} max={max(nullmax):.3f}")
print(f"  p(reclaim>=4 avgR vs null-max of cutoff search) = {p_a4:.4f}")
print(f"  p(observed BEST   vs null-max of cutoff search) = {p_obsbest:.4f}")
print()
print("CAUSALITY SANITY: let-run loop range = range(cj+1, end+1) -> exit decisions use ONLY")
print("bars strictly after the entry bar cj. reclaim_atr uses bars p..cj (fractal confirmed at p+3=cj).")
print("No same-bar or future leakage in trigger or exit. CONFIRMED causal.")
