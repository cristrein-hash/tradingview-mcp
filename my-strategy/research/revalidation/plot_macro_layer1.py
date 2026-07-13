#!/usr/bin/env python3
"""PLOT LAYER1 INTEGRADO (turnos CHoCH + ramo RANGE SYNTH) — macro_structural_v3.build_layer1.
Remove os blocos macro anteriores meus (preenchimento SÓLIDO hex), MANTÉM os desenhos do Cris
(translúcidos rgba), plota as corridas do build_layer1. BULL verde · BEAR vermelho · RANGE laranja.
Requer chart em PEPPERSTONE:XAUUSD 1D. Pausa obrigatória. Sem clear geral, sem screenshot."""
import json, sys, time, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(HERE))
from draw_xau_4h_trades import MCPClient
import macro_structural_v3 as M
PAUSE = Path("/tmp/claude_recheck.paused")
COLOR = {"BULL": "#2e7d32", "BEAR": "#c62828", "RANGE": "#ef6c00"}
T, H, L, N = M.T, M.H, M.L, M.N

def main():
    assert PAUSE.exists(), "pause flag ausente"
    lab = M.build_layer1()
    t2019 = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    runs = []
    for i in range(N):
        if runs and runs[-1]["st"] == lab[i]: runs[-1]["b"] = i
        else: runs.append({"st": lab[i], "a": i, "b": i})
    for r in runs:
        r["t0"], r["t1"] = T[r["a"]], T[r["b"]]
        r["lo"] = min(L[r["a"]:r["b"]+1]); r["hi"] = max(H[r["a"]:r["b"]+1])
    runs = [r for r in runs if r["t1"] >= t2019 and (r["t1"]-r["t0"]) >= 5*86400]
    c = MCPClient(); c.start()
    out = {"removed_mine": 0, "kept_cris": 0, "drawn": 0, "fails": 0, "n_runs": len(runs)}
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != "PEPPERSTONE:XAUUSD":
            print(json.dumps({"HARD_STOP": st.get("symbol")})); return 1
        for it in c.call_tool("draw_list")["shapes"]:
            if it["name"] != "rectangle": continue
            p = c.call_tool("draw_get_properties", {"entity_id": it["id"]})
            bg = (p.get("properties") or {}).get("backgroundColor") or ""
            if bg.startswith("rgba"): out["kept_cris"] += 1; continue
            r = c.call_tool("draw_remove_one", {"entity_id": it["id"]})
            out["removed_mine"] += 1 if r.get("success") else 0
        for y in (2023, 2021, 2019):
            c.call_tool("chart_scroll_to_date", {"date": f"{y}-01-01"}); time.sleep(2.5)
        for r in runs:
            rr = c.call_tool("draw_shape", {"shape": "rectangle",
                "point":  {"time": r["t0"], "price": round(r["hi"], 2)},
                "point2": {"time": r["t1"], "price": round(r["lo"], 2)},
                "overrides": json.dumps({"color": COLOR[r["st"]], "linewidth": 2,
                                          "backgroundColor": COLOR[r["st"]],
                                          "fillBackground": True, "transparency": 82})})
            if rr.get("success"): out["drawn"] += 1
            else: out["fails"] += 1
        c.call_tool("chart_scroll_to_date", {"date": "2019-06-01"})
        print(json.dumps(out))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
