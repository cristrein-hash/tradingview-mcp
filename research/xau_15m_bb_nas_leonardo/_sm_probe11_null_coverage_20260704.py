#!/usr/bin/env python3
"""SM probe 11 — NULL de cobertura para a config final Z1 (outcome-blind).
Circular-shift dos indices dos sinais Z1 (mantem clustering/frequencia), 400 shifts;
distribui cobertura35 (±6 barras) sob o nulo. Valida se 6/35 e acima do acaso.
Nao e look de desenho: e o teste nulo da metrica reportada."""
import json, bisect, glob, statistics as stt
from pathlib import Path

HERE = Path(__file__).resolve().parent
series, smc = {}, {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    for e in d["smc_events"]:
        if "CHOCH" in str(e.get("text", "")).upper(): smc.setdefault((e["t"], e.get("id")), e)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]
CH_TS = sorted(e["t"] for e in smc.values())
b30 = {}
for b in S:
    key = b["t"] // 1800
    r = b30.setdefault(key, {"h": b["h"], "l": b["l"], "t_close": b["t"]})
    r["h"] = max(r["h"], b["h"]); r["l"] = min(r["l"], b["l"]); r["t_close"] = max(r["t_close"], b["t"])
B30 = sorted(b30.values(), key=lambda r: r["t_close"])
B30_CLOSE = [r["t_close"] for r in B30]; TR30 = [r["h"] - r["l"] for r in B30]
ATR30 = []; a = None
for tr in TR30:
    a = tr if a is None else (a * 13 + tr) / 14.0; ATR30.append(a)
def quiet30_at(t0):
    j = bisect.bisect_right(B30_CLOSE, t0) - 1
    return None if j < 20 else sum(TR30[j - 3:j + 1]) / 4.0 / max(1e-9, ATR30[j])

AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
T35 = sorted(r["t"] for r in AN)
W = 96; BUF = 0.15

def scan_z1():
    idxs = []; last = -10**9
    for i in range(W + 2, len(S)):
        b, pb = S[i], S[i - 1]
        if b.get("ema21") is None or pb.get("ema21") is None: continue
        atr = b["atr"] or 1.0
        if not (b["c"] >= b["ema21"] + BUF * atr): continue
        if not (pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)): continue
        if not any(S[k]["c"] < S[k]["ema21"] for k in range(i - 24, i) if S[k].get("ema21")): continue
        if i - last <= 48: continue
        win = S[i - W:i + 1]; lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
        jh = max(range(len(win)), key=lambda k: win[k]["h"])
        if len(win) - 1 - jh < 8: continue
        swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
        if not (len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]): continue
        jc = bisect.bisect_right(CH_TS, b["t"]) - 1
        if not (jc >= 0 and (b["t"] - CH_TS[jc]) // 900 <= 32): continue
        hi96, lo96 = max(highs), min(lows)
        ret = (hi96 - b["c"]) / ((hi96 - lo96) or atr)
        q = quiet30_at(b["t"])
        if not (0.25 <= ret <= 0.75 and q is not None and q <= 1.15): continue
        idxs.append(i); last = i
    return idxs

IDX = scan_z1()
N = len(S)
def cov_of(idxs):
    ts = sorted(S[i % N]["t"] for i in idxs)
    c = 0
    for t0 in T35:
        j = bisect.bisect_left(ts, t0 - 6 * 900)
        if j < len(ts) and ts[j] <= t0 + 6 * 900: c += 1
    return c

obs = cov_of(IDX)
nulls = []
for s in range(1, 401):
    shift = 137 * s  # passos grandes, evita janelas vizinhas
    nulls.append(cov_of([i + shift for i in IDX]))
nulls_sorted = sorted(nulls)
ge = sum(1 for v in nulls if v >= obs)
print(f"Z1: N sinais={len(IDX)}  cobertura obs={obs}/35")
print(f"NULL circular-shift x400: media={stt.mean(nulls):.2f}  mediana={nulls_sorted[200]}  p95={nulls_sorted[379]}  max={max(nulls)}")
print(f"P(null >= obs) = {ge/400:.3f}")
