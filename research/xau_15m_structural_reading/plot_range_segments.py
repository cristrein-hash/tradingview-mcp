#!/usr/bin/env python3
"""PLOT — TODOS os segmentos macro==RANGE (macro_at PURO do leg engine; regime 1D estável +
override 1H) de 2025-09-01 em diante, como RETÂNGULOS [início→fim] × [low..high do segmento],
com label RANGE_SEG #k (ordem Cris 2026-07-10). Sem clear, sem screenshot."""
import json, sys, time, datetime as dt
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from draw_xau_4h_trades import MCPClient
from f1_structural_leg_machine import Data
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF = "PEPPERSTONE:XAUUSD", "15"
ORANGE = "#e8a33d"

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    D = Data()
    T0 = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())
    segs = []; cur = None
    for i in range(len(D.TS)):
        if D.TS[i] < T0: continue
        if D.macro_at(D.TS[i]) == "RANGE":
            cur = [i, i] if cur is None else [cur[0], i]
        elif cur is not None:
            segs.append(cur); cur = None
    if cur is not None: segs.append(cur)
    c = MCPClient(); c.start(); out = {"drawn": [], "fails": []}
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL or str(st.get("resolution")) != TF:
            print(json.dumps({"HARD_STOP": f"chart {st.get('symbol')}/{st.get('resolution')}"})); return 1
        for k, (a, b) in enumerate(segs, 1):
            day = dt.datetime.utcfromtimestamp(D.TS[a]).strftime("%Y-%m-%d")
            c.call_tool("chart_scroll_to_date", {"date": day})
            time.sleep(2.5)
            lo = min(D.L[a:b+1]); hi = max(D.H[a:b+1])
            r1 = c.call_tool("draw_shape", {"shape": "rectangle",
                "point": {"time": D.TS[a], "price": round(hi, 2)},
                "point2": {"time": D.TS[b], "price": round(lo, 2)}})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": D.TS[a], "price": round(hi, 2)},
                "text": f"RANGE_SEG {k}",
                "overrides": json.dumps({"color": ORANGE, "fontsize": 12, "bold": True})})
            if r1.get("success") and r2.get("success"):
                out["drawn"].append([k, day, dt.datetime.utcfromtimestamp(D.TS[b]).strftime("%Y-%m-%d")])
            else:
                out["fails"].append(k)
        c.call_tool("chart_scroll_to_date", {"date": "2025-09-01"})
        print(json.dumps(out))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
