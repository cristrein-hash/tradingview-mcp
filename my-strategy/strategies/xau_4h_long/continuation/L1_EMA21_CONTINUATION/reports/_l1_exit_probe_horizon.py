#!/usr/bin/env python3
"""SANITY_PROBE — recuperar o horizonte/cutoff canónico dos estudos L1 (não backtest de estratégia).
Mapeia os 3 conjuntos (FINAL-24/estudo-34) ts->bar, recomputa entry/stop V1 via scanner, e varre
horizontes de first-touch para achar H* que reproduz o split salvo (res TARGET/STOP/TIME + sumR).
Read-only. Sem produção/chart. Output: stdout only (probe)."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
def u(ts):
    if len(ts)==16: ts=ts+":00"
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
S=scanner.build_series()
def trade(tsu):
    i=S.idx.get(tsu)
    if i is None: return None
    entry=S.C[i]; stop=scanner.structural_sl(S,i)
    if not (entry-stop>0): return None
    target=entry+scanner.TARGET_R*(entry-stop)
    return dict(i=i,entry=entry,stop=stop,target=target)
def ft(tr,H):
    i=tr["i"]; e,st,tg=tr["entry"],tr["stop"],tr["target"]; risk=e-st
    for j in range(i+1,min(i+H,S.N-1)+1):
        lo,hi=S.L[j],S.H[j]
        if lo<=st: return "STOP",-1.0,j-i
        if hi>=tg: return "TARGET",3.0,j-i
    # TIME: R = (close_at_cutoff - entry)/risk
    jend=min(i+H,S.N-1); R=(S.C[jend]-e)/risk
    return "TIME",round(R,2),jend-i
s34=json.load(open(DATA/"l1_approved34.json"))
f24=json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]
def probe(name,rows,rkey="R"):
    print(f"\n=== {name} (N={len(rows)}) ===")
    savedR=[r[rkey] for r in rows]; savedsum=round(sum(savedR),1)
    from collections import Counter
    savedres=Counter(r.get("res") for r in rows if "res" in r)
    print(f"saved: sumR={savedsum:+.1f}"+(f" res={dict(savedres)}" if savedres else ""))
    miss=0; built=[]
    for r in rows:
        tr=trade(u(r["ts"]))
        if tr is None: miss+=1; continue
        built.append((r,tr))
    print(f"mapped {len(built)}/{len(rows)} (miss={miss})")
    for H in [40,60,80,100,120,150,200,300,500]:
        res=Counter(); Rs=[]
        for r,tr in built:
            rr,R,_=ft(tr,H); res[rr]+=1; Rs.append(R)
        print(f"  H={H:>3}: sumR={sum(Rs):+6.1f} T/S/TIME={res['TARGET']}/{res['STOP']}/{res['TIME']}")
probe("estudo-34",s34)
probe("FINAL-24",f24)
