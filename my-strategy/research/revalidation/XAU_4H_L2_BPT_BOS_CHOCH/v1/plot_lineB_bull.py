#!/usr/bin/env python3
"""Plota os fundos BULL da Linha B (universo amplo) na régua oficial — long_position canônico (SL demanda −0.1ATR,
target +3R, 20-bar), label verde=ganhou/vermelho=perdeu (net let-run). Para o Cris ENXERGAR. Verified 2026-06-25."""
import sys, json, time, gzip, bisect
from pathlib import Path
V1 = Path(__file__).resolve().parent
ROOT = V1.parents[4]
sys.path.insert(0, str(ROOT / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset, SYMBOL, TIMEFRAME, PAUSE_FLAG  # noqa: E402
BAR = 14400; WIDTH = 20
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
res = json.load(open(V1 / "results/l2_bpt_lineB_broad.json"))
bull = [r for r in res if r["reg"] == "BULL"]
# demanda RAW p/ SL
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t): t = float(t); return int(t / 1000) if t > 1e11 else int(t)
ob = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if "Custom OB" not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in ob: continue
        g = next((x for x in (rec.get("pine_boxes") or []) if "Custom OB" in str(x.get("name", ""))), None)
        if g: ob[at] = [(z["high"], z["low"]) for z in (g.get("zones") or []) if z.get("high") is not None]
obt = sorted(ob)
def sl_of(i):
    et = TS[i]; entry = C[i]; k = bisect.bisect_right(obt, et) - 1
    zs = ob.get(obt[k], []) if k >= 0 else []; below = [(hi, lo) for hi, lo in zs if hi <= entry]
    return (max(below, key=lambda z: z[0])[1] - 0.1 * ATR[i]) if below else (min(L[max(0, i - 5):i + 1]) - 0.1 * ATR[i])
print(f"BULL fundos = {len(bull)} | winners={sum(1 for r in bull if r['net']>0)} losers={sum(1 for r in bull if r['net']<=0)} runners={sum(1 for r in bull if r['lr']>=5)}")
if not PAUSE_FLAG.exists(): print("ERRO pause"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for r in bull:
    i = r["i"]; entry = C[i]; sl = sl_of(i); risk = entry - sl
    if risk <= 0: continue
    tgt = entry + 3 * risk; et = TS[i]
    r1 = cli.call_tool("draw_shape", {"shape": "long_position", "point": {"time": et, "price": entry},
        "point2": {"time": et + WIDTH * BAR, "price": tgt},
        "overrides": json.dumps({"stopLevel": price_to_ticks_offset(entry, sl), "profitLevel": price_to_ticks_offset(entry, tgt)})})
    if r1.get("success"): drawn += 1
    col = "#1a8917" if r["net"] > 0 else "#cc0000"
    cli.call_tool("draw_shape", {"shape": "text", "point": {"time": et, "price": entry + 0.5 * risk},
        "text": f"{'+' if r['lr']>0 else ''}{r['lr']:.1f}R", "overrides": json.dumps({"color": col, "bold": True, "fontsize": 11})})
print(f"desenhados {drawn} long_position BULL (verde win/vermelho loss); chart NAO restaurado")
cli.stop()
