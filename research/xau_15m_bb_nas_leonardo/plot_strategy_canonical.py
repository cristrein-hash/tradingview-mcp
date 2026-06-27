#!/usr/bin/env python3
"""Plotagem CANÔNICA da ESTRATÉGIA (strategy_trades.csv): long/short_position + label #N (docs/CANONICAL_TRADE_PLOTTING.md).
- entry/stop (SL estrutural já calculado) / profit = SAÍDA REAL do let-run (exit). stopLevel/profitLevel em TICKS (mintick 0.01).
- label #N cronológico global; VERDE LONG / VERMELHO SHORT; adds (2 unidades) marcados com '+' (azul) e box mais largo.
- janela por índice: argv lo hi → n in (lo,hi]  | --count só conta. Requer pause flag. NÃO screenshot, NÃO draw_clear.
Uso: python3 plot_strategy_canonical.py 369 409   (últimos 40)   |   ... --count . 2026-06-26."""
import sys,csv,json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
HERE=Path(__file__).parent; PAUSE=Path("/tmp/claude_recheck.paused")
SYMBOL,TF,BAR_S="PEPPERSTONE:XAUUSD","15",900
GREEN,RED,BLUE,ORANGE="#1a8917","#cc0000","#1e6fd0","#e8820c"
def build_items(sub,added_only):
    """Cada item = 1 posição canônica + 1 label. added_only: por trade c/ add → 1ª unidade (laranja) + 2ª unidade (azul)."""
    items=[]
    for r in sub:
        d=r["dir"]; shape="long_position" if d=="LONG" else "short_position"; exit_=float(r["exit"]); n=r["n"]; added=int(r["added"])
        # 1ª unidade (base)
        entry=float(r["entry"]); stop=float(r["stop"]); risk=abs(entry-stop); t=int(r["entry_t"])
        ly=entry+(0.5*risk if d=="LONG" else -0.5*risk)
        col1=ORANGE if (added_only and added) else (GREEN if d=="LONG" else RED)
        items.append({"shape":shape,"t":t,"entry":entry,"stop":stop,"exit":exit_,"width":10,
                      "label":f"#{n}","ly":ly,"col":col1})
        # 2ª unidade (add) — só no modo added_only
        if added_only and added and r["P_add"] and r["add_t"]:
            pa=float(r["P_add"]); ast=float(r["add_stop"]); arisk=abs(pa-ast); at=int(r["add_t"])
            aly=pa+(0.5*arisk if d=="LONG" else -0.5*arisk)
            items.append({"shape":shape,"t":at,"entry":pa,"stop":ast,"exit":exit_,"width":8,
                          "label":f"#{n}·2u","ly":aly,"col":BLUE})
    return items
def main():
    if not PAUSE.exists(): print("ERRO: pause flag ausente"); return 1
    added_only="--added-only" in sys.argv
    rows=list(csv.DictReader(open(HERE/"strategy_trades.csv"))); rows.sort(key=lambda r:int(r["entry_t"]))
    for n,r in enumerate(rows,1): r["n"]=n
    nums=[a for a in sys.argv[1:] if a.lstrip('-').isdigit()]
    lo=int(nums[0]) if len(nums)>0 else 0; hi=int(nums[1]) if len(nums)>1 else len(rows)
    sub=[r for r in rows if lo<r["n"]<=hi]
    if added_only: sub=[r for r in sub if int(r["added"])]
    items=build_items(sub,added_only)
    if "--count" in sys.argv:
        print(json.dumps({"total":len(rows),"trades_na_faixa":len(sub),"added_only":added_only,"posicoes_a_desenhar":len(items),
                          "n_min":sub[0]['n'] if sub else None,"n_max":sub[-1]['n'] if sub else None})); return 0
    c=MCPClient(); c.start(); drawn=0; fails=[]; chart={}
    try:
        st=c.call_tool("chart_get_state"); chart["before"]={"symbol":st.get("symbol"),"tf":str(st.get("resolution"))}
        if st.get("symbol")!=SYMBOL: c.call_tool("chart_set_symbol",{"symbol":SYMBOL})
        if str(st.get("resolution"))!=TF: c.call_tool("chart_set_timeframe",{"timeframe":TF})
        chk=c.call_tool("chart_get_state"); sym,res=chk.get("symbol"),str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res==TF):
            c.stop(); print(json.dumps({"HARD_STOP":f"chart não confirmou 15: {sym}/{res}"})); return 1
        chart["used"]={"symbol":sym,"tf":res}
        for it in items:
            r1=c.call_tool("draw_shape",{"shape":it["shape"],"point":{"time":it["t"],"price":round(it["entry"],2)},
                "point2":{"time":it["t"]+it["width"]*BAR_S,"price":round(it["exit"],2)},
                "overrides":json.dumps({"stopLevel":price_to_ticks_offset(it["entry"],it["stop"]),"profitLevel":price_to_ticks_offset(it["entry"],it["exit"])})})
            if r1.get("success"): drawn+=1
            else: fails.append({"label":it["label"],"err":str(r1)[:140]})
            c.call_tool("draw_shape",{"shape":"text","point":{"time":it["t"],"price":round(it["ly"],2)},
                "text":it["label"],"overrides":json.dumps({"color":it["col"],"bold":True,"fontsize":11})})
        dl=c.call_tool("draw_list"); chart["draw_list_count"]=dl.get("count") if isinstance(dl,dict) else None
    finally:
        try: c.stop()
        except Exception: pass
    print(json.dumps({"added_only":added_only,"trades":len(sub),"posicoes_desenhadas":drawn,"itens":len(items),
                      "falhas":len(fails),"falhas_amostra":fails[:4],"chart":chart},indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__": sys.exit(main())
