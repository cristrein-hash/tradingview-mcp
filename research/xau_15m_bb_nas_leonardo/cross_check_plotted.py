#!/usr/bin/env python3
"""Cross-check: entry/SL/exit dos 170 long_position plotados no chart vs CSV fonte (Cris 2026-06-27).
Cris moveu posicao dos LABELS; talvez 1 entry tenha sido movido por engano. Compara por PRECO
(reader de 'time' e' rebaseado/nao confiavel). Ordem do draw_list = ordem de criacao = num CSV.
long_position: points[0].price=entry; stopLevel(ticks)=|entry-sl|; profitLevel(ticks)=|entry-exit|."""
import sys,csv,json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
HERE=Path(__file__).parent; TICK=0.01
rows=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
rows.sort(key=lambda r:int(r["entry_t"]))   # mesma ordem do plot
c=MCPClient(); c.start()
try:
    dl=c.call_tool("draw_list"); shapes=dl["shapes"]
    lp=[s["id"] for s in shapes if s["name"]=="long_position"]
    print(f"long_positions no chart: {len(lp)} | trades CSV: {len(rows)}")
    n=min(len(lp),len(rows)); diffs=[]
    for k in range(n):
        pr=c.call_tool("draw_get_properties",{"entity_id":lp[k]})
        pts=pr.get("points",[]); props=pr.get("properties",{})
        e_chart=pts[0]["price"] if pts else None
        sl_ticks=props.get("stopLevel"); tp_ticks=props.get("profitLevel")
        r=rows[k]; e_csv=float(r["entry"]); sl_csv=float(r["sl"]); ex_csv=float(r["exit"])
        d_entry=abs(e_chart-e_csv) if e_chart is not None else 999
        # SL/exit reconstruidos do chart via ticks (offset do entry plotado)
        sl_chart=e_chart-sl_ticks*TICK if (e_chart is not None and sl_ticks is not None) else None
        ex_chart=e_chart+tp_ticks*TICK if (e_chart is not None and tp_ticks is not None) else None
        d_sl=abs(sl_chart-sl_csv) if sl_chart is not None else 999
        d_ex=abs(ex_chart-ex_csv) if ex_chart is not None else 999
        if d_entry>0.05 or d_sl>0.05 or d_ex>0.05:
            diffs.append({"num":r["num"],"d_entry":round(d_entry,3),"d_sl":round(d_sl,3),"d_exit":round(d_ex,3),
                          "entry_chart":e_chart,"entry_csv":e_csv})
    print(f"\nDISCREPANCIAS (>0.05 = $0.05): {len(diffs)}")
    for d in diffs: print(" ", json.dumps(d,ensure_ascii=False))
    if not diffs: print("  nenhuma — chart == CSV em entry/SL/exit nos 170.")
finally:
    try: c.stop()
    except Exception: pass
