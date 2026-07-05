#!/usr/bin/env python3
"""Plota os 54 sinais RWS-15M (engine sequencial, hardening 2026-07-05) no chart 15M, via canon.
FONTE: results/rws15m_signals_20260705.json (SELADO, sha verificado) + alvo R3 (outcome).
Canon 15M (MASTER §7): long_position + label #id (fontsize 12, entry+0,5R), WIDTH 10 barras,
ticks 0.01 offsets. EXIT = alvo 3R first-touch (o árbitro do engine): exit=entry+3*risk.
COLOR = outcome-mode (§8): verde se hit3R (R3>=3) / vermelho senão. Label #id GLOBAL cronológico 1-54.
Limite de chart (Cris): 15M carrega a partir de AGO/2025 → plota subconjunto entry>=2025-08-01,
conta e declara os anteriores (sem sampling silencioso). NO_CLEAR default (nenhuma remoção; mantém
desenhos do Cris). HARD_STOP se chart != XAUUSD/15. Sem screenshot; verificação por draw_list. Pause flag."""
import sys, json, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S, WIDTH = "PEPPERSTONE:XAUUSD", "15", 900, 10
GREEN, RED = "#1a8917", "#cc0000"
CUTOFF_AUG2025 = int(dt.datetime(2025, 8, 1, tzinfo=dt.timezone.utc).timestamp())

# fonte selada + outcome
SIG = HERE / "results" / "rws15m_signals_20260705.json"
sha = hashlib.sha256(SIG.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "rws15m_signals_20260705.sha256").read_text().split()[0], "selo violado"
sig = json.load(open(SIG))
assert len(sig) == 54, len(sig)
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
trades = []
for gid, s in enumerate(sorted(sig, key=lambda x: x["cj_t"]), 1):
    risk = s["entry"] - s["sl"]
    assert risk > 0
    hit = R3[s["cj_t"]]["R3"] >= 3
    trades.append({"gid": gid, "t": int(s["cj_t"]), "entry": round(s["entry"], 2), "sl": round(s["sl"], 2),
                   "exit": round(s["entry"] + 3 * risk, 2), "win": hit,
                   "utc": dt.datetime.utcfromtimestamp(s["cj_t"]).strftime("%Y-%m-%d %H:%M")})
plot_set = [t for t in trades if t["t"] >= CUTOFF_AUG2025]
skip = len(trades) - len(plot_set)
wins = sum(1 for t in plot_set if t["win"])
print(f"RWS-15M: 54 sinais (hit3R {sum(1 for t in trades if t['win'])}/54) · "
      f"plot AGO2025+ = {len(plot_set)} (#{plot_set[0]['gid']}–#{plot_set[-1]['gid']}, {wins}W/{len(plot_set)-wins}L) · "
      f"{skip} anteriores fora do chart (declarado)")

if "--prepare-only" in sys.argv:
    print("prepare-only: sem MCP/chart."); sys.exit(0)
c = MCPClient(); c.start()
report = {"posicoes": 0, "labels": 0, "falhas": [], "removed": 0}
try:
    st = c.call_tool("chart_get_state")
    sym, res = st.get("symbol"), str(st.get("resolution"))
    dl0 = c.call_tool("draw_list")
    print(f"CHART: {sym}/{res} · drawings existentes: {dl0.get('count')}")
    report["before"] = dl0.get("count")
    if "--probe-only" in sys.argv: c.stop(); sys.exit(0)
    if not str(sym).endswith("XAUUSD") or res != TF:
        c.stop(); sys.exit(f"HARD_STOP: chart={sym}/{res} (esperado XAUUSD/15 — não troco TF)")
    if not PAUSE.exists():
        c.stop(); sys.exit("ERRO: pause flag ausente (touch /tmp/claude_recheck.paused)")
    for t in plot_set:
        risk = t["entry"] - t["sl"]
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": t["t"], "price": t["entry"]},
            "point2": {"time": t["t"] + WIDTH * BAR_S, "price": t["exit"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(t["entry"], t["sl"]),
                                     "profitLevel": price_to_ticks_offset(t["entry"], t["exit"])})})
        if isinstance(r1, dict) and r1.get("success"): report["posicoes"] += 1
        else: report["falhas"].append(f"pos #{t['gid']} {t['utc']}: {str(r1)[:50]}")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": t["t"], "price": round(t["entry"] + 0.5 * risk, 2)},
            "text": f"#{t['gid']}",
            "overrides": json.dumps({"color": GREEN if t["win"] else RED, "bold": True, "fontsize": 12})})
        if isinstance(r2, dict) and r2.get("success"): report["labels"] += 1
        else: report["falhas"].append(f"label #{t['gid']}: {str(r2)[:50]}")
    dl = c.call_tool("draw_list"); report["after"] = dl.get("count")
finally:
    try: c.stop()
    except Exception: pass
print(json.dumps({k: (v if k != "falhas" else v[:8]) for k, v in report.items()}, indent=1, ensure_ascii=False))
