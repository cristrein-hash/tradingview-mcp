#!/usr/bin/env python3
"""PLOT CANÓNICO — velas do gate v2 com 'zona certa mas SEM AUTORIDADE', como operações de compra
(ordem Cris). long_position na data da vela: entry = topo da zona que a continha, SL = piso,
alvo 3R; label preto com #n e idade da zona. Sem clear, sem screenshot."""
import json, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
GT = REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S = "PEPPERSTONE:XAUUSD", "15", 900
BLACK = "#e8a33d"

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    rows = json.load(open(HERE/"results/a2_v2_gate42_result.json"))["rows"]
    cat = json.load(open(GT))
    tmap = {x["date"]: x["t"] for x in cat["notes"]["FUNDO"]}
    sel = [r for r in rows if r["status"] == "FALHA" and "SEM AUTORIDADE" in r["motivo"]]
    c = MCPClient(); c.start(); drawn = 0; fails = []
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL or str(st.get("resolution")) != TF:
            print(json.dumps({"HARD_STOP": f"chart {st.get('symbol')}/{st.get('resolution')}"})); return 1
        for r in sel:
            t = tmap[r["date"]]
            lo, hi = r["regiao"]["band"]
            ent, sl = hi, lo
            tgt = ent+3*(ent-sl)
            lab = f"SEM_AUT #{r['n']} idade {r['regiao']['idade_h']:.0f}h"
            r1 = c.call_tool("draw_shape", {"shape": "long_position",
                "point": {"time": t, "price": round(ent, 2)},
                "point2": {"time": t+10*BAR_S, "price": round(tgt, 2)},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(ent, sl),
                                          "profitLevel": price_to_ticks_offset(ent, tgt)})})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": t, "price": round(ent+0.5*(ent-sl), 2)},
                "text": lab,
                "overrides": json.dumps({"color": BLACK, "fontsize": 11, "bold": True})})
            if r1.get("success") and r2.get("success"): drawn += 1
            else: fails.append(r["n"])
        print(json.dumps({"selecionadas": [r["n"] for r in sel], "drawn": drawn, "fails": fails}))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
