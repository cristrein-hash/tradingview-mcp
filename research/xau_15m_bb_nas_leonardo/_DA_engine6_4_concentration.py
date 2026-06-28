#!/usr/bin/env python3
"""DA ENGINE6 ATTACK #4 — CONCENTRATION. reclaim>=4 +53.8R over 153: top5/top10 R share,
remove-top5 avgR, RCAP20 monsters count, and avgR with RCAP capped lower (5R,3R) to test
if a few let-run home-runs carry it."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
HMAX=480
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr,rcap=20.0):
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
    return max(-1.0,min(rcap,(ex-entry)/risk))
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"]); r["R"]=None
    for cap in (20.0,5.0,3.0):
        r[f"R{int(cap)}"]=None
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if atr:
        entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr
        r["R"]=letrun(s,cj,entry,sl,atr,20.0)
        for cap in (20.0,5.0,3.0): r[f"R{int(cap)}"]=letrun(s,cj,entry,sl,atr,cap)
G=[r for r in ROWS if r["R"] is not None]
def sub(thr): return [r for r in G if f(r,"reclaim_atr",0)>=thr]
print("="*78); print("ATTACK #4 — CONCENTRATION"); print("="*78)
for thr in (4.0,3.5):
    sel=sub(thr); rs=sorted([r["R"] for r in sel],reverse=True); tot=sum(rs); n=len(sel)
    top5=sum(rs[:5]); top10=sum(rs[:10])
    rem5=rs[5:]; rem10=rs[10:]
    mons=sum(1 for x in rs if x>=15)
    print(f"--- reclaim>={thr} (N={n}, sumR={tot:.1f}, avgR={tot/n:.3f}) ---")
    print(f"   top5 R={top5:.1f} ({100*top5/tot:.0f}% of sumR)  top10 R={top10:.1f} ({100*top10/tot:.0f}%)")
    print(f"   remove top5: avgR={st.mean(rem5):+.3f} (sumR={sum(rem5):+.1f})")
    print(f"   remove top10: avgR={st.mean(rem10):+.3f} (sumR={sum(rem10):+.1f})")
    print(f"   RCAP20 monsters (R>=15): {mons}")
    print(f"   top 8 R values: {[round(x,1) for x in rs[:8]]}")
    for cap in (5.0,3.0):
        cr=[r[f'R{int(cap)}'] for r in sel]
        print(f"   if RCAP={cap}: avgR={st.mean(cr):+.3f} sumR={sum(cr):+.1f} WR={100*sum(1 for x in cr if x>0)/n:.1f}%")
    print()
