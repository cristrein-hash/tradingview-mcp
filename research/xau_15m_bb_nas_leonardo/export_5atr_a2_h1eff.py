#!/usr/bin/env python3
"""Exporta os 211 trades da base A2 5ATR + filtro anti-range h1_eff>=0.15 (APROVADO Cris 2026-06-27).
SL=A (flush-0.1ATR), EXIT let-run. exit price = entry + R*(entry-sl). dedup uma-posicao.
-> strategy_5atr_a2_h1eff_trades.csv (num,entry_t,entry,sl,exit,R,win,yr) p/ plotagem canonica. RAW-causal."""
import json, csv
from pathlib import Path
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines()]
kept=[c for c in ROWS if c["h1_eff"] is not None and c["h1_eff"]>=0.15]
# dedup uma-posicao por bloco (cj/exi)
byblk={}
for c in kept: byblk.setdefault(c["block"],[]).append(c)
taken=[]
for blk,cs in byblk.items():
    cs.sort(key=lambda x:x["cj"]); busy=-10**9
    for c in cs:
        if c["cj"]<=busy: continue
        busy=c["exi"]; taken.append(c)
taken.sort(key=lambda x:x["t"])
for n,c in enumerate(taken,1): c["num"]=n
with open(HERE/"strategy_5atr_a2_h1eff_trades.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["num","entry_t","entry","sl","exit","R","win","yr"])
    for c in taken:
        risk=c["entry"]-c["sl"]; exit_px=c["entry"]+c["R"]*risk
        w.writerow([c["num"],c["t"],round(c["entry"],2),round(c["sl"],2),round(exit_px,2),round(c["R"],2),c["win"],c["yr"]])
n=len(taken); wn=sum(c["win"] for c in taken)
print(f"strategy_5atr_a2_h1eff_trades.csv: N={n} winners={wn} losers={n-wn} WR={100*wn/n:.1f}% sumR={sum(c['R'] for c in taken):+.1f}")
