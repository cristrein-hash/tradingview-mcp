#!/usr/bin/env python3
# LEGACY_PRE_CANON / DO_NOT_USE_AS_CANONICAL — convencao pre-canon (width 12 / label R). PLOTTING_CANON_MASTER_REQUIRED: docs/project_authority/PLOTTING_CANON_MASTER.md e a autoridade para novos plots (R2 2026-07-02).
"""Cris: validação VISUAL da medição fundo/meio/topo. Para cada REGIME BOX (2023+) que contém trades, gerar as 2 linhas
que dividem a box em terços: fundo(<0.34) / meio(0.34-0.67) / topo(>=0.67). Níveis = lo+1/3·amp e lo+2/3·amp.
⚠️ Usa hi/lo FINAL da box (geometria completa) — a medição CAUSAL (phase33) classifica cada entrada pelo running-min/max
até à barra dela, que CONVERGE para estas linhas à medida que a box se forma (fundo≈causal cedo; topo pode formar-se tarde).
Estas linhas são a geometria de referência p/ o Cris ver as regiões. Saída JSON p/ plot via MCP trend_line."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T
segs=json.load(open("/tmp/causal_segments_v10.json"))
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
trades=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi]
    if dt.datetime.utcfromtimestamp(t).year>=2023: trades.append(t)
out=[]
for s in segs:
    if int(s['d0'][:4])<2023: continue
    hi=s['hi'];lo=s['lo'];amp=hi-lo
    if amp<=0: continue
    ntr=sum(1 for t in trades if s['start']<=t<=s['end'])
    if ntr==0: continue
    out.append({"regime":s['regime'],"start":s['start'],"end":s['end'],"d0":s['d0'],"d1":s['d1'],
                "lo":round(lo,2),"hi":round(hi,2),"l1":round(lo+amp/3,2),"l2":round(lo+2*amp/3,2),"ntr":ntr})
json.dump(out,open("/tmp/regime_thirds.json","w"))
print(f"{len(out)} regime-boxes 2023+ com trades (2 linhas cada = {2*len(out)} trend_lines)")
for x in out:
    print(f"  {x['d0']}->{x['d1']} {x['regime']:5} n={x['ntr']:2} | lo {x['lo']} | 1/3 {x['l1']} | 2/3 {x['l2']} | hi {x['hi']}")
