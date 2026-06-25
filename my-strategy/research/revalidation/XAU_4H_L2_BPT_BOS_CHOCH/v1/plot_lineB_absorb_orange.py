#!/usr/bin/env python3
"""Plota os 44 trades BULL com absorb (bubble SELL cluster) ON — long_position canônico (SL demanda −0.1ATR, +3R, 20b)
+ label LARANJA com R (let-run). Verified 2026-06-25. Pre: pause flag + daemon off."""
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
bull = {r["i"]: r for r in json.load(open(V1 / "results/l2_bpt_lineB_broad.json")) if r["reg"] == "BULL"}
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t): t = float(t); return int(t / 1000) if t > 1e11 else int(t)
def pv(s):
    if s is None: return 0
    s = str(s).replace(" ", "").replace(",", "").strip(); m = 1.0
    if s[-1:] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return 0
D = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if '"ohlcv"' not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in D: continue
        g = next((x for x in (rec.get("pine_boxes") or []) if "Custom OB" in str(x.get("name", ""))), {})
        zones = [(z["high"], z["low"]) for z in (g.get("zones") or []) if z.get("high") is not None]
        bg = next((x for x in (rec.get("pine_shapes_bubbles") or []) if "Bubble" in str(x.get("name", ""))), {})
        a = bg.get("activations_per_plot") or {}
        D[at] = dict(zones=zones, sell=sum(pv(a.get(f"plot_{k}")) for k in (6, 8, 10)), large=pv(a.get("plot_10")))
DT = sorted(D)
def asof(et): k = bisect.bisect_right(DT, et) - 1; return D[DT[k]] if k >= 0 else {}
def sell10(et): return sum(D[t]["sell"] for t in [t for t in DT if t <= et][-10:])
absorb = [i for i in bull if (sell10(TS[i]) >= 2 or asof(TS[i]).get("large", 0) >= 1)]
print(f"absorb BULL = {len(absorb)}")
if not PAUSE_FLAG.exists(): print("ERRO pause"); sys.exit(1)
cli = MCPClient(); cli.start()
st = cli.call_tool("chart_get_state")
if st.get("symbol") != SYMBOL: cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
if str(st.get("resolution")) != TIMEFRAME: cli.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME}); time.sleep(1)
drawn = 0
for i in absorb:
    entry = C[i]; et = TS[i]; zs = asof(et).get("zones", []); below = [(hi, lo) for hi, lo in zs if hi <= entry]
    sl = (max(below, key=lambda z: z[0])[1] - 0.1 * ATR[i]) if below else (min(L[max(0, i - 5):i + 1]) - 0.1 * ATR[i])
    risk = entry - sl
    if risk <= 0: continue
    tgt = entry + 3 * risk
    r1 = cli.call_tool("draw_shape", {"shape": "long_position", "point": {"time": et, "price": entry},
        "point2": {"time": et + WIDTH * BAR, "price": tgt},
        "overrides": json.dumps({"stopLevel": price_to_ticks_offset(entry, sl), "profitLevel": price_to_ticks_offset(entry, tgt)})})
    if r1.get("success"): drawn += 1
    lr = bull[i]["lr"]
    cli.call_tool("draw_shape", {"shape": "text", "point": {"time": et, "price": entry + 0.5 * risk},
        "text": f"{'+' if lr>0 else ''}{lr:.1f}R", "overrides": json.dumps({"color": "#f57c00", "bold": True, "fontsize": 11})})
print(f"desenhados {drawn} long_position absorb-BULL + labels LARANJA; chart NAO restaurado")
cli.stop()
