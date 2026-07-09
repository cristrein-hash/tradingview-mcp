#!/usr/bin/env python3
"""Plotagem CANONICA de TODOS os trades da L1 EMA21 4H LONG Continuation (conjunto FINAL-24 aprovado,
l1_FINAL_regime_gated.json, N24 75% +45.2R). entry=close do bar; SL OFICIAL V1 = zona_OB_low - 0.1xATR
(scanner.demand_zone; fallback swing low); TARGET = entry + 3R. long_position width 20, tick offsets
(mintick 0.01). OUTCOME-MODE: verde winner (R>0) / vermelho loser (R<=0) — outcome real do FINAL-24.
Label curto #N. NAO draw_clear, NAO screenshot, NAO Telegram/broker. Deixa em PEPPERSTONE:XAUUSD/240.
Uso: --check (so reporta estado do chart, nao plota) | (default) plota."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
from tv_read_adapter import _MCP
SRC=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_FINAL_regime_gated.json"
WANT_SYMBOL,WANT_TF,MINTICK="PEPPERSTONE:XAUUSD","240",0.01
BOX_BARS,R_MULT=20,3.0
GREEN,RED="#1a8917","#cc0000"
def to_unix(ts): return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def ticks(entry,level): return int(round(abs(level-entry)/MINTICK))
def structural_sl(S,i):
    atr=S.ATR14[i] or 0; dz=scanner.demand_zone(S,i)
    if dz is not None: return dz[1]-0.1*atr,"OB_zone_low"
    return min(S.L[max(0,i-9):i+1])-0.1*atr,"swing_low_10"
def build_plan():
    d=json.load(open(SRC)); trades=d["trades"]
    S=scanner.build_series(); plan,skip=[],[]
    for n,r in enumerate(trades,1):
        u=to_unix(r["ts"]); i=S.idx.get(u)
        if i is None:
            cand=[k for k in range(S.N) if abs(S.T[k]-u)<=4*3600]
            i=min(cand,key=lambda k:abs(S.T[k]-u)) if cand else None
        if i is None: skip.append({"n":n,"ts":r["ts"],"reason":"bar ausente"}); continue
        entry=S.C[i]; sl,slsrc=structural_sl(S,i); risk=entry-sl
        if risk<=0: skip.append({"n":n,"ts":r["ts"],"reason":"risco<=0"}); continue
        target=entry+R_MULT*risk; exit_i=min(i+BOX_BARS,S.N-1)
        plan.append({"n":n,"ts":r["ts"],"entry_time":S.T[i],"exit_time":S.T[exit_i],
                     "entry":round(entry,2),"sl":round(sl,2),"target":round(target,2),
                     "R":r["R"],"win":r["R"]>0,"sl_src":slsrc})
    return S,plan,skip
def main():
    check="--check" in sys.argv
    S,plan,skip=build_plan()
    print(f"FINAL-24: plan={len(plan)} skip={len(skip)} | winners={sum(1 for p in plan if p['win'])} losers={sum(1 for p in plan if not p['win'])}")
    c=_MCP(); c.start(); drawn=0; chart={}
    try:
        st=c.call("chart_get_state"); chart["before"]={"symbol":st.get("symbol"),"tf":str(st.get("resolution"))}
        dl=c.call("draw_list"); chart["draw_list_before"]=dl.get("count") if isinstance(dl,dict) else None
        if check:
            print(json.dumps({"MODE":"CHECK","chart_before":chart["before"],"draw_list_before":chart["draw_list_before"],"plan":len(plan)},indent=2)); c.stop(); return 0
        if st.get("symbol")!=WANT_SYMBOL: c.call("chart_set_symbol",{"symbol":WANT_SYMBOL})
        if str(st.get("resolution"))!=WANT_TF: c.call("chart_set_timeframe",{"timeframe":WANT_TF})
        chk=c.call("chart_get_state"); sym,res=chk.get("symbol"),str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res==WANT_TF): c.stop(); print(json.dumps({"HARD_STOP":f"{sym}/{res}"})); return 1
        chart["used"]={"symbol":sym,"tf":res}
        for p in plan:
            col=GREEN if p["win"] else RED
            r1=c.call("draw_shape",{"shape":"long_position","point":{"time":p["entry_time"],"price":p["entry"]},
                "point2":{"time":p["exit_time"],"price":p["target"]},
                "overrides":json.dumps({"stopLevel":ticks(p["entry"],p["sl"]),"profitLevel":ticks(p["entry"],p["target"])})})
            if r1.get("success"): drawn+=1
            else: p["draw_error"]=str(r1)[:100]
            ly=p["target"]+0.4*(S.ATR14[S.idx.get(p["entry_time"],0)] or 1)
            c.call("draw_shape",{"shape":"text","point":{"time":p["entry_time"],"price":round(ly,2)},
                "text":f"#{p['n']}","overrides":json.dumps({"color":col,"bold":True,"fontsize":11})})
        dl2=c.call("draw_list"); chart["draw_list_after"]=dl2.get("count") if isinstance(dl2,dict) else None
        chart["left_on"]=chart["used"]
    finally:
        try: c.stop()
        except Exception: pass
    res={"strategy":"L1_EMA21_4H_LONG_FINAL24","planned":len(plan),"drawn_long_position":drawn,"skipped":skip,
         "target":"3R","sl":"V1 structural OB_zone_low -0.1ATR","color_mode":"outcome","chart":chart,"telegram":"none","broker":"untouched","trades":plan}
    (HERE/"l1_all_canonical_plotting_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
    print(json.dumps({k:res[k] for k in ["planned","drawn_long_position","skipped","target","sl","color_mode","chart"]},indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__": sys.exit(main())
