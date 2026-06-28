#!/usr/bin/env python3
"""DA ENGINE6 ATTACK #6 — WHAT IS IT REALLY. recall only 16% MON+FORTE => not a bottom-quality
selector. Is reclaim>=4 a momentum/continuation-confirmation trigger? Does it work only in non-BEAR?
Break reclaim>=4 by macro regime (macro_bull/macro_bear as-of), by is_bottom, by h1_trend/h4 trend.
Compare base-rate of MON+FORTE among reclaim>=4 vs whole universe (is it bottom-enriched at all?)."""
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
G=[r for r in ROWS if r["R"] is not None]
def m(sel):
    n=len(sel)
    if not n: return "n=0"
    rs=[r["R"] for r in sel]; w=sum(1 for x in rs if x>0)
    return f"n={n:4d} WR={100*w/n:4.1f}% avgR={st.mean(rs):+.3f} sumR={sum(rs):+.1f}"
sel=[r for r in G if f(r,"reclaim_atr",0)>=4.0]
print("="*78); print("ATTACK #6 — WHAT IS IT REALLY"); print("="*78)
# bottom enrichment
base_mf=sum(r["is_monforte"] for r in G)/len(G)
base_bot=sum(r["is_bottom"] for r in G)/len(G)
sel_mf=sum(r["is_monforte"] for r in sel)/len(sel)
sel_bot=sum(r["is_bottom"] for r in sel)/len(sel)
print(f"MON+FORTE base-rate: universe={100*base_mf:.1f}%  reclaim>=4={100*sel_mf:.1f}%  (lift {sel_mf/base_mf:.2f}x)")
print(f"is_bottom base-rate: universe={100*base_bot:.1f}%  reclaim>=4={100*sel_bot:.1f}%  (lift {sel_bot/base_bot:.2f}x)")
print("=> NOT a bottom-quality selector (low recall, weak enrichment)\n")
# by macro regime
print("BY MACRO REGIME (as-of, causal flags in jsonl):")
print(f"  macro_bull=1 : {m([r for r in sel if f(r,'macro_bull',0)==1])}")
print(f"  macro_bear=1 : {m([r for r in sel if f(r,'macro_bear',0)==1])}")
print(f"  neither(neutral): {m([r for r in sel if f(r,'macro_bull',0)==0 and f(r,'macro_bear',0)==0])}")
print()
print("BY H1 TREND (as-of):")
for tv in (1,0,-1):
    print(f"  h1_trend={tv:+d}: {m([r for r in sel if f(r,'h1_trend')==tv])}")
print()
print("BY H4 TREND (h4n_trend as-of):")
for tv in (1,0,-1):
    print(f"  h4n_trend={tv:+d}: {m([r for r in sel if f(r,'h4n_trend')==tv])}")
print()
# is it momentum-continuation? above_ema21 + up_closes
print("MOMENTUM CHARACTER:")
print(f"  above_ema21=1: {m([r for r in sel if f(r,'above_ema21',0)==1])}")
print(f"  above_ema21=0: {m([r for r in sel if f(r,'above_ema21',0)==0])}")
print(f"  swept_prior_low=1: {m([r for r in sel if f(r,'swept_prior_low',0)==1])}")
print(f"  swept_prior_low=0: {m([r for r in sel if f(r,'swept_prior_low',0)==0])}")
print(f"\n  mean up_closes_pc(of 3)={st.mean([f(r,'up_closes_pc',0) for r in sel]):.2f}, mean confirm_body_atr={st.mean([f(r,'confirm_body_atr',0) for r in sel]):.2f}")
print(f"  mean legpos60={st.mean([f(r,'legpos60',0) for r in sel]):.2f} (0=low of leg,1=high) — where in the leg is the entry")
