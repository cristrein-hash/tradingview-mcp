#!/usr/bin/env python3
"""COPILOT/JOURNAL — leitura READ-ONLY das trades do Cris no chart 15M via MCP (P0, Cris 2026-07-19).
Deteta tag verde Text '#N razão' + pareia com Long/Short Position -> entry/SL/TP/dir (ticks 0,01).
Debounced contra o vazio-transitório do draw_list (_activeChartWidgetWV.getAllShapes() enquanto o Cris
edita). Read-only, tab pinada (tab_pin), NUNCA toca/pausa o chart. py3.9."""
import os, re, sys, time
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "alert-bridge"))
import tab_pin
from draw_xau_4h_trades import MCPClient

TICK = 0.01
TAG_RE = re.compile(r"^#(\d+)\b\s*(.*)$")


def _is_green(color):
    """Verde dominante (rgba(76,175,80,1) e afins). Robusto a variações do verde do TradingView."""
    m = re.search(r"(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", str(color or ""))
    if not m:
        return False
    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return g >= 140 and g > r + 40 and g > b + 40


def _debounced_list(c, tries=3, gap=1.5):
    """Lê draw_list até estabilizar num set NÃO-vazio idêntico 2x (evita o vazio transitório de edição)."""
    prev = None; items = []
    for _ in range(tries):
        dl = c.call_tool("draw_list") or []
        items = dl if isinstance(dl, list) else (dl.get("shapes") or dl.get("drawings") or [])
        ids = tuple(sorted(str(i.get("id")) for i in items))
        if items and ids == prev:
            return items
        prev = ids
        time.sleep(gap)
    return items                                     # último (pode ser vazio = chart vazio ou em edição)


def _nearest(tag, positions):
    if not positions:
        return None
    tt = tag.get("time") or 0; tp = tag.get("price") or 0
    return min(positions, key=lambda p: (abs((p.get("time") or 0) - tt), abs((p.get("entry") or 0) - tp)))


def read_trades():
    """Devolve {ok, trades:[{trade_id,direction,entry,sl,tp,rr,risk,reason,entity_ids,status}], raw_n}."""
    tid = tab_pin.discover_tab("15", "XAUUSD")
    if not tid:
        return {"ok": False, "reason": "sem tab 15M", "trades": []}
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        items = _debounced_list(c)
        if not items:
            return {"ok": True, "reason": "sem desenhos (ou em edição)", "trades": [], "raw_n": 0}
        props = {}
        for it in items:
            eid = it.get("id")
            p = c.call_tool("draw_get_properties", {"entity_id": eid}) or {}
            props[eid] = {"name": it.get("name"), "points": p.get("points") or [],
                          "properties": p.get("properties", {}) or {}}
    finally:
        c.stop()
    tags, positions = [], []
    for eid, d in props.items():
        pr = d["properties"]; pt0 = (d["points"] or [{}])[0]
        if d["name"] == "text":
            txt = (pr.get("text") or "").strip()
            col = pr.get("color") or pr.get("linecolor") or pr.get("textcolor")
            m = TAG_RE.match(txt)
            if m and _is_green(col):
                tags.append({"eid": eid, "num": m.group(1), "reason": m.group(2).strip(),
                             "time": pt0.get("time"), "price": pt0.get("price")})
        elif d["name"] in ("long_position", "short_position"):
            positions.append({"eid": eid, "name": d["name"], "entry": pt0.get("price"), "time": pt0.get("time"),
                              "stopLevel": pr.get("stopLevel"), "profitLevel": pr.get("profitLevel"),
                              "risk": pr.get("risk")})
    trades = []
    for t in tags:
        pos = _nearest(t, positions)
        if not pos or pos.get("entry") is None:
            trades.append({"trade_id": f"#{t['num']}", "reason": t["reason"], "status": "UNPAIRED"})
            continue
        d = "short" if pos["name"] == "short_position" else "long"
        e = pos["entry"]; sl_off = (pos["stopLevel"] or 0) * TICK; tp_off = (pos["profitLevel"] or 0) * TICK
        sl = round(e + sl_off, 2) if d == "short" else round(e - sl_off, 2)
        tp = round(e - tp_off, 2) if d == "short" else round(e + tp_off, 2)
        rr = round(abs(tp - e) / max(1e-9, abs(e - sl)), 2)
        trades.append({"trade_id": f"#{t['num']}", "direction": d, "entry": round(e, 2), "sl": sl, "tp": tp,
                       "rr": rr, "risk": pos["risk"], "reason": t["reason"],
                       "entity_ids": {"tag": t["eid"], "position": pos["eid"]}, "status": "READ"})
    return {"ok": True, "trades": trades, "raw_n": len(items)}


if __name__ == "__main__":
    import json
    print(json.dumps(read_trades(), ensure_ascii=False, indent=1))
