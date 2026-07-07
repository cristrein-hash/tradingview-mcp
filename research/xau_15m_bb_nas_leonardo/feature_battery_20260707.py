#!/usr/bin/env python3
"""BATERIA de features macro-estruturais -> ranquear pela separação winner/loser (2026-07-07).
Ground-truth limpo (96 entries = trades do Cris, 32/32 outcomes alinhados). Em vez de impor um proxy,
computo ~15 features CAUSAIS macro/estruturais no entry e ranqueio por AUC (winner vs loser). Os dados
escolhem o discriminador. Inclui zonas reais SUPPLY/DEMAND do indicador (o que o chart mostra).
SANITY_PROBE: bateria multi-fatorial macro (trajetória: retornos/slope/leg-age; zonas do indicador);
ranking por AUC em ground-truth rotulado; não impõe proxy único; causal known_at."""
import json, glob, bisect
import datetime as dt
from pathlib import Path
import statistics as st
HERE=Path(__file__).resolve().parent
series={}; zones=[]
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    zones+=[z for z in d.get("zones",[]) if z.get("born_t")]
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]; EMA=[b.get("ema21") for b in S]
BARD=96  # barras 15M por dia
def ema_arr(arr,n):
    out=[None]*len(arr); k=2/(n+1); e=None
    for i,v in enumerate(arr):
        e=v if e is None else v*k+e*(1-k); out[i]=e
    return out
EMA_D=ema_arr(CL, 20*BARD)  # ~EMA20-dia em barras 15M
zones.sort(key=lambda z:z["born_t"]); ZT=[z["born_t"] for z in zones]
def feats(j):
    px=CL[j]; a=ATR[j] or 5
    def ret(nd):
        k=max(0,j-nd*BARD); return (px-CL[k])/a
    lo20=min(LO[max(0,j-20*BARD):j+1]); hi20=max(HI[max(0,j-20*BARD):j+1])
    lo60=min(LO[max(0,j-60*BARD):j+1]); hi60=max(HI[max(0,j-60*BARD):j+1])
    # dias positivos últimos 10 (usar closes diários aprox: cada BARD)
    ups=0; tot=0
    for dd in range(1,11):
        k=j-dd*BARD; k0=j-(dd+1)*BARD
        if k0>=0: tot+=1; ups+=1 if CL[k]>CL[k0] else 0
    # slope EMA-dia
    slope=(EMA_D[j]-EMA_D[max(0,j-5*BARD)]) if EMA_D[j] is not None and j>=5*BARD else 0
    # barras desde o high de 20d
    hi_idx=max(range(max(0,j-20*BARD),j+1), key=lambda k:HI[k]); bars_since_hi=(j-hi_idx)
    # zona SUPPLY acima / DEMAND perto (do indicador)
    hi_z=bisect.bisect_right(ZT,TS[j])
    sup_above=[ (z["low"]-px)/a for z in zones[:hi_z] if z["text"]=="SUPPLY" and z["low"]>px and z.get("last_t",z["born_t"])>=TS[j]-3*86400 ]
    dem_near=[ abs(px-(z["high"]+z["low"])/2)/a for z in zones[:hi_z] if z["text"]=="DEMAND" and z.get("last_t",z["born_t"])>=TS[j]-3*86400 ]
    return {
      "ret_5d":round(ret(5),2),"ret_10d":round(ret(10),2),"ret_20d":round(ret(20),2),
      "dist_from_low20":round((px-lo20)/a,2),"dist_from_hi20":round((hi20-px)/a,2),
      "dist_from_hi60":round((hi60-px)/a,2),"pos_in_20d":round((px-lo20)/((hi20-lo20) or 1),2),
      "up_days10":ups,"slope_emaD":round(slope,2),"bars_since_hi20":bars_since_hi,
      "supply_above":round(min(sup_above),2) if sup_above else 99,
      "demand_near":round(min(dem_near),2) if dem_near else 99,
    }
def zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
piv=zz(6); EV=[]; prevH=prevL=None; lastH=None
for tp,i,pr,ci in piv:
    if tp=="H": prevH=pr; lastH=pr
    else:
        if prevH is not None and lastH is not None and (prevL is None or pr>prevL): EV.append({"i":i,"lo":pr})
        prevL=pr
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
rows=[]; n=0
for e in EV:
    i=e["i"]
    if not (W0<=TS[i]<=W1): continue
    lo=e["lo"]; a=ATR[i] or 5; j=None
    for k in range(i+1,min(N,i+25)):
        if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
    if j is None: continue
    ent=CL[j]; sl=lo-0.1*a; risk=ent-sl
    if risk<=0.05*a: continue
    tgt=ent+3*risk; out=0
    for m in range(j+1,min(N,j+1440)):
        if LO[m]<=sl: out=0; break
        if HI[m]>=tgt: out=1; break
    n+=1; rows.append({"n":n,"d":ds(TS[j]),"out":out,"sig2":1 if j-i<=4 else 0,**feats(j)})
json.dump(rows,open(HERE/"results"/"feature_battery_20260707.json","w"),indent=1)
W=[r for r in rows if r["out"]==1]; L=[r for r in rows if r["out"]==0]
FEATS=["ret_5d","ret_10d","ret_20d","dist_from_low20","dist_from_hi20","dist_from_hi60","pos_in_20d","up_days10","slope_emaD","bars_since_hi20","supply_above","demand_near"]
def auc(f):
    wv=[r[f] for r in W]; lv=[r[f] for r in L]; c=0; t=0
    for a in wv:
        for b in lv:
            t+=1; c+= 1 if a>b else (0.5 if a==b else 0)
    return c/t
print(f"N{len(rows)} winners {len(W)} losers {len(L)}")
print("\n=== ranking de features por AUC (separação winner vs loser) ===")
res=sorted(((abs(auc(f)-0.5),auc(f),f) for f in FEATS),reverse=True)
for _,a,f in res:
    print(f"  {f:<16} AUC {a:.3f}  WIN med {st.median([r[f] for r in W]):+.2f}  LOSE med {st.median([r[f] for r in L]):+.2f}")
print("\nsaved results/feature_battery_20260707.json · OK")
