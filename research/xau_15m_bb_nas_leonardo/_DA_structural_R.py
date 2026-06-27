#!/usr/bin/env python3
"""DECISIVO tradeável: large-SELL no fundo prediz R maior com STOP ESTRUTURAL (no flush) + let-run? (não ATR-normalizado).
Entrada no close do bar seguinte ao fundo fractal; SL = flush_low - 0.1*ATR; let-run trailing em swing lows; R=result.
Compara avgR/sumR/WR por bucket de large-SELL. Controla por macro_drop. RAW-causal. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900; RCAP=20.0; HMAX=192
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
def selL(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    return sum(1 for x in bb[a:b] if x["side"]=="SELL" and x["size"]=="L")
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def sim_long(s,p):
    atr=s[p]["atr"] or 1.0; ei=p+1
    if ei+2>=len(s): return None
    entry=s[ei]["c"]; sl=s[p]["l"]-0.1*atr; risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-4:p+5])]
rows=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        R=sim_long(s,p)
        if R is None: continue
        a=s[p]["atr"] or 1.0; lo=max(0,p-192); md=(max(b["h"] for b in s[lo:p+1])-s[p]["l"])/a
        rows.append({"sL":selL(k,s[p]["t"]),"R":R,"md":md})
def rep(v,lab):
    if len(v)<20: print(f"  {lab}: n={len(v)} (poucos)"); return
    n=len(v); sm=sum(x["R"] for x in v); wr=100*sum(1 for x in v if x["R"]>0)/n
    print(f"  {lab}: n={n} avgR={sm/n:+.2f} sumR={sm:+.0f} WR={wr:.0f}%")
print(f"entradas long em fundos fractais: {len(rows)} | STOP ESTRUTURAL + let-run")
print("por bucket de large-SELL na janela:")
for lo,hi,lab in [(0,1,"L-SELL=0"),(1,2,"L-SELL=1"),(2,4,"L-SELL 2-3"),(4,99,"L-SELL>=4")]:
    rep([x for x in rows if lo<=x["sL"]<hi],lab)
print("CONDICIONADO macro_drop>=10 (perna estendida):")
for lo,hi,lab in [(0,1,"L-SELL=0"),(2,99,"L-SELL>=2")]:
    rep([x for x in rows if lo<=x["sL"]<hi and x["md"]>=10],lab)
