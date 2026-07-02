#!/usr/bin/env python3
"""AFINAR A CAPITULAÇÃO (multi-fatorial + trajetória + validação). Expande amostra: todos os sinais L2 (245) em fundo
profundo (pos<0.35 do Donchian-60 causal). Para cada, features de TRAJETÓRIA causais na entrada: pos, rsi14, drop_atr
(queda do topo-20 em ATR), vel5 (velocidade queda 5b), swept (varreu low-20 anterior), reclaim (fechou>high-1),
atr_z (vol corrente vs média-50). Objetivo DUPLO: separar winner (reversão que corre) de loser (continua a cair).
R = let-run HZ120. Fase 1: amostra+distribuição. Fase 2: separação bruta por feature (win vs loss). custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
from statistics import mean,median
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
def rsi(i,k=14):
    g=l=0
    for j in range(i-k+1,i+1):
        d=C[j]-C[j-1]
        if d>0: g+=d
        else: l-=d
    if g+l==0: return 50
    rs=(g/k)/((l/k) if l>0 else 1e-9);return 100-100/(1+rs)
def letrun(bi,entry,sl):
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
rows=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"])
    if bi<60 or entry-sl<=0: continue
    dmin=min(L[bi-59:bi+1]);dmax=max(H[bi-59:bi+1])
    pos=(entry-dmin)/(dmax-dmin) if dmax>dmin else .5
    if pos>=0.35: continue   # capitulação = fundo profundo
    a=atr(bi)
    top20=max(H[bi-19:bi+1]);drop_atr=(top20-entry)/a
    vel5=(max(H[bi-5:bi])-L[bi])/a
    swept=1 if L[bi]<min(L[bi-20:bi]) else 0
    reclaim=1 if C[bi]>H[bi-1] else 0
    atr_z=a/ (mean(atr(j) for j in range(bi-4,bi+1)) if bi>60 else a)  # proxy simples
    atr50=mean(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(bi-49,bi+1))
    atrz=a/atr50 if atr50>0 else 1
    R=round(letrun(bi,entry,sl)-COST,2)
    rows.append({"bi":bi,"yr":dt.datetime.utcfromtimestamp(T[bi]).year,"date":dt.datetime.utcfromtimestamp(T[bi]).strftime("%Y-%m-%d"),
        "pos":round(pos,3),"rsi":round(rsi(bi),1),"drop_atr":round(drop_atr,2),"vel5":round(vel5,2),
        "swept":swept,"reclaim":reclaim,"atrz":round(atrz,2),"R":R,"win":R>0})
n=len(rows);w=sum(1 for x in rows if x['win']);s=sum(x['R'] for x in rows)
print(f"AMOSTRA capitulação (pos<0.35 Donchian60): N={n} WR={100*w/n:.0f}% sumR={s:+.1f} avgR={s/n:+.2f}")
print(f"  por ano: "+", ".join(f"{y}:N{sum(1 for x in rows if x['yr']==y)}/sum{sum(x['R'] for x in rows if x['yr']==y):+.0f}" for y in sorted(set(x['yr'] for x in rows))))
print(f"\nSEPARAÇÃO por feature (média WINNERS vs LOSERS):")
W=[x for x in rows if x['win']];Lo=[x for x in rows if not x['win']]
for f in ('pos','rsi','drop_atr','vel5','swept','reclaim','atrz'):
    mw=mean(x[f] for x in W);ml=mean(x[f] for x in Lo);sep=mw-ml
    flag=" <-- separa" if abs(sep)>0.15*(abs(mw)+abs(ml)+1e-9)*2 else ""
    print(f"  {f:9} winners={mw:+7.2f}  losers={ml:+7.2f}  Δ={sep:+7.2f}{flag}")
print(f"\n(winners N={len(W)} / losers N={len(Lo)})")
# guardar p/ fase 2
json.dump(rows,open("/tmp/capit_refine_rows.json","w"))
