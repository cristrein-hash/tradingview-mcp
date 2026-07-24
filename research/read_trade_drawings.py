#!/usr/bin/env python3
"""LER os position-drawings frescos via MCP PINADO por tab (procedimento salvo: tab_pin.py + TVMCP_TARGET_CHART_ID
antes do MCPClient.start()). Os tools do Claude Code estão presos a um pin antigo; aqui pinamos cada tab XAU
(5M/15M/1H/4H) e lemos draw_list + draw_get_properties dessa tab, achando os trades com entry ~4039.49/4046.43.
SL/TP derivados das linhas do desenho (stopLevel/profitLevel ÷100 = distância em $, direção-aware). py3.9.
"""
import os, sys, json
HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE)
sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient

RES = ["5", "15", "60", "240"]


def sltp(entry, name, stop_lvl, prof_lvl):
    d = (stop_lvl or 0) / 100.0
    t = (prof_lvl or 0) / 100.0
    if name == "short_position":
        return round(entry + d, 2), round(entry - t, 2)  # SL acima, TP abaixo
    return round(entry - d, 2), round(entry + t, 2)       # long: SL abaixo, TP acima


found = []
for res in RES:
    tid = None
    try:
        tid = tab_pin.discover_tab(res, symbol_suffix="XAUUSD")
    except Exception as e:
        print(f"[{res}] discover erro: {str(e)[:60]}"); continue
    if not tid:
        print(f"[{res}] sem tab"); continue
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = None
    try:
        c = MCPClient(); c.start()
        dl = c.call_tool("draw_list") or {}
        shapes = dl.get("shapes", [])
        positions = [s for s in shapes if s.get("name") in ("long_position", "short_position")]
        print(f"[{res}] tab {tid[:8]} · {len(shapes)} desenhos · {len(positions)} posições")
        for s in positions:
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            entry = pts[0]["price"] if pts else None
            props = pr.get("properties", {})
            sl, tp = (sltp(entry, s["name"], props.get("stopLevel"), props.get("profitLevel"))
                      if entry is not None else (None, None))
            rec = {"res": res, "id": s["id"], "name": s["name"], "entry": entry, "sl": sl, "tp": tp,
                   "stopLevel": props.get("stopLevel"), "profitLevel": props.get("profitLevel")}
            found.append(rec)
            direc = "SHORT" if s["name"] == "short_position" else "LONG"
            print(f"    {direc:5} {s['id']} entry {entry} · SL {sl} · TP {tp}")
    except Exception as e:
        print(f"[{res}] MCP erro: {str(e)[:80]}")
    finally:
        try:
            if c: c.stop()
        except Exception: pass

print("\n=== MATCH com as entries do Cris (SELL 4039.49 / BUY 4046.43) ===")
for r in found:
    e = r["entry"]
    if e is None: continue
    if abs(e - 4039.49) < 0.6 or abs(e - 4046.43) < 0.6:
        print(f"  ★ {r['name']} entry {e} · SL {r['sl']} · TP {r['tp']}  (res {r['res']}, {r['id']})")
print(f"\ntotal posições lidas: {len(found)}")
