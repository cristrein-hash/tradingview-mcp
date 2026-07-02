#!/usr/bin/env python3
"""Crítica do Cris (válida): "comprar a demanda perde (facas)" é IMPOSSÍVEL num range genuíno — se perde, a demanda
FALHOU = o range QUEBROU (transição p/ bear), logo NÃO é trade intra-range. Medir a tese do fundo só em INTRA-RANGE.
Pego os near-demand (dist<=1.5 ATR da demanda-so-far, o bucket que o DA disse 'perder −6.9R') e separo:
  HELD  = a demanda segurou (não fechou abaixo de floor−0.5ATR nos próximos 20 barras) = intra-range genuíno
  FAILED= a demanda quebrou (breakdown) = NÃO é range, é transição.
Se HELD ganha e FAILED perde → a crítica do Cris está certa e o 'fundo perde' era contaminado por breakdowns.
⚠️ HELD/FAILED é FORWARD (só sabido depois) — isto é CARACTERIZAÇÃO estrutural, não regra live. let-run pós-custo 0.35."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
COST=0.35;K=20;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
near=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t)
    if not box: continue
    i0=bisect.bisect_left(T,box['start']);floor=min(L[i0:bi+1]);a=atr(bi)
    dist=(float(r["entry"])-floor)/a
    if dist>1.5: continue                       # só near-demand (bucket que o DA disse perder)
    R=round(float(r["letrun_struct"])-COST,2)
    # FORWARD: a demanda quebrou (fechou < floor-0.5ATR) nos próximos K barras?
    failed=any(C[j]<floor-0.5*a for j in range(bi+1,min(bi+K+1,n4)))
    near.append({"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"dist":round(dist,2),"R":R,
                 "held":not failed,"win":R>0,"yr":y})
def agg(g,nm):
    if not g: print(f"  {nm:38} N=0");return
    print(f"  {nm:38} N={len(g):2} WR={100*sum(1 for x in g if x['win'])/len(g):3.0f}% sumR={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+5.2f}")
print("="*90);print("NEAR-DEMAND (dist<=1.5 ATR da demanda-so-far) — HELD (intra-range) vs FAILED (breakdown)");print("="*90)
agg(near,"TODOS near-demand (o que o DA mediu)")
agg([x for x in near if x["held"]],"  HELD  = demanda segurou (INTRA-RANGE real)")
agg([x for x in near if not x["held"]],"  FAILED= demanda quebrou (breakdown, NÃO é range)")
print("\n-- lista near-demand 1 a 1 --")
for x in sorted(near,key=lambda z:z["date"]):
    print(f"    {x['date']} dist {x['dist']:.2f}ATR R {x['R']:+.2f}  {'HELD' if x['held'] else 'FAILED-breakdown'}  {'WIN' if x['win'] else ''}")
hd=[x for x in near if x["held"]]
print(f"\n  fração dos near-demand que eram BREAKDOWN (não-range): {sum(1 for x in near if not x['held'])}/{len(near)}")
print(f"  >> se HELD ganha e FAILED perde: a crítica do Cris procede (o 'fundo perde' era contaminado por breakdowns).")
