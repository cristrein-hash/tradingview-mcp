#!/usr/bin/env python3
"""DA — streak (block+iid), exit sensitivity, 2026 sub-window, multiplicity. READ-ONLY."""
import json, glob, bisect, random, collections
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
SIG = json.load(open(HERE / "results" / "rws15m_signals_20260705.json"))
CJ = [s["cj_t"] for s in SIG]
nets = [R3[c]["net3"] for c in CJ]
SB = 0.80

# ---- observed streak (max consecutive losers, net<=0) ----
def maxstreak(seq):
    mL = cl = 0
    for x in seq:
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    return mL
print("=== STREAK ===")
print("observed max consecutive losers (net<=0):", maxstreak(nets))
WR = sum(1 for x in nets if x > 0) / len(nets)
print(f"WR(net)={WR:.3f}  N={len(nets)}")

# episodes (same clustering as author: gap <= 96 bars = 24h)
eps = []; lastt = None
for j, c in enumerate(CJ):
    if lastt is not None and c - lastt <= 96 * 900: eps[-1].append(j)
    else: eps.append([j])
    lastt = c
print(f"n episodes={len(eps)} (from {len(CJ)} trades)")

random.seed(7)  # INDEPENDENT seed (author used 42)
NR = 20000
# block-episode bootstrap
wb = [maxstreak([nets[j] for _ in range(len(eps)) for j in eps[random.randrange(len(eps))]]) for _ in range(NR)]
wb.sort()
# iid per-trade bootstrap
wi = [maxstreak([random.choice(nets) for _ in range(len(nets))]) for _ in range(NR)]
wi.sort()
def pctl(a, p): return a[int(p * len(a))]
print(f"block-episode: mean={sum(wb)/NR:.2f} q50={pctl(wb,.50)} q95={pctl(wb,.95)} q99={pctl(wb,.99)} P(>5)={sum(1 for x in wb if x>5)/NR:.3f} P(>=6)={sum(1 for x in wb if x>=6)/NR:.3f}")
print(f"iid-trade:     mean={sum(wi)/NR:.2f} q50={pctl(wi,.50)} q95={pctl(wi,.95)} q99={pctl(wi,.99)} P(>5)={sum(1 for x in wi if x>5)/NR:.3f} P(>=6)={sum(1 for x in wi if x>=6)/NR:.3f}")
# theoretical iid expected max run of losses for N trials, loss prob (1-WR)
import math
q = 1 - WR
approx = math.log(len(nets) * (1 - q), 1 / q) if q > 0 else 0
print(f"iid theoretical approx expected longest loss-run ~ log_(1/q)(N*(1-q)) = {approx:.2f}")

print("\n=== EXIT SENSITIVITY (fixed R targets, first-touch on R3 dataset only has 3R) ===")
# We only have R3 (3R) and can recompute let-run needs series; here compare 3R vs let-run from author output
print("3R-fixed net=+38.8 (WR46.3, 2026=+1.4) | let-run net=+21.9 (WR57.4, 2026=-2.7)")
print("-> both positive overall; let-run 2026 NEGATIVE. 3R is the more robust arbiter but higher-variance exit.")

print("\n=== 2026 SUB-WINDOW ===")
by_mo = collections.defaultdict(list)
for s in SIG:
    if s["yr"] == 2026:
        mo = dt.datetime.utcfromtimestamp(s["cj_t"]).strftime("%Y-%m")
        by_mo[mo].append(R3[s["cj_t"]])
for mo in sorted(by_mo):
    rows = by_mo[mo]
    n = len(rows); hit = sum(1 for r in rows if r["R3"] >= 3); net = sum(r["net3"] for r in rows)
    print(f"  {mo}: N{n} hit{hit}/{n} net{net:+.1f}")
tot26 = [R3[s["cj_t"]] for s in SIG if s["yr"] == 2026]
print(f"  2026 total: N{len(tot26)} hit{sum(1 for r in tot26 if r['R3']>=3)} net{sum(r['net3'] for r in tot26):+.1f}")

print("\n=== MULTIPLICITY (informal Bonferroni over ~5 explored families) ===")
p_hit = 0.008
for m in (1, 3, 5, 8):
    print(f"  looks={m}: adjusted P(hit) ~ {min(1, p_hit*m):.3f}")
print("  net P=0.0 (empirical <1/1000) survives even x8 (<0.008).")
