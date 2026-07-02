#!/usr/bin/env python3
# HISTORICAL_ONE_SHOT / DO_NOT_USE_AS_CANONICAL — width original mantida. PLOTTING_CANON_MASTER_REQUIRED: ler docs/project_authority/PLOTTING_CANON_MASTER.md antes de qualquer novo plot (R2 2026-07-02).
"""Plota TODOS os trades da BASE FIXA (3120+h4_up&h1d_up) na janela 2025-08-01 -> 2026-01-01 (fixed_base_h4h1.csv).
Canônico: long_position (stopLevel/profitLevel em TICKS) + label #N, verde=win/vermelho=loss. exit = entry + R*(entry-sl).
Requer pause flag. NÃO captura screenshot (Cris vê o chart). Salva window CSV reprodutível."""
import sys,csv,json,datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
HERE=Path(__file__).parent; PAUSE=Path("/tmp/claude_recheck.paused")
SYMBOL,TF,BAR_S,WIDTH="PEPPERSTONE:XAUUSD","15",900,8
GREEN,RED="#1a8917","#cc0000"
LO=dt.datetime(2025,8,1).timestamp(); HI=dt.datetime(2026,1,1).timestamp()
def load():
    rows=[r for r in csv.DictReader(open(HERE/"fixed_base_h4h1.csv")) if LO<=int(r["cj_t"])<HI]
    rows.sort(key=lambda r:int(r["cj_t"]))
    out=[]
    for i,r in enumerate(rows,1):
        entry=float(r["entry"]); sl=float(r["sl"]); R=float(r["R"]); risk=entry-sl
        out.append({"num":i,"cj_t":int(r["cj_t"]),"date":r["date"],"entry":entry,"sl":sl,
                    "exit":round(entry+R*risk,2),"R":R,"win":R>0})
    return out
def main():
    rows=load()
    with open(HERE/"window_aug2025_jan2026.csv","w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=["num","cj_t","date","entry","sl","exit","R","win"]); w.writeheader(); w.writerows(rows)
    if not PAUSE.exists(): print("ERRO: pause flag ausente"); return 1
    c=MCPClient(); c.start(); drawn=0; fails=[]; chart={}
    try:
        st=c.call_tool("chart_get_state")
        if st.get("symbol")!=SYMBOL: c.call_tool("chart_set_symbol",{"symbol":SYMBOL})
        if str(st.get("resolution"))!=TF: c.call_tool("chart_set_timeframe",{"timeframe":TF})
        chk=c.call_tool("chart_get_state"); sym,res=chk.get("symbol"),str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res==TF):
            c.stop(); print(json.dumps({"HARD_STOP":f"{sym}/{res}"})); return 1
        dl0=c.call_tool("draw_list"); chart["before"]=dl0.get("count") if isinstance(dl0,dict) else None
        for r in rows:
            entry,sl,ex,t,win,num=r["entry"],r["sl"],r["exit"],r["cj_t"],r["win"],r["num"]
            risk=abs(entry-sl); ly=entry+0.5*risk; col=GREEN if win else RED
            r1=c.call_tool("draw_shape",{"shape":"long_position","point":{"time":t,"price":round(entry,2)},
                "point2":{"time":t+WIDTH*BAR_S,"price":ex},
                "overrides":json.dumps({"stopLevel":price_to_ticks_offset(entry,sl),"profitLevel":price_to_ticks_offset(entry,ex)})})
            if r1.get("success"): drawn+=1
            else: fails.append({"num":num,"err":str(r1)[:80]})
            c.call_tool("draw_shape",{"shape":"text","point":{"time":t,"price":round(ly,2)},
                "text":f"#{num}","overrides":json.dumps({"color":col,"bold":True,"fontsize":10})})
        dl=c.call_tool("draw_list"); chart["after"]=dl.get("count") if isinstance(dl,dict) else None
    finally:
        try: c.stop()
        except Exception: pass
    print(json.dumps({"trades":len(rows),"posicoes":drawn,"falhas":len(fails),"falhas_amostra":fails[:3],"chart":chart},indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__": sys.exit(main())
