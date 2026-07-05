#!/usr/bin/env python3
"""SM probe 6 — DESENHO FINAL 'HL-RECLAIM K-de-N' (outcome-blind).

Correcoes vs v2 (probe 4/5):
  * RETleg abandonada (quebrava quando a perna de alta > janela 96) -> volta a lente
    SOBREVIVENTE original: retrace box96 no CLOSE (1.27x no mapa reprecificado)
  * borda da CONJUNCAO (estado completo vira verdadeiro), nao borda do cross da EMA21
  * nucleo obrigatorio (timing/arquetipo) + score K-de-4 nas lentes estruturais
    (convergencia, nao conjuncao dura — coerente com 'eliminacao convergente')

NUCLEO (obrigatorio, close da barra i):
  M1 RECLAIM fresco: c > ema21  E  algum close < ema21 nas ultimas 24 barras
  M2 PACIENCIA:      pullback_age >= 8 (barras desde o high da janela 96)
  M3 NAO-PERSEGUIR:  (c - ema21)/atr <= DCAP
SCORE (>= K de 4):
  HL (fractal ±2, ultimo > penultimo na janela 96)
  CHOCH <= 32 barras
  RETRACE box96 no close em [0.25, 0.75]
  QUIET30 <= 1.15 (resample causal 30M)
BORDA: dispara na 1a barra em que NUCLEO+SCORE fica verdadeiro (falso em i-1); cooldown 24.
SL: fundo da perna de queda (min low desde o high96) - 0.1*ATR  [estrutural largo]
    e tambem reporta variante hl_low para comparacao de geometria.

Metricas permitidas: freq/sem (total e no span dos 35), cobertura35 (±6 barras), SL geo, por-ano.
LOOK LEDGER probe 6: 6 linhas de grade (K, DCAP) — somam ao ledger (12 anteriores).
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
Q30 = {}
for j in range(20, len(B30)):
    Q30[B30_CLOSE[j]] = sum(TR30[j - 3:j + 1]) / 4.0 / max(1e-9, ATR30[j])
def quiet30_at(t0):
    j = bisect.bisect_right(B30_CLOSE, t0) - 1
    return Q30.get(B30_CLOSE[j]) if j >= 20 else None

AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
T35 = sorted(r["t"] for r in AN)
T35_SPAN = (T35[0] - 86400, T35[-1] + 86400)
W = 96

def full_state(i, DCAP, K):
    """True/False do NUCLEO+SCORE na barra i + dados de SL."""
    b = S[i]
    e21 = b.get("ema21")
    if e21 is None: return None
    atr = b["atr"] or 1.0; c = b["c"]
    # M1
    if not (c > e21): return None
    if not any(S[k]["c"] < S[k]["ema21"] for k in range(max(0, i - 24), i) if S[k].get("ema21")): return None
    win = S[i - W:i + 1]; lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
    jh = max(range(len(win)), key=lambda k: win[k]["h"])
    age = len(win) - 1 - jh
    if age < 8: return None                                   # M2
    if (c - e21) / atr > DCAP: return None                    # M3
    hi96, lo96 = max(highs), min(lows)
    ret = (hi96 - c) / ((hi96 - lo96) or atr)
    swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
    hl = len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]
    jc = bisect.bisect_right(CH_TS, b["t"]) - 1
    ch = jc >= 0 and (b["t"] - CH_TS[jc]) // 900 <= 32
    q = quiet30_at(b["t"])
    qok = q is not None and q <= 1.15
    rok = 0.25 <= ret <= 0.75
    score = int(hl) + int(ch) + int(rok) + int(qok)
    if score < K: return None
    dip_low = min(lows[jh:])
    hl_low = lows[swl[-1]] if swl else None
    return dict(t=b["t"], c=c, atr=atr, dip_low=dip_low, hl_low=hl_low, score=score)

def scan(DCAP, K, COOLDOWN=24):
    sigs = []; last = -10**9; prev_true = False
    for i in range(W + 2, len(S)):
        st = full_state(i, DCAP, K)
        ok = st is not None
        if ok and not prev_true and i - last > COOLDOWN:
            sl = st["dip_low"] - 0.1 * st["atr"]
            sl_hl = (st["hl_low"] - 0.1 * st["atr"]) if st["hl_low"] is not None else sl
            sigs.append(dict(i=i, t=st["t"], c=st["c"],
                             d_atr=(st["c"] - sl) / st["atr"], d_usd=st["c"] - sl,
                             dhl_atr=(st["c"] - sl_hl) / st["atr"], dhl_usd=st["c"] - sl_hl,
                             score=st["score"]))
            last = i
        prev_true = ok
    return sigs

def report(name, sigs):
    if not sigs: print(f"{name}: 0 sinais"); return
    weeks = len({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
    sig_ts = [s["t"] for s in sigs]
    cov = sum(1 for t0 in T35 if any(abs(st - t0) <= 6 * 900 for st in sig_ts))
    in_span = sum(1 for st in sig_ts if T35_SPAN[0] <= st <= T35_SPAN[1])
    d_atr = sorted(s["d_atr"] for s in sigs); d_usd = sorted(s["d_usd"] for s in sigs)
    dhl = sorted(s["dhl_atr"] for s in sigs)
    med = lambda a: a[len(a) // 2]; q1 = lambda a: a[len(a) // 4]; q3 = lambda a: a[3 * len(a) // 4]
    byyear = {}
    for s in sigs:
        y = dt.datetime.utcfromtimestamp(s["t"]).year; byyear[y] = byyear.get(y, 0) + 1
    print(f"{name}: N={len(sigs)} {len(sigs)/weeks:.2f}/sem | span35 {in_span} ({in_span/29:.2f}/sem)"
          f" | cobertura35={cov}/35 | SLdip_atr {med(d_atr):.2f}[{q1(d_atr):.2f}-{q3(d_atr):.2f}]"
          f" SLdip$ {med(d_usd):.1f}[{q1(d_usd):.1f}-{q3(d_usd):.1f}]"
          f" | SLhl_atr {med(dhl):.2f} | por-ano {byyear}")

GRID = [
    ("F1 K=3 DCAP=1.5", dict(DCAP=1.5, K=3)),
    ("F2 K=3 DCAP=2.0", dict(DCAP=2.0, K=3)),
    ("F3 K=4 DCAP=1.5", dict(DCAP=1.5, K=4)),
    ("F4 K=4 DCAP=2.0", dict(DCAP=2.0, K=4)),
    ("F5 K=2 DCAP=1.5", dict(DCAP=1.5, K=2)),
    ("F6 K=3 DCAP=1.0", dict(DCAP=1.0, K=3)),
]
for name, kw in GRID:
    report(name, scan(**kw))
