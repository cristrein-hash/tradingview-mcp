#!/usr/bin/env python3
"""DA ATTACK 1 — PROPER NULL for the best-of-frontier avgR. (Cris 2026-06-28)
The standout combo (reclaim_atr+swept_prior_low+buy_bub_w, avgR +0.206) was CHOSEN as best-of-frontier.
Naive 'random same-n' null underestimates selection bias. Proper null: the search scanned MANY combos and
PICKED the max avgR. So permute the R-outcomes across the knife-gated universe K times; each shuffle, re-run
the SAME combo search (all 2- and 3-feature combos over TOP14, same tight q80/20 thresholds, same n>=8 filter)
and record the BEST avgR achievable. Where does 0.206 fall in that null-of-the-max distribution? p-value +
Bonferroni over n_combos actually scanned."""
import random
from itertools import combinations
from _DA_engine3_core import G, TOP, passes, R_of, metr, STANDOUT

# precompute R for every knife-gated row ONCE (fast, deterministic)
Rvals = [R_of(r) for r in G]
idx_valid = [i for i, x in enumerate(Rvals) if x is not None]
Rv = [Rvals[i] for i in idx_valid]
Gv = [G[i] for i in idx_valid]
N = len(Gv)

# enumerate every combo the search considers (size 2 and 3 over TOP14), precompute member masks
COMBOS = list(combinations(TOP, 2)) + list(combinations(TOP, 3))
masks = []
for cc in COMBOS:
    m = [i for i, r in enumerate(Gv) if passes(r, cc)]
    if len(m) >= 8:
        masks.append((cc, m))
n_combos = len(masks)
print(f"N(valid R, knife-gated)={N}  combos scanned (n>=8)={n_combos}")

# observed best avgR over the search
obs = []
for cc, m in masks:
    avg = sum(Rv[i] for i in m) / len(m)
    obs.append((cc, len(m), avg))
obs.sort(key=lambda x: -x[2])
print("\nObserved top-8 combos by avgR (knife-gated, real R):")
for cc, nn, a in obs[:8]:
    print(f"  {'+'.join(c[:14] for c in cc):<46} n={nn:>4} avgR={a:+.3f}")
obs_best = obs[0][2]
standout_rank = next((i for i, (cc, nn, a) in enumerate(obs) if cc == STANDOUT), -1)
standout_avg = next((a for cc, nn, a in obs if cc == STANDOUT), None)
print(f"\nSTANDOUT {STANDOUT} avgR={standout_avg:+.3f} rank={standout_rank+1}/{n_combos}  (observed best avgR={obs_best:+.3f})")

# NULL of the MAX: shuffle R labels across universe, recompute best avgR over the SAME combo set
K = 2000
random.seed(13)
null_best = []
order = list(range(N))
for _ in range(K):
    random.shuffle(order)
    Rs = [Rv[order[i]] for i in range(N)]
    bm = -9
    for cc, m in masks:
        a = sum(Rs[i] for i in m) / len(m)
        if a > bm: bm = a
    null_best.append(bm)
null_best.sort()
ge = sum(1 for b in null_best if b >= standout_avg)
ge_obsbest = sum(1 for b in null_best if b >= obs_best)
import statistics as stt
print(f"\nNULL-of-the-MAX over {K} shuffles, same {n_combos} combos:")
print(f"  null best avgR: mean={stt.mean(null_best):+.3f} p50={null_best[K//2]:+.3f} "
      f"p95={null_best[int(.95*K)]:+.3f} p99={null_best[int(.99*K)]:+.3f} max={null_best[-1]:+.3f}")
print(f"  P(null max-avgR >= standout {standout_avg:+.3f}) = {ge}/{K} = {ge/K:.4f}")
print(f"  P(null max-avgR >= observed-best {obs_best:+.3f}) = {ge_obsbest}/{K} = {ge_obsbest/K:.4f}")

# also single-combo null (NOT max-corrected): how often does THIS exact mask beat 0.206 under shuffle
nmask = next(m for cc, m in masks if cc == STANDOUT)
random.seed(13)
single = 0
for _ in range(K):
    random.shuffle(order)
    a = sum(Rv[order[i]] for i in nmask) / len(nmask)
    if a >= standout_avg: single += 1
print(f"\n  (single-combo, NOT max-corrected) P >= {standout_avg:+.3f} = {single}/{K} = {single/K:.4f}")
# Bonferroni: multiply single-combo p by n_combos
p_bonf = min(1.0, (single / K) * n_combos)
print(f"  Bonferroni single-p x n_combos({n_combos}) = {p_bonf:.4f}")
print("\nVERDICT 1: standout survives null-of-the-max iff P(null max>=0.206) is small (<0.05).")
