#!/usr/bin/env python3
"""Plota a UNIÃO 65 (2026-07-06, ordem Cris): 20 CAPITULAÇÃO em LARANJA (#C), 45 SUAVE em AZUL (#S).
Apaga trades plotados anteriormente (long_position + labels de trade), NÃO apaga círculos/notas do Cris.
Canon: long_position (SL/alvo 3R reais) + width 10 · price_to_ticks · HARD_STOP se chart!=XAUUSD/15 ·
pause flag. Outcome no texto: ✓ = hit-3R, ✗ = não (cor reservada ao TIPO por ordem)."""
import sys, json, re
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE = Path("/tmp/claude_recheck.paused")
TF, BAR_S, WIDTH = "15", 900, 10
ORANGE, BLUE = "#e07b00", "#1560d4"
# recomputa cap/soft do soft_layer (reusa EV, FAM, lay_cap, lay_soft, R3)
import os
os.chdir(HERE)
exec(open(HERE / "event_soft_layer_20260706.py").read().split('print(f"eventos')[0])
cap = lay_cap()
soft = lay_soft(38, "poc")
cap_t = {u["cj_t"] for u in cap}
signals = []
for gid, u in enumerate(sorted(cap, key=lambda x: x["cj_t"]), 1):
    signals.append((u, f"#C{gid}", ORANGE))
sid = 0
for u in sorted(soft, key=lambda x: x["cj_t"]):
    if u["cj_t"] in cap_t:
        continue
    sid += 1
    signals.append((u, f"#S{sid}", BLUE))
signals.sort(key=lambda x: x[0]["cj_t"])
print(f"CAP {len(cap)} · SOFT {len(soft)} · overlap {sum(1 for u in soft if u['cj_t'] in cap_t)} → únicos {len(signals)}")
if "--prepare-only" in sys.argv:
    for u, lab, col in signals:
        r3 = R3[u["cj_t"]]
        print(f"  {lab:>5} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} "
              f"{'WIN' if r3['R3']>=3 else 'loss'}")
    sys.exit(0)

TRADE_RE = re.compile(r"^#[A-Z]?\d+")   # #C.. #S.. #G.. #D.. #N.. (trades); círculos/notas não casam
c = MCPClient(); c.start()
rep = {"posicoes": 0, "labels": 0, "falhas": [], "removed": 0}
try:
    st = c.call_tool("chart_get_state")
    sym, res = st.get("symbol"), str(st.get("resolution"))
    dl0 = c.call_tool("draw_list"); rep["before"] = dl0.get("count")
    print(f"CHART: {sym}/{res} · antes: {dl0.get('count')}")
    if not str(sym).endswith("XAUUSD") or res != TF:
        c.stop(); sys.exit(f"HARD_STOP: chart={sym}/{res}")
    if "--probe-only" in sys.argv:
        c.stop(); sys.exit(0)
    if not PAUSE.exists():
        c.stop(); sys.exit("ERRO: pause flag ausente")
    # HIGIENE: apagar trades anteriores (long_position + labels de trade); círculos/notas do Cris intocados
    for s in dl0.get("shapes", []):
        nm = s.get("name")
        if nm == "long_position":
            r = c.call_tool("draw_remove_one", {"entity_id": s["id"]})
            rep["removed"] += bool(isinstance(r, dict) and r.get("success"))
        elif nm == "text":
            p = c.call_tool("draw_get_properties", {"entity_id": s["id"]})
            txt = (p.get("properties") or {}).get("text") or p.get("text") or ""
            if TRADE_RE.match(str(txt).strip()):
                r = c.call_tool("draw_remove_one", {"entity_id": s["id"]})
                rep["removed"] += bool(isinstance(r, dict) and r.get("success"))
    for u, lab, col in signals:
        e, sl = u["g_entry"], u["g_sl"]; risk = e - sl; tgt = e + 3 * risk
        win = R3[u["cj_t"]]["R3"] >= 3
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": int(u["cj_t"]), "price": round(e, 2)},
            "point2": {"time": int(u["cj_t"]) + WIDTH * BAR_S, "price": round(tgt, 2)},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(e, sl),
                                     "profitLevel": price_to_ticks_offset(e, tgt)})})
        rep["posicoes"] += bool(isinstance(r1, dict) and r1.get("success")) or rep["falhas"].append(f"pos {lab}")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": int(u["cj_t"]), "price": round(e + 0.5 * risk, 2)},
            "text": f"{lab} {'✓' if win else '✗'}",
            "overrides": json.dumps({"color": col, "bold": True, "fontsize": 12})})
        rep["labels"] += bool(isinstance(r2, dict) and r2.get("success")) or rep["falhas"].append(f"lab {lab}")
    dl = c.call_tool("draw_list"); rep["after"] = dl.get("count")
finally:
    try: c.stop()
    except Exception: pass
print(json.dumps({k: (v if k != "falhas" else v[:8]) for k, v in rep.items()}, indent=1, ensure_ascii=False))
