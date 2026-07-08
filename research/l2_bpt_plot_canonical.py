#!/usr/bin/env python3
"""Plotagem CANONICA 4H dos 17 trades APROVADOS L2/BPT (fonte research/results/l2_bpt_17_trades.csv).
plotting-canon §6: long_position entry/SL/saida-let-run + label #num VERDE(winner)/VERMELHO(loser),
width 20 barras (4H), tick offsets. Requer pause flag. NAO screenshot, NAO draw_clear. Verificacao = draw_list."""
import sys,csv,json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
HERE=REPO/"research"; PAUSE=Path("/tmp/claude_recheck.paused")
SYMBOL,TF,BAR_S,WIDTH="PEPPERSTONE:XAUUSD","240",14400,20  # canon 4H=20
GREEN,RED="#1a8917","#cc0000"
def main():
    if not PAUSE.exists(): print(json.dumps({"ERRO":"pause flag ausente"})); return 1
    rows=list(csv.DictReader(open(HERE/"results/l2_bpt_17_trades.csv"))); rows.sort(key=lambda r:int(r["entry_t"]))
    if "--count" in sys.argv:
        print(json.dumps({"n":len(rows),"win":sum(1 for r in rows if r["win"]=="1"),"loss":sum(1 for r in rows if r["win"]=="0")})); return 0
    c=MCPClient(); c.start(); drawn=0; fails=[]; chart={}
    try:
        st=c.call_tool("chart_get_state"); chart["before"]={"symbol":st.get("symbol"),"tf":str(st.get("resolution"))}
        if st.get("symbol")!=SYMBOL: c.call_tool("chart_set_symbol",{"symbol":SYMBOL})
        if str(st.get("resolution"))!=TF: c.call_tool("chart_set_timeframe",{"timeframe":TF})
        chk=c.call_tool("chart_get_state"); sym,res=chk.get("symbol"),str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res==TF):
            c.stop(); print(json.dumps({"HARD_STOP":f"chart nao 4H: {sym}/{res}"})); return 1
        chart["used"]={"symbol":sym,"tf":res}
        for r in rows:
            entry=float(r["entry"]); sl=float(r["sl"]); ex=float(r["exit"]); t=int(r["entry_t"]); win=r["win"]=="1"; num=r["num"]
            risk=abs(entry-sl); ly=entry+0.5*risk; col=GREEN if win else RED
            r1=c.call_tool("draw_shape",{"shape":"long_position","point":{"time":t,"price":round(entry,2)},
                "point2":{"time":t+WIDTH*BAR_S,"price":round(ex,2)},
                "overrides":json.dumps({"stopLevel":price_to_ticks_offset(entry,sl),"profitLevel":price_to_ticks_offset(entry,ex)})})
            if r1.get("success"): drawn+=1
            else: fails.append({"num":num,"err":str(r1)[:120]})
            c.call_tool("draw_shape",{"shape":"text","point":{"time":t,"price":round(ly,2)},
                "text":f"#{num}","overrides":json.dumps({"color":col,"bold":True,"fontsize":12})})
        dl=c.call_tool("draw_list"); chart["draw_list_count"]=dl.get("count") if isinstance(dl,dict) else None
    finally:
        try: c.stop()
        except Exception: pass
    print(json.dumps({"trades":len(rows),"posicoes":drawn,"falhas":len(fails),"falhas_amostra":fails[:4],"chart":chart},indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__": sys.exit(main())
