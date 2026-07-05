#!/usr/bin/env python3
"""SM probe 9 — dedup por EPISODIO de pullback (outcome-blind, fecha o desenho).

Mesmo nucleo do probe 8 (E1 borda reclaim BUF 0.15 + E2 fresco<=24 + paciencia +
C1 HL + C2 CHoCH<=32 + C3 >=1 de {retrace .25-.75, quiet30<=1.15}).
DEDUP novo: episodio = identidade do high da janela 96 (timestamp da barra do high).
  1 sinal por episodio (primeira barra qualificada); cooldown residual 24 barras
  entre episodios distintos.
Grade final: paciencia AGE>=8 vs >=16 (2 looks; acumulado 28).
"""
import json, bisect, glob, datetime as dt, collections
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
T35_SPAN = (T35[0] - 86400, T35[-1] + 86400)
W = 96
BUF = 0.15

def scan(P_AGE, COOLDOWN=24):
    sigs = []; last = -10**9; fired_epi = set()
    for i in range(W + 2, len(S)):
        b, pb = S[i], S[i - 1]
        if b.get("ema21") is None or pb.get("ema21") is None: continue
        atr = b["atr"] or 1.0
        if not (b["c"] >= b["ema21"] + BUF * atr): continue
        if not (pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)): continue
        if not any(S[k]["c"] < S[k]["ema21"] for k in range(i - 24, i) if S[k].get("ema21")): continue
        if i - last <= COOLDOWN: continue
        win = S[i - W:i + 1]; lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
        jh = max(range(len(win)), key=lambda k: win[k]["h"])
        epi = win[jh]["t"]                              # identidade do episodio
        if epi in fired_epi: continue
        if len(win) - 1 - jh < P_AGE: continue
        swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
        if not (len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]): continue
        jc = bisect.bisect_right(CH_TS, b["t"]) - 1
        if not (jc >= 0 and (b["t"] - CH_TS[jc]) // 900 <= 32): continue
        hi96, lo96 = max(highs), min(lows)
        ret = (hi96 - b["c"]) / ((hi96 - lo96) or atr)
        q = quiet30_at(b["t"])
        if not ((0.25 <= ret <= 0.75) or (q is not None and q <= 1.15)): continue
        dip_low = min(lows[jh:])
        sl = dip_low - 0.1 * atr
        sigs.append(dict(i=i, t=b["t"], c=b["c"], sl=sl,
                         d_atr=(b["c"] - sl) / atr, d_usd=b["c"] - sl))
        last = i; fired_epi.add(epi)
    return sigs

def report(name, sigs):
    weeks_all = sorted({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
    wk_count = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).strftime("%G-%V") for s in sigs)
    sig_ts = [s["t"] for s in sigs]
    cov35 = [t0 for t0 in T35 if any(abs(st - t0) <= 6 * 900 for st in sig_ts)]
    in_span = sum(1 for st in sig_ts if T35_SPAN[0] <= st <= T35_SPAN[1])
    d_atr = sorted(s["d_atr"] for s in sigs); d_usd = sorted(s["d_usd"] for s in sigs)
    med = lambda a: a[len(a) // 2]; q1 = lambda a: a[len(a) // 4]; q3 = lambda a: a[3 * len(a) // 4]
    byyear = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).year for s in sigs)
    burst = collections.Counter(wk_count.values())
    zero_wk = len(weeks_all) - len(wk_count)
    idx = {t0: n for n, t0 in enumerate(T35, 1)}
    print(f"\n{name}: N={len(sigs)}  {len(sigs)/len(weeks_all):.2f}/sem  span35: {in_span} ({in_span/29:.2f}/sem)")
    print(f"  dist semanal: 0-sinal {zero_wk} sem; " + "; ".join(f"{k}/sem x{v}" for k, v in sorted(burst.items())))
    print(f"  cobertura35 = {len(cov35)}/35 -> #{sorted(idx[t] for t in cov35)}")
    print(f"  SL: {med(d_atr):.2f} ATR [{q1(d_atr):.2f}-{q3(d_atr):.2f}]  ${med(d_usd):.1f} [{q1(d_usd):.1f}-{q3(d_usd):.1f}]")
    print(f"  por-ano: {dict(sorted(byyear.items()))}")

report("EPI AGE>=8", scan(8))
report("EPI AGE>=16", scan(16))
