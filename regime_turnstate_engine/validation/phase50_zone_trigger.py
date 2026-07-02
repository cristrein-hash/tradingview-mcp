#!/usr/bin/env python3
"""Cris (V3): ENTRADA = TOQUE da zona (gatilho de zona), não filtro dos sinais L2. Entradas SINTÉTICAS geradas pela zona.
  BULL  -> após rompimento (close>hi_prev), entrar no 1º pullback que TOCA a zona-top [hi_prev-amp/3, hi_prev].
           FALLBACK (Cris): se o bull DESCOLA sem retestar em <=20 barras, entrar na demanda-origem (1ª barra do bull).
  BEAR  -> entrar quando o preço TOCA a zona de capitulação profunda [lo_min_acum180d, +amp/3].
  RANGE -> entrar no 1º toque do terço inferior do range corrente (pos<0.34, running-min/max causal).
SL = fundo-da-zona − 0.5ATR. Exit = let-run HZ120. 1 entrada por regime-box. custo 0.35. Régua L2 preservada (confirmação futura).
Comparar com V2-filtro (17tr). Medir se mantém edge (avgR/DD) ou vira beta."""
import json,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def letrun(bi,entry,sl):
    if entry-sl<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
def entries():
    out=[]
    for idx in range(1,len(segs)):
        s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo']
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<3: continue
        if s['regime']=='BULL':
            niv=prev['hi'];zlo=niv-amp/3
            k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
            if k is None: continue
            rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
            if rj is not None:
                entry=C[rj];sl=zlo-0.5*atr(rj);out.append((rj,entry,sl,'BULL','reteste'))
            else:   # FALLBACK: descolou -> demanda-origem (1ª barra do bull)
                entry=C[i0];sl=min(L[i0:k+1])-0.5*atr(i0);out.append((i0,entry,sl,'BULL','fallback'))
        elif s['regime']=='BEAR':
            zd=bear_deep(idx)
            if not zd: continue
            j=next((j for j in range(i0,i1+1) if L[j]<=zd[1]),None)  # tocou a zona profunda
            if j is not None:
                entry=C[j];sl=zd[0]-0.5*atr(j);out.append((j,entry,sl,'BEAR','capit'))
        else:  # RANGE: 1º toque do terço inferior do range corrente
            for j in range(i0+2,i1+1):
                rmin=min(L[i0:j+1]);rmax=max(H[i0:j+1])
                if rmax>rmin and (C[j]-rmin)/(rmax-rmin)<0.34:
                    entry=C[j];sl=rmin-0.5*atr(j);out.append((j,entry,sl,'RANGE','fundo'));break
    return out
rows=[]
for j,entry,sl,rg,typ in entries():
    R=letrun(j,entry,sl)
    if R is None: continue
    rows.append({"bi":j,"date":dt.datetime.utcfromtimestamp(T[j]).strftime("%Y-%m-%d"),"ym":dt.datetime.utcfromtimestamp(T[j]).strftime("%Y-%m"),
                 "yr":dt.datetime.utcfromtimestamp(T[j]).year,"reg":rg,"typ":typ,"entry":entry,"R":round(R-COST,2)})
rows.sort(key=lambda x:x['bi'])
n=len(rows);w=sum(1 for x in rows if x['R']>0);s=sum(x['R'] for x in rows)
cum=peak=dd=0;st=mx=0
for x in rows:
    cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x['R']<=0 else 0;mx=max(mx,st)
print(f"V3 GATILHO-DE-ZONA — todas as entradas sintéticas (toque da zona)")
print(f"  N={n} WR={100*w/n:.0f}% sumR={s:+.1f} avgR={s/n:+.2f} DD={dd:.1f} streak={mx} big={sum(1 for x in rows if x['R']>=3)}")
print(f"  (comparar: V2-filtro N17 +36R avgR+2.13 DD-4.1 streak3)")
for RG in ('BULL','BEAR','RANGE'):
    g=[x for x in rows if x['reg']==RG]
    if g: print(f"  {RG:5} N={len(g):2} WR={100*sum(1 for x in g if x['R']>0)/len(g):3.0f}% sumR={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+.2f}")
print("  BULL por tipo:")
for typ in ('reteste','fallback'):
    g=[x for x in rows if x['reg']=='BULL' and x['typ']==typ]
    if g: print(f"     {typ:9} N={len(g):2} WR={100*sum(1 for x in g if x['R']>0)/len(g):3.0f}% sumR={sum(x['R'] for x in g):+.1f}")
print("\n### por-ano ###")
by=defaultdict(list)
for x in rows: by[x['yr']].append(x['R'])
for y in sorted(by): print(f"  {y}: N={len(by[y]):2} sumR={sum(by[y]):+6.1f}")
