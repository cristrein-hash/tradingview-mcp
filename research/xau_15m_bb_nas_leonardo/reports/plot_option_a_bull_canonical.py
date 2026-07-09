#!/usr/bin/env python3
"""PLOT CANÓNICO — Opção A · A-BULL (set/2025 em diante), ordem Cris (revisão visual dos 37).
Canon (skill plotting-canon / plot_entry_signals_canonical_20260707.py): long_position + label ·
width 10 barras (900s) · stopLevel/profitLevel em TICKS (mintick 0.01) · outcome-mode VERDE #1a8917
winner / VERMELHO #cc0000 loser · label #A<n> em entry+0.5*risk · NÃO remove drawings do Cris ·
NÃO clear · NÃO screenshot · pause-flag + HARD_STOP se chart != XAUUSD/15.
Fonte: xau_15m_option_a_candidates.csv (regime==BULL; d>=2025-09-01).
Output: plot_option_a_bull_result.json."""
import json, sys, csv
from pathlib import Path
HERE=Path(__file__).resolve().parent; RD=HERE.parent
sys.path.insert(0,str(RD.parents[1]/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE=Path("/tmp/claude_recheck.paused")
SYMBOL,TF,BAR_S="PEPPERSTONE:XAUUSD","15",900
GREEN,RED="#1a8917","#cc0000"

def main():
    if not PAUSE.exists():
        print(json.dumps({"ERRO":"pause flag ausente"})); return 1
    rows=list(csv.DictReader(open(HERE/"xau_15m_option_a_candidates.csv")))
    bull=[r for r in rows if r["regime"]=="BULL"]
    bull.sort(key=lambda r:int(r["t"]))
    # numerar A1..A37 na ordem temporal COMPLETA (mapa estável), depois filtrar set/2025+
    for n,r in enumerate(bull,1): r["an"]=n
    sub=[r for r in bull if r["d"]>="2025-09-01"]
    items=[]
    for r in sub:
        ent=float(r["ent"]); sl=float(r["sl"]); risk=float(r["risk"]); tgt=ent+3*risk
        t=int(r["t"]); col=GREEN if int(r["out"])==1 else RED
        items.append({"t":t,"entry":ent,"stop":sl,"exit":tgt,"label":f"#A{r['an']}",
                      "ly":ent+0.5*risk,"col":col,"out":int(r["out"]),"d":r["d"]})
    c=MCPClient(); c.start(); drawn=0; fails=[]
    try:
        st=c.call_tool("chart_get_state")
        sym,res=st.get("symbol"),str(st.get("resolution"))
        if sym!=SYMBOL or res!=TF:
            print(json.dumps({"HARD_STOP":f"chart {sym}/{res} != {SYMBOL}/{TF}"})); return 1
        for it in items:
            r1=c.call_tool("draw_shape",{"shape":"long_position",
                "point":{"time":it["t"],"price":round(it["entry"],2)},
                "point2":{"time":it["t"]+10*BAR_S,"price":round(it["exit"],2)},
                "overrides":json.dumps({"stopLevel":price_to_ticks_offset(it["entry"],it["stop"]),
                                        "profitLevel":price_to_ticks_offset(it["entry"],it["exit"])})})
            ok1=r1.get("success")
            r2=c.call_tool("draw_shape",{"shape":"text","point":{"time":it["t"],"price":round(it["ly"],2)},
                "text":it["label"],"overrides":json.dumps({"color":it["col"],"fontsize":12,"bold":True})})
            ok2=r2.get("success")
            if ok1 and ok2: drawn+=1
            else: fails.append({"label":it["label"],"pos":ok1,"lbl":ok2})
        res_out={"total_A_BULL":len(bull),"plotted_sep2025_plus":drawn,"requested":len(items),
                 "fails":fails[:5],"winners":sum(1 for i in items if i["out"]==1),
                 "losers":sum(1 for i in items if i["out"]==0),
                 "range":[items[0]["d"],items[-1]["d"]] if items else None,
                 "mapa":[{"label":i["label"],"d":i["d"],"out":i["out"]} for i in items]}
        (HERE/"plot_option_a_bull_result.json").write_text(json.dumps(res_out,indent=2,ensure_ascii=False))
        print(json.dumps({k:v for k,v in res_out.items() if k!="mapa"},indent=2,ensure_ascii=False))
    finally:
        try: c.stop()
        except Exception: pass
    return 0
if __name__=="__main__": sys.exit(main())
