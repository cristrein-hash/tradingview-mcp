#!/usr/bin/env python3
"""Plotagem CANÔNICA dos FUNDOS/TOPOS verdadeiros (M=8) — APENAS VISUALIZAÇÃO (não é estratégia, Cris 2026-06-26).
LONG nos fundos (verde) / SHORT nos topos (vermelho). entry=pivô; SL estrutural=pivô ∓ 0.5*ATR; alvo=10R (=±5*ATR).
long/short_position + label F#/T# (docs/CANONICAL_TRADE_PLOTTING.md). stopLevel/profitLevel em TICKS. Requer pause flag.
NÃO screenshot, NÃO draw_clear."""
import sys,csv,json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
HERE=Path(__file__).parent; PAUSE=Path("/tmp/claude_recheck.paused")
SYMBOL,TF,BAR_S,WIDTH="PEPPERSTONE:XAUUSD","15",900,10
GREEN,RED="#1a8917","#cc0000"; BUF,RMULT=0.5,10.0
def main():
    if not PAUSE.exists(): print("ERRO: pause flag ausente"); return 1
    rows=list(csv.DictReader(open(HERE/"true_reversals_M8.csv"))); rows.sort(key=lambda r:int(r["t"]))
    cb=ct=0; items=[]
    for r in rows:
        t=int(r["t"]); price=float(r["price"]); atr=float(r["atr"]); risk=BUF*atr
        if r["kind"]=="BOT":
            cb+=1; shape="long_position"; stop=price-risk; tgt=price+RMULT*risk; col=GREEN; lab=f"F{cb}"; ly=price+0.5*risk
        else:
            ct+=1; shape="short_position"; stop=price+risk; tgt=price-RMULT*risk; col=RED; lab=f"T{ct}"; ly=price-0.5*risk
        items.append({"shape":shape,"t":t,"entry":round(price,2),"stop":round(stop,2),"tgt":round(tgt,2),"col":col,"lab":lab,"ly":round(ly,2)})
    if "--count" in sys.argv:
        print(json.dumps({"fundos":cb,"topos":ct,"total":len(items)})); return 0
    c=MCPClient(); c.start(); drawn=0; fails=[]; chart={}
    try:
        st=c.call_tool("chart_get_state"); chart["before"]={"symbol":st.get("symbol"),"tf":str(st.get("resolution"))}
        if st.get("symbol")!=SYMBOL: c.call_tool("chart_set_symbol",{"symbol":SYMBOL})
        if str(st.get("resolution"))!=TF: c.call_tool("chart_set_timeframe",{"timeframe":TF})
        chk=c.call_tool("chart_get_state"); sym,res=chk.get("symbol"),str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res==TF):
            c.stop(); print(json.dumps({"HARD_STOP":f"chart não 15: {sym}/{res}"})); return 1
        chart["used"]={"symbol":sym,"tf":res}
        for it in items:
            r1=c.call_tool("draw_shape",{"shape":it["shape"],"point":{"time":it["t"],"price":it["entry"]},
                "point2":{"time":it["t"]+WIDTH*BAR_S,"price":it["tgt"]},
                "overrides":json.dumps({"stopLevel":price_to_ticks_offset(it["entry"],it["stop"]),"profitLevel":price_to_ticks_offset(it["entry"],it["tgt"])})})
            if r1.get("success"): drawn+=1
            else: fails.append({"lab":it["lab"],"err":str(r1)[:140]})
            c.call_tool("draw_shape",{"shape":"text","point":{"time":it["t"],"price":it["ly"]},
                "text":it["lab"],"overrides":json.dumps({"color":it["col"],"bold":True,"fontsize":11})})
        dl=c.call_tool("draw_list"); chart["draw_list_count"]=dl.get("count") if isinstance(dl,dict) else None
    finally:
        try: c.stop()
        except Exception: pass
    print(json.dumps({"fundos_long":cb,"topos_short":ct,"posicoes_desenhadas":drawn,"falhas":len(fails),"falhas_amostra":fails[:4],"chart":chart},indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__": sys.exit(main())
