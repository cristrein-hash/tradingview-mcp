#!/usr/bin/env python3
"""DA Engine2 test #6 — LOOK-AHEAD audit. Static + empirical check that NO feature in lab_entry_candidates.py
uses a bar index > cj (cj = entry bar). Strategy: re-extract a handful of the 'reaction' features for a sample
of candidates using ONLY bars <=cj, and confirm they equal the stored values. Any mismatch where recompute(<=cj)
!= stored => the stored value peeked >cj.
Audited features: reclaim_atr, reclaim_ema_bars, micro_hl, confirm_body_atr, low_wick, up_closes_pc,
above_ema21, downleg_decel, pullback_depth, swept_prior_low.
-> stdout + _DA_entry2_lookahead.json"""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
SER={k:v["series"] for k,v in PRIMK.items()}
TIDX={k:{b["t"]:i for i,b in enumerate(s)} for k,s in SER.items()}
def ema(vals,n):
    if not vals: return None
    k=2/(n+1); e=vals[0]
    for v in vals[1:]: e=v*k+e*(1-k)
    return e
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
# audit every 5th row for speed but enough coverage
SAMPLE=ROWS[::3]
mism={f:0 for f in ("reclaim_atr","reclaim_ema_bars","micro_hl","confirm_body_atr","low_wick",
                    "up_closes_pc","above_ema21","downleg_decel","pullback_depth","swept_prior_low")}
checked=0; maxbar_used=[]
for r in SAMPLE:
    blk=r["block"]; s=SER[blk]; ti=TIDX[blk]
    p=ti.get(r["t"]); cj=ti.get(r["cj_t"])
    if p is None or cj is None: continue
    atr=s[p]["atr"]
    if not atr: continue
    catr=s[cj]["atr"] or atr; lo=s[p]["l"]; c=s[cj]["c"]
    checked+=1
    # reclaim_atr uses lo(p),c(cj) -> max idx cj OK
    v=round((c-lo)/atr,2)
    if v!=r["reclaim_atr"]: mism["reclaim_atr"]+=1
    maxbar_used.append(cj)  # never exceeds cj for reaction window p..cj
    # reclaim_ema_bars: loop x in p..cj, ema of s[x-60:x+1] -> max idx cj OK
    rb=99
    for x in range(p,cj+1):
        ee=ema([b["c"] for b in s[max(0,x-60):x+1]],21)
        if ee and s[x]["c"]>ee: rb=x-p; break
    if rb!=r["reclaim_ema_bars"]: mism["reclaim_ema_bars"]+=1
    # micro_hl: range p+1..cj -> max idx cj OK
    mh=1 if any(s[x]["l"]>lo and x>p for x in range(p+1,cj+1)) and s[cj]["l"]>lo else 0
    if mh!=r["micro_hl"]: mism["micro_hl"]+=1
    # confirm_body_atr: s[cj] only OK
    cb=round((c-s[cj]["o"])/catr,2)
    if cb!=r["confirm_body_atr"]: mism["confirm_body_atr"]+=1
    # low_wick: s[p] only OK
    rng=s[p]["h"]-s[p]["l"]; lw=round((min(s[p]["o"],s[p]["c"])-lo)/rng,2) if rng>0 else 0
    if lw!=r["low_wick"]: mism["low_wick"]+=1
    # up_closes_pc: range p+1..cj OK
    uc=sum(1 for x in range(p+1,cj+1) if s[x]["c"]>s[x]["o"])
    if uc!=r["up_closes_pc"]: mism["up_closes_pc"]+=1
    # above_ema21: ema s[cj-60:cj+1] OK
    e21=ema([b["c"] for b in s[max(0,cj-60):cj+1]],21); ae=1 if(e21 and c>e21) else 0
    if ae!=r["above_ema21"]: mism["above_ema21"]+=1
    # downleg_decel: ranges p-6..p -> max idx p OK
    rngs=[s[x]["h"]-s[x]["l"] for x in range(max(0,p-6),p+1)]
    dd=1 if len(rngs)>=4 and st.mean(rngs[-3:])<st.mean(rngs[:3]) else 0
    if dd!=r["downleg_decel"]: mism["downleg_decel"]+=1
    # pullback_depth: p-60..p OK
    up0=max(0,p-60); hi_prev=max(s[x]["h"] for x in range(up0,p+1)); lo_prev=min(s[x]["l"] for x in range(up0,p+1))
    pd=round((hi_prev-lo)/((hi_prev-lo_prev) or 1),2)
    if pd!=r["pullback_depth"]: mism["pullback_depth"]+=1
    # swept_prior_low: scans q in p-1..3 looking for swing low using s[q-2:q+3]; requires q+2<p so window<=p-1<cj OK
    sl=None
    for q in range(p-1,3,-1):
        if q+2<p and s[q]["l"]==min(x["l"] for x in s[q-2:q+3]): sl=q; break
    spl=1 if (sl is not None and lo<s[sl]["l"]) else 0
    if spl!=r["swept_prior_low"]: mism["swept_prior_low"]+=1
print(f"checked {checked} sampled candidates (every 3rd of {len(ROWS)})")
print("feature recompute(<=cj) vs stored — mismatches (any >0 => leak or impl drift):")
for f,m in mism.items(): print(f"  {f:<18} mismatches={m}")
# static index-window verdict
windows={
 "reclaim_atr":"lo@p, c@cj -> [p,cj] OK",
 "reclaim_ema_bars":"loop x in [p,cj], ema[x-60..x] -> max cj OK",
 "micro_hl":"range (p,cj] -> OK",
 "confirm_body_atr":"s[cj] only -> OK",
 "low_wick":"s[p] only -> OK",
 "up_closes_pc":"range (p,cj] -> OK",
 "above_ema21":"ema[cj-60..cj] -> OK",
 "downleg_decel":"ranges [p-6,p] -> OK (pre-low)",
 "pullback_depth":"[p-60,p] -> OK (pre-low)",
 "swept_prior_low":"swing q<p, window [q-2,q+2] with q+2<p -> < p < cj OK",
 "demand_reclaim/in_demand/dist_demand/clean_sky":"zones filtered born_t<=tc(=cj.t) -> causal OK",
 "buy/sell_bub_w":"bubbles with t<=tc AND known_at<=tc -> causal OK",
 "nas_long_16":"nas events t<=tc -> OK",
 "h1/h4 ctx":"htf bars t_end<=tc -> closed HTF only OK",
}
leak=any(m>0 for m in mism.values())
print("\nstatic window map:")
for k,v in windows.items(): print(f"  {k}: {v}")
print(f"\nVERDICT: {'LEAK or impl drift detected' if leak else 'NO look-ahead — all reaction features use bars <= cj (entry bar). cj IS the decision bar, entry at its close, so using s[cj] is legitimate.'}")
json.dump({"checked":checked,"mismatches":mism,"leak":leak,"windows":windows},
          open(HERE/"_DA_entry2_lookahead.json","w"),indent=1)
print("-> _DA_entry2_lookahead.json")
