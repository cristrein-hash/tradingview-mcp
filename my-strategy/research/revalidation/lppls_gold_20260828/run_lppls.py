#!/usr/bin/env python3
"""LPPLS ouro 1D — manifest selado. numpy lstsq; py3.9. SANITY_PROBE: read-only research."""
import json, sys, datetime as dt
import numpy as np
sys.path.insert(0, '/Users/cristrein/tradingview-mcp/my-strategy/core/layer1_service')
import layer1_cycle as LC
from pathlib import Path
OUT = Path(__file__).resolve().parent

x = LC._merge_xau_1d()
T = np.array([b['t'] for b in x], float) / 86400.0     # dias
P = np.log(np.array([b['c'] for b in x], float))
WINDOWS = [120, 180, 240, 300, 360, 420, 480, 540, 640, 750]
MS = np.arange(0.1, 0.91, 0.1); WS = np.arange(6.0, 13.01, 1.0)

def fit_window(i_end, n):
    """Melhor fit LPPLS na janela [i_end-n, i_end]; devolve dict ou None."""
    a = i_end - n
    if a < 0: return None
    t = T[a:i_end + 1] - T[a]; y = P[a:i_end + 1]; t2 = t[-1]
    best = None
    for tc in np.arange(t2 + 1, t2 + 251, 10):
        dtc = tc - t
        for m in MS:
            f = dtc ** m
            lg = np.log(dtc)
            for w in WS:
                g = f * np.cos(w * lg); h = f * np.sin(w * lg)
                A = np.column_stack([np.ones_like(t), f, g, h])
                coef, res, *_ = np.linalg.lstsq(A, y, rcond=None)
                sse = res[0] if len(res) else np.sum((A @ coef - y) ** 2)
                if best is None or sse < best[0]:
                    best = (sse, tc - t2, m, w, coef)
    if best is None: return None
    sse, tc_days, m, w, coef = best
    B, C1, C2 = coef[1], coef[2], coef[3]
    C = np.hypot(C1, C2)
    damping = (m * abs(B)) / (w * C) if C > 0 else np.inf
    ok = (B < 0) and (0.1 < m < 0.9) and (6 <= w <= 13) and (damping >= 1)
    return dict(n=n, tc_days=round(float(tc_days)), m=round(float(m), 2), w=round(float(w), 1),
                B=round(float(B), 4), damping=round(float(damping), 2), ok=bool(ok),
                rmse=round(float(np.sqrt(sse / len(y))), 4))

def confidence(i_end):
    fits = [fit_window(i_end, n) for n in WINDOWS]
    fits = [f for f in fits if f]
    okf = [f for f in fits if f['ok']]
    conf = len(okf) / len(fits) if fits else 0.0
    tcs = sorted(f['tc_days'] for f in okf)
    return conf, (tcs[len(tcs) // 2] if tcs else None), fits

# 1) HOJE
conf, tc_med, fits = confidence(len(T) - 1)
today = dt.datetime.utcfromtimestamp(x[-1]['t']).date()
print(f"HOJE ({today}): confidence {conf:.0%} · tc mediano {'+' + str(tc_med) + 'd' if tc_med else 'n/a'}")
for f in fits: print("  ", f)

# 2) varrimento histórico trimestral 2016→
hist = []
i = 400
while i < len(T):
    c, tcm, _ = confidence(i)
    d = dt.datetime.utcfromtimestamp(x[i]['t']).date()
    hist.append(dict(date=str(d), conf=round(c, 2), tc_med=tcm, price=round(float(np.exp(P[i])), 0)))
    i += 63
peaks = [h for h in hist if h['conf'] >= 0.5]
print(f"\nHISTÓRICO trimestral: {len(hist)} pontos · conf>=50%: {len(peaks)}")
for h in hist: print("  ", h)
json.dump(dict(today=dict(date=str(today), conf=conf, tc_med=tc_med, fits=fits), hist=hist),
          open(OUT / 'results.json', 'w'), indent=1)
print("gravado results.json")
