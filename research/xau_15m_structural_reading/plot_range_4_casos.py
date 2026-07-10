#!/usr/bin/env python3
"""PLOT CANÓNICO — os 4 casos RANGE do GT (ordem Cris 2026-07-10), como operações de compra.
long_position na vela: entry = preço da marca, SL = −1·ATR, alvo 3R; label laranja RANGE #n.
Sem clear, sem screenshot."""
import json, sys, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
from f1_structural_leg_machine import Data
GT = REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S = "PEPPERSTONE:XAUUSD", "15", 900
ORANGE = "#e8a33d"

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    rows = json.load(open(HERE/"results/a2_v2_gate42_result.json"))["rows"]
    cat = json.load(open(GT))
    tmap = {x["date"]: (x["t"], x["price"]) for x in cat["notes"]["FUNDO"]}
    sel = [r for r in rows if r["familia"] == "RANGE_BOTTOM"]
    D = Data()
    c = MCPClient(); c.start(); drawn = 0; fails = []
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL or str(st.get("resolution")) != TF:
            print(json.dumps({"HARD_STOP": f"chart {st.get('symbol')}/{st.get('resolution')}"})); return 1
        for r in sel:
            t, px = tmap[r["date"]]
            i = bisect.bisect_right(D.TS, t)-1; a = D.ATR[i] or 5.0
            ent, sl = px, px-1.0*a
            tgt = ent+3*(ent-sl)
            r1 = c.call_tool("draw_shape", {"shape": "long_position",
                "point": {"time": t, "price": round(ent, 2)},
                "point2": {"time": t+10*BAR_S, "price": round(tgt, 2)},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(ent, sl),
                                          "profitLevel": price_to_ticks_offset(ent, tgt)})})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": t, "price": round(ent+0.5*(ent-sl), 2)},
                "text": f"RANGE #{r['n']}",
                "overrides": json.dumps({"color": ORANGE, "fontsize": 11, "bold": True})})
            if r1.get("success") and r2.get("success"): drawn += 1
            else: fails.append(r["n"])
        print(json.dumps({"selecionadas": [(r["n"], r["date"]) for r in sel],
                          "drawn": drawn, "fails": fails}))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
