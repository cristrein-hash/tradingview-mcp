#!/usr/bin/env python3
"""DA EXIT FAMILY LAB — ataque 3: precisão no IC borderline (E1 sem 2025-01) com 10000 reps e
2 seeds; +2 traces bar-a-bar (timeout e caso médio) para fechar os 5 exigidos. READ-ONLY."""
import json, glob, bisect, hashlib, random
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
HMAX, RCAP, FR_WIN = 480, 20.0, 120
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"])
TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]
LASTFR = [None] * N; _last = None
for k in range(N):
    q = k - 2
    if q >= 2 and q < N - 2 and L[q] <= min(L[q-2:q+3]):
        _last = q
    LASTFR[k] = _last

def run_trail(i, entry, sl, atr, arm_R, trace=None):
    risk = entry - sl; stop = sl; armed = False; end = min(i + HMAX, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= stop:
            if trace is not None: trace.append((k - i, "STOP", round(stop, 2)))
            return max(-1.0, min(RCAP, (stop - entry) / risk))
        if not armed and (H[k] - entry) >= arm_R * risk:
            armed = True
            if trace is not None: trace.append((k - i, "ARM", round(H[k], 2)))
        if armed:
            p = LASTFR[k]
            if p is not None and p >= k - FR_WIN:
                new = L[p] - 0.1 * atr
                if new > stop:
                    stop = new
                    if trace is not None: trace.append((k - i, "TRAIL", round(stop, 2)))
    if trace is not None: trace.append((end - i, "TIMEOUT", round(C[end], 2)))
    return max(-1.0, min(RCAP, (C[end] - entry) / risk))

def run_fixed(i, entry, sl, atr, mult, trace=None):
    risk = entry - sl; tgt = entry + mult * risk; end = min(i + HMAX, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= sl:
            if trace is not None: trace.append((k - i, "SL", round(sl, 2)))
            return -1.0
        if H[k] >= tgt:
            if trace is not None: trace.append((k - i, "TP", round(tgt, 2)))
            return float(mult)
    if trace is not None: trace.append((end - i, "TIMEOUT", round(C[end], 2)))
    return max(-1.0, min(RCAP, (C[end] - entry) / risk))

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == \
    (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
sset = sorted((bisect.bisect_right(TS, r["cj_t"]) - 1, r["g_entry"], r["g_sl"], r["g_atr"],
               r["cj_t"], r["yr"]) for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR")

netsE0 = [run_trail(i, e, sl, a, 1) - SB / (e - sl) for i, e, sl, a, t, y in sset]
netsE1 = [run_trail(i, e, sl, a, 3) - SB / (e - sl) for i, e, sl, a, t, y in sset]
d = [a - b for a, b in zip(netsE1, netsE0)]
mk = [dt.datetime.utcfromtimestamp(t).strftime("%Y-%m") for _i, _e, _sl, _a, t, _y in sset]
keep = [j for j, k in enumerate(mk) if k != "2025-01"]
d_wo = [d[j] for j in keep]
times_wo = [sset[j][4] for j in keep]
eps = []; lastt = None
for j, t in enumerate(times_wo):
    if lastt is not None and t - lastt <= 96 * 900: eps[-1].append(j)
    else: eps.append([j])
    lastt = t
for seed in (777, 20260704):
    random.seed(seed)
    sums = []
    for _ in range(10000):
        s = 0.0
        for _e in range(len(eps)):
            for j in eps[random.randrange(len(eps))]:
                s += d_wo[j]
        sums.append(s)
    sums.sort()
    lo, hi = sums[250], sums[9750]
    p_neg = sum(1 for s in sums if s <= 0) / len(sums)
    print(f"E1-E0 SEM 2025-01, 10000x seed{seed}: Δ={sum(d_wo):+.2f} IC95 [{lo:+.2f},{hi:+.2f}] "
          f"P(Δ<=0)={p_neg:.3f} {'EXCLUI 0' if lo > 0 else 'CRUZA/TOCA 0'}")

# ---- +2 traces: um timeout (qualquer exit) e um caso médio (E1 ganha moderado) ----
print("\nTRACES ADICIONAIS")
EX = {"E0_trail": lambda i, e, s, a, tr: run_trail(i, e, s, a, 1, tr),
      "E1_trail3R": lambda i, e, s, a, tr: run_trail(i, e, s, a, 3, tr),
      "E2_alvo3R": lambda i, e, s, a, tr: run_fixed(i, e, s, a, 3, tr),
      "E3_alvo5R": lambda i, e, s, a, tr: run_fixed(i, e, s, a, 5, tr)}
picks = []
for j, (i, e, sl, a, t, y) in enumerate(sset):  # timeout sob E1
    tr = []
    run_trail(i, e, sl, a, 3, tr)
    if tr and tr[-1][1] == "TIMEOUT":
        picks.append(("timeout_E1", j)); break
med = sorted((abs(dj - 1.0), j) for j, dj in enumerate(d))[0][1]  # delta ~ +1R (caso médio)
picks.append(("delta_medio_+1R", med))
for tag, j in picks:
    i, e, sl, a, t, y = sset[j]
    dd = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
    print(f"\n trade#{j} [{tag}] {dd} entry {e} sl {round(sl,2)} risk {e-sl:.2f}")
    for en, fn in EX.items():
        tr = []
        r = fn(i, e, sl, a, tr)
        ev = " · ".join(f"b+{b}:{tag2}@{v}" for b, tag2, v in tr[:5])
        print(f"   {en:<11} R={r:+.2f}  {ev}" + (f" (+{len(tr)-5}ev)" if len(tr) > 5 else ""))
print("\nOK")
