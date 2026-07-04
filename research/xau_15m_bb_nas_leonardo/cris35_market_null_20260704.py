#!/usr/bin/env python3
"""NULL DECISIVO das 35 entradas do Cris a MERCADO sob alvo fixo 3R (2026-07-04).
Pergunta: +68,5 NET / WR 85,7 é SELEÇÃO dele ou o regime (mega-bull) dava isso a qualquer LONG
de SL largo com alvo 3R no mesmo período? Nulls: (a) uniforme no período dele (500 reps) ·
(b) time-matched weekday×hora (500). Cada rep: 35 barras aleatórias; risco = a MESMA distribuição
de riscos $ dele (pareada por shuffle); SL = close − risco; exit F3 first-touch (ambíguo=-1),
HMAX 480, custo SB 0,8/risco. Percentil do observado + WR do null. Seed 42."""
import json, glob, bisect, random
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
random.seed(42)
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]

raw = json.load(open(HERE / "results" / "cris_manual_trades_20260704.json"))
cris = []
for sh in raw["shapes"]:
    if sh.get("name") != "long_position": continue
    pts = sh["props"]["points"]; pr = sh["props"]["properties"]
    t0 = pts[0]["time"]; drawn = pts[0]["price"]
    i = bisect.bisect_right(TS, t0) - 1
    sl_abs = drawn - pr["stopLevel"] * 0.01
    if C[i] - sl_abs <= 0: continue
    cris.append({"i": i, "risk": C[i] - sl_abs})
RISKS = [c["risk"] for c in cris]
T0, T1 = S[cris[0]["i"]]["t"], S[cris[-1]["i"]]["t"]

def f3(i, risk):
    entry = C[i]; sl = entry - risk; tgt = entry + 3 * risk; end = min(i + 480, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= sl: return -1.0
        if H[k] >= tgt: return 3.0
    return max(-1.0, (C[end] - entry) / risk)

obs = [(f3(c["i"], c["risk"]), c["risk"]) for c in cris]
obs_net = sum(R - SB / rk for R, rk in obs)
obs_wr = 100 * sum(1 for R, rk in obs if R - SB / rk > 0) / len(obs)
print(f"OBSERVADO (35 @ mercado, F3): NET {obs_net:+.1f} · WR {obs_wr:.1f}")

ELIG = [i for i in range(100, N - 481) if T0 <= S[i]["t"] <= T1]
bywh = {}
for i in ELIG:
    d = dt.datetime.utcfromtimestamp(S[i]["t"]); bywh.setdefault((d.weekday(), d.hour), []).append(i)
obs_wh = [( (dt.datetime.utcfromtimestamp(S[c['i']]['t']).weekday(), dt.datetime.utcfromtimestamp(S[c['i']]['t']).hour) ) for c in cris]

def run_null(time_matched, reps=500):
    nets, wrs = [], []
    for _ in range(reps):
        rks = RISKS[:]; random.shuffle(rks)
        tot = 0.0; w = 0
        for j in range(len(rks)):
            i = random.choice(bywh[obs_wh[j]]) if time_matched else random.choice(ELIG)
            R = f3(i, rks[j]); net = R - SB / rks[j]
            tot += net; w += net > 0
        nets.append(tot); wrs.append(100 * w / len(rks))
    return nets, wrs
for nm, tm in (("uniforme", False), ("time-matched", True)):
    nets, wrs = run_null(tm)
    med = sorted(nets)[250]; q95 = sorted(nets)[475]
    pct = 100 * sum(1 for x in nets if x < obs_net) / len(nets)
    medw = sorted(wrs)[250]
    print(f"null {nm:<13}: NET med {med:+.1f} · q95 {q95:+.1f} · WR med {medw:.0f} → obs pct {pct:.1f}%")
