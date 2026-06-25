#!/usr/bin/env python3
"""Plota os 23 trades REMOVIDOS pela regra conv<=1 (elimination sweep) — long_position canonico (ticks) + label R
colorido: VERDE nos 6 winners (capped_realR>0), VERMELHO nos 17 losers restantes. Reusa MCPClient + convencao de
draw_xau_4h_trades.py (NAO modifica). Diagnostico visual; nao restaura chart, nao captura screenshot. Verified 2026-06-25.
Pre: touch /tmp/claude_recheck.paused ; daemon XAU desligado."""
import sys, json, time
from pathlib import Path
V1 = Path(__file__).resolve().parent
ROOT = V1.parents[4]  # .../tradingview-mcp
sys.path.insert(0, str(ROOT / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset, SYMBOL, TIMEFRAME, PAUSE_FLAG  # noqa: E402

BAR = 14400
ATRm_TGT, ATRm_STP, HORIZON = 2.7, 1.0, 10
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
import csv
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
SW = json.load(open(V1 / "results/l2_bpt_elimination_sweep.json"))

removed = [r for r in SW if r["conv"] <= 1]
trades = []
for r in removed:
    b = r["b"]; o = OUT[b]; f = F[b]
    et = int(f["ts_epoch"]); atr = float(o["risk_atr"]); entry = float(f["close"]); realR = float(r["realR"])
    trades.append({"b": b, "dt": r["dt"], "entry_time": et, "exit_time": et + HORIZON * BAR,
                   "entry": entry, "atr": atr, "target": entry + ATRm_TGT * atr, "stop": entry - ATRm_STP * atr,
                   "realR": realR, "win": realR > 0})
nW = sum(1 for t in trades if t["win"]); nL = len(trades) - nW
print(f"conv<=1 removidos: {len(trades)} | winners(verde)={nW} losers(vermelho)={nL}")
assert nW == 6 and len(trades) == 23, f"esperado 23/6, obtido {len(trades)}/{nW}"

if not PAUSE_FLAG.exists():
    print("ERRO: pause flag ausente"); sys.exit(1)
cli = MCPClient(); print("MCP start..."); cli.start()
st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
print("draw_clear:", cli.call_tool("draw_clear"))
drawn = 0
for k, t in enumerate(sorted(trades, key=lambda x: x["entry_time"])):
    r1 = cli.call_tool("draw_shape", {"shape": "long_position",
        "point": {"time": t["entry_time"], "price": t["entry"]},
        "point2": {"time": t["exit_time"], "price": t["target"]},
        "overrides": json.dumps({"stopLevel": price_to_ticks_offset(t["entry"], t["stop"]),
                                 "profitLevel": price_to_ticks_offset(t["entry"], t["target"])})})
    if r1.get("success"): drawn += 1
    else: print(f"  #{t['b']} long_position falhou: {r1}")
    col = "#1a8917" if t["win"] else "#cc0000"
    txt = f"#{t['b']} {'+' if t['realR']>0 else ''}{t['realR']:.1f}R"
    cli.call_tool("draw_shape", {"shape": "text",
        "point": {"time": t["entry_time"], "price": t["target"] + 0.3 * t["atr"]},
        "text": txt, "overrides": json.dumps({"color": col, "bold": True, "fontsize": 12})})
print(f"desenhados: {drawn} long_position + {len(trades)} labels (verde={nW} vermelho={nL}); chart NAO restaurado")
cli.stop(); print("MCP stop.")
