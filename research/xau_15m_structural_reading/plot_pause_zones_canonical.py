#!/usr/bin/env python3
"""PLOT CANÓNICO — zonas Pause Ruler de SET/2025 em diante como operações de compra (ordem Cris).
long_position: entry = topo da zona (hi), SL = piso (lo), alvo = 3R; anchor = known_at; width 10
barras; label PRETO P#### + data. Sem clear, sem screenshot. HARD_STOP se chart != XAUUSD/15."""
import json, sys, io, contextlib, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
import pause_ruler_gate as G
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S = "PEPPERSTONE:XAUUSD", "15", 900
BLACK = "#000000"
T0 = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    zones = []
    orig = G._publish
    def cap(zs, lids, p, i, t, a):
        orig(zs, lids, p, i, t, a); zones.append(zs[-1])
    G._publish = cap
    with contextlib.redirect_stdout(io.StringIO()):
        G.main()
    sel = [z for z in zones if z["known_at"] >= T0]
    c = MCPClient(); c.start(); drawn = 0; fails = []
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL or str(st.get("resolution")) != TF:
            print(json.dumps({"HARD_STOP": f"chart {st.get('symbol')}/{st.get('resolution')}"})); return 1
        for z in sel:
            ent, sl = z["hi"], z["lo"]
            tgt = ent+3*(ent-sl)
            lab = f"{z['id']} {dt.datetime.utcfromtimestamp(z['known_at']).strftime('%m-%d %H:%M')}"
            r1 = c.call_tool("draw_shape", {"shape": "long_position",
                "point": {"time": z["known_at"], "price": round(ent, 2)},
                "point2": {"time": z["known_at"]+10*BAR_S, "price": round(tgt, 2)},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(ent, sl),
                                          "profitLevel": price_to_ticks_offset(ent, tgt)})})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": z["known_at"], "price": round(ent+0.5*(ent-sl), 2)},
                "text": lab,
                "overrides": json.dumps({"color": BLACK, "fontsize": 11, "bold": True})})
            if r1.get("success") and r2.get("success"): drawn += 1
            else: fails.append(z["id"])
        print(json.dumps({"selecionadas_set2025_mais": len(sel), "drawn": drawn, "fails": fails}))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
