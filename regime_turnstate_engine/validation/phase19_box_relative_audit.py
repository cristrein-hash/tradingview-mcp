#!/usr/bin/env python3
"""AUTO-AUDITORIA (Cris apanhou o erro): re-medir posição de cada trade contra o FUNDO-DEMANDA FIXO do BOX que o
REGIME DETECTOR (phase10) criou — NÃO contra o segmento causal-até-à-barra nem o reg[bi] que pisca (bug do phase18).
Cada trade → box que o contém (segmentos plotados do phase10) → box_pos=(entry-box_lo)/(box_hi-box_lo). Lista 1-a-1 por box RANGE.
Mostra lado-a-lado a posição VELHA (phase18, errada) vs NOVA (box-fixo). let-run pós-custo 0.35."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L
segs=json.load(open("/tmp/causal_segments_v10.json"))   # boxes do detector: {start,end,regime,hi,lo}
def box_of(ts):
    cand=[s for s in segs if s['start']<=ts<=s['end']]
    return cand[0] if cand else None
def old_seg_lohi(bi):  # a medição ERRADA do phase18 (causal-até-barra, regime que pisca)
    rg=reg[bi];s=bi
    while s>0 and reg[s-1]==rg: s-=1
    return min(L[s:bi+1]),max(H[s:bi+1])
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    entry=float(r["entry"]);R=round(float(r["letrun_struct"])-COST,2)
    box=box_of(t)
    if not box: continue
    box_pos=(entry-box['lo'])/(box['hi']-box['lo']) if box['hi']>box['lo'] else 0.5
    olo,ohi=old_seg_lohi(bi);old_pos=(entry-olo)/(ohi-olo) if ohi>olo else 0.5
    tr.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"entry":entry,"R":R,
        "box_reg":box['regime'],"box_lo":box['lo'],"box_hi":box['hi'],"box_d0":box['d0'],"box_d1":box['d1'],
        "box_pos":box_pos,"old_pos":old_pos,"reg_bi":reg[bi]})
# lista por BOX RANGE (o que o Cris pediu: trade-a-trade vs fundo dos ranges)
from collections import defaultdict
bybox=defaultdict(list)
for x in tr:
    if x["box_reg"]=="RANGE": bybox[(x["box_d0"],x["box_d1"],x["box_lo"],x["box_hi"])].append(x)
print("="*100);print("TRADE-A-TRADE POR BOX RANGE DO DETECTOR (pos vs FUNDO-DEMANDA FIXO do box)");print("="*100)
for (d0,d1,lo,hi),g in sorted(bybox.items()) if False else sorted(bybox.items()):
    g.sort(key=lambda x:x["bi"]);n=len(g);w=sum(1 for x in g if x["R"]>0)
    print(f"\n### RANGE BOX {d0}→{d1}  demanda-fundo={lo:.0f} topo={hi:.0f}  | N={n} WR={100*w/n:.0f}% sumR={sum(x['R'] for x in g):+.1f}")
    print(f"  {'#':>2} {'data':10} {'entry':>7} {'boxPOS':>6} {'R':>6} {'reg[bi]':>7} {'oldPOS':>6}")
    for i,x in enumerate(g,1):
        fl="WIN" if x['R']>0 else ""
        print(f"  {i:>2} {x['date']:10} {x['entry']:>7.0f} {x['box_pos']:>6.2f} {x['R']:>+6.2f} {x['reg_bi']:>7} {x['old_pos']:>6.2f}  {fl}")
# agregado por faixa de box_pos (a lógica correta)
print("\n"+"="*100);print("AGREGADO — RANGE-box por faixa de box_pos (0=fundo-demanda, 1=topo)");print("="*100)
allr=[x for x in tr if x["box_reg"]=="RANGE"]
import statistics as st
for a,b,nm in [(0.0,0.25,"FUNDO 0-0.25"),(0.25,0.5,"0.25-0.5"),(0.5,0.75,"0.5-0.75"),(0.75,1.01,"TOPO 0.75-1")]:
    gg=[x for x in allr if a<=x["box_pos"]<b]
    if gg: print(f"  {nm:14} N={len(gg):2} WR={100*sum(1 for x in gg if x['R']>0)/len(gg):3.0f}% sumR={sum(x['R'] for x in gg):+6.1f} avgR={sum(x['R'] for x in gg)/len(gg):+5.2f}")
print(f"\n  [check bug] trades RANGE-box com reg[bi] != RANGE (flicker que o phase18 mediu errado): {sum(1 for x in allr if x['reg_bi']!='RANGE')}/{len(allr)}")
