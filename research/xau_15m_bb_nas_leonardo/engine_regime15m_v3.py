#!/usr/bin/env python3
"""Detector REGIME 15M v3 (Cris 2026-06-28): lapida o ONSET DE BAIXA. Adiciona gatilhos de baixa RÁPIDOS
(reversão-do-topo com velocidade, cruz EMA20<EMA50 com momentum, quebra de estrutura BOS-down longa) ao v2.
Resample diário, causal. Calibra vs regime_zones_cris.json + reporta LAG do onset BEAR por zona. Sem lookahead."""
import json,itertools,datetime as dt
from pathlib import Path
from collections import Counter
HERE=Path(__file__).parent
Z=json.loads((HERE/"regime_zones_cris.json").read_text())
PRIM=[json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))]
bars={}
for pr in PRIM:
    for b in pr["series"]: bars.setdefault(b["t"],b)
T15=sorted(bars)
days={}
for t in T15:
    b=bars[t]; k=t//86400
    g=days.setdefault(k,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"]})
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
def raw_label(i,N,eff_thr,slope_thr,R_thr,velK):
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
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a
    lower_high= max(DH[i-N:i]) < max(DH[i-2*N:i-N])
    below_ema_fall= DC[i]<E50[i] and (E50[i]-E50[i-5])<0
    broke_low= DC[i] < min(DL[i-N:i-2])
    # --- v3: gatilhos de baixa RÁPIDOS ---
    vel5=(DC[i]-DC[i-5])/a                                   # velocidade 5d em ATR
    e20_roll= E20[i]<E50[i] and (E20[i]-E20[i-3])<0           # cruz/rolagem rápida da média curta
    bos_down= DC[i] < min(DL[i-2*N:i-2])                     # quebra de estrutura mais longa
    fast_bear= (retreat>=R_thr and vel5<=-velK) or (e20_roll and slope<0 and pos<0.5) or (bos_down and DC[i]<E20[i] and slope<0)
    # --- gatilhos lentos (v2) ---
    slow_bear= (broke_low and below_ema_fall) or (retreat>=R_thr and lower_high and below_ema_fall) or trend_dn or (sec_bear and pos<0.6 and not contained)
    if fast_bear or slow_bear: return "BEAR"
    if trend_up or (sec_bull and pos>0.55 and not contained): return "BULL"
    return "RANGE"
def classify(N,eff_thr,slope_thr,R_thr,velK,K,Kbear):
    raw=[raw_label(i,N,eff_thr,slope_thr,R_thr,velK) for i in range(len(DK))]
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
def bear_lag(lab):
    # para cada zona BEAR sua: lag (dias) entre início e 1º dia BEAR do detector dentro da zona
    lags=[]
    for z in Z:
        if z["type"]!="BEAR": continue
        first=None
        for i in idx:
            tt=DK[i]*86400+43200
            if z["t_start"]<=tt<=z["t_end"] and lab[i]=="BEAR": first=tt; break
        lags.append((z["start"][:10], round((first-z["t_start"])/86400,1) if first else 999))
    return lags
best=None
GRID=itertools.product((10,15,20),(0.30,0.40),(0.10,0.20),(2.0,3.0),(2.0,2.5,3.0),(5,),(2,3,5))
for N,eff_thr,slope_thr,R_thr,velK,K,Kbear in GRID:
    lab=classify(N,eff_thr,slope_thr,R_thr,velK,K,Kbear); glob,bal,pt=score(lab)
    # objetivo: balanceada, desempate por concordância BEAR (queremos onset cedo)
    key=(round(bal,4), pt.get("BEAR",0))
    if best is None or key>best[0]: best=(key,glob,bal,pt,(N,eff_thr,slope_thr,R_thr,velK,K,Kbear),lab)
_,glob,bal,pt,par,lab=best
print(f"v3 melhor: N={par[0]} eff={par[1]} slope={par[2]} R={par[3]} velK={par[4]} K={par[5]} Kbear={par[6]}")
print(f"GLOBAL={100*glob:.1f}% | BALANCEADA={100*bal:.1f}% | por tipo: {pt}")
print(f"LAG onset BEAR por zona: {bear_lag(lab)}")
segs=[];
for i in idx:
    l=lab[i]
    if not segs or segs[-1][0]!=l: segs.append([l,DK[i],DK[i]])
    else: segs[-1][2]=DK[i]
def d(k): return dt.datetime.utcfromtimestamp(k*86400).strftime("%Y-%m-%d")
print("\nZONAS v3:")
for l,a,b in segs:
    if (b-a)<2: continue
    print(f"  {l:<6} {d(a)} .. {d(b)} ({b-a}d)")
print("\nSUAS zonas:")
for z in Z: print(f"  {z['type']:<6} {z['start'][:10]} .. {z['end'][:10]} ({z['dias']:.0f}d)")
# comparação direta v2 (sem fast) p/ ver ganho — fixa velK altíssimo desliga fast
labv2=classify(15,0.30,0.20,2.0,99,5,5); _,balv2,ptv2=score(labv2)[1:] if False else (None,*score(labv2)[1:])
print(f"\nv2 (fast OFF) balanceada={100*score(labv2)[1]:.1f}% por tipo {score(labv2)[2]} | lag BEAR {bear_lag(labv2)}")
