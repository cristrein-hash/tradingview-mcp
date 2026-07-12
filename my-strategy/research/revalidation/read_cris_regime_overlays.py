#!/usr/bin/env python3
"""LEITURA via MCP dos retângulos de correção de regime desenhados pelo CRIS sobre o plot 4H
(ordem 2026-07-12). Dump de TODOS os desenhos com properties; separa os 98 do plot (match por
cor exata + coordenadas dos segmentos do engine) dos overlays do Cris. Sem alteração no chart."""
import io, json, sys, contextlib
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
MINE_COLORS = {"#ff9800", "#4caf50", "#b22833"}
OUT = HERE/"results/cris_regime_overlays_20260712.json"

def load_engine_segments():
    spec = importlib.util.spec_from_file_location("eng", HERE/"engine_4h_regime_gate_RAW.py")
    eng = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(eng)
    segs = []; cur = None
    for i, t in enumerate(eng.TS4):
        r = eng.regime_at(t)
        if cur and cur[0] == r: cur[2] = t
        else:
            if cur: segs.append(cur)
            cur = [r, t, t]
    segs.append(cur)
    return {(s[1], s[2]) for s in segs}

def main():
    myseg = load_engine_segments()
    c = MCPClient(); c.start()
    mine, cris = [], []
    try:
        items = c.call_tool("draw_list")["shapes"]
        for it in items:
            p = c.call_tool("draw_get_properties", {"entity_id": it["id"]})
            pts = p.get("points") or []
            pr = p.get("properties") or {}
            times = sorted(pt["time"] for pt in pts) if pts else []
            rec = {"id": it["id"], "name": it["name"], "points": pts,
                   "color": pr.get("color"), "bg": pr.get("backgroundColor"),
                   "transparency": pr.get("transparency"), "text": pr.get("text") or p.get("text")}
            is_mine = (it["name"] == "rectangle" and pr.get("color") in MINE_COLORS
                       and len(times) == 2 and (times[0], times[1]) in myseg)
            (mine if is_mine else cris).append(rec)
    finally:
        c.stop()
    OUT.write_text(json.dumps({"mine_n": len(mine), "cris": cris}, indent=1, ensure_ascii=False))
    print("meus (match engine):", len(mine), "| do Cris/outros:", len(cris))
    for r in cris:
        ts = sorted(pt["time"] for pt in (r["points"] or []))
        px = sorted(pt["price"] for pt in (r["points"] or []))
        import datetime as dt
        w = [dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d") for t in ts]
        print(f"{r['name']:<10} {r['id']} cor {r['color']} bg {r['bg']} janela {w} px {[round(x,0) for x in px]} text={str(r['text'])[:60]}")

if __name__ == "__main__":
    main()
