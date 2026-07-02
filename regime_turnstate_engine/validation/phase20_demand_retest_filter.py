#!/usr/bin/env python3
"""TESTA (Cris) o filtro: BLOQUEAR entradas de TOPO do range ATÉ a demanda-original ser testada >=1x.
Tese: topo-TARDIO (já retestou demanda) = virada-bull WINNER; topo-PRECOCE (0 retestes) = chasing LOSER.
CAUSAL: conta retestes da demanda (running-min low, bounce>=1ATR e volta<=0.5ATR) ANTES de cada entrada.
Box RANGE = box do detector (causal_segments_v10.json). box_pos vs box_lo (fundo). let-run pós-custo 0.35.
Objetivo: o filtro salva winners de topo e corta só os precoces? Muda a leitura? Calibração — n pequeno, honesto."""
import json,csv,io,contextlib,sys,statistics as st,datetime as dt
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atr(i,k=14):
    return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
import bisect
Tt=T
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
# pré-computa retestes da demanda por box (causal, running-min)
def tests_before(box,bi):
    i0=bisect.bisect_left(T,box['start']);a=atr(max(20,i0))
    rmin=L[i0];armed=False;count=0
    for j in range(i0+1,bi):     # só barras ANTES da entrada
        rmin=min(rmin,L[j])
        if C[j]>rmin+1.0*a: armed=True          # subiu >=1ATR da demanda (bounce real)
        if armed and L[j]<=rmin+0.5*a: count+=1;armed=False   # voltou <=0.5ATR = reteste
    return count
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t)
    if not box: continue
    entry=float(r["entry"]);R=round(float(r["letrun_struct"])-COST,2)
    i0=bisect.bisect_left(T,box['start'])                 # bounds CAUSAIS (so-far), guardrail do DA
    sofar_lo=min(L[i0:bi+1]);sofar_hi=max(H[i0:bi+1])
    pos=(entry-sofar_lo)/(sofar_hi-sofar_lo) if sofar_hi>sofar_lo else 0.5
    dist_atr=(entry-sofar_lo)/atr(bi)
    tr.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"pos":pos,"dist":dist_atr,"R":R,
               "tests":tests_before(box,bi),"win":R>0})
def agg(g,nm):
    if not g: print(f"  {nm:34} N=0");return
    print(f"  {nm:34} N={len(g):2} WR={100*sum(1 for x in g if x['win'])/len(g):3.0f}% sumR={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+5.2f}")
TOPO=0.5   # topo do range
print("="*92);print("FILTRO: bloquear TOPO (pos>=%.2f) até demanda testada >=1x  (n retestes ANTES da entrada)"%TOPO);print("="*92)
topo=[x for x in tr if x["pos"]>=TOPO]
print(f"\nEntradas de TOPO (pos>={TOPO}): N={len(topo)}")
agg([x for x in topo if x["tests"]==0],"  topo PRECOCE (0 retestes) -> BLOQUEAR?")
agg([x for x in topo if x["tests"]>=1],"  topo TARDIO (>=1 reteste) -> MANTER?")
print("\n-- lista topo (# / data / pos / retestes / R) --")
for x in sorted(topo,key=lambda z:z["bi"]):
    fl="WIN" if x["win"] else ""
    print(f"    {x['date']:10} pos {x['pos']:.2f} tests {x['tests']} R {x['R']:+.2f}  {fl}")
print("\n"+"="*92);print("EFEITO DO FILTRO na base RANGE-box inteira (bloquear topo-precoce)");print("="*92)
block=[x for x in tr if x["pos"]>=TOPO and x["tests"]==0]
keep=[x for x in tr if not (x["pos"]>=TOPO and x["tests"]==0)]
agg(tr,"BASE RANGE-box (todos)")
agg(keep,"COM FILTRO (bloqueia topo-precoce)")
print(f"  bloqueados: {len(block)} | winners entre bloqueados: {sum(1 for x in block if x['win'])} (queremos 0) | sumR bloqueado: {sum(x['R'] for x in block):+.1f}")
print("\n-- os winners de topo que o filtro DEVE preservar (pos>=0.5 & win) --")
for x in sorted([z for z in topo if z["win"]],key=lambda z:z["bi"]):
    print(f"    {x['date']} pos {x['pos']:.2f} tests {x['tests']} R {x['R']:+.2f}  {'PRESERVADO' if x['tests']>=1 else 'PERDIDO pelo filtro!'}")
