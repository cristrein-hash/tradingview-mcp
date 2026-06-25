#!/usr/bin/env python3
"""RE-PLOT canonico dos 23 trades conv<=1 (CANONICAL_TRADE_PLOTTING.md): long_position LARGURA 20 BARRAS +
SL ESTRUTURAL (SL_CONTEXTUAL adotado = sl_context_policy.sl_atr, demanda defendida repaint-audited) + TARGET +3R
(entry+3*(entry-SL), canon §4) + label #id colorido pelo resultado OFICIAL capped_realR (verde win / vermelho loss).
Box = geometria de risco estrutural; cor = outcome oficial. NAO chama draw_clear (Cris ja limpou; canon §6).
Verified 2026-06-25. Pre: pause flag + daemon XAU off."""
import sys, json, time, csv
from pathlib import Path
V1 = Path(__file__).resolve().parent
ROOT = V1.parents[4]
sys.path.insert(0, str(ROOT / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset, SYMBOL, TIMEFRAME, PAUSE_FLAG  # noqa: E402

BAR = 14400; WIDTH_BARS = 20; TARGET_R = 3.0
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
SLCTX = {}
for r in csv.DictReader(open(V1 / "results/l2_bpt_sl_context_policy_results.csv")):
    k = r.get("bar_idx") or list(r.values())[0]
    try: SLCTX[int(float(k))] = float(r["sl_atr"])
    except Exception: pass
SW = json.load(open(V1 / "results/l2_bpt_elimination_sweep.json"))

rem = sorted([r for r in SW if r["conv"] <= 1], key=lambda r: r["dt"])
trades = []
for r in rem:
    b = r["b"]; o = OUT[b]; f = F[b]
    et = int(f["ts_epoch"]); atr = float(o["risk_atr"]); entry = float(f["close"])
    sl_dist = SLCTX[b] * atr                      # SL estrutural em preco
    sl = entry - sl_dist; tgt = entry + TARGET_R * sl_dist
    realR = float(r["realR"])
    trades.append({"b": b, "entry_time": et, "exit_time": et + WIDTH_BARS * BAR, "entry": entry,
                   "sl": sl, "tgt": tgt, "sl_atr": SLCTX[b], "realR": realR, "win": realR > 0})
nW = sum(1 for t in trades if t["win"])
assert len(trades) == 23 and nW == 6, f"esperado 23/6 obtido {len(trades)}/{nW}"
wide = [t["b"] for t in trades if t["sl_atr"] > 4]
print(f"23 trades | win(verde)={nW} loss(vermelho)={23-nW} | SL>4ATR(review): {wide}")

if not PAUSE_FLAG.exists(): print("ERRO pause flag"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for t in trades:
    assert t["entry"] > t["sl"] and t["tgt"] > t["entry"]
    r1 = cli.call_tool("draw_shape", {"shape": "long_position",
        "point": {"time": t["entry_time"], "price": t["entry"]},
        "point2": {"time": t["exit_time"], "price": t["tgt"]},
        "overrides": json.dumps({"stopLevel": price_to_ticks_offset(t["entry"], t["sl"]),
                                 "profitLevel": price_to_ticks_offset(t["entry"], t["tgt"])})})
    if r1.get("success"): drawn += 1
    else: print(f"  #{t['b']} long_position falhou: {r1}")
    Rd = t["entry"] - t["sl"]
    cli.call_tool("draw_shape", {"shape": "text",
        "point": {"time": t["entry_time"], "price": t["entry"] + 0.5 * Rd},
        "text": f"#{t['b']} {'+' if t['realR']>0 else ''}{t['realR']:.1f}R",
        "overrides": json.dumps({"color": "#1a8917" if t["win"] else "#cc0000", "bold": True, "fontsize": 12})})
print(f"desenhados: {drawn} long_position (20-bar, SL estrutural, target +3R) + {len(trades)} labels; chart NAO restaurado")
cli.stop()
