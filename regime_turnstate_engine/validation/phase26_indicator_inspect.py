#!/usr/bin/env python3
"""Frente INDICADORES — passo 1: INSPECIONAR estrutura de rsi/nas_recent/bubbles_recent no RAW full-bar
(raw_features_2020_2026.jsonl, 9880 bars). Preciso ver o formato antes de escrever extração/teste.
Indexa por bar_idx, imprime os campos de indicador de 3 range-trades (1 winner, 2 losers do caso 2025)."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
RR=D/"repro_recovery"
lines=[json.loads(l) for l in open(RR/"raw_features_2020_2026.jsonl")]
print(f"raw_features: {len(lines)} linhas. chaves:",list(lines[0].keys()))
raw={int(d["ts_epoch"]):d for d in lines}   # index por epoch; junta via T[bi]
def rf(bi): return raw.get(int(T[bi]))       # raw-feature do bar bi
# range trades 2023+
rng=[]
for r in csv.DictReader(open(D/"results/l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    if not any(s['start']<=t<=s['end'] for s in segs): continue
    R=round(float(r["letrun_struct"])-0.35,2)
    rng.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"R":R,"win":R>0})
print(f"\nRANGE-trades 2023+: {len(rng)} | com raw_features: {sum(1 for x in rng if rf(x['bi']))}")
print("\n=== estrutura rsi/nas_recent/bubbles_recent/smc_recent — amostra ===")
for x in rng[:6]:
    d=rf(x["bi"]) or {}
    print(f"\n  {x['date']} R{x['R']:+.1f} {'WIN' if x['win'] else 'loss'} bi={x['bi']}")
    for k in ("rsi","nas_recent","bubbles_recent","smc_recent"):
        if k in d: print(f"    {k} = {json.dumps(d[k])[:320]}")
