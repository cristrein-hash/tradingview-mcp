#!/usr/bin/env python3
"""ENGINE 5 — evaluator determinístico da síntese transversal (Cris 2026-06-28). Fonte única.
Testa a CONVERGÊNCIA "absorção-quieta+spring" (predicados da síntese) no UNIVERSO CHEIO (4502), não no curado 61/144.
Mede R REALIZADO (let-run) + recall MON+FORTE + precisão + per-ano + leave-block + null-of-max + concentração.
Predicados (as-of, dos campos de entry_candidates_htf): P1 atr_regime<1.0 · P2 h1n_trend==1 (1D up) · P3 sell_bub_w<=2 ·
P4 downleg_eff<0.30 · P5 h1_pos>=0.10 · P6 killzone==0. (drp omitido: ~trivial). RAW-causal."""
import json,statistics as st,random
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
    # predicados
    P=[f(r,"atr_regime",1)<1.0, f(r,"h1n_trend",0)==1, f(r,"sell_bub_w",9)<=2,
       f(r,"downleg_eff",1)<0.30, f(r,"h1_pos",0)>=0.10, f(r,"killzone",1)==0]
    r["conv"]=sum(1 for x in P if x); r["P"]=P
G=[r for r in ROWS if r["R"] is not None]
MF=sum(r["is_monforte"] for r in G); base=MF/len(G); baseavg=st.mean([r["R"] for r in G])
def metr(sel):
    n=len(sel)
    if not n: return None
    rs=[r["R"] for r in sel]; sm=sum(rs); w=sum(1 for x in rs if x>0); mf=sum(r["is_monforte"] for r in sel)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(st.mean([r["R"] for r in sel if r["yr"]==y]),3) if [r for r in sel if r["yr"]==y] else None for y in (2024,2025,2026)}
    top5=sorted(rs,reverse=True)[:5]; conc=round(sum(top5)/sm,2) if sm>0 else None
    return dict(n=n,mf=mf,recall=round(mf/MF,2),prec=round(mf/n,3),precLift=round((mf/n)/base,1),
                WR=round(100*w/n,1),sumR=round(sm,1),avgR=round(sm/n,3),DD=round(dd,1),py=py,conc=conc)
print(f"universo R-ok={len(G)} | MON+FORTE={MF} (base {100*base:.2f}%) | base avgR={baseavg:.3f}")
print(f"\n=== CONVERGÊNCIA (R REALIZADO no universo cheio) ===")
print(f"{'regra':<14}{'n':>5}{'rec':>5}{'precLift':>9}{'WR':>6}{'sumR':>7}{'avgR':>7}{'DD':>7}{'conc':>6}  yr24/25/26")
print(f"{'TAKE-ALL':<14}{len(G):>5}{1.0:>5}{1.0:>9}{round(100*sum(1 for r in G if r['R']>0)/len(G),1):>6}{round(sum(r['R'] for r in G),1):>7}{baseavg:>7.3f}{'':>7}{'':>6}  {st.mean([r['R'] for r in G if r['yr']==2024]):.2f}/{st.mean([r['R'] for r in G if r['yr']==2025]):.2f}/{st.mean([r['R'] for r in G if r['yr']==2026]):.2f}")
rules={f"conv>={k}":(lambda r,k=k:r["conv"]>=k) for k in (3,4,5,6)}
rules["R1 onset(P1&P2&P5)"]=lambda r:r["P"][0] and r["P"][1] and r["P"][4]
rules["R3 absorb(P1&P3&P4)"]=lambda r:r["P"][0] and r["P"][2] and r["P"][3]
random.seed(13)
allrules=list(rules.items())
def nullmax(n_list):  # null-of-max sobre as regras: shuffle R, recomputa avgR de cada regra, pega max
    sizes=[len([r for r in G if fn(r)]) for _,fn in allrules]
    obs=[st.mean([r["R"] for r in G if fn(r)]) if any(fn(r) for r in G) else -9 for _,fn in allrules]
    Rs=[r["R"] for r in G]
    cnt=[0]*len(allrules)
    for _ in range(400):
        random.shuffle(Rs)
        # reatribui R embaralhado
        for r,x in zip(G,Rs): r["_sh"]=x
        sh=[st.mean([r["_sh"] for r in G if fn(r)]) if any(fn(r) for r in G) else -9 for _,fn in allrules]
        mx=max(sh)
        for j in range(len(allrules)):
            if mx>=obs[j]: cnt[j]+=1
    return [c/400 for c in cnt]
nm=nullmax(None)
for (name,fn),pmax in zip(allrules,nm):
    m=metr([r for r in G if fn(r)])
    if not m: continue
    py=m["py"]
    print(f"{name:<14}{m['n']:>5}{m['recall']:>5}{m['precLift']:>9}{m['WR']:>6}{m['sumR']:>7}{m['avgR']:>7}{m['DD']:>7}{str(m['conc']):>6}  {py[2024]}/{py[2025]}/{py[2026]}  nullmax_p={pmax:.3f}")
