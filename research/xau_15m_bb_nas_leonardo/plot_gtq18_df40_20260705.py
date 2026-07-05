#!/usr/bin/env python3
"""Plota GTQ-18 (labels LARANJA #G) e L2-DF-40 (labels AZUL #D) — janela AGO2025→fim (ordem Cris).
Sobreposição: trade em ambos os sets recebe label LARANJA (GTQ prioridade) com sufixo 'D'.
Outcome no TEXTO do label: ✓ = hit-3R, ✗ = não (cores dos labels reservadas para o SET, por ordem).
Canon: long_position (SL/alvo 3R reais) + width 10 · NO_CLEAR (CASCEX aprovada + círculos ficam).
HARD_STOP se chart != XAUUSD/15. Pause flag. Verificação draw_list."""
import sys, json
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE = Path("/tmp/claude_recheck.paused")
TF, BAR_S, WIDTH = "15", 900, 10
ORANGE, BLUE = "#e07b00", "#1560d4"
CUT = int(dt.datetime(2025, 8, 1, tzinfo=dt.timezone.utc).timestamp())

exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
H1 = [u for u in BASE if fv(u, "h1_trend", 0) == 1]
import statistics
gt = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
import bisect as bs2
BSs = sorted(BASE, key=lambda u: u["cj_t"]); BT = [u["cj_t"] for u in BSs]
for u in BASE:
    u["_gt"] = 0
for g in gt:
    j = bs2.bisect_left(BT, g["flush_t"] - 8 * 3600)
    while j < len(BT) and BT[j] <= g["flush_t"] + 8 * 3600:
        u = BSs[j]
        if abs((u["g_sl"] + 0.1 * u["g_atr"]) - g["flush_low"]) <= (u.get("g_atr") or 5.0):
            u["_gt"] = 1
        j += 1
GTm = [u for u in H1 if u["_gt"]]
FE = ["legpos60", "g_atr_spike", "g_ema21_dist", "g_sweep_depth", "n_supply_overhead"]
def qs(f, lo, hi):
    v = sorted(fv(u, f) for u in GTm if fv(u, f) is not None)
    return v[int(lo * (len(v) - 1))], v[int(hi * (len(v) - 1))]
bands = {f: qs(f, 0.25, 0.75) for f in FE}
GTQ = [u for u in H1
       if fv(u, "legpos60", 9) <= bands["legpos60"][1]
       and fv(u, "g_atr_spike", 0) >= bands["g_atr_spike"][0]
       and fv(u, "g_ema21_dist", 9) <= bands["g_ema21_dist"][1]
       and fv(u, "g_sweep_depth", -9) >= bands["g_sweep_depth"][0]
       and fv(u, "n_supply_overhead", 99) <= bands["n_supply_overhead"][1]]
DF = [u for u in BASE if fv(u, "h1_trend", 0) == 1 and fv(u, "legpos60", 9) <= 0.20
      and fv(u, "g_atr_spike", 0) >= 1.3 and fv(u, "g_ema21_dist", 9) < 0]
assert len(GTQ) == 18 and len(DF) == 40, (len(GTQ), len(DF))
gtq_cj = {u["cj_t"] for u in GTQ}
trades = []
for gid, u in enumerate(sorted(GTQ, key=lambda x: x["cj_t"]), 1):
    trades.append((u, f"#G{gid}", ORANGE, True))
did = 0
for u in sorted(DF, key=lambda x: x["cj_t"]):
    if u["cj_t"] in gtq_cj:
        continue
    did += 1
    trades.append((u, f"#D{did}", BLUE, False))
plot_set = [(u, lab, col, isg) for u, lab, col, isg in trades if u["cj_t"] >= CUT]
plot_set.sort(key=lambda x: x[0]["cj_t"])
both = sum(1 for u in DF if u["cj_t"] in gtq_cj)
print(f"GTQ 18 · DF 40 · overlap {both} → shapes únicos {len(trades)} · AGO2025+ = {len(plot_set)}")
if "--prepare-only" in sys.argv:
    for u, lab, col, isg in plot_set:
        r3 = R3[u["cj_t"]]
        print(f"  {lab:>5} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} "
              f"{'WIN' if r3['R3']>=3 else 'loss'}")
    sys.exit(0)

c = MCPClient(); c.start()
rep = {"posicoes": 0, "labels": 0, "falhas": []}
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
    # HIGIENE (ordem Cris): apagar operações CASCEX anteriores — long_position + labels '#<n>' puros;
    # círculos e notas do Cris intocados
    import re
    rep["removed_cascex"] = 0
    for s in dl0.get("shapes", []):
        nm = s.get("name")
        if nm == "long_position":
            r = c.call_tool("draw_remove_one", {"entity_id": s["id"]})
            rep["removed_cascex"] += bool(isinstance(r, dict) and r.get("success"))
        elif nm == "text":
            p = c.call_tool("draw_get_properties", {"entity_id": s["id"]})
            txt = (p.get("properties") or {}).get("text") or p.get("text") or ""
            if re.fullmatch(r"#\d+", str(txt).strip()):
                r = c.call_tool("draw_remove_one", {"entity_id": s["id"]})
                rep["removed_cascex"] += bool(isinstance(r, dict) and r.get("success"))
    for u, lab, col, isg in plot_set:
        e, sl = u["g_entry"], u["g_sl"]; risk = e - sl
        tgt = e + 3 * risk
        win = R3[u["cj_t"]]["R3"] >= 3
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": int(u["cj_t"]), "price": round(e, 2)},
            "point2": {"time": int(u["cj_t"]) + WIDTH * BAR_S, "price": round(tgt, 2)},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(e, sl),
                                     "profitLevel": price_to_ticks_offset(e, tgt)})})
        if isinstance(r1, dict) and r1.get("success"):
            rep["posicoes"] += 1
        else:
            rep["falhas"].append(f"pos {lab}")
        suffix = ("D" if (isg and u["cj_t"] in gtq_cj and any(v["cj_t"] == u["cj_t"] for v in DF)) else "")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": int(u["cj_t"]), "price": round(e + 0.5 * risk, 2)},
            "text": f"{lab}{suffix} {'✓' if win else '✗'}",
            "overrides": json.dumps({"color": col, "bold": True, "fontsize": 12})})
        if isinstance(r2, dict) and r2.get("success"):
            rep["labels"] += 1
        else:
            rep["falhas"].append(f"label {lab}")
    dl = c.call_tool("draw_list"); rep["after"] = dl.get("count")
finally:
    try:
        c.stop()
    except Exception:
        pass
print(json.dumps({k: (v if k != "falhas" else v[:8]) for k, v in rep.items()}, indent=1, ensure_ascii=False))
