#!/usr/bin/env python3
"""CORREÇÃO do plot dos 4 casos RANGE: remove APENAS os desenhos que eu criei (texts 'RANGE #'
e long_positions com entry nos 4 preços), faz scroll para carregar histórico de 2025, re-plota.
Sem clear geral, sem screenshot."""
import json, sys, bisect, time
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
    c = MCPClient(); c.start()
    out = {"removed": 0, "replot": [], "fails": []}
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL or str(st.get("resolution")) != TF:
            print(json.dumps({"HARD_STOP": f"chart {st.get('symbol')}/{st.get('resolution')}"})); return 1
        # 1) remover SÓ os meus desenhos errados
        entries = {round(tmap[r["date"]][1], 2) for r in sel}
        dl = c.call_tool("draw_list")
        for sh in dl.get("shapes", dl.get("drawings", [])) or []:
            sid = sh.get("id"); nm = (sh.get("name") or sh.get("tool") or "").lower()
            txt = sh.get("text") or ""
            pts = sh.get("points") or []
            is_my_text = "RANGE #" in txt
            is_my_pos = ("position" in nm) and any(
                abs((p.get("price") or 0)-e) < 0.02 for p in pts for e in entries)
            if is_my_text or is_my_pos:
                r = c.call_tool("draw_remove_one", {"id": sid})
                if r.get("success"): out["removed"] += 1
        # 2) por período: scroll para carregar histórico, depois re-plotar
        for r in sel:
            t, px = tmap[r["date"]]
            day = r["date"][:10]
            c.call_tool("chart_scroll_to_date", {"date": day})
            time.sleep(2.5)   # dar tempo do histórico carregar
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
            if r1.get("success") and r2.get("success"): out["replot"].append([r["n"], day])
            else: out["fails"].append(r["n"])
        # 3) deixar o gráfico no primeiro caso
        c.call_tool("chart_scroll_to_date", {"date": "2025-08-01"})
        print(json.dumps(out))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
