#!/usr/bin/env python3
"""Detector REGIME 15M v5 (Cris 2026-06-28): MTF. CAMADA ESTÁVEL diária (v2: RANGE/BULL bons) + OVERRIDE INTRADAY 1H
de BEAR por drawdown% do topo (pega o colapso em HORAS, não no fechamento diário+Kbear). Resolve o lag mantendo
RANGE/BULL. Causal. Calibra override vs regime_zones_cris.json + reporta onset por fronteira. Serve p/ cortar long
15M rápido + acionar short 15M rápido."""
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
# ---- 1H resample ----
H={}
for t in T15:
    b=bars[t]; hk=t//3600; g=H.setdefault(hk,{"c":b["c"],"h":b["h"]}); g["h"]=max(g["h"],b["h"]); g["c"]=b["c"]
HK=sorted(H); HC=[H[k]["c"] for k in HK]; HH=[H[k]["h"] for k in HK]
# ---- diário ----
days={}
for t in T15:
    b=bars[t]; k=t//86400; g=days.setdefault(k,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]
for i in range(1,len(DK)): TR.append(max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])))
def atr(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(arr,i,n):
    c=arr[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(DC,i,50) for i in range(len(DK))]; E100=[ema_at(DC,i,100) for i in range(len(DK))]
# ---- camada estável diária (v2 fixo: RANGE 1.0 / BULL 0.89) ----
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw_stable(i):
    if i<max(2*N,40): return "RANGE"
    a=atr(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; s100=(E100[i]-E100[i-10])/a
    tu=eff>=eff_thr and slope>slope_thr; td=eff>=eff_thr and slope<-slope_thr
    sb=E50[i]>E100[i] and s100>0; se=E50[i]<E100[i] and s100<0
    cont=eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rawS=[raw_stable(i) for i in range(len(DK))]
stable=[]; cur="RANGE"; pend=None; pn=0
for v in rawS:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    need=Kbear if pend=="BEAR" else K
    if pn>=need: cur=pend; pend=None; pn=0
    stable.append(cur)
# ---- OVERRIDE INTRADAY 1H: drawdown% do topo móvel ----
def intraday_bear_days(P,mom,dd_intra):
    """retorna set de day-keys em que houve gatilho intraday de baixa (1H)."""
    trig_h=set()
    for j in range(max(P,mom),len(HK)):
        peak=max(HH[j-P:j+1]); ddp=(peak-HC[j])/peak if peak>0 else 0
        if ddp>=dd_intra and HC[j]<HC[j-mom]: trig_h.add(HK[j])
    dayset=set(hk*3600//86400 for hk in trig_h)
    return dayset
def classify(P,mom,dd_intra,Krec):
    dset=intraday_bear_days(P,mom,dd_intra)
    out=[]; ov=False; quiet=0
    for i in range(len(DK)):
        dk=DK[i]; fired=dk in dset
        if fired: ov=True; quiet=0
        elif ov:
            quiet+=1
            if quiet>=Krec: ov=False
        out.append("BEAR" if (ov or stable[i]=="BEAR") else stable[i])
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
def onset(lab):
    out=[]
    for z in Z[1:]:
        first=None
        for i in idx:
            tt=DK[i]*86400+43200
            if z["t_start"]<=tt<=z["t_end"] and lab[i]==z["type"]: first=tt; break
        out.append((z["type"],z["start"][:10],round((first-z["t_start"])/86400,1) if first else 60.0))
    return out
best=None
for P,mom,dd_intra,Krec in itertools.product((24,36,48,72),(12,24,36),(0.04,0.05,0.06,0.07),(2,3,5)):
    lab=classify(P,mom,dd_intra,Krec); glob,bal,pt=score(lab); mlag=sum(l for _,_,l in onset(lab))/5
    obj=bal-0.010*mlag
    if best is None or obj>best[0]: best=(obj,glob,bal,pt,mlag,(P,mom,dd_intra,Krec),lab)
_,glob,bal,pt,mlag,par,lab=best
g0,b0,pt0=score(stable)
print(f"camada ESTÁVEL (v2) sozinha: GLOBAL={100*g0:.1f}% BAL={100*b0:.1f}% {pt0}")
print(f"\nv5 (estável + override 1H): P={par[0]}h mom={par[1]}h dd_intra={par[2]} Krec={par[3]}")
print(f"GLOBAL={100*glob:.1f}% | BALANCEADA={100*bal:.1f}% | por tipo: {pt} | onset médio={mlag:.1f}d")
print("LAG onset por fronteira:")
for tp,st,lg in onset(lab): print(f"  -> {tp:<6} {st}  lag {lg}d")
segs=[]
for i in idx:
    l=lab[i]
    if not segs or segs[-1][0]!=l: segs.append([l,DK[i],DK[i]])
    else: segs[-1][2]=DK[i]
def d(k): return dt.datetime.utcfromtimestamp(k*86400).strftime("%Y-%m-%d")
print("\nZONAS v5:")
for l,a,b in segs:
    if (b-a)<2: continue
    print(f"  {l:<6} {d(a)} .. {d(b)} ({b-a}d)")
print("\nSUAS zonas:")
for z in Z: print(f"  {z['type']:<6} {z['start'][:10]} .. {z['end'][:10]} ({z['dias']:.0f}d)")
json.dump({"config":par,"global":glob,"balanced":bal,"per_type":pt,"onset":onset(lab),
           "segments":[[l,d(a),d(b)] for l,a,b in segs if (b-a)>=2]},open(HERE/"regime15m_v5_result.json","w"),indent=1)
print("\n-> regime15m_v5_result.json")
