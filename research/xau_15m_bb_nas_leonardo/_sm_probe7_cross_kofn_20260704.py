#!/usr/bin/env python3
"""SM probe 7 — sintese final: borda do CROSS da EMA21 (controle de frequencia)
+ convergencia K-de-4 (cobertura), paciencia obrigatoria. Outcome-blind.

TRIGGER (close da barra i):
  E1 borda: c[i] >= ema21[i] + BUF*atr  E  c[i-1] < ema21[i-1] + BUF*atr[i-1]
  E2 fresco: algum close < ema21 nas ultimas 24 barras
  M2 paciencia: pullback_age >= 8
  SCORE >= K de 4: HL | CHoCH<=32b | retrace box96 no close em [0.25,0.75] | quiet30<=1.15
  cooldown 24 barras
SL: fundo da perna (min low desde high96) - 0.1*ATR (variante hl_low reportada).
LOOK LEDGER probe 7: 6 linhas (BUF, K) — total acumulado 24 looks de freq/cobertura.
"""
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
T35_SPAN = (T35[0] - 86400, T35[-1] + 86400)
W = 96

def scan(BUF, K, COOLDOWN=24):
    sigs = []; last = -10**9
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
        if len(win) - 1 - jh < 8: continue
        hi96, lo96 = max(highs), min(lows)
        ret = (hi96 - b["c"]) / ((hi96 - lo96) or atr)
        swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
        hl = len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]
        jc = bisect.bisect_right(CH_TS, b["t"]) - 1
        ch = jc >= 0 and (b["t"] - CH_TS[jc]) // 900 <= 32
        q = quiet30_at(b["t"])
        score = int(hl) + int(ch) + int(0.25 <= ret <= 0.75) + int(q is not None and q <= 1.15)
        if score < K: continue
        dip_low = min(lows[jh:])
        sl = dip_low - 0.1 * atr
        sl_hl = (lows[swl[-1]] - 0.1 * atr) if swl else sl
        sigs.append(dict(i=i, t=b["t"], c=b["c"], score=score,
                         d_atr=(b["c"] - sl) / atr, d_usd=b["c"] - sl,
                         dhl_atr=(b["c"] - sl_hl) / atr))
        last = i
    return sigs

def report(name, sigs):
    if not sigs: print(f"{name}: 0 sinais"); return
    weeks = len({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
    sig_ts = [s["t"] for s in sigs]
    cov35 = [t0 for t0 in T35 if any(abs(st - t0) <= 6 * 900 for st in sig_ts)]
    in_span = sum(1 for st in sig_ts if T35_SPAN[0] <= st <= T35_SPAN[1])
    d_atr = sorted(s["d_atr"] for s in sigs); d_usd = sorted(s["d_usd"] for s in sigs)
    dhl = sorted(s["dhl_atr"] for s in sigs)
    med = lambda a: a[len(a) // 2]; q1 = lambda a: a[len(a) // 4]; q3 = lambda a: a[3 * len(a) // 4]
    byyear = {}
    for s in sigs:
        y = dt.datetime.utcfromtimestamp(s["t"]).year; byyear[y] = byyear.get(y, 0) + 1
    print(f"{name}: N={len(sigs)} {len(sigs)/weeks:.2f}/sem | span35 {in_span} ({in_span/29:.2f}/sem)"
          f" | cobertura35={len(cov35)}/35 | SLdip_atr {med(d_atr):.2f}[{q1(d_atr):.2f}-{q3(d_atr):.2f}]"
          f" SLdip$ {med(d_usd):.1f}[{q1(d_usd):.1f}-{q3(d_usd):.1f}] SLhl_atr {med(dhl):.2f}"
          f" | por-ano {byyear}")
    return cov35

GRID = [
    ("X1 BUF=0.15 K=2", dict(BUF=0.15, K=2)),
    ("X2 BUF=0.15 K=3", dict(BUF=0.15, K=3)),
    ("X3 BUF=0.10 K=2", dict(BUF=0.10, K=2)),
    ("X4 BUF=0.10 K=3", dict(BUF=0.10, K=3)),
    ("X5 BUF=0.00 K=2", dict(BUF=0.00, K=2)),
    ("X6 BUF=0.15 K=4", dict(BUF=0.15, K=4)),
]
res = {}
for name, kw in GRID:
    res[name] = report(name, scan(**kw))

# quais dos 35 sao cobertos na config X1 (detalhe)
cov = res.get("X1 BUF=0.15 K=2") or []
idx = {t0: n for n, t0 in enumerate(sorted(T35), 1)}
print("\nX1 cobre trades #:", sorted(idx[t] for t in cov))
