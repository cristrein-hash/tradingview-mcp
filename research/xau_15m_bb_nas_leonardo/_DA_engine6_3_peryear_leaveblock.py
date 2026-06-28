#!/usr/bin/env python3
"""DA ENGINE6 ATTACK #3 — PER-YEAR (avgR not sumR) + LEAVE-ONE-BLOCK (8 folds).
Is reclaim>=4 / >=3.5 genuinely all-years or 2025-driven? Report avgR & n per year, and
avgR across 8 leave-one-block folds (min/max). Also bootstrap CI on avgR per threshold."""
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
BLOCKS=sorted(set(r["block"] for r in G))
def sub(thr): return [r for r in G if f(r,"reclaim_atr",0)>=thr]

print("="*78); print("ATTACK #3 — PER-YEAR (avgR) + LEAVE-ONE-BLOCK (8 folds)"); print("="*78)
print(f"blocks: {len(BLOCKS)}\n")
for thr in (4.0,3.5):
    sel=sub(thr)
    print(f"--- reclaim>={thr}  (N={len(sel)}) ---")
    for y in (2024,2025,2026):
        ys=[r["R"] for r in sel if r["yr"]==y]
        if ys: print(f"   {y}: n={len(ys):3d} avgR={st.mean(ys):+.3f} sumR={sum(ys):+.1f} WR={100*sum(1 for x in ys if x>0)/len(ys):.0f}%")
        else:  print(f"   {y}: n=0")
    # leave-one-block: avgR of REMAINING 7 blocks
    folds=[]
    for b in BLOCKS:
        rem=[r["R"] for r in sel if r["block"]!=b]
        folds.append(st.mean(rem) if rem else None)
    fv=[x for x in folds if x is not None]
    print(f"   leave-one-block avgR: min={min(fv):+.3f} max={max(fv):+.3f} (full={st.mean([r['R'] for r in sel]):+.3f})")
    # which block carries it: avgR contribution per block
    print(f"   per-block avgR (n):")
    for b in BLOCKS:
        bs=[r["R"] for r in sel if r["block"]==b]
        if bs: print(f"      {b}: n={len(bs):3d} avgR={st.mean(bs):+.3f} sumR={sum(bs):+.1f}")
    # bootstrap CI on avgR
    random.seed(7); rs=[r["R"] for r in sel]; boot=[]
    for _ in range(3000):
        bx=[random.choice(rs) for _ in rs]; boot.append(st.mean(bx))
    boot.sort()
    print(f"   bootstrap avgR 95% CI: [{boot[int(.025*3000)]:+.3f}, {boot[int(.975*3000)]:+.3f}]  (incl 0? {'YES' if boot[int(.025*3000)]<=0 else 'no'})")
    print()
