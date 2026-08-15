#!/usr/bin/env python3
"""Plota no 15M os 14 trades SINALIZADOS AO GRUPO esta semana (reader+A1/A2), cor por RESULTADO.
Reutiliza a mecânica CANÓNICA de plot_today_signals.py (long_position + label §0 ticks-offset / §2 point2
no target 20 barras / §3 label #nº). Cor: verde=win, vermelho=loss, azul=aberto. Outcome forward das bars_15m.
NÃO inventa: consome os sinais reais (scratchpad) + as bars nativas. Pausar a stack ANTES (feito no bash)."""
import os, sys, json, urllib.request
from pathlib import Path
BASE = Path("/Users/cristrein/tradingview-mcp/alert-bridge")
sys.path.insert(0, str(BASE))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset

SIGS = json.load(open("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/week_group_signals.json"))
BOX_BARS = 20; BAR_S = 900
WIN = "#2e7d32"; LOSS = "#c62828"; OPEN = "#1565c0"

# outcome forward das bars_15m nativas
bars = sorted([(int(json.loads(l)["t"]), float(json.loads(l)["h"]), float(json.loads(l)["l"]))
               for l in open(BASE.parent / "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()])
def outcome(s):
    e, sl, tg = s["entry"], s["sl"], s["tgt"]
    if None in (e, sl, tg):
        return "open"
    for t, h, l in bars:
        if t <= s["t"]:
            continue
        hit_t = h >= tg; hit_s = l <= sl        # LONG: target=high>=tgt, stop=low<=sl
        if hit_s and hit_t:
            return "loss"                        # ambos na mesma barra = conservador (loss)
        if hit_s:
            return "loss"
        if hit_t:
            return "win"
    return "open"

for s in SIGS:
    s["out"] = outcome(s)
w = sum(1 for s in SIGS if s["out"] == "win"); ls = sum(1 for s in SIGS if s["out"] == "loss"); op = sum(1 for s in SIGS if s["out"] == "open")
print(f"outcomes: {w} WIN · {ls} LOSS · {op} abertos (de {len(SIGS)})")

def find_tf15():
    tabs = []
    with urllib.request.urlopen("http://localhost:9222/json/list", timeout=8) as r:
        for tt in json.loads(r.read()):
            if tt.get("type") == "page" and "tradingview.com/chart" in (tt.get("url") or "").lower():
                tabs.append(tt["id"])
    # 1) preferir uma tab já em 15M
    for tid in tabs:
        os.environ["TVMCP_TARGET_CHART_ID"] = tid
        c = MCPClient(); c.start()
        res = str((c.call_tool("chart_get_state") or {}).get("resolution")); c.stop()
        if res == "15":
            return tid
    # 2) senão, pôr a 1ª tab em 15M
    if tabs:
        tid = tabs[0]; os.environ["TVMCP_TARGET_CHART_ID"] = tid
        c = MCPClient(); c.start()
        c.call_tool("chart_set_timeframe", {"timeframe": "15"})
        res = str((c.call_tool("chart_get_state") or {}).get("resolution")); c.stop()
        if res == "15":
            print("(chart posto em 15M)")
            return tid
    return None

if "--dry" in sys.argv:
    for i, s in enumerate(SIGS, 1):
        print(f"  #{i} {s['dir']} entry {s['entry']} SL {s['sl']} tgt {s['tgt']} -> {s['out'].upper()} [{s['src']}]")
    sys.exit(0)

tid = find_tf15()
if not tid:
    print("!! sem tab 15M — abortado (chart não está em 15M; set manual ou preflight)"); sys.exit(2)
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
drawn = 0
try:
    st = c.call_tool("chart_get_state") or {}
    print("plotando na tab res", st.get("resolution"), "...")
    for i, s in enumerate(SIGS, 1):
        t0 = int(s["t"])
        r = c.call_tool("draw_shape", {
            "shape": "long_position", "point": {"time": t0, "price": s["entry"]},
            "point2": {"time": t0 + BOX_BARS * BAR_S, "price": s["tgt"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(s["entry"], s["sl"]),
                                     "profitLevel": price_to_ticks_offset(s["entry"], s["tgt"])})})
        if r.get("success"):
            drawn += 1
            col = {"win": WIN, "loss": LOSS}.get(s["out"], OPEN)
            Rd = abs(s["entry"] - s["sl"])
            label_y = s["entry"] + 0.5 * Rd
            c.call_tool("draw_shape", {"shape": "text", "point": {"time": t0, "price": label_y},
                        "text": f"#{i} {s['out'].upper()}", "overrides": json.dumps({"color": col, "bold": True, "fontsize": 12})})
        else:
            print(f"  falhou #{i} @{t0}: {r}")
    print(f"desenhados {drawn}/{len(SIGS)} no 15M (verde=win vermelho=loss azul=aberto)")
finally:
    c.stop()
