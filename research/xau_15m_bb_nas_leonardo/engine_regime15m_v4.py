#!/usr/bin/env python3
"""Detector REGIME 15M v4 (Cris 2026-06-28): lapida TODAS as 6 transições (RANGE/BULL/BEAR/RANGE/BULL/BEAR).
Adiciona gatilho de BAIXA por DRAWDOWN PERCENTUAL do topo (robusto a ATR inflado em topo parabólico) — pega o
colapso no dia (cortar long rápido + acionar short rápido). Objetivo de calibração = concordância balanceada com
PENALIDADE forte no LAG de onset por fronteira. Resample diário, causal. vs regime_zones_cris.json."""
import json,itertools,datetime as dt
from pathlib import Path
from collections import Counter
HERE=Path(__file__).parent
Z=json.loads((HERE/"regime_zones_cris.json").read_text())
PRIM=[json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))]
bars={}
for pr in PRIM:
    for b in pr["series"]: bars.setdefault(b["t"],b)
T15=sorted(bars); days={}
for t in T15:
    b=bars[t]; k=t//86400; g=days.setdefault(k,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]
for i in range(1,len(DK)): TR.append(max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])))
def atr(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E20=[ema_at(i,20) for i in range(len(DK))]; E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
def raw_label(i,N,eff_thr,slope_thr,R_thr,dd_thr):
    if i<max(2*N,40): return "RANGE"
    a=atr(i) or 1.0
    slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5
    slope100=(E100[i]-E100[i-10])/a
    trend_up= eff>=eff_thr and slope> slope_thr
    trend_dn= eff>=eff_thr and slope<-slope_thr
    sec_bull= E50[i]>E100[i] and slope100>0
    sec_bear= E50[i]<E100[i] and slope100<0
    contained= eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak30=max(DH[i-30:i+1]); retreat=(peak30-DC[i])/a
    lower_high= max(DH[i-N:i]) < max(DH[i-2*N:i-N])
    below_ema_fall= DC[i]<E50[i] and (E50[i]-E50[i-5])<0
    broke_low= DC[i] < min(DL[i-N:i-2])
    # v4: DRAWDOWN PERCENTUAL do topo (robusto a ATR inflado) — pega colapso pós-parabólico no dia
    pct_dd=(peak30-DC[i])/peak30 if peak30>0 else 0
    fast_dd= pct_dd>=dd_thr and DC[i]<DC[i-2]
    # v3 rápidos
    vel5=(DC[i]-DC[i-5])/a; e20_roll= E20[i]<E50[i] and (E20[i]-E20[i-3])<0
    fast_bear= fast_dd or (retreat>=R_thr and vel5<=-2.5) or (e20_roll and slope<0 and pos<0.5)
    slow_bear= (broke_low and below_ema_fall) or (retreat>=R_thr and lower_high and below_ema_fall) or trend_dn or (sec_bear and pos<0.6 and not contained)
    if fast_bear or slow_bear: return "BEAR"
    if trend_up or (sec_bull and pos>0.55 and not contained): return "BULL"
    return "RANGE"
def classify(N,eff_thr,slope_thr,R_thr,dd_thr,K,Kbear):
    raw=[raw_label(i,N,eff_thr,slope_thr,R_thr,dd_thr) for i in range(len(DK))]
    out=[]; cur="RANGE"; pend=None; pn=0
    for v in raw:
        if v==cur: pend=None; pn=0
        elif v==pend: pn+=1
        else: pend=v; pn=1
        need=Kbear if pend=="BEAR" else K
        if pn>=need: cur=pend; pend=None; pn=0
        out.append(cur)
    return out
def cris_at(t):
    for z in Z:
        if z["t_start"]<=t<=z["t_end"]: return z["type"]
    return None
zmin=min(z["t_start"] for z in Z); zmax=min(max(z["t_end"] for z in Z),T15[-1])
idx=[i for i,k in enumerate(DK) if zmin<=k*86400+43200<=zmax]
truth=[cris_at(DK[i]*86400+43200) for i in idx]
def score(lab):
    per=Counter(); cnt=Counter(); ag=0
    for j,i in enumerate(idx):
        c=truth[j]
        if not c: continue
        cnt[c]+=1
        if lab[i]==c: ag+=1; per[c]+=1
    bal=sum(per[c]/cnt[c] for c in cnt)/len(cnt); glob=ag/sum(cnt.values())
    return glob,bal,{c:round(per[c]/cnt[c],2) for c in cnt}
def onset_lags(lab):
    # para cada fronteira (zona 2..6): dias até o detector bater o NOVO label dentro da zona
    out=[]
    for z in Z[1:]:
        first=None
        for i in idx:
            tt=DK[i]*86400+43200
            if z["t_start"]<=tt<=z["t_end"] and lab[i]==z["type"]: first=tt; break
        lag=round((first-z["t_start"])/86400,1) if first else 60.0  # 60=cap (não bateu na zona)
        out.append((z["type"],z["start"][:10],lag))
    return out
best=None
GRID=itertools.product((10,15,20),(0.30,0.40),(0.10,0.20),(2.0,3.0),(0.04,0.05,0.06,0.07,0.08),(4,5),(2,3))
for N,eff_thr,slope_thr,R_thr,dd_thr,K,Kbear in GRID:
    lab=classify(N,eff_thr,slope_thr,R_thr,dd_thr,K,Kbear); glob,bal,pt=score(lab)
    lags=[l for _,_,l in onset_lags(lab)]; mlag=sum(lags)/len(lags)
    obj=bal-0.012*mlag   # prioriza onset rápido em TODAS as transições
    if best is None or obj>best[0]: best=(obj,glob,bal,pt,mlag,(N,eff_thr,slope_thr,R_thr,dd_thr,K,Kbear),lab)
_,glob,bal,pt,mlag,par,lab=best
print(f"v4 melhor: N={par[0]} eff={par[1]} slope={par[2]} R={par[3]} dd_thr={par[4]} K={par[5]} Kbear={par[6]}")
print(f"GLOBAL={100*glob:.1f}% | BALANCEADA={100*bal:.1f}% | por tipo: {pt} | LAG-onset médio={mlag:.1f}d")
print("LAG onset por fronteira:")
for tp,st,lg in onset_lags(lab): print(f"  -> {tp:<6} {st}  lag {lg}d")
segs=[]
for i in idx:
    l=lab[i]
    if not segs or segs[-1][0]!=l: segs.append([l,DK[i],DK[i]])
    else: segs[-1][2]=DK[i]
def d(k): return dt.datetime.utcfromtimestamp(k*86400).strftime("%Y-%m-%d")
print("\nZONAS v4:")
for l,a,b in segs:
    if (b-a)<2: continue
    print(f"  {l:<6} {d(a)} .. {d(b)} ({b-a}d)")
print("\nSUAS zonas:")
for z in Z: print(f"  {z['type']:<6} {z['start'][:10]} .. {z['end'][:10]} ({z['dias']:.0f}d)")
json.dump({"config":par,"global":glob,"balanced":bal,"per_type":pt,"mean_onset_lag":mlag,
           "onset_lags":onset_lags(lab),"segments":[[l,d(a),d(b)] for l,a,b in segs if (b-a)>=2]},
          open(HERE/"regime15m_v4_result.json","w"),indent=1)
print("\n-> regime15m_v4_result.json")
