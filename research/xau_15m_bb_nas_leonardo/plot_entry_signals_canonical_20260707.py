#!/usr/bin/env python3
"""Plotagem CANÔNICA 15M dos SINAIS DE ENTRY 3R (2026-07-07) — segue PLOTTING_CANON_MASTER.
Fonte: results/entry_signals_plot_20260707.json (MARKUP master + tag reclaim_lag<=4).
- long_position + label · width 10 (bar 900s) · stopLevel/profitLevel em TICKS (mintick 0.01) via
  price_to_ticks_offset · point2=(entry+10 barras, target).
- OUTCOME-MODE (outcome real: hit-3R via SL estrutural −0,1ATR + target +3R = exit_policy ESTRUTURAL,
  NÃO legacy): VERDE #1a8917 winner (out=1) · VERMELHO #cc0000 loser (out=0).
- label #N cronológico; SINAL 2 (reclaim_lag<=4) marcado com sufixo 'R' (variante declarada, §9).
- NÃO draw_clear · NÃO screenshot · requer pause flag · confirma 15M (HARD_STOP senão). Preserva draws do Cris.
Uso: python3 plot_entry_signals_canonical_20260707.py [lo hi] [--count]"""
import sys,json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
HERE=Path(__file__).parent; PAUSE=Path("/tmp/claude_recheck.paused")
SYMBOL,TF,BAR_S="PEPPERSTONE:XAUUSD","15",900
GREEN,RED="#1a8917","#cc0000"
def build_items(sub):
    items=[]
    for r in sub:
        entry=float(r["entry"]); stop=float(r["stop"]); tgt=float(r["target"]); risk=abs(entry-stop); t=int(r["entry_t"])
        ly=entry+0.5*risk
        col=GREEN if int(r["outcome"])==1 else RED
        label=f"#{r['n']}"+("R" if int(r["signal2"])==1 else "")
        items.append({"shape":"long_position","t":t,"entry":entry,"stop":stop,"exit":tgt,"width":10,
                      "label":label,"ly":ly,"col":col})
    return items
def main():
    if not PAUSE.exists(): print(json.dumps({"ERRO":"pause flag ausente"})); return 1
    rows=json.load(open(HERE/"results"/"entry_signals_plot_20260707.json")); rows.sort(key=lambda r:int(r["entry_t"]))
    nums=[a for a in sys.argv[1:] if a.lstrip('-').isdigit()]
    lo=int(nums[0]) if len(nums)>0 else 0; hi=int(nums[1]) if len(nums)>1 else len(rows)
    sub=[r for r in rows if lo<int(r["n"])<=hi]
    items=build_items(sub)
    if "--count" in sys.argv:
        print(json.dumps({"total":len(rows),"na_faixa":len(sub),"posicoes":len(items),
                          "winners":sum(1 for r in sub if int(r['outcome'])==1),"sinal2":sum(1 for r in sub if int(r['signal2'])==1)})); return 0
    c=MCPClient(); c.start(); drawn=0; fails=[]; chart={}
    try:
        st=c.call_tool("chart_get_state"); chart["before"]={"symbol":st.get("symbol"),"tf":str(st.get("resolution"))}
        sym,res=st.get("symbol"),str(st.get("resolution"))
        if sym!=SYMBOL or res!=TF:
            print(json.dumps({"HARD_STOP":f"chart {sym}/{res} != {SYMBOL}/{TF} — confirmar com Cris (não troco symbol/TF sem confirmação)"})); c.stop(); return 1
        for it in items:
            r1=c.call_tool("draw_shape",{"shape":it["shape"],"point":{"time":it["t"],"price":round(it["entry"],2)},
                "point2":{"time":it["t"]+it["width"]*BAR_S,"price":round(it["exit"],2)},
                "overrides":json.dumps({"stopLevel":price_to_ticks_offset(it["entry"],it["stop"]),
                                        "profitLevel":price_to_ticks_offset(it["entry"],it["exit"])})})
            ok1=r1.get("success"); eid=r1.get("entity_id")
            r2=c.call_tool("draw_shape",{"shape":"text","point":{"time":it["t"],"price":round(it["ly"],2)},
                "text":it["label"],"overrides":json.dumps({"color":it["col"],"fontsize":12,"bold":True})})
            ok2=r2.get("success")
            if ok1 and ok2: drawn+=1
            else: fails.append({"label":it["label"],"pos":ok1,"lbl":ok2})
        dl=c.call_tool("draw_list");
        print(json.dumps({"drawn":drawn,"items":len(items),"fails":len(fails),
                          "draw_list_total":dl.get("count"),"chart":chart,"fail_detail":fails[:5]}))
    finally:
        try: c.stop()
        except Exception: pass
    return 0
if __name__=="__main__": sys.exit(main())
