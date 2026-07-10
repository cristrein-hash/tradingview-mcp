#!/usr/bin/env python3
"""PLOT — 57 zonas do Pause Ruler (ordem Cris 2026-07-10). Retângulos proporcionais: [known_at →
fim real da zona (inv/kill/supersessão; senão +168h de autoridade)] × [lo, hi]. LABEL PRETO com id
e data. Sem clear, sem screenshot. HARD_STOP se chart != XAUUSD/15."""
import json, sys, io, contextlib, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from draw_xau_4h_trades import MCPClient
import pause_ruler_gate as G
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF = "PEPPERSTONE:XAUUSD", "15"
GRAY, BLACK = "#787b86", "#000000"

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    zones = []
    orig = G._publish
    def cap(zs, lids, p, i, t, a):
        orig(zs, lids, p, i, t, a); zones.append(zs[-1])
    G._publish = cap
    with contextlib.redirect_stdout(io.StringIO()):
        G.main()
    c = MCPClient(); c.start(); drawn = 0; fails = []
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL or str(st.get("resolution")) != TF:
            print(json.dumps({"HARD_STOP": f"chart {st.get('symbol')}/{st.get('resolution')}"})); return 1
        for z in zones:
            end = min(x for x in (z["inv_at"], z["kill_at"], z["sup_at"],
                                  z["known_at"]+168*3600) if x is not None)
            lab = f"{z['id']} {dt.datetime.utcfromtimestamp(z['known_at']).strftime('%m-%d %H:%M')}"
            r1 = c.call_tool("draw_shape", {"shape": "rectangle",
                "point": {"time": z["known_at"], "price": round(z["lo"], 2)},
                "point2": {"time": end, "price": round(z["hi"], 2)},
                "overrides": json.dumps({"color": GRAY, "backgroundColor": GRAY,
                                          "transparency": 82, "linewidth": 1})})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": z["known_at"], "price": round(z["hi"]*1.0005, 2)},
                "text": lab,
                "overrides": json.dumps({"color": BLACK, "fontsize": 11, "bold": True})})
            if r1.get("success") and r2.get("success"): drawn += 1
            else: fails.append(z["id"])
        print(json.dumps({"drawn": drawn, "requested": len(zones), "fails": fails}))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
