#!/usr/bin/env python3
"""RECLAIM + STOP JUSTO cruzado com large-SELL / velocidade-do-reclaim / capitulação. known_at-filtered (bubbles repintam).
Entrada no close do bar que RECLAIMA (fecha acima do flush+0.25ATR). 2 stops: (A) no fundo do flush; (B) JUSTO (mínima
local da entrada). let-run. Reporta avgR/WR/sumR por large-SELL, por velocidade do reclaim, e cruzado c/ macro_drop. RAW-causal."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900; RCAP=20.0; HMAX=192; RWIN=48
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
def selL(key,t,entry_t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    return sum(1 for x in bb[a:b] if x["side"]=="SELL" and x["size"]=="L" and (x.get("known_at") or x["t"])<=entry_t)
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,ei,entry,sl):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*(s[ei]["atr"] or 1))
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-4:p+5])]
rows=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        a=s[p]["atr"] or 1.0; flush=s[p]["l"]
        j=None
        for q in range(p+1,min(p+RWIN,len(s)-2)):
            if s[q]["c"]>flush+0.25*a: j=q; break
        if j is None: continue
        entry=s[j]["c"]; et=s[j]["t"]
        slA=flush-0.1*a
        slB=min(x["l"] for x in s[max(0,j-2):j+1])-0.1*a  # stop JUSTO local
        RA=letrun(s,j,entry,slA); RB=letrun(s,j,entry,slB)
        if RA is None or RB is None: continue
        lo=max(0,p-192); md=(max(b["h"] for b in s[lo:p+1])-flush)/a
        rows.append({"sL":selL(k,s[p]["t"],et),"RA":RA,"RB":RB,"rspeed":j-p,"md":md,"yr":dt.datetime.utcfromtimestamp(s[p]["t"]).year})
def rep(v,lab,col):
    if len(v)<15: print(f"  {lab}: n={len(v)} (poucos)"); return
    n=len(v); sm=sum(x[col] for x in v); wr=100*sum(1 for x in v if x[col]>0)/n
    print(f"  {lab}: n={n} avgR={sm/n:+.2f} sumR={sm:+.0f} WR={wr:.0f}%")
print(f"entradas reclaim: {len(rows)} | stop A=flush  stop B=JUSTO(local) | let-run, known_at-filtered")
for col in ("A","B"):
    cc="R"+col; print(f"\n=== STOP {col} ({'flush' if col=='A' else 'JUSTO'}) — por large-SELL ===")
    for lo,hi,lab in [(0,1,"L-SELL=0"),(1,2,"L-SELL=1"),(2,99,"L-SELL>=2")]:
        rep([x for x in rows if lo<=x["sL"]<hi],lab,cc)
print("\n=== STOP JUSTO (B) — reclaim RÁPIDO (<=4 bars, =absorção) por large-SELL ===")
for lo,hi,lab in [(0,1,"L-SELL=0"),(2,99,"L-SELL>=2")]:
    rep([x for x in rows if lo<=x["sL"]<hi and x["rspeed"]<=4],lab,"RB")
print("\n=== STOP JUSTO (B) — capitulação (macro_drop>=10) + reclaim rápido + L-SELL>=2 ===")
cap=[x for x in rows if x["md"]>=10 and x["rspeed"]<=4 and x["sL"]>=2]
rep(cap,"capit+fast+LSELL>=2","RB"); rep([x for x in rows if x["md"]>=10 and x["rspeed"]<=4 and x["sL"]==0],"capit+fast+LSELL=0","RB")
if len(cap)>=15:
    for yr in (2024,2025,2026):
        rep([x for x in cap if x["yr"]==yr],f"  {yr}","RB")
