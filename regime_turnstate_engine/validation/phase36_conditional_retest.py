#!/usr/bin/env python3
"""Cris (2026-07-01) — REGRA CONDICIONAL À DIREÇÃO, mapeada objetivamente e CAUSAL:
  regime corrente BEAR  -> mercado retesta o BOTTOM (lo) do regime ANTERIOR
  regime corrente BULL  -> mercado retesta o TOP (hi) do regime ANTERIOR
  (RANGE testado nas duas pontas). Níveis = hi/lo dos regimes JÁ detectados (phase10), conhecidos no fecho de cada
regime = 100% causal (nada desenhado à mão, nada do futuro). Medir: frequência de reteste + distância do extremo ao nível (ATR).
Cruzar com trades L2 (letrun−0.35): entradas perto do nível-condicional ganham?"""
import json,csv,io,contextlib,sys,bisect,datetime as dt,statistics as st
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
def dds(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json"))]
segs.sort(key=lambda s:s['start'])
print("="*96);print("REGRA CONDICIONAL — reteste do nível do REGIME ANTERIOR (causal), por direção do regime corrente");print("="*96)
rows=[]
for i in range(1,len(segs)):
    s=segs[i];prev=segs[i-1]
    i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
    if i1<=i0: continue
    a=atrb(i0)
    if s['regime']=='BEAR': nivel=prev['lo'];lado='bottom_prev'
    elif s['regime']=='BULL': nivel=prev['hi'];lado='top_prev'
    else: nivel=prev['lo'];lado='bottom_prev(RANGE)'
    lowp=min(L[i0:i1+1]);highp=max(H[i0:i1+1])
    # tocou o nível? (o intervalo [low,high] do regime engloba o nível)
    touched=lowp<=nivel<=highp
    # distância do EXTREMO relevante ao nível: bear/range->low, bull->high
    if s['regime']=='BULL': dist=(highp-nivel)/a
    else: dist=(nivel-lowp)/a   # quanto o low do regime passou ABAIXO do nível (>0 = overshoot)
    rows.append({"i":i,"reg":s['regime'],"d0":dds(s['start']),"prev":prev['regime'],"nivel":nivel,
                 "touched":touched,"dist_extremo_atr":round(dist,1),"lado":lado})
    print(f"  {s['d0'] if 'd0' in s else dds(s['start'])} {s['regime']:5} <- prev {prev['regime']:5} | nivel({lado})={nivel:.0f} | retestou={touched} | extremo passou {dist:+.1f}ATR do nivel")
# resumo por regime
print("\n### RESUMO: frequência de reteste + distância mediana do extremo ao nível-do-anterior ###")
for RG in ('BULL','RANGE','BEAR'):
    g=[x for x in rows if x['reg']==RG]
    if not g: continue
    tt=sum(1 for x in g if x['touched']);dd=[x['dist_extremo_atr'] for x in g]
    within1=sum(1 for x in g if abs(x['dist_extremo_atr'])<=1)
    print(f"  {RG:5} N={len(g):2} retestou={tt}/{len(g)} | extremo vs nivel: mediana {st.median(dd):+.1f}ATR, |dist|<=1ATR em {within1}/{len(g)}")
# trades: entry perto do nível-condicional do regime anterior (causal), por regime corrente
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
def nivel_prev(bi):
    t=T[bi]
    idx=None
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: idx=i;break
    if idx is None or idx==0: return None,None,None
    s=segs[idx];prev=segs[idx-1]
    niv=prev['lo'] if s['regime']!='BULL' else prev['hi']
    return niv,s['regime'],atrb(bi)
print("\n### TRADES L2 — entry a <=1 ATR do nível-condicional do regime anterior (causal) ###")
buck=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);y=dt.datetime.utcfromtimestamp(T[bi]).year
    if y<2023: continue
    niv,rg,a=nivel_prev(bi)
    if niv is None: continue
    entry=float(r["entry"]);R=round(float(r["letrun_struct"])-0.35,2)
    near=abs(entry-niv)/a<=1.0
    buck.append({"near":near,"reg":rg,"R":R})
for lab,filt in [("TODOS",lambda x:True),("perto do nivel (<=1ATR)",lambda x:x["near"]),("longe (>1ATR)",lambda x:not x["near"])]:
    g=[x for x in buck if filt(x)]
    if g: print(f"  {lab:26} N={len(g):3} WR={100*sum(1 for x in g if x['R']>0)/len(g):3.0f}% sumR={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+.2f}")
print("  -- perto do nivel, por regime corrente --")
for RG in ('BULL','RANGE','BEAR'):
    g=[x for x in buck if x["near"] and x["reg"]==RG]
    if g: print(f"     {RG:5} N={len(g):2} WR={100*sum(1 for x in g if x['R']>0)/len(g):3.0f}% sumR={sum(x['R'] for x in g):+6.1f}")
