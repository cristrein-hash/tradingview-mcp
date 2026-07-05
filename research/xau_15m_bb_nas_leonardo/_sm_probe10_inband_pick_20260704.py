#!/usr/bin/env python3
"""SM probe 10 — escolha final DENTRO da banda 1-3/sem (outcome-blind).

3 candidatos (nucleo comum: borda reclaim BUF0.15 + fresco<=24 + HL + CHoCH<=32):
  Z1: + retrace[.25,.75] E quiet30<=1.15 (ambos), AGE>=8,  cooldown 48
  Z2: + >=1 de {retrace, quiet},          AGE>=24, cooldown 48
  Z3: + retrace E quiet (ambos),          AGE>=16, cooldown 24
Criterio de escolha: freq em [1,3]/sem; entre validos, maior cobertura35.
Colhe tambem perfil geometrico dos sinais (pullback_age, ema21_dist, retrace) p/ spec.
LOOK LEDGER probe 10: 3 linhas — ACUMULADO FINAL 31 looks de frequencia/cobertura.
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
W = 96; BUF = 0.15

def scan(P_AGE, mode_and, COOLDOWN):
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
        age = len(win) - 1 - jh
        if age < P_AGE: continue
        swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
        if not (len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]): continue
        jc = bisect.bisect_right(CH_TS, b["t"]) - 1
        if not (jc >= 0 and (b["t"] - CH_TS[jc]) // 900 <= 32): continue
        hi96, lo96 = max(highs), min(lows)
        ret = (hi96 - b["c"]) / ((hi96 - lo96) or atr)
        q = quiet30_at(b["t"])
        rok = 0.25 <= ret <= 0.75; qok = q is not None and q <= 1.15
        if mode_and and not (rok and qok): continue
        if not mode_and and not (rok or qok): continue
        dip_low = min(lows[jh:])
        sl = dip_low - 0.1 * atr
        sigs.append(dict(i=i, t=b["t"], c=b["c"], sl=sl, age=age, ret=round(ret, 2),
                         e21d=round((b["c"] - b["ema21"]) / atr, 2),
                         d_atr=(b["c"] - sl) / atr, d_usd=b["c"] - sl))
        last = i
    return sigs

def report(name, sigs):
    weeks_all = sorted({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
    wk_count = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).strftime("%G-%V") for s in sigs)
    sig_ts = [s["t"] for s in sigs]
    cov35 = [t0 for t0 in T35 if any(abs(st - t0) <= 6 * 900 for st in sig_ts)]
    in_span = sum(1 for st in sig_ts if T35_SPAN[0] <= st <= T35_SPAN[1])
    med = lambda a: sorted(a)[len(a) // 2]; q1 = lambda a: sorted(a)[len(a) // 4]; q3 = lambda a: sorted(a)[3 * len(a) // 4]
    d_atr = [s["d_atr"] for s in sigs]; d_usd = [s["d_usd"] for s in sigs]
    byyear = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).year for s in sigs)
    burst = collections.Counter(wk_count.values())
    idx = {t0: n for n, t0 in enumerate(T35, 1)}
    print(f"\n{name}: N={len(sigs)}  {len(sigs)/len(weeks_all):.2f}/sem  span35 {in_span} ({in_span/29:.2f}/sem)")
    print(f"  dist semanal: 0-sinal {len(weeks_all)-len(wk_count)} sem; " + "; ".join(f"{k}x{v}" for k, v in sorted(burst.items())))
    print(f"  cobertura35 = {len(cov35)}/35 -> #{sorted(idx[t] for t in cov35)}")
    print(f"  SL {med(d_atr):.2f} ATR [{q1(d_atr):.2f}-{q3(d_atr):.2f}] ${med(d_usd):.1f} [{q1(d_usd):.1f}-{q3(d_usd):.1f}]")
    print(f"  perfil sinais: age med {med([s['age'] for s in sigs])} | ema21_dist med {med([s['e21d'] for s in sigs]):.2f} | retrace med {med([s['ret'] for s in sigs]):.2f}")
    print(f"  por-ano {dict(sorted(byyear.items()))}")

report("Z1 AND age8 cd48", scan(8, True, 48))
report("Z2 OR  age24 cd48", scan(24, False, 48))
report("Z3 AND age16 cd24", scan(16, True, 24))
