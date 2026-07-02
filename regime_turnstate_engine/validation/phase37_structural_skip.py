#!/usr/bin/env python3
"""Cris (2026-07-01) — LÓGICA ESTRUTURAL como FILTRO (o maior ganho pode ser o SKIP, não só entry).
Todos os anos. Para cada trade: posição do entry vs o NÍVEL do regime ANTERIOR (causal), condicional à direção:
  BEAR/RANGE -> lo do regime anterior ; BULL -> hi do regime anterior.  dist_signed=(entry-nivel)/ATR (i-1, causal).
Mapear onde vivem BIG-WINNERS (R>=3) / winners / losers por regime × faixa de dist. Deixar o padrão emergir (flexível).
Depois: regra de skip estrutural candidata que MANTÉM winners/big-winners e capa losers em regiões não-adequadas -> book.
Inclui a hipótese do Cris: BEAR entrar SÓ na zona de capitulação (no/abaixo do bottom-do-anterior)."""
import json,csv,io,contextlib,sys,bisect,datetime as dt,statistics as st
from pathlib import Path
from collections import defaultdict
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
def prev_level(bi):
    t=T[bi];idx=None
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: idx=i;break
    if idx is None or idx==0: return None,None
    s=segs[idx];prev=segs[idx-1]
    return (prev['hi'] if s['regime']=='BULL' else prev['lo']), s['regime']
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);niv,rg=prev_level(bi)
    if niv is None: continue
    a=atrb(bi);entry=float(r["entry"]);R=round(float(r["letrun_struct"])-0.35,2)
    tr.append({"bi":bi,"yr":dt.datetime.utcfromtimestamp(T[bi]).year,"reg":rg,"R":R,
               "dist":(entry-niv)/a,"big":R>=3,"win":R>0})
print(f"TRADES totais (todos anos) com nível-anterior: {len(tr)}")
BK=[("<= -2  (abaixo/capit)",lambda d:d<=-2),("-2..-0.5",lambda d:-2<d<=-0.5),
    ("-0.5..0.5 (no nível)",lambda d:-0.5<d<=0.5),("0.5..2",lambda d:0.5<d<=2),("> 2 (bem acima)",lambda d:d>2)]
def line(g):
    if not g: return "N=0"
    n=len(g);w=sum(1 for x in g if x['win']);big=sum(1 for x in g if x['big'])
    return f"N={n:3} WR={100*w/n:3.0f}% avgR={sum(x['R'] for x in g)/n:+5.2f} sumR={sum(x['R'] for x in g):+6.1f} big(>=3R)={big}"
print("\n### onde vivem winners/big-winners/losers: por REGIME × faixa de dist ao nível-anterior ###")
for RG in ('BULL','RANGE','BEAR'):
    grg=[x for x in tr if x['reg']==RG]
    print(f"\n  -- {RG} (N={len(grg)}) [nível = {'hi' if RG=='BULL' else 'lo'} do regime anterior] --")
    for lab,f in BK:
        g=[x for x in grg if f(x['dist'])]
        print(f"     dist {lab:22} {line(g)}")
# regra de skip estrutural candidata (flexível, emergente) — ajustar após ver os buckets
def book(keepfn,lab):
    k=[x for x in tr if keepfn(x)];k.sort(key=lambda z:z['bi'])
    if not k: print(f"  {lab:40} N=0");return
    n=len(k);w=sum(1 for x in k if x['win']);s=sum(x['R'] for x in k);big=sum(1 for x in k if x['big'])
    cum=peak=dd=0;streak=mx=0
    for x in k:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak)
        if x['R']<=0: streak+=1;mx=max(mx,streak)
        else: streak=0
    print(f"  {lab:40} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} DD={dd:6.1f} maxStreak={mx:2} big(>=3R)={big}")
print("\n### BOOK sob regras de SKIP estrutural (mantém winners/big, capa losers em região não-adequada) ###")
book(lambda x:True,"BASE (todos)")
# candidata A: skip BEAR acima do nível (faca), manter BEAR<=nível (capitulação) [ideia do Cris]
book(lambda x: not (x['reg']=='BEAR' and x['dist']>0.5),"skip BEAR acima do bottom-anterior")
# candidata B: skip RANGE bem acima do bottom-anterior (chasing meio/topo)
book(lambda x: not (x['reg']=='RANGE' and x['dist']>2),"skip RANGE dist>2 (chasing)")
# candidata C: combinada A+B
book(lambda x: not ((x['reg']=='BEAR' and x['dist']>0.5) or (x['reg']=='RANGE' and x['dist']>2)),"skip BEAR>0.5 & RANGE>2 (combinada)")
# quantos big-winners existem por regime/região (não matar)
print("\n### BIG-WINNERS (R>=3): onde estão (não capar) ###")
for x in sorted([z for z in tr if z['big']],key=lambda z:-z['R'])[:20]:
    print(f"   {dt.datetime.utcfromtimestamp(T[x['bi']]).strftime('%Y-%m-%d')} {x['reg']:5} dist{x['dist']:+5.1f}ATR R{x['R']:+5.1f}")
