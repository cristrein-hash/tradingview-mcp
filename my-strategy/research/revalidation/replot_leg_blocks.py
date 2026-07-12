#!/usr/bin/env python3
"""REPLOT NOVA LEITURA (ordem Cris 2026-07-12): (1) apaga APENAS os retângulos MEUS do plot
antigo do detector (cores sólidas #ff9800/#4caf50/#b22833) — os desenhos do Cris (rgba
translúcidos + notas) ficam intocados; (2) plota BLOCOS DA NOVA LEITURA = corridas do campo
`leg` (leg_state_4h) de 2020 em diante, cores por estado:
  IMPULSO_UP #4caf50 · PULLBACK_BULL #81c784 · ACUMULACAO #ff9800 ·
  PULLBACK_BEAR #e57373 · IMPULSO_DOWN #b22833 · (WARMUP não plotado)
Retângulo = [t0,t1] × [low,high] da corrida. Sem clear geral, sem screenshot."""
import json, sys, time, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(HERE))
from draw_xau_4h_trades import MCPClient
from leg_state_4h import build_leg_series
import gt_pivot_structural_harness as R1
PAUSE = Path("/tmp/claude_recheck.paused")
MINE_COLORS = {"#ff9800", "#4caf50", "#b22833"}
LEG_COLOR = {"IMPULSO_UP": "#4caf50", "PULLBACK_BULL": "#81c784", "ACUMULACAO": "#ff9800",
             "PULLBACK_BEAR": "#e57373", "IMPULSO_DOWN": "#b22833"}
T2I = R1.T2I

def main():
    assert PAUSE.exists(), "pause flag ausente"
    ser = build_leg_series()
    t0_2020 = int(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    runs = []
    for r in ser:
        if r["t"] < t0_2020 or r["leg"] == "WARMUP": continue
        if runs and runs[-1]["leg"] == r["leg"]: runs[-1]["t1"] = r["t"]
        else: runs.append({"leg": r["leg"], "t0": r["t"], "t1": r["t"]})
    for run in runs:
        i0, i1 = T2I[run["t0"]], T2I[run["t1"]]
        run["lo"] = min(R1.L4[i0:i1+1]); run["hi"] = max(R1.H4[i0:i1+1])
    c = MCPClient(); c.start()
    out = {"removed_mine": 0, "kept": 0, "drawn": 0, "fails": 0, "n_runs": len(runs)}
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != "PEPPERSTONE:XAUUSD":
            print(json.dumps({"HARD_STOP": st.get("symbol")})); return 1
        # 1) apagar SÓ os meus retângulos sólidos
        items = c.call_tool("draw_list")["shapes"]
        for it in items:
            if it["name"] != "rectangle":
                out["kept"] += 1; continue
            p = c.call_tool("draw_get_properties", {"entity_id": it["id"]})
            if (p.get("properties") or {}).get("color") in MINE_COLORS:
                r = c.call_tool("draw_remove_one", {"entity_id": it["id"]})
                out["removed_mine"] += 1 if r.get("success") else 0
            else:
                out["kept"] += 1
        # 2) carregar histórico e plotar corridas do leg
        for y in (2024, 2022, 2020):
            c.call_tool("chart_scroll_to_date", {"date": f"{y}-01-01"}); time.sleep(2.5)
        for run in runs:
            r1 = c.call_tool("draw_shape", {"shape": "rectangle",
                "point":  {"time": run["t0"], "price": round(run["hi"], 2)},
                "point2": {"time": run["t1"], "price": round(run["lo"], 2)},
                "overrides": json.dumps({"color": LEG_COLOR[run["leg"]],
                                          "backgroundColor": LEG_COLOR[run["leg"]],
                                          "fillBackground": True, "transparency": 80})})
            if r1.get("success"): out["drawn"] += 1
            else: out["fails"] += 1
        c.call_tool("chart_scroll_to_date", {"date": "2020-01-01"})
        print(json.dumps(out))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
