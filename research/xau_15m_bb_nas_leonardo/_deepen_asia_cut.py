#!/usr/bin/env python3
"""APROFUNDAMENTO 4 (corrigido pelo DA) — sessão como LOSER-CUT (cortar Asia 00-06), NÃO winner-pick (NY). Base ampla
with_macro (n131, LONG+SHORT, let-run). Estratificado por ANO (mata confound macro-window): Asia-cut tem que ajudar
em 2024 E 2025-26. + por bloco + leave-one-out + ortogonalidade com cbfs-gate. Causal. Verified 2026-06-26."""
import csv, json, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}; TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, MIN_RISK_ATR, R_CAP = 2, 480, 0.5, 15.0
def conf_low(s,i):
    L=[b["l"] for b in s]; lo=max(K,i-120); best=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): best=L[p]
    return best
def conf_high(s,i):
    H=[b["h"] for b in s]; lo=max(K,i-120); best=None
    for p in range(lo,i-K+1):
        if H[p]==max(H[p-K:p+K+1]): best=H[p]
    return best
def outcome(s,ei,entry,sl0,long,atr):
    struct=(entry-sl0) if long else (sl0-entry)
    if struct<=0: return None
    risk=max(struct,MIN_RISK_ATR*atr); sl0=(entry-risk) if long else (entry+risk); trail=sl0; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        bar=s[i]
        if long:
            if bar["l"]<=trail: ex=trail; break
            if (bar["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=conf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if bar["h"]>=trail: ex=trail; break
            if (entry-bar["l"])/risk>=1: r1=True
            if r1:
                sh=conf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(R_CAP,((ex-entry) if long else (entry-ex))/risk))
def cbfs(s,i):
    bos=0;fail=0
    for j in range(max(40,i-40),i+1):
        rh=max(x["h"] for x in s[j-20:j]); rl=min(x["l"] for x in s[j-20:j])
        if s[j]["c"]>rh:
            bos+=1
            if any(s[k]["c"]<rh for k in range(j+1,min(j+5,i+1))): fail+=1
        elif s[j]["c"]<rl:
            bos+=1
            if any(s[k]["c"]>rl for k in range(j+1,min(j+5,i+1))): fail+=1
    return bos>=3 and fail/bos>0.6
T=[]
for r in csv.DictReader(open(HERE/"candidates_annotated.csv")):
    if r["setup_vs_macro"]!="with_macro": continue
    b=r["block"]; s=SER.get(b); ei=TID.get(b,{}).get(int(r["entry_t"])); j=TID.get(b,{}).get(int(r["nas_t"]))
    if s is None or ei is None or j is None or ei+2>=len(s): continue
    entry=float(r["entry_close"]); zlo=float(r["zone_low"]); zhi=float(r["zone_high"]); zwa=float(r["zone_width_atr"])
    atr=(zhi-zlo)/zwa if zwa>0 else None
    if not atr: continue
    long=r["dir"]=="LONG"; sl0=(zlo-0.1*atr) if long else (zhi+0.1*atr)
    R=outcome(s,ei,entry,sl0,long,atr)
    if R is None: continue
    t=int(r["entry_t"]); d=dt.datetime.utcfromtimestamp(t)
    T.append({"block":b,"t":t,"R":R,"win":R>0,"hr":d.hour,"yr":d.year,"asia":0<=d.hour<7,"cbfs":cbfs(s,j)})
span=lambda sub:(max(x["t"] for x in sub)-min(x["t"] for x in sub))/(7*86400) or 1
def agg(sub,label):
    if not sub: print(f"  [{label}] vazio"); return
    n=len(sub);w=sum(1 for x in sub if x["win"]);sm=sum(x["R"] for x in sub)
    print(f"  [{label:>22}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} freq={n/span(sub):.2f}/sem")
print(f"base with_macro n={len(T)} (let-run). Teste: cortar Asia 00-06 (loser-cut), estratificado por ano:")
agg(T,"BASE (todos)"); agg([x for x in T if not x["asia"]],"sem Asia")
print("\n por ANO (confound-killer — Asia-cut tem que ajudar nos DOIS):")
for yr in (2024,2025,2026):
    sub=[x for x in T if x["yr"]==yr]
    if sub:
        agg(sub,f"{yr} base"); agg([x for x in sub if not x["asia"]],f"{yr} sem-Asia")
print("\n Asia isolada (o que se corta):"); agg([x for x in T if x["asia"]],"Asia 00-06 (cortado)")
print("\n leave-one-block-out (sem Asia):")
na=[x for x in T if not x["asia"]]; byb={}
for x in na: byb.setdefault(x["block"][:16],[]).append(x)
cap=lambda x:max(-1.0,min(R_CAP,x["R"])); drop=set(sorted(byb,key=lambda b:sum(cap(x) for x in byb[b]),reverse=True)[:2])
rem=[x for x in na if x["block"][:16] not in drop]; pos=sum(1 for b in byb if sum(x['R'] for x in byb[b])>0)
print(f"   sem-Asia: sumR {sum(cap(x) for x in na):+.0f} → −top2bloc {sum(cap(x) for x in rem):+.0f}(n{len(rem)}) | blocos net+ {pos}/{len(byb)}")
print("\n ortogonalidade com cbfs-gate (sem Asia E sem cbfs):")
agg([x for x in T if not x["asia"] and not x["cbfs"]],"sem-Asia & cbfs-pass")
