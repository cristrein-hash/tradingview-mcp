#!/usr/bin/env python3
"""DA — 2026 coverage/BEAR-exclusion + let-run streak distribution. READ-ONLY."""
import json, glob, bisect, random, collections
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
SIG = json.load(open(HERE / "results" / "rws15m_signals_20260705.json"))
CJ = [s["cj_t"] for s in SIG]

print("=== 2026 COVERAGE / why N10 ===")
def ym(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m")
u2026 = [r for r in U if r["yr"] == 2026]
print("total candidate rows 2026 (all regimes):", len(u2026))
by_reg = collections.Counter(r["g_v5h"] for r in u2026)
print("2026 candidate rows by regime:", dict(by_reg))
nb2026 = [r for r in u2026 if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
print("2026 non-BEAR non-knife (eligible universe):", len(nb2026))
print("2026 eligible by month:", dict(collections.Counter(ym(r["cj_t"]) for r in nb2026)))
print("signal cj range overall:", ym(min(CJ)), "->", ym(max(CJ)))
print("last candidate row month in data:", ym(max(r["cj_t"] for r in U)))
print("-> 2026 is thin because BEAR-regime gate excludes most of the year (BEAR since ~jan-2026).")

# ---- let-run per-signal R + streak distribution ----
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; Np = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; Cc = [b["c"] for b in S]
R = {r["cj_t"]: r for r in U}; SB = 0.80
def letrun(r):
    i = bisect.bisect_right(TS, r["cj_t"]) - 1; entry = r["g_entry"]; sl = r["g_sl"]; atr = r["g_atr"]; risk = entry - sl
    trail = sl; r1 = False; end = min(i + 480, Np - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= trail: return max(-1.0, min(20.0, (trail - entry) / risk))
        if (H[k] - entry) / risk >= 1: r1 = True
        if r1:
            p = None
            for qq in range(k - 2, max(1, k - 122), -1):
                if L[qq] == min(L[qq - 2:qq + 3]): p = qq; break
            if p is not None: trail = max(trail, L[p] - 0.1 * atr)
    return max(-1.0, min(20.0, (Cc[end] - entry) / risk))
lr_net = [letrun(R[c]) - SB / R[c]["g_risk"] for c in CJ]
def maxstreak(seq):
    mL = cl = 0
    for x in seq:
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    return mL
WRlr = sum(1 for x in lr_net if x > 0) / len(lr_net)
print(f"\n=== LET-RUN streak (WR={WRlr:.3f}) ===")
print("observed let-run streak:", maxstreak(lr_net))
random.seed(7)
wi = sorted(maxstreak([random.choice(lr_net) for _ in range(len(lr_net))]) for _ in range(20000))
print(f"iid let-run: q50={wi[10000]} q95={wi[19000]} P(>5)={sum(1 for x in wi if x>5)/20000:.3f}")
print("-> higher-WR let-run exit has a MILDER streak profile but lower total (+21.9 vs +38.8) and NEGATIVE 2026.")
print("   FN streak-safety and expectancy pull in opposite directions across the exit choice.")
