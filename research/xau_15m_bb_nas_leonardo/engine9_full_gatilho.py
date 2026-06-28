#!/usr/bin/env python3
"""ENGINE 9 (Cris 2026-06-28): aplica TODAS as features como confluência de GATILHO sobre a base LONG BULL/RANGE
(knife-gated). Cada feature = 1 voto na direção favorável a fundo. Frontier conv>=k: N/WR/sumR/avgR/DD/por-ano.
Determinístico, régua let-run. Mostra como o N encolhe e as métricas mudam ao empilhar tudo."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
# regime v2
allbars={}
for pr in PRIM.values():
    for b in pr["series"]: allbars.setdefault(b["t"],b)
days={}
for t in sorted(allbars):
    b=allbars[t]; k=t//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw(i):
    if i<max(2*N,40): return "RANGE"
    a=atrd(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; s100=(E100[i]-E100[i-10])/a
    tu=eff>=eff_thr and slope>slope_thr; td=eff>=eff_thr and slope<-slope_thr
    sb=E50[i]>E100[i] and s100>0; se=E50[i]<E100[i] and s100<0
    cont=eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rl=[raw(i) for i in range(len(DK))]; reg=[]; cur="RANGE"; pend=None; pn=0
for v in rl:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    if pn>=(Kbear if pend=="BEAR" else K): cur=pend; pend=None; pn=0
    reg.append(cur)
DAYREG={DK[i]:reg[i] for i in range(len(DK))}
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
def knife_v2(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
base=[]
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    R=letrun(s,cj,s[cj]["c"],min(x["l"] for x in s[p:cj+1])-0.1*atr,atr)
    if R is None: continue
    r["R"]=R; base.append(r)
print(f"base LONG BULL/RANGE (knife-gated)={len(base)}")
# medianas para thresholds contínuos
def med(k):
    v=[f(r,k) for r in base if f(r,k) is not None]; return st.median(v) if v else 0
M={k:med(k) for k in ("downleg_eff","pullback_depth","legpos90","legpos60","reclaim_atr","dist_demand_atr","clean_sky_atr","h4n_dist_demand_atr","h1n_dist_demand_atr","h4n_clean_sky_atr")}
# PREDICADOS (favorável a fundo), por família
def preds(r):
    return {
      # perna/posição
      "downleg_grind": f(r,"downleg_eff",1)<M["downleg_eff"],
      "pullback_raso": f(r,"pullback_depth",1)<M["pullback_depth"],
      "legpos90_alto": f(r,"legpos90",0)>=M["legpos90"],
      "micro_hl": f(r,"micro_hl",0)==1,
      # rsi (tese oversold do Cris)
      "rsi_low<40": f(r,"rsi_low",50)<40,
      "rsi_min8<35": f(r,"rsi_min8",50)<35,
      "reclaim_forte": f(r,"reclaim_atr",0)>=M["reclaim_atr"],
      # volatilidade
      "atr_baixo": f(r,"atr_regime",1)<1.0,
      "coiled_spring": f(r,"atr_compression_pre",0)>1.0,
      # OB/demanda
      "in_demand": f(r,"in_demand",0)==1,
      "demand_reclaim": f(r,"demand_reclaim",0)==1,
      "perto_demanda": f(r,"dist_demand_atr",99)<M["dist_demand_atr"],
      "clean_sky": f(r,"clean_sky_atr",0)>=M["clean_sky_atr"],
      "sem_supply_acima": f(r,"n_supply_overhead",9)<=1,
      # fluxo
      "sell_bubble_absorb": f(r,"sell_bub_w",0)>=2,
      "sem_buy_exaustao": f(r,"buy_bub_w",9)<4,
      "nas_long": f(r,"nas_long_16",0)>=1,
      # multi-TF nativo
      "h4_up": f(r,"h4n_trend",0)==1,
      "h1d_up": f(r,"h1n_trend",0)==1,
      "h4_demanda": f(r,"h4n_in_demand",0)==1,
    }
NP=20
for r in base: r["conv"]=sum(1 for v in preds(r).values() if v)
def metr(sel):
    n=len(sel)
    if not n: return None
    rs=[r["R"] for r in sel]; sm=sum(rs); w=sum(1 for x in rs if x>0)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(r["R"] for r in sel if r["yr"]==y),1) for y in (2024,2025,2026)}
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),py
print(f"\nFRONTIER (empilhar as {NP} lentes; base BULL/RANGE knife-gated):")
print(f"{'conv>=':<7}{'N':>5}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>8}  yr24/25/26")
for k in range(0,NP+1):
    sel=[r for r in base if r["conv"]>=k]
    m=metr(sel)
    if not m: continue
    n,wr,sm,avg,dd,py=m
    flag=" <==50-75" if 50<=n<=75 else (" <==100-200" if 100<=n<=200 else "")
    print(f"{k:<7}{n:>5}{wr:>6}{sm:>8}{avg:>7}{dd:>8}  {py[2024]}/{py[2025]}/{py[2026]}{flag}")
