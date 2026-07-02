#!/usr/bin/env python3
"""Gera dados de PLOT CANÓNICO (long_position + label R) dos trades da BASE L2/BPT (universo 276 + SL_CONTEXT + let-run)
a partir de 2023. Convenção canónica (alert-bridge/draw_xau_4h_trades.py): long_position com stopLevel/profitLevel em
TICKS (mintick 0.01), alvo +3R, label = R realizado (letrun_struct). Saída JSON p/ plotagem via MCP."""
import csv,json,datetime as dt
from pathlib import Path
REV=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
B=[json.loads(l) for l in open(REV/"raw_4h_ohlc.jsonl")];B.sort(key=lambda x:x["t"]);T=[b["t"] for b in B]
R=REV/"XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"
MT=0.01;out=[]
for r in csv.DictReader(open(R)):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    entry=float(r["entry"]);sl=float(r["sl"]);risk=entry-sl;Rr=float(r["letrun_struct"])
    if risk<=0: continue
    target=entry+3*risk
    out.append({"bar":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
        "entry_time":t,"exit_time":t+12*14400,"entry":round(entry,2),"target":round(target,2),
        "stopLevel":int(round((entry-sl)/MT)),"profitLevel":int(round((target-entry)/MT)),"R":round(Rr,1)})
json.dump(out,open("/tmp/l2_base_trades_2023.json","w"))
w=sum(1 for x in out if x["R"]>0)
print(f"trades 2023+: {len(out)} (win {w} / loss {len(out)-w})")
print("por ano:", {y:sum(1 for x in out if x['date'][:4]==str(y)) for y in (2023,2024,2025,2026)})
print("amostra:", json.dumps(out[0]))
