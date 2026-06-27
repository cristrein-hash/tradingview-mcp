#!/usr/bin/env python3
"""SÍNTESE v2 — combina peças VALIDADAS: universo SWEEP+RECLAIM (macro-gated) + filtro SESSÃO NY (13-18 UTC) + EXIT
partial2R + (opcional) cbfs-gate. Mede WR/avgR/streak/DD/freq + por ANO + por bloco + leave-one-out + mediana-bloco +
top5 (cauda). Causal RAW. SEM grab de positivo — reporto os caveats. Verified 2026-06-26."""
import json, bisect, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
M = json.loads((HERE / "macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in M]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return M[k]["macro"] if k>=0 else "WARMUP"
K, LB, EPS_ATR, MIN_GAP, MIN_RISK_ATR, R_CAP, HMAX = 2, 50, 0.05, 8, 0.5, 15.0, 480
def sw_low(L,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if L[p]==min(L[p-K:p+K+1]): return L[p]
    return None
def sw_high(H,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if H[p]==max(H[p-K:p+K+1]): return H[p]
    return None
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(K,i-120); bst=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): bst=L[p]
    return bst
def cf_high(s,i):
    H=[b["h"] for b in s]; lo=max(K,i-120); bst=None
    for p in range(lo,i-K+1):
        if H[p]==max(H[p-K:p+K+1]): bst=H[p]
    return bst
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
def partial2R(s,ei,entry,risk,long):
    # CORRIGIDO (DA 2026-06-26): antes de bancar (part=False) a posicao CHEIA stopa = -1.0R (era pontuado -0.5R=bug).
    # Apos bancar metade @2R (part=True): +1.0R banked + 0.5*(trail) na metade restante.
    sl=(entry-risk) if long else (entry+risk); tgt=(entry+2*risk) if long else (entry-2*risk)
    part=False; pr=0.0; atr=risk/MIN_RISK_ATR; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        bar=s[i]
        if long:
            if bar["l"]<=sl: return -1.0 if not part else max(-1.0,min(R_CAP, pr+0.5*((sl-entry)/risk)))
            if not part and bar["h"]>=tgt: pr=1.0; part=True; sl=entry
            if part:
                sw=cf_low(s,i)
                if sw: sl=max(sl,sw-0.1*atr)
        else:
            if bar["h"]>=sl: return -1.0 if not part else max(-1.0,min(R_CAP, pr+0.5*((entry-sl)/risk)))
            if not part and bar["l"]<=tgt: pr=1.0; part=True; sl=entry
            if part:
                sh=cf_high(s,i)
                if sh: sl=min(sl,sh+0.1*atr)
    cl=s[end]["c"]
    full=((cl-entry)/risk) if long else ((entry-cl)/risk)
    return max(-1.0,min(R_CAP, full if not part else pr+0.5*full))
def detect(use_cbfs):
    out=[]
    for b,pr in PRIM.items():
        s=pr["series"]; n=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]; last=-999
        for i in range(LB+K,n-2):
            t=s[i]["t"]; atr=s[i]["atr"]
            if not atr or i-last<MIN_GAP: continue
            hr=dt.datetime.utcfromtimestamp(t).hour
            if not (13<=hr<19): continue                       # FILTRO NY
            mac=macro_at(t)
            long = mac=="BULL"; short = mac=="BEAR"
            if not (long or short): continue
            if use_cbfs and cbfs(s,i): continue                 # cbfs-gate
            if long:
                liq=sw_low(L,i)
                if not (liq and L[i]<liq-EPS_ATR*atr and s[i]["c"]>liq): continue
                ei=i+1; sl0=L[i]-0.1*atr
            else:
                liq=sw_high(H,i)
                if not (liq and H[i]>liq+EPS_ATR*atr and s[i]["c"]<liq): continue
                ei=i+1; sl0=H[i]+0.1*atr
            if ei+2>=n: continue
            entry=s[ei]["c"]; risk=max((entry-sl0) if long else (sl0-entry), MIN_RISK_ATR*atr)
            if risk<=0: continue
            R=partial2R(s,ei,entry,risk,long)
            out.append({"block":b,"t":t,"dir":"LONG" if long else "SHORT","yr":dt.datetime.utcfromtimestamp(t).year,"R":R,"w":R>0}); last=i
    return out
def report(trs,label):
    if not trs: print(f"  [{label}] vazio"); return
    n=len(trs);w=sum(1 for x in trs if x["w"]);sm=sum(x["R"] for x in trs)
    ts=sorted(trs,key=lambda x:x["t"]);eq=0;pk=0;dd=0;stk=0;mstk=0
    for x in ts:
        eq+=x["R"];pk=max(pk,eq);dd=min(dd,eq-pk)
        if x["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    span=(ts[-1]["t"]-ts[0]["t"])/(7*86400) or 1
    print(f"  [{label:>18}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} DD={dd:.1f}R streakL={mstk} freq={n/span:.2f}/sem")
    return ts
for use_cbfs in (False,True):
    tag="NY+partial2R"+(" +cbfs" if use_cbfs else "")
    print(f"\n=== SÍNTESE: {tag} (sweep macro-gated, meta aliviada WR40-50/streak≤5/1-5sem) ===")
    c=detect(use_cbfs); report(c,"TOTAL")
    for yr in (2024,2025,2026): report([x for x in c if x["yr"]==yr],f"{yr}")
    byb={};
    for x in c: byb.setdefault(x["block"][:16],[]).append(x)
    pos=sum(1 for b in byb if sum(x["R"] for x in byb[b])>0)
    cap=lambda x:max(-1.0,min(R_CAP,x["R"])); drop=set(sorted(byb,key=lambda b:sum(cap(x) for x in byb[b]),reverse=True)[:2])
    rem=[x for x in c if x["block"][:16] not in drop]; allr=sorted([cap(x) for x in c],reverse=True)
    print(f"   blocos net+ {pos}/{len(byb)} | leave−top2bloc {sum(cap(x) for x in c):+.0f}→{sum(cap(x) for x in rem):+.0f}(n{len(rem)},WR{100*sum(1 for x in rem if x['w'])/max(1,len(rem)):.0f}%) | top5={sum(allr[:5]):+.0f}/{sum(allr):+.0f}R")
