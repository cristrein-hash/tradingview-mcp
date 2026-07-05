#!/usr/bin/env python3
"""Plota CASCATA-EXAUSTA v0.1 (XAU15M_CASCEX) — N34 — no chart 15M, via canon.
Config: cascata SMC>=4 (known_at) & reclaim>=1,5ATR & demanda & h1_rsi<=42, MENOS veto macro-leg
(vel>=0,10 OU recent_frac>=0,5). Reusa construção determinística do macro_leg_position_veto (selada
em bb62287). Canon 15M: long_position + label #id (bold 12, entry+0,5R), width 10, exit=3R,
color outcome-mode (verde hit-3R / vermelho). Filtro AGO2025+ (limite chart), anteriores declarados.
HIGIENE (ordem Cris): remove APENAS long_position e text '#<n>' anteriores; circles/text_note
do Cris intocados. HARD_STOP se chart!=XAUUSD/15. Pause flag. Verificação por draw_list."""
import sys, json, re
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE = Path("/tmp/claude_recheck.paused")
TF, BAR_S, WIDTH = "15", 900, 10
GREEN, RED = "#1a8917", "#cc0000"
CUT = int(dt.datetime(2025, 8, 1, tzinfo=dt.timezone.utc).timestamp())

src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # constrói U, R3, POCKET (N56) e u["_ml"]
CASCEX = sorted([u for u in POCKET if u["_ml"]["vel"] < 0.10 and u["_ml"]["recent_frac"] < 0.5],
                key=lambda u: u["cj_t"])
assert len(CASCEX) == 34, len(CASCEX)
trades = []
for gid, u in enumerate(CASCEX, 1):
    e, sl = u["g_entry"], u["g_sl"]; risk = e - sl
    assert risk > 0
    trades.append({"gid": gid, "t": int(u["cj_t"]), "entry": round(e, 2), "sl": round(sl, 2),
                   "exit": round(e + 3 * risk, 2), "win": R3[u["cj_t"]]["R3"] >= 3,
                   "utc": dt.datetime.utcfromtimestamp(u["cj_t"]).strftime("%Y-%m-%d %H:%M")})
plot_set = [t for t in trades if t["t"] >= CUT]
wins = sum(1 for t in plot_set if t["win"])
print(f"CASCEX v0.1: N34 (hit3R {sum(1 for t in trades if t['win'])}/34) · AGO2025+ = {len(plot_set)} "
      f"(#{plot_set[0]['gid']}–#{plot_set[-1]['gid']}, {wins}W/{len(plot_set)-wins}L) · "
      f"{34-len(plot_set)} anteriores fora do chart (declarado)")
if "--prepare-only" in sys.argv:
    sys.exit(0)

c = MCPClient(); c.start()
rep = {"removed_mine": 0, "posicoes": 0, "labels": 0, "falhas": []}
try:
    st = c.call_tool("chart_get_state")
    sym, res = st.get("symbol"), str(st.get("resolution"))
    dl0 = c.call_tool("draw_list"); rep["before"] = dl0.get("count")
    print(f"CHART: {sym}/{res} · drawings antes: {dl0.get('count')}")
    if not str(sym).endswith("XAUUSD") or res != TF:
        c.stop(); sys.exit(f"HARD_STOP: chart={sym}/{res}")
    if "--probe-only" in sys.argv:
        c.stop(); sys.exit(0)
    if not PAUSE.exists():
        c.stop(); sys.exit("ERRO: pause flag ausente")
    for s in dl0.get("shapes", []):
        nm = s.get("name")
        if nm == "long_position":
            r = c.call_tool("draw_remove_one", {"entity_id": s["id"]})
            rep["removed_mine"] += bool(isinstance(r, dict) and r.get("success"))
        elif nm == "text":
            p = c.call_tool("draw_get_properties", {"entity_id": s["id"]})
            txt = (p.get("properties") or {}).get("text") or p.get("text") or ""
            if re.fullmatch(r"#\d+", str(txt).strip()):
                r = c.call_tool("draw_remove_one", {"entity_id": s["id"]})
                rep["removed_mine"] += bool(isinstance(r, dict) and r.get("success"))
    for t in plot_set:
        risk = t["entry"] - t["sl"]
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": t["t"], "price": t["entry"]},
            "point2": {"time": t["t"] + WIDTH * BAR_S, "price": t["exit"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(t["entry"], t["sl"]),
                                     "profitLevel": price_to_ticks_offset(t["entry"], t["exit"])})})
        if isinstance(r1, dict) and r1.get("success"):
            rep["posicoes"] += 1
        else:
            rep["falhas"].append(f"pos #{t['gid']}: {str(r1)[:40]}")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": t["t"], "price": round(t["entry"] + 0.5 * risk, 2)},
            "text": f"#{t['gid']}",
            "overrides": json.dumps({"color": GREEN if t["win"] else RED, "bold": True, "fontsize": 12})})
        if isinstance(r2, dict) and r2.get("success"):
            rep["labels"] += 1
        else:
            rep["falhas"].append(f"label #{t['gid']}: {str(r2)[:40]}")
    dl = c.call_tool("draw_list"); rep["after"] = dl.get("count")
finally:
    try:
        c.stop()
    except Exception:
        pass
print(json.dumps({k: (v if k != "falhas" else v[:8]) for k, v in rep.items()}, indent=1, ensure_ascii=False))
