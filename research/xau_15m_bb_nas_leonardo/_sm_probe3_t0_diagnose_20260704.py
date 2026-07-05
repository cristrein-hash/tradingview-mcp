#!/usr/bin/env python3
"""SM probe 3 — diagnostico outcome-blind: em cada um dos 35 t0, quais condicoes do
esqueleto valem na barra dele? E qual a distancia do t0 ate a borda de reclaim mais
proxima? Objetivo: entender por que a cobertura ficou 4-7/35 e redesenhar o gatilho
(borda da CONJUNCAO em vez de borda do cross). Nenhum outcome lido."""
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

W = 96
def state_at(i):
    b = S[i]; c = b["c"]; atr = b["atr"] or 1.0
    win = S[i - W:i + 1]; lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
    hi96, lo96 = max(highs), min(lows)
    jh = max(range(len(win)), key=lambda k: win[k]["h"])
    swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
    jc = bisect.bisect_right(CH_TS, b["t"]) - 1
    below_recent = lambda LB: any(S[k]["c"] < S[k]["ema21"] for k in range(max(0, i - LB), i) if S[k].get("ema21"))
    return dict(
        HL=int(len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]),
        CH24=int(jc >= 0 and (b["t"] - CH_TS[jc]) // 900 <= 24),
        RET=int(0.30 <= (hi96 - c) / ((hi96 - lo96) or atr) <= 0.70),
        AGE=len(win) - 1 - jh,
        Q30=quiet30_at(b["t"]),
        ABOVE=int(b.get("ema21") is not None and c > b["ema21"]),
        BEL8=int(below_recent(8)), BEL24=int(below_recent(24)), BEL48=int(below_recent(48)),
        dist=round((c - b["ema21"]) / atr, 2) if b.get("ema21") else None,
    )

AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
T35 = sorted(r["t"] for r in AN)

# reclaim edges (BUF=0.15, LB=8) for distance diagnosis
edges = []
for i in range(W + 2, len(S)):
    b, pb = S[i], S[i - 1]
    if b.get("ema21") is None or pb.get("ema21") is None: continue
    atr = b["atr"] or 1.0
    if b["c"] >= b["ema21"] + 0.15 * atr and pb["c"] < pb["ema21"] + 0.15 * (pb["atr"] or atr) \
       and any(S[k]["c"] < S[k]["ema21"] for k in range(i - 8, i) if S[k].get("ema21")):
        edges.append(b["t"])

print(f"{'#':>2} {'utc':<17} {'HL':>2} {'CH':>2} {'RET':>3} {'AGE':>4} {'Q30':>5} {'ABV':>3} {'B8':>2} {'B24':>3} {'B48':>3} {'dist':>5} {'edge_d(bars)':>12}")
agg = dict(HL=0, CH24=0, RET=0, AGE8=0, AGE24=0, Q=0, ABOVE=0, BEL8=0, BEL24=0, BEL48=0, SKEL=0)
for n, t0 in enumerate(T35, 1):
    j = bisect.bisect_right(TS, t0) - 1
    st = state_at(j)
    je = bisect.bisect_left(edges, t0)
    cands = []
    if je < len(edges): cands.append((edges[je] - t0) // 900)
    if je > 0: cands.append((edges[je - 1] - t0) // 900)
    ed = min(cands, key=abs) if cands else None
    q = st["Q30"]
    print(f"{n:>2} {dt.datetime.utcfromtimestamp(t0):%m-%d %H:%M}     {st['HL']:>2} {st['CH24']:>2} {st['RET']:>3} {st['AGE']:>4} "
          f"{q:>5.2f} {st['ABOVE']:>3} {st['BEL8']:>2} {st['BEL24']:>3} {st['BEL48']:>3} {st['dist']:>5} {str(ed):>12}")
    agg["HL"] += st["HL"]; agg["CH24"] += st["CH24"]; agg["RET"] += st["RET"]
    agg["AGE8"] += int(st["AGE"] >= 8); agg["AGE24"] += int(st["AGE"] >= 24)
    agg["Q"] += int(q is not None and q <= 1.0); agg["ABOVE"] += st["ABOVE"]
    agg["BEL8"] += st["BEL8"]; agg["BEL24"] += st["BEL24"]; agg["BEL48"] += st["BEL48"]
    agg["SKEL"] += int(st["HL"] and st["CH24"] and st["RET"] and st["AGE"] >= 8 and st["ABOVE"])
print("\ncontagens/35:", agg)
