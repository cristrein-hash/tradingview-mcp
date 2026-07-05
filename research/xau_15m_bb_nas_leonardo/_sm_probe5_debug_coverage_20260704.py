#!/usr/bin/env python3
"""SM probe 5 — debug: por que cobertura35 caiu a 0 no scanner v2?
Para cada t0: distancia (barras) ao sinal v2 mais proximo; e na janela t0±6,
para cada barra com borda de reclaim, qual condicao do v2 falha. Outcome-blind."""
import json, bisect, glob, datetime as dt
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
W = 96

def edge_at(i, BUF=0.15, LB=24):
    b, pb = S[i], S[i - 1]
    if b.get("ema21") is None or pb.get("ema21") is None: return False
    atr = b["atr"] or 1.0
    return (b["c"] >= b["ema21"] + BUF * atr
            and pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)
            and any(S[k]["c"] < S[k]["ema21"] for k in range(i - LB, i) if S[k].get("ema21")))

def conds(i, Q_MAX=1.1, RET_LO=0.30, RET_HI=0.70, P_AGE=8, CH_WIN=24):
    b = S[i]; atr = b["atr"] or 1.0
    win = S[i - W:i + 1]; lows = [x["l"] for x in win]
    jh = max(range(len(win)), key=lambda k: win[k]["h"]); hi = win[jh]["h"]
    leg_start = min(lows[:jh + 1]); dip_low = min(lows[jh:]); leg = hi - leg_start
    rl = (hi - dip_low) / leg if leg > 0 else None
    swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
    hl = len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]
    jc = bisect.bisect_right(CH_TS, b["t"]) - 1
    ch_age = (b["t"] - CH_TS[jc]) // 900 if jc >= 0 else 10**9
    age = len(win) - 1 - jh
    q = quiet30_at(b["t"])
    fails = []
    if not hl: fails.append("HL")
    if ch_age > CH_WIN: fails.append(f"CH({ch_age})")
    if rl is None or not (RET_LO <= rl <= RET_HI): fails.append(f"RETleg({rl:.2f})" if rl is not None else "RETleg(None)")
    if age < P_AGE: fails.append(f"AGE({age})")
    if q is None or q > Q_MAX: fails.append(f"Q({q:.2f})" if q is not None else "Q(None)")
    return fails

# rebuild v2-a signals for nearest-distance
def scan():
    sigs = []; last = -10**9
    for i in range(W + 2, len(S)):
        if not edge_at(i): continue
        if i - last <= 24: continue
        if conds(i): continue
        sigs.append(i); last = i
    return sigs
sig_i = scan()
sig_ts = [S[i]["t"] for i in sig_i]
print(f"v2-a sinais: {len(sig_i)}")

for n, t0 in enumerate(T35, 1):
    j = bisect.bisect_right(TS, t0) - 1
    nd = min((abs(st - t0) // 900 for st in sig_ts), default=None)
    lines = []
    for i in range(max(W + 2, j - 6), min(len(S), j + 7)):
        if edge_at(i):
            f = conds(i)
            lines.append(f"d={i-j:+d} fails={','.join(f) if f else 'NENHUMA(sinal!)'}")
    print(f"#{n:>2} {dt.datetime.utcfromtimestamp(t0):%m-%d %H:%M}  sinal_mais_proximo={nd} barras  bordas±6: {'; '.join(lines) if lines else '—'}")
