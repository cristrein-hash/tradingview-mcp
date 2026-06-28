#!/usr/bin/env python3
"""DA ENGINE6 ATTACK #1 — WIDE-STOP / LATE-ENTRY REALISM (the #1 threat).
reclaim>=4 enters ~4 ATR above the low; SL at the low => risk ~4 ATR. Quantify risk size,
3-bar move shape, then re-run let-run R with REALISTIC fills:
  - fill at NEXT bar open (cj+1) instead of cj close
  - + 1 tick slippage
  - + 0.5*spread slippage (XAUUSD spot spread ~ assume 0.30 $ -> half = 0.15 $; tick=0.01)
Does avgR survive? Is the edge just a wide stop rarely hit (high WR) + let-run continuation?
RAW-causal, in-sample. Reproduces engine6 base let-run exactly first."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
HMAX=480; RCAP=20.0; WK=2*52
MINTICK=0.01            # XAUUSD spot price granularity used
SPREAD=0.30            # assumed spot spread in $ (gold spot ~ 0.20-0.40); half-spread cost
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr,start=None):
    """let-run trail sim. start = first bar checked (default cj+1)."""
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None
    s0=start if start is not None else cj+1
    end=min(s0-1+HMAX,len(s)-1)
    for k in range(s0,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d

# attach geometry + multiple R variants
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    r["R"]=None; r["R_open"]=None; r["R_open_slip"]=None
    r["risk_atr"]=None; r["risk_usd"]=None; r["entry_px"]=None; r["atr_usd"]=None
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    lo_seg=min(x["l"] for x in s[p:cj+1])
    sl=lo_seg-0.1*atr
    # --- base (engine6 canonical): entry=close[cj], trail from cj+1 ---
    entry=s[cj]["c"]
    r["R"]=letrun(s,cj,entry,sl,atr,start=cj+1)
    r["risk_usd"]=round(entry-sl,3); r["risk_atr"]=round((entry-sl)/atr,3)
    r["entry_px"]=entry; r["atr_usd"]=round(atr,3)
    # --- realistic fill: entry at NEXT bar open (cj+1), SL still anchored to low, trail from cj+2 ---
    if cj+1<len(s):
        e_open=s[cj+1]["o"]
        # SL must include the low through cj+1? No: decision at cj close, SL = low[p..cj]. keep same SL.
        r["R_open"]=letrun(s,cj,e_open,sl,atr,start=cj+2)
        # --- + slippage: pay half-spread + 1 tick on the buy (worse entry) ---
        e_slip=e_open+SPREAD/2.0+MINTICK
        r["R_open_slip"]=letrun(s,cj,e_slip,sl,atr,start=cj+2)

G=[r for r in ROWS if r["R"] is not None]
MF=sum(r["is_monforte"] for r in G)

def metr(sel,rkey="R"):
    sel=[r for r in sel if r.get(rkey) is not None]
    n=len(sel)
    if n<5: return None
    rs=[r[rkey] for r in sel]; sm=sum(rs); w=sum(1 for x in rs if x>0)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return dict(n=n,WR=round(100*w/n,1),sumR=round(sm,1),avgR=round(sm/n,3),DD=round(dd,1))

def sub(thr): return [r for r in G if f(r,"reclaim_atr",0)>=thr]

print("="*78)
print("ATTACK #1 — WIDE-STOP / LATE-ENTRY REALISM")
print("="*78)
print(f"universe R-ok={len(G)}  MON+FORTE={MF}\n")

for thr in (4.0,3.5,3.0,2.5):
    sel=sub(thr)
    rusd=[r["risk_usd"] for r in sel if r["risk_usd"]]
    ratr=[r["risk_atr"] for r in sel if r["risk_atr"]]
    ausd=[r["atr_usd"] for r in sel if r["atr_usd"]]
    print(f"--- reclaim>={thr}  (N={len(sel)}) ---")
    print(f"  median risk: {st.median(ratr):.2f} ATR  =  ${st.median(rusd):.2f}   (median ATR=${st.median(ausd):.2f})")
    print(f"  risk ATR range: {min(ratr):.1f} .. {max(ratr):.1f}")
    b=metr(sel,"R"); o=metr(sel,"R_open"); osl=metr(sel,"R_open_slip")
    print(f"  base close-fill   : N={b['n']} WR={b['WR']} avgR={b['avgR']} sumR={b['sumR']} DD={b['DD']}")
    print(f"  NEXT-OPEN fill    : N={o['n']} WR={o['WR']} avgR={o['avgR']} sumR={o['sumR']} DD={o['DD']}")
    print(f"  OPEN+slip(.5sprd+tick): N={osl['n']} WR={osl['WR']} avgR={osl['avgR']} sumR={osl['sumR']} DD={osl['DD']}")
    # WR if SL never moved (pure wide-stop survival) vs let-run: how many ever hit -1 (stopped before any move)?
    stopped=sum(1 for r in sel if r["R"]<=-0.999)
    print(f"  stopped at -1R (wide-stop hit): {stopped}/{len(sel)} = {100*stopped/len(sel):.1f}%")
    print()

# 3-bar move shape: confirm_body_atr + up_closes_pc distribution for reclaim>=4
sel=sub(4.0)
ucp=[r.get("up_closes_pc",0) for r in sel]
print(f"reclaim>=4 3-bar reaction shape: up_closes_pc mean={st.mean(ucp):.2f} (of 3 bars)")
print(f"  => entry buys after a {st.median([r['risk_atr'] for r in sel]):.1f}-ATR vertical bounce in 3 bars (violent spike)")
