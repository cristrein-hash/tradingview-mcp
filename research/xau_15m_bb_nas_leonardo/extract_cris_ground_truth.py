#!/usr/bin/env python3
"""Extrai o GROUND-TRUTH do Cris dos 170 long_position no chart (Cris 2026-06-27):
Cris editou MANUALMENTE o SL (correto) e o profit/exit (potencial maior) de cada posicao.
cris_sl = entry - stopLevel*tick ; cris_exit = entry + profitLevel*tick (offsets em ticks do entry).
Entry: ponto[0].price do chart, EXCETO #138 (Cris moveu sem querer -> usar entry do CSV).
Salva cris_ground_truth.csv: num,entry_t,entry,csv_sl,csv_exit,cris_sl,cris_exit,cris_risk,cris_Rpot."""
import sys,csv,json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
HERE=Path(__file__).parent; TICK=0.01
rows=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
rows.sort(key=lambda r:int(r["entry_t"]))
c=MCPClient(); c.start(); out=[]
try:
    dl=c.call_tool("draw_list")
    lp=[s["id"] for s in dl["shapes"] if s["name"]=="long_position"]
    assert len(lp)==len(rows), f"{len(lp)} vs {len(rows)}"
    for k,r in enumerate(rows):
        pr=c.call_tool("draw_get_properties",{"entity_id":lp[k]})
        e_chart=pr["points"][0]["price"]; P=pr["properties"]
        slt=P.get("stopLevel"); tpt=P.get("profitLevel")
        num=int(r["num"]); csv_entry=float(r["entry"])
        entry = csv_entry if num==138 else e_chart
        cris_sl = round(entry - slt*TICK,2) if slt is not None else None
        cris_exit = round(entry + tpt*TICK,2) if tpt is not None else None
        risk = round(entry-cris_sl,2) if cris_sl else None
        rpot = round((cris_exit-entry)/risk,2) if (cris_exit and risk and risk>0) else None
        out.append({"num":num,"entry_t":int(r["entry_t"]),"entry":round(entry,2),
                    "csv_sl":float(r["sl"]),"csv_exit":float(r["exit"]),"win":r["win"],
                    "cris_sl":cris_sl,"cris_exit":cris_exit,"cris_risk":risk,"cris_Rpot":rpot,
                    "entry_moved_138": (num==138)})
finally:
    try: c.stop()
    except Exception: pass
out.sort(key=lambda x:x["num"])
with open(HERE/"cris_ground_truth.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
# resumo
import statistics as st
chg_sl=[o for o in out if o["cris_sl"] is not None and abs(o["cris_sl"]-o["csv_sl"])>0.05]
chg_ex=[o for o in out if o["cris_exit"] is not None and abs(o["cris_exit"]-o["csv_exit"])>0.05]
rpots=[o["cris_Rpot"] for o in out if o["cris_Rpot"] is not None]
print(f"170 extraidos -> cris_ground_truth.csv")
print(f"SL editado por Cris (vs csv): {len(chg_sl)} trades")
print(f"EXIT editado por Cris (vs csv): {len(chg_ex)} trades")
print(f"cris_Rpot (potencial R com SL+exit do Cris): mediana {st.median(rpots):.2f}  media {st.mean(rpots):.2f}  max {max(rpots):.1f}")
print("amostra:", json.dumps(out[:3],ensure_ascii=False))
