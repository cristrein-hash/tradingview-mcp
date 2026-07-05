#!/usr/bin/env python3
"""SM probe 4 — SCANNER v2 outcome-blind do entry HL-RECLAIM.

Mudancas vs probe 2 (motivadas pelo diagnostico do probe 3, tudo outcome-blind):
  * RETRACAO DA PERNA medida no FUNDO do dip (nao no close do trigger):
      hi = high maximo da janela 96; leg_start = menor low ANTES do high (dentro da janela);
      dip_low = menor low DEPOIS do high; retrace_leg = (hi-dip_low)/(hi-leg_start)
  * 'esteve abaixo da EMA21' com lookback 24 barras (era 8)
  * quiet30 com limiar em grade {1.0, 1.1}
  * demais lentes iguais: HL fractal, CHoCH<=24, AGE>=8, borda de reclaim BUF=0.15, cooldown 24

Metricas permitidas: frequencia/sem, cobertura dos 35 (±6 barras), SL geometria, por-ano.
LOOK LEDGER v2: 6 linhas de grade abaixo (somadas as 6 do probe 2 = 12 looks de freq/cobertura).
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

def state_at(i):
    b = S[i]; c = b["c"]; atr = b["atr"] or 1.0
    win = S[i - W:i + 1]; lows = [x["l"] for x in win]
    jh = max(range(len(win)), key=lambda k: win[k]["h"])
    hi = win[jh]["h"]
    leg_start = min(lows[:jh + 1])
    dip_low = min(lows[jh:])
    leg = hi - leg_start
    retrace_leg = (hi - dip_low) / leg if leg > 0 else None
    swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
    hl = len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]
    jc = bisect.bisect_right(CH_TS, b["t"]) - 1
    return dict(hl=hl, hl_low=lows[swl[-1]] if swl else None, dip_low=dip_low,
                retrace_leg=retrace_leg, age=len(win) - 1 - jh,
                choch_age=(b["t"] - CH_TS[jc]) // 900 if jc >= 0 else 10**9)

def scan(BUF=0.15, LB=24, P_AGE=8, Q_MAX=1.1, RET_LO=0.30, RET_HI=0.70, CH_WIN=24, COOLDOWN=24):
    sigs = []; last = -10**9
    for i in range(W + 2, len(S)):
        b, pb = S[i], S[i - 1]
        if b.get("ema21") is None or pb.get("ema21") is None: continue
        atr = b["atr"] or 1.0
        if not (b["c"] >= b["ema21"] + BUF * atr): continue
        if not (pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)): continue
        if not any(S[k]["c"] < S[k]["ema21"] for k in range(i - LB, i) if S[k].get("ema21")): continue
        if i - last <= COOLDOWN: continue
        st = state_at(i)
        if not st["hl"]: continue
        if st["choch_age"] > CH_WIN: continue
        if st["retrace_leg"] is None or not (RET_LO <= st["retrace_leg"] <= RET_HI): continue
        if st["age"] < P_AGE: continue
        q = quiet30_at(b["t"])
        if q is None or q > Q_MAX: continue
        sl = st["hl_low"] - 0.1 * atr if st["hl_low"] is not None else st["dip_low"] - 0.1 * atr
        if b["c"] - sl < 1.0 * atr: sl = st["dip_low"] - 0.1 * atr
        sigs.append(dict(i=i, t=b["t"], c=b["c"], sl=sl,
                         dist_atr=(b["c"] - sl) / atr, dist_usd=b["c"] - sl))
        last = i
    return sigs

def report(name, sigs):
    if not sigs: print(f"{name}: 0 sinais"); return
    weeks = len({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
    sig_ts = [s["t"] for s in sigs]
    cov = sum(1 for t0 in T35 if any(abs(st - t0) <= 6 * 900 for st in sig_ts))
    in_span = sum(1 for st in sig_ts if T35_SPAN[0] <= st <= T35_SPAN[1])
    wk_span = 29
    d_atr = sorted(s["dist_atr"] for s in sigs); d_usd = sorted(s["dist_usd"] for s in sigs)
    med = lambda a: a[len(a) // 2]; q1 = lambda a: a[len(a) // 4]; q3 = lambda a: a[3 * len(a) // 4]
    byyear = {}
    for s in sigs:
        y = dt.datetime.utcfromtimestamp(s["t"]).year; byyear[y] = byyear.get(y, 0) + 1
    print(f"{name}: N={len(sigs)}  {len(sigs)/weeks:.2f}/sem  span35 {in_span} sinais ({in_span/wk_span:.2f}/sem)"
          f"  cobertura35={cov}/35  SL_atr med {med(d_atr):.2f} [{q1(d_atr):.2f}-{q3(d_atr):.2f}]"
          f"  SL$ med {med(d_usd):.1f} [{q1(d_usd):.1f}-{q3(d_usd):.1f}]  por-ano {byyear}")

GRID = [
    ("V2-a base (Q1.1 RET.30-.70)", dict()),
    ("V2-b Q1.0",                   dict(Q_MAX=1.0)),
    ("V2-c RET.25-.80",             dict(RET_LO=0.25, RET_HI=0.80)),
    ("V2-d AGE>=16",                dict(P_AGE=16)),
    ("V2-e CH_WIN=48",              dict(CH_WIN=48)),
    ("V2-f semRET",                 dict(RET_LO=0.0, RET_HI=1.0)),
]
for name, kw in GRID:
    report(name, scan(**kw))
