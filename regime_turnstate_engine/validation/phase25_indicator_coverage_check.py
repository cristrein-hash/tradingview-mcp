#!/usr/bin/env python3
"""Frente INDICADORES (Cris nomeou: rsi_bull_div, NAS, bubbles) — antes de testar, verificar COBERTURA.
Os features de indicador só existem em deep_master_matrix_62 (62 dos 276 episódios). As 70 range-trades 2023+
têm quantas com cobertura? Join por datetime (matriz = '%Y-%m-%d %H:%M', régua = bar_idx->T unix).
Se a cobertura for ~0, a frente indicadores NÃO é testável nas range-trades com este ficheiro — reportar honesto."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
mm={}
for r in csv.DictReader(open(D/"l2_bpt_deep_master_matrix_62.csv")):
    mm[r["datetime"]]=r
def keys(t):  # tenta vários formatos
    d=dt.datetime.utcfromtimestamp(t)
    return [d.strftime("%Y-%m-%d %H:%M"),d.strftime("%Y-%m-%d %H:%M:%S"),d.strftime("%Y-%m-%dT%H:%M")]
# span temporal da matriz_62
yrs=sorted({k[:4] for k in mm})
print(f"matrix_62: {len(mm)} linhas | anos cobertos: {yrs}")
rng=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    if not any(s['start']<=t<=s['end'] for s in segs): continue
    hit=next((mm[k] for k in keys(t) if k in mm),None)
    rng.append((dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M"),hit is not None))
n=len(rng);cov=sum(1 for _,h in rng if h)
print(f"RANGE-trades 2023+: {n} | com cobertura de indicador (matrix_62): {cov}")
# quantos dos 276 no total a matriz cobre por ano
mm_yr={}
for k in mm: mm_yr[k[:4]]=mm_yr.get(k[:4],0)+1
print("matrix_62 por ano:",dict(sorted(mm_yr.items())))
