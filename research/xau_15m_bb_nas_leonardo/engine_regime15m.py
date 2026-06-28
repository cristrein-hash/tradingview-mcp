#!/usr/bin/env python3
"""Detector de REGIME 15M específico (Cris 2026-06-28): state-machine multi-fator + histerese, resample diário do RAW 15M,
CAUSAL (só dias <=i). Calibra thresholds contra regime_zones_cris.json (n=6, calibração). Reporta concordância global +
por tipo + erro de datas de transição + zonas geradas lado a lado. Sem lookahead."""
import json,bisect,itertools,datetime as dt
from pathlib import Path
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
# ATR diário
TR=[0.0]
for i in range(1,len(DK)): TR.append(max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])))
def atr(i,n=14):
    a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
# pré-computa emas/slopes
E20=[ema_at(i,20) for i in range(len(DK))]; E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
def raw_label(i,N,eff_thr,slope_thr,R_thr):
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
    # --- ONSET DE BAIXA (estrutural, causal) ---
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a
    lower_high= max(DH[i-N:i]) < max(DH[i-2*N:i-N])
    below_ema_fall= DC[i]<E50[i] and (E50[i]-E50[i-5])<0
    broke_low= DC[i] < min(DL[i-N:i-2])
    bear_struct= (broke_low and below_ema_fall) or (retreat>=R_thr and lower_high and below_ema_fall) or (trend_dn) or (sec_bear and pos<0.6 and not contained)
    if bear_struct: return "BEAR"
    if trend_up or (sec_bull and pos>0.55 and not contained): return "BULL"
    return "RANGE"
def classify(N,eff_thr,slope_thr,R_thr,K,Kbear):
    raw=[raw_label(i,N,eff_thr,slope_thr,R_thr) for i in range(len(DK))]
    out=[]; cur="RANGE"; pend=None; pn=0
    for v in raw:
        if v==cur: pend=None; pn=0
        elif v==pend: pn+=1
        else: pend=v; pn=1
        need=Kbear if pend=="BEAR" else K   # BEAR confirma mais rápido (assimétrico)
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
from collections import Counter
def score(lab):
    per=Counter(); cnt=Counter(); ag=0
    for j,i in enumerate(idx):
        c=truth[j]
        if not c: continue
        cnt[c]+=1
        if lab[i]==c: ag+=1; per[c]+=1
    bal=sum(per[c]/cnt[c] for c in cnt)/len(cnt)  # média dos matches por tipo (balanceado)
    glob=ag/sum(cnt.values())
    return glob,bal,{c:round(per[c]/cnt[c],2) for c in cnt}
best=None
for N,eff_thr,slope_thr,R_thr,K,Kbear in itertools.product((10,15,20),(0.30,0.40,0.50),(0.05,0.10,0.20),(2.0,3.0,4.0),(5,8),(2,3,5)):
    lab=classify(N,eff_thr,slope_thr,R_thr,K,Kbear); glob,bal,pt=score(lab)
    if best is None or bal>best[0]: best=(bal,glob,pt,(N,eff_thr,slope_thr,R_thr,K,Kbear),lab)
bal,glob,pt,par,lab=best
print(f"melhor config (balanceada): N={par[0]} eff_thr={par[1]} slope_thr={par[2]} R_thr={par[3]} K={par[4]} Kbear={par[5]}")
print(f"concordância GLOBAL={100*glob:.1f}% | BALANCEADA(média por tipo)={100*bal:.1f}% | por tipo: {pt}")
# zonas geradas (merge dias consecutivos mesmo label) na cobertura
segs=[]; cur=None
for i in idx:
    l=lab[i]
    if not segs or segs[-1][0]!=l: segs.append([l,DK[i],DK[i]])
    else: segs[-1][2]=DK[i]
def d(k): return dt.datetime.utcfromtimestamp(k*86400).strftime("%Y-%m-%d")
print(f"\nZONAS GERADAS pelo detector (cobertura {d(DK[idx[0]])}..):")
for l,a,b in segs:
    if (b-a) < 2: continue  # dias (DK ja e dia-numero)
    print(f"  {l:<6} {d(a)} .. {d(b)}  ({b-a}d)")
print(f"\nSUAS zonas (referência):")
for i,z in enumerate(Z,1): print(f"  {z['type']:<6} {z['start'][:10]} .. {z['end'][:10]}  ({z['dias']:.0f}d)")
# erro de datas de transição: para cada fronteira sua, menor distância a uma transição gerada
gen_tr=[a*86400 for l,a,b in segs[1:]]  # epoch dos inícios
err=[]
for z in Z[1:]:
    diffs=[abs(z["t_start"]-g)/86400 for g in gen_tr]
    if diffs: err.append(min(diffs))
print(f"\nerro de datas de transição (dias) vs suas 5 fronteiras internas: "+", ".join(f"{e:.0f}" for e in err)+f" | médio {sum(err)/len(err):.1f}d" if err else "")
json.dump({"config":par,"global":glob,"balanced":bal,"per_type":pt,"segments":[[l,d(a),d(b)] for l,a,b in segs if (b-a)>=2]},open(HERE/"regime15m_result.json","w"),indent=1)
print("\n-> regime15m_result.json")
