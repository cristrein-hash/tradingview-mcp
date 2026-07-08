#!/usr/bin/env python3
"""Gera a FONTE canonica de plotagem dos 83 trades VALIDOS do N96 (96 - 13 cortados intra-BEAR).
Research-only, NAO toca o chart. Formato = strategy_chosen_trades.csv (num,entry_t,entry,sl,exit,R,win,yr)
p/ plot canonico 15M (plotting-canon: long_position + label #num, GREEN winner/RED loser, width 10).
exit = tgt (winner, hit-3R) | sl (loser). Os 13 cortados = intra-BEAR (BEAR v5 & 1D_px_vs_ema>=0)."""
import csv, sys, datetime as dt
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE
from agent_ctx_kit import ENTRIES
assert len(ENTRIES)==96 and sum(e["out"] for e in ENTRIES)==52, "FAIL-LOUD: N96 nao reproduz"
CUT13={24,25,55,56,57,58,59,66,67,79,83,84,85}   # cortados intra-BEAR (doc USER_APPROVAL)
valid=[e for e in ENTRIES if e["n"] not in CUT13]
assert len(valid)==83, f"esperado 83 validos, obtido {len(valid)}"
rows=[]
for e in sorted(valid, key=lambda x:x["t"]):
    win=e["out"]; entry=e["ent"]; sl=e["sl"]; exit_=e["tgt"] if win==1 else sl
    R=round((exit_-entry)/(entry-sl),2) if (entry-sl)!=0 else 0
    rows.append({"num":e["n"],"entry_t":e["t"],"entry":round(entry,2),"sl":round(sl,2),
                 "exit":round(exit_,2),"R":R,"win":win,"yr":dt.datetime.utcfromtimestamp(e["t"]).year})
out=HERE+"/n96_valid_trades.csv"
with open(out,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["num","entry_t","entry","sl","exit","R","win","yr"]); w.writeheader(); w.writerows(rows)
nw=sum(1 for r in rows if r["win"]==1); nl=len(rows)-nw
print(f"VALIDOS plotaveis: {len(rows)} (winners={nw} losers={nl}) | cortados excluidos: {sorted(CUT13)}")
print(f"saved {out}")
print("nums validos:", [r["num"] for r in rows])
