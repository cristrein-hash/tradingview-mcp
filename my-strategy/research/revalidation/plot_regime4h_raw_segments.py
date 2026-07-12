#!/usr/bin/env python3
"""PLOT VERIFICAÇÃO VISUAL — detector de regime 4H-nativo RAW (v5-mirror, engine_4h_regime_gate_RAW.py)
como RETÂNGULOS coloridos por regime, 2019-12-31 em diante (ordem Cris 2026-07-12):
laranja=RANGE (#ff9800) · verde=BULL (#4caf50) · vermelho=BEAR (#b22833) — convenção das zonas GT do Cris.
Segmento = corrida de regime_at(t) constante sobre os bars RAW 4H; retângulo = [t_ini,t_fim] × [low,high]
do segmento. Chart em 4H (240); scroll prévio para carregar histórico. Sem clear, sem screenshot, sem labels."""
import io, json, sys, time, contextlib, datetime as dt
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF = "PEPPERSTONE:XAUUSD", "240"
COLOR = {"RANGE": "#ff9800", "BULL": "#4caf50", "BEAR": "#b22833"}

def load_engine():
    spec = importlib.util.spec_from_file_location("eng", HERE/"engine_4h_regime_gate_RAW.py")
    eng = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(eng)
    return eng

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    eng = load_engine()
    TS4, B4 = eng.TS4, eng.B4
    segs = []; cur = None
    for i, t in enumerate(TS4):
        r = eng.regime_at(t)
        if cur and cur["regime"] == r:
            cur["b"] = i
        else:
            if cur: segs.append(cur)
            cur = {"regime": r, "a": i, "b": i}
    segs.append(cur)
    for s in segs:
        bars = B4[s["a"]:s["b"]+1]
        s["t0"], s["t1"] = TS4[s["a"]], TS4[s["b"]]
        s["lo"] = min(b["l"] for b in bars); s["hi"] = max(b["h"] for b in bars)
    c = MCPClient(); c.start()
    out = {"n_segmentos": len(segs), "drawn": 0, "fails": []}
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL:
            print(json.dumps({"HARD_STOP": f"chart {st.get('symbol')}"})); return 1
        if str(st.get("resolution")) != TF:
            c.call_tool("chart_set_timeframe", {"timeframe": TF}); time.sleep(2)
        # carregar histórico até o início (scroll em saltos anuais)
        for y in (2024, 2022, 2020):
            c.call_tool("chart_scroll_to_date", {"date": f"{y}-01-01"}); time.sleep(2.5)
        for k, s in enumerate(segs, 1):
            r1 = c.call_tool("draw_shape", {"shape": "rectangle",
                "point":  {"time": s["t0"], "price": round(s["hi"], 2)},
                "point2": {"time": s["t1"], "price": round(s["lo"], 2)},
                "overrides": json.dumps({"color": COLOR[s["regime"]],
                                          "backgroundColor": COLOR[s["regime"]],
                                          "fillBackground": True, "transparency": 80})})
            if r1.get("success"): out["drawn"] += 1
            else: out["fails"].append(k)
        c.call_tool("chart_scroll_to_date", {"date": "2020-01-01"})
        print(json.dumps(out))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
