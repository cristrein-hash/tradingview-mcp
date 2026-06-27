#!/usr/bin/env python3
"""ENGINE v2 — CANDIDATO combinando peças VALIDADAS: base with_macro BULL-long + GATE cbfs-only (DA: WR/freq sem comer
cauda) + EXIT partial2R (DA: streak é sequencing, resolve-se no exit, não no gate). Avalia sob meta ALIVIADA
(WR40-50/streak≤5/1-5sem/DD-livre) + leave-one-block-out + por bloco. Emite trades p/ plotagem visual. Causal RAW.
Verified 2026-06-26."""
import csv, json, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}; TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
K, HMAX, MIN_RISK_ATR, R_CAP, RUNNER = 2, 480, 0.5, 15.0, 3.0
def conf_low(s, i):
    L=[b["l"] for b in s]; lo=max(K,i-120); best=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): best=L[p]
    return best
def cbfs_veto(s, i):  # breakout-failure rate > 0.6 em 40 barras (causal)
    bos=0; fail=0
    for j in range(max(40,i-40),i+1):
        rh=max(x["h"] for x in s[j-20:j]); rl=min(x["l"] for x in s[j-20:j])
        if s[j]["c"]>rh:
            bos+=1
            if any(s[k]["c"]<rh for k in range(j+1,min(j+5,i+1))): fail+=1
        elif s[j]["c"]<rl:
            bos+=1
            if any(s[k]["c"]>rl for k in range(j+1,min(j+5,i+1))): fail+=1
    return bos>=3 and fail/bos>0.6
def partial2R(s, ei, entry, risk):  # LONG: realiza 50%@2R, resto BE+trail; retorna (R, mfe)
    sl=entry-risk; tgt2=entry+2*risk; part=False; pr=0.0; mfe=0.0; end=min(ei+HMAX,len(s)-1); atr=risk/MIN_RISK_ATR
    for i in range(ei+1,end+1):
        bar=s[i]; mfe=max(mfe,(bar["h"]-entry)/risk)
        if bar["l"]<=sl: return max(-1.0,min(R_CAP, pr+0.5*((sl-entry)/risk))), mfe
        if not part and bar["h"]>=tgt2: pr=0.5*2.0; part=True; sl=entry
        if part:
            sw=conf_low(s,i)
            if sw: sl=max(sl,sw-0.1*atr)
    return max(-1.0,min(R_CAP, pr+0.5*((s[end]["c"]-entry)/risk))), mfe
def build():
    out=[]
    for r in csv.DictReader(open(HERE/"candidates_annotated.csv")):
        if r["setup_vs_macro"]!="with_macro" or r["dir"]!="LONG": continue
        b=r["block"]; s=SER.get(b); ei=TID.get(b,{}).get(int(r["entry_t"])); j=TID.get(b,{}).get(int(r["nas_t"]))
        if s is None or ei is None or j is None or ei+2>=len(s): continue
        entry=float(r["entry_close"]); zlo=float(r["zone_low"]); zhi=float(r["zone_high"]); zwa=float(r["zone_width_atr"])
        atr=(zhi-zlo)/zwa if zwa>0 else None
        if not atr: continue
        sl0=zlo-0.1*atr; risk=max(entry-sl0,MIN_RISK_ATR*atr)
        if risk<=0: continue
        if cbfs_veto(s,j): continue   # GATE
        R,mfe=partial2R(s,ei,entry,risk)
        out.append({"block":b,"t":int(r["entry_t"]),"entry":round(entry,2),"sl":round(entry-risk,2),"R":R,"mfe":mfe,"win":R>0,"runner":mfe>=RUNNER})
    return out
def agg(trs,label):
    if not trs: print(f"  [{label}] vazio"); return
    n=len(trs);w=sum(1 for t in trs if t["win"]);sm=sum(t["R"] for t in trs);run=sum(1 for t in trs if t["runner"])
    ts=sorted(trs,key=lambda t:t["t"]);eq=0;pk=0;dd=0;stk=0;mstk=0
    for t in ts:
        eq+=t["R"];pk=max(pk,eq);dd=min(dd,eq-pk)
        if t["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    span=(ts[-1]["t"]-ts[0]["t"])/(7*86400) or 1
    print(f"  [{label}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} run={run}({100*run/n:.0f}%) DD={dd:.1f}R streakL={mstk} freq={n/span:.2f}/sem")
c=build()
print("=== ENGINE v2 FINAL | with_macro BULL-long + cbfs-gate + partial2R (meta aliviada) ===")
agg(c,"v2 candidato")
byb={};
for t in c: byb.setdefault(t["block"],[]).append(t)
print("\n por bloco (leave-one-block-out):")
for b in sorted(byb): agg(byb[b],b[:21])
pos=sum(1 for b in byb if sum(t["R"] for t in byb[b])>0)
sm=sum(t["R"] for t in c); drop=sorted(byb,key=lambda b:sum(t["R"] for t in byb[b]),reverse=True)[:2]
lo=sum(t["R"] for t in c if t["block"] not in drop)
print(f"\n blocos net+ : {pos}/{len(byb)} | leave−top2bloc: {sm:+.0f}R → {lo:+.0f}R")
import csv as _csv
with open(HERE/"candidates_v2_final.csv","w",newline="") as f:
    _csv.DictWriter(f,fieldnames=list(c[0].keys())).writeheader() or [None]
    w=_csv.DictWriter(f,fieldnames=list(c[0].keys())); w.writeheader(); w.writerows(c)
print(f"\n trades salvos -> candidates_v2_final.csv (n={len(c)}) p/ plotagem visual")
