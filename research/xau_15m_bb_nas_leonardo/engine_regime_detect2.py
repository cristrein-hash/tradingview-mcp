#!/usr/bin/env python3
"""Detectores causais de regime (RANGE/BULL/BEAR) no RAW 15M vs zonas do Cris (2026-06-28). Sem lookahead.
Testa: D_ema (EMA50 vs EMA200 + slope), D_eff (efficiency-ratio trend/range), D_sm (state-machine histerese estrutural).
Computados em resample DIÁRIO (regime é lento; 15M cru = ruído) as-of cada dia FECHADO; mapeado de volta às barras 15M.
Reporta concordância global + por tipo vs regime_zones_cris.json. Só dados (match com 6 zonas = calibração, não validação)."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
Z=json.loads((HERE/"regime_zones_cris.json").read_text())
PRIM=[json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))]
bars={}
for pr in PRIM:
    for b in pr["series"]: bars.setdefault(b["t"],b)
T15=sorted(bars)
# resample diário (epoch//86400)
days={}
for t in T15:
    b=bars[t]; k=t//86400
    g=days.setdefault(k,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"],"t_end":t+900})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]; g["t_end"]=t+900
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
def ema(vals,n):
    k=2/(n+1); e=vals[0]
    for v in vals[1:]: e=v*k+e*(1-k)
    return e
# label diário as-of (só dias <= i)
def D_ema(i):
    if i<55: return "RANGE"
    c=DC[:i+1]; e50=ema(c[-80:],50); e200=ema(c,min(200,len(c))); e50p=ema(c[-85:-5],50)
    if e50>e200 and e50>e50p: return "BULL"
    if e50<e200 and e50<e50p: return "BEAR"
    return "RANGE"
def D_eff(i,N=20,thr=0.35):
    if i<N: return "RANGE"
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg)))
    eff=abs(net)/path if path>0 else 0
    if eff<thr: return "RANGE"
    return "BULL" if net>0 else "BEAR"
# state-machine: entra BULL ao romper máxima de 10d; BEAR ao perder mínima de 10d; senão mantém; RANGE se sem rompimento há 10d
def D_sm():
    st_=["RANGE"]*len(DK); cur="RANGE"; last_break=0
    for i in range(11,len(DK)):
        hh=max(DH[i-11:i-1]); ll=min(DL[i-11:i-1])
        if DC[i]>hh: cur="BULL"; last_break=i
        elif DC[i]<ll: cur="BEAR"; last_break=i
        elif i-last_break>10 and cur!="RANGE":
            # sem novo rompimento na direção -> se preço dentro do range recente, vira RANGE
            if ll<=DC[i]<=hh: cur="RANGE"
        st_[i]=cur
    return st_
SM=D_sm()
def lab(det,i): return SM[i] if det=="sm" else (D_ema(i) if det=="ema" else D_eff(i))
def cris_at(t):
    for z in Z:
        if z["t_start"]<=t<=z["t_end"]: return z["type"]
    return None
# map cada dia ao label do detector, compara com Cris (no centro do dia)
zmin=min(z["t_start"] for z in Z); zmax=min(max(z["t_end"] for z in Z),T15[-1])
from collections import Counter,defaultdict
print("detector  | concord.global | RANGE | BULL | BEAR  (match% por tipo)")
for det in ("ema","eff","sm"):
    tot=ag=0; per=defaultdict(Counter)
    for i,k in enumerate(DK):
        tmid=k*86400+43200
        if not (zmin<=tmid<=zmax): continue
        c=cris_at(tmid)
        if not c: continue
        m=lab(det,i); tot+=1; per[c][m]+=1
        if m==c: ag+=1
    def mp(c): n=sum(per[c].values()); return f"{100*per[c][c]/n:.0f}%" if n else "-"
    print(f"{det:<9} | {100*ag/tot:>13.1f}% | {mp('RANGE'):>5} | {mp('BULL'):>4} | {mp('BEAR'):>4}")
# por zona individual p/ o melhor (sm)
print("\npor zona (detector state-machine 'sm'):")
for i,z in enumerate(Z,1):
    g=[j for j,k in enumerate(DK) if z['t_start']<=k*86400+43200<=z['t_end']]
    cc=Counter(SM[j] for j in g); n=sum(cc.values())
    if n: print(f"  {i} {z['type']:<6} {z['start'][:10]}..{z['end'][:10]}  "+", ".join(f"{k}{100*v/n:.0f}%" for k,v in cc.most_common())+f"  (match {100*cc[z['type']]/n:.0f}%)")
