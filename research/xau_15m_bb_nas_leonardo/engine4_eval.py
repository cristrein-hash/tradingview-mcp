#!/usr/bin/env python3
"""ENGINE 4 (contextual) — evaluator DETERMINÍSTICO das propostas dos 3 leitores (Cris 2026-06-28). Fonte única de R.
Alvo = RISK-SHAPING do universo lucrativo (subir avgR, cair DD −125, manter MON+FORTE, fewer-better) — NÃO isolar label.
Mede cada regra: n, recall_MF, WR, sumR, avgR, maxDD, por-ano avgR, null(random same-n), leave-block. RAW-causal."""
import json,statistics as st,random,bisect
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
H4=json.loads((HERE/"htf_primitives"/"htf_4H.primitives.json").read_text())
H4D=sorted([z for z in H4["zones"] if "DEMAND" in str(z.get("text","")).upper() and z.get("born_t") and z.get("high") is not None],key=lambda z:z["born_t"])
H4Db=[z["born_t"] for z in H4D]
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
# enriquece cada row com R + c + q4_fresh (nearest 4H demand abaixo, idade em 4H-bars)
def prep():
    for r in ROWS:
        pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
        p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"]); r["R"]=None; r["q4_fresh"]=999
        if p is None or cj is None or cj+2>=len(s): continue
        atr=s[p]["atr"] or s[cj]["atr"]
        if not atr: continue
        c=s[cj]["c"]; entry=c; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr
        r["R"]=letrun(s,cj,entry,sl,atr)
        # q4_fresh: nearest 4H DEMAND com high<=c+0.3atr e born<=cj_t, idade (cj_t-born)/14400
        best=None
        hi=bisect.bisect_right(H4Db,r["cj_t"])
        for z in H4D[:hi]:
            if z["high"]<=c+0.3*atr:
                d=c-z["high"]
                if best is None or d<best[0]: best=(d,z["born_t"])
        if best: r["q4_fresh"]=round((r["cj_t"]-best[1])/14400,1)
prep()
G=[r for r in ROWS if r["R"] is not None]
MFtot=sum(r["is_monforte"] for r in G)
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
# ---- regras dos leitores ----
def knife_v2(r):  # FLOW: remover se True
    a = f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b = (f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
         and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
def V_absorb(r): return f(r,"sell_bub_w",0)>=8 and f(r,"sell_bub_w",0)>f(r,"buy_bub_w",0)
def V_nas(r): return f(r,"nas_long_16",0)>=2 or f(r,"h4n_nas_long_rec",0)>=1
def V_snap(r): return f(r,"reclaim_atr",0)>=2.0
def V_capit(r): return f(r,"rsi_min8",50)<30 and f(r,"atr_regime",1)>1.3 and f(r,"swept_prior_low",0)==1
def voices(r): return sum([V_absorb(r),V_nas(r),V_snap(r),V_capit(r)])
RULES={
 "TAKE-ALL": lambda r: True,
 "M1 anti-knife(macro)": lambda r: not (f(r,"h4n_trend")==-1 and f(r,"h4n_in_demand")==0),
 "KNIFEKILL_v2(flow)": lambda r: not knife_v2(r),
 "M2 bullpullback+demand": lambda r: f(r,"h1n_trend")==1 and f(r,"h4n_in_demand")==1 and f(r,"h4n_dist_demand_atr",9)<=0.3,
 "V_capit_done": lambda r: V_capit(r) and V_snap(r),
 "V_absorb_snap": lambda r: V_absorb(r) and V_snap(r),
 "voices>=2": lambda r: voices(r)>=2,
 "voices>=3": lambda r: voices(r)>=3,
 "R_ROOM sky>=1.5": lambda r: f(r,"h4n_clean_sky_atr",0)>=1.5,
 "R_CONV fresh+room": lambda r: f(r,"q4_fresh",999)<=30 and f(r,"h4n_clean_sky_atr",0)>=1.5,
 "KK + voices>=2": lambda r: (not knife_v2(r)) and voices(r)>=2,
 "KK + V_capit_done": lambda r: (not knife_v2(r)) and V_capit(r) and V_snap(r),
 "KK + R_ROOM": lambda r: (not knife_v2(r)) and f(r,"h4n_clean_sky_atr",0)>=1.5,
}
def metr(sel):
    rs=[r["R"] for r in sel]; n=len(rs)
    if not n: return None
    sm=sum(rs); w=sum(1 for x in rs if x>0); eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mf=sum(r["is_monforte"] for r in sel)
    py={y:round(st.mean([r["R"] for r in sel if r["yr"]==y]),3) if [r for r in sel if r["yr"]==y] else None for y in (2024,2025,2026)}
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),mf,round(mf/MFtot,2),py
random.seed(11)
print(f"universo R-ok={len(G)} | MON+FORTE={MFtot} | baseline take-all abaixo")
print(f"{'regra':<24}{'n':>5}{'rec':>5}{'WR':>6}{'sumR':>7}{'avgR':>7}{'DD':>7}{'null_p':>7}  yr24/25/26")
for name,fn in RULES.items():
    sel=[r for r in G if fn(r)]; m=metr(sel)
    if not m: continue
    n,wr,sm,avg,dd,mf,rec,py=m
    # null: random same-n avgR >= obs
    if name=="TAKE-ALL": pv="-"
    else:
        cnt=0
        for _ in range(400):
            samp=random.sample(G,min(n,len(G))); a=st.mean([r["R"] for r in samp]); cnt+= (a>=avg)
        pv=f"{cnt/400:.3f}"
    pys=f"{py[2024]}/{py[2025]}/{py[2026]}"
    print(f"{name:<24}{n:>5}{rec:>5}{wr:>6}{sm:>7}{avg:>7}{dd:>7}{pv:>7}  {pys}")
