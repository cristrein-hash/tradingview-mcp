#!/usr/bin/env python3
"""Plota o pocket CASCATA>=4 & reclaim_forte & demanda & oversold1h (N56) no chart 15M, via canon.
FONTE: recomputação determinística (lab_g selado + smc_events primitives, mesma lógica do v2) +
outcome R3. Canon 15M (MASTER §7): long_position + label #id (fontsize 12, entry+0,5R), WIDTH 10
barras, ticks offsets. EXIT = alvo 3R (árbitro). COLOR outcome-mode: verde hit-3R / vermelho não.
Filtro: cj>=2025-08-01 (limite de carregamento do chart, regra Cris); anteriores declarados.
HIGIENE DECLARADA: remove APENAS os meus shapes anteriores (long_position; text cujo conteúdo é
'#<n>'), preservando circles e text_note do Cris. HARD_STOP se chart!=XAUUSD/15. Pause flag.
Sem screenshot; verificação por draw_list."""
import sys, json, glob, bisect, re
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

U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
series = {}; EV = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]:
        series.setdefault(b["t"], b)
    EV += d["smc_events"]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

def close_at(t):
    i = bisect.bisect_right(TS, t) - 1
    return S[i]["c"] if i >= 0 else None

seen = set(); events = []
for e in sorted(EV, key=lambda x: x["t"]):
    key = (e["t"], e["text"], round(e["price"], 2))
    if key in seen or e["text"] not in ("BOS", "CHoCH"):
        continue
    seen.add(key)
    c = close_at(e["t"])
    if c is None:
        continue
    events.append({"t": e["t"], "tok": e["text"] + ("+" if c > e["price"] else "-")})
ET = [e["t"] for e in events]

def cascade(cj):
    hi = bisect.bisect_right(ET, cj)
    dirs = [events[i]["tok"] for i in range(hi) if events[i]["t"] >= cj - 192 * 900]
    n = 0
    for tok in reversed(dirs):
        if tok in ("BOS-", "CHoCH-"):
            n += 1
        else:
            break
    return n

def fv(u, k, d=None):
    v = u.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

POCKET = [u for u in U if u["cj_t"] in R3 and cascade(u["cj_t"]) >= 4
          and fv(u, "reclaim_atr", 0) >= 1.5
          and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
          and fv(u, "h1_rsi", 99) <= 42]
POCKET.sort(key=lambda u: u["cj_t"])
assert len(POCKET) == 56, len(POCKET)
trades = []
for gid, u in enumerate(POCKET, 1):
    e, sl = u["g_entry"], u["g_sl"]; risk = e - sl
    assert risk > 0
    trades.append({"gid": gid, "t": int(u["cj_t"]), "entry": round(e, 2), "sl": round(sl, 2),
                   "exit": round(e + 3 * risk, 2), "win": R3[u["cj_t"]]["R3"] >= 3,
                   "utc": dt.datetime.utcfromtimestamp(u["cj_t"]).strftime("%Y-%m-%d %H:%M")})
plot_set = [t for t in trades if t["t"] >= CUT]
wins = sum(1 for t in plot_set if t["win"])
print(f"POCKET TRIO: 56 trades (hit3R {sum(1 for t in trades if t['win'])}/56) · AGO2025+ = {len(plot_set)} "
      f"(#{plot_set[0]['gid']}–#{plot_set[-1]['gid']}, {wins}W/{len(plot_set)-wins}L) · "
      f"{56-len(plot_set)} anteriores fora do chart (declarado)")
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
    # higiene: remover SÓ os meus shapes (long_position; text '#<n>'); circles/text_note intocados
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
