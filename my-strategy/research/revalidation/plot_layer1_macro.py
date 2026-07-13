#!/usr/bin/env python3
"""PLOT LAYER 1 MACRO (ordem Cris 2026-07-13): remove os blocos leg v2 (meus, preenchimento
SÓLIDO hex) e plota as corridas do detector Layer 1 macro (round 3b, config equilibrada K=5).
Mantém os desenhos do Cris (translúcidos rgba). Cores: BULL verde · BEAR vermelho · RANGE laranja.
Sem clear geral, sem screenshot."""
import json, sys, time, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(HERE))
from draw_xau_4h_trades import MCPClient
import layer1_macro_detector_r3b as R
CFG = (5, -4.0, -5.0, 20, 90)          # best balanced (bal 51 · BULL78/BEAR49/RANGE26)
DWELL = 20                             # persistência MACRO causal (novo estado só troca após 20d) -> 21 blocos ~94d
PAUSE = Path("/tmp/claude_recheck.paused")
COLOR = {"BULL": "#2e7d32", "BEAR": "#c62828", "RANGE": "#ef6c00"}
T = R.R.T; H = R.H; L = R.L; N = R.N

def macro_smooth(labels, dwell):
    """causal: o rótulo de saída só troca quando um novo estado persiste 'dwell' dias seguidos."""
    out = []; cur = labels[0]; cand = None; cn = 0
    for s in labels:
        if s == cur: cand = None; cn = 0
        elif s == cand: cn += 1
        else: cand = s; cn = 1
        if cand is not None and cn >= dwell: cur = cand; cand = None; cn = 0
        out.append(cur)
    return out

def main():
    assert PAUSE.exists(), "pause flag ausente"
    raw = [s for _, s in R.build(*CFG)]
    lab = macro_smooth(raw, DWELL)      # persistência macro causal
    # runs de estado, alinhados aos dias (usar T[i] = abertura da barra diária)
    runs = []
    for i in range(N):
        state = lab[i]
        if runs and runs[-1]["st"] == state: runs[-1]["b"] = i
        else: runs.append({"st": state, "a": i, "b": i})
    for r in runs:
        r["t0"], r["t1"] = T[r["a"]], T[r["b"]]
        r["lo"] = min(L[r["a"]:r["b"]+1]); r["hi"] = max(H[r["a"]:r["b"]+1])
    runs = [r for r in runs if r["t1"] >= int(dt.datetime(2019,1,1,tzinfo=dt.timezone.utc).timestamp())]
    c = MCPClient(); c.start()
    out = {"removed_mine": 0, "kept_cris": 0, "drawn": 0, "fails": 0, "n_runs": len(runs)}
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != "PEPPERSTONE:XAUUSD":
            print(json.dumps({"HARD_STOP": st.get("symbol")})); return 1
        items = c.call_tool("draw_list")["shapes"]
        for it in items:
            if it["name"] != "rectangle": continue
            p = c.call_tool("draw_get_properties", {"entity_id": it["id"]})
            bg = (p.get("properties") or {}).get("backgroundColor") or ""
            if bg.startswith("rgba"): out["kept_cris"] += 1; continue   # Cris = translúcido
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
