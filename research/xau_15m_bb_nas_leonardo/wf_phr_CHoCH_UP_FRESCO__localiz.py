#!/usr/bin/env python3
"""ROBUSTNESS AUDIT — candidate: CHoCH-UP FRESCO (localizado no lado do FUNDO) — phase classifier V2_hl_nochase.
NULL test (permuta + rotaciona outcomes) + poison + both-years gate.
null_p = P(a filter of the SAME N reaches hit3r >= observed by chance).
"""
import sys, random
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score
import datetime as dt

def _yr(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y")

KEEP = set([1,6,10,11,12,15,17,20,22,28,30,32,33,34,35,38,42,43,46,47,54,59,60,61,62,63,64,66,70,73,74,75,76,77,78,79,81,82,83,84,88,90,91,94,95])
N_KEEP = len(KEEP)

# --- observed ---
obs = score(KEEP)
print("=== OBSERVED (strict keep_ns) ===")
for k,v in obs.items(): print(f"  {k}: {v}")
obs_hit = obs["winners_kept"] / obs["N_kept"]  # exact, unrounded
N = len(ENTRIES)
baseW = sum(e["out"] for e in ENTRIES)
base_rate = baseW / N
print(f"  N={N} baseW={baseW} base_rate={base_rate:.4f} obs_hit={obs_hit} N_keep={N_KEEP}")

# time-ordered outcomes (ENTRIES already time-ordered by construction; sort to be safe)
order = sorted(range(N), key=lambda k: ENTRIES[k]["t"])
outs = [ENTRIES[k]["out"] for k in order]
# fixed keep mask aligned to time order
keep_mask = [ (ENTRIES[k]["n"] in KEEP) for k in order ]
n_keep = sum(keep_mask)
assert n_keep == N_KEEP, (n_keep, N_KEEP)

def hit_of(out_vec):
    w = sum(o for o,m in zip(out_vec, keep_mask) if m)
    return w / n_keep

# sanity: rebuild observed hit from mask
assert abs(hit_of(outs) - obs_hit) < 1e-9, (hit_of(outs), obs_hit)

# --- NULL 1: PERMUTATION (shuffle outcomes across all N, apply fixed mask) ---
random.seed(20260707)
TRIALS = 200000
ge_perm = 0
perm = outs[:]
for _ in range(TRIALS):
    random.shuffle(perm)
    if hit_of(perm) >= obs_hit - 1e-12:
        ge_perm += 1
null_p_perm = ge_perm / TRIALS

# --- NULL 2: ROTATION (circular shift of time-ordered outcomes; preserves autocorrelation) ---
# enumerate ALL N rotations (exact)
ge_rot = 0
for s in range(N):
    rot = outs[s:] + outs[:s]
    if hit_of(rot) >= obs_hit - 1e-12:
        ge_rot += 1
null_p_rot = ge_rot / N

# also a randomized rotation p over many random offsets (identical support, sanity)
print("\n=== NULL RESULTS ===")
print(f"  permutation null_p = {null_p_perm:.5f}  (trials={TRIALS})")
print(f"  rotation    null_p = {null_p_rot:.5f}  (all {N} exact rotations, {ge_rot} >= obs)")
# conservative null_p = max of the two
null_p = max(null_p_perm, null_p_rot)
print(f"  CONSERVATIVE null_p = {null_p:.5f}")

# --- poison ---
poison_ok = obs["winners_cut"] < obs["losers_cut"]

# --- both years vs base 54.2% ---
def rate(s):
    a,b = s.split("/"); a,b=int(a),int(b)
    return (a/b if b else 0.0), b
r25,n25 = rate(obs["y2025"]); r26,n26 = rate(obs["y2026"])
both_years_ok = (r25 > base_rate) and (r26 > base_rate)
print("\n=== GATES ===")
print(f"  poison_ok        = {poison_ok}  (winners_cut {obs['winners_cut']} < losers_cut {obs['losers_cut']})")
print(f"  y2025 {obs['y2025']} = {r25:.3f} > base {base_rate:.3f} ? {r25>base_rate}  (N25={n25})")
print(f"  y2026 {obs['y2026']} = {r26:.3f} > base {base_rate:.3f} ? {r26>base_rate}  (N26={n26})")
print(f"  both_years_ok    = {both_years_ok}")
N_ok = N_KEEP >= 20

survives = (null_p < 0.1) and poison_ok and both_years_ok and N_ok
print("\n=== VERDICT ===")
print(f"  null_p<0.1={null_p<0.1}  poison_ok={poison_ok}  both_years_ok={both_years_ok}  N>=20={N_ok}")
print(f"  SURVIVES = {survives}")

import json
print("\nJSON " + json.dumps({
  "candidate":"CHoCH-UP FRESCO (localiz FUNDO) V2_hl_nochase",
  "N_kept":N_KEEP,"hit3r_kept":obs_hit,"base_rate":round(base_rate,4),
  "winners_cut":obs["winners_cut"],"losers_cut":obs["losers_cut"],"poison_ratio":obs["poison_ratio"],
  "y2025":obs["y2025"],"y2026":obs["y2026"],
  "null_p_perm":round(null_p_perm,5),"null_p_rot":round(null_p_rot,5),"null_p":round(null_p,5),
  "poison_ok":poison_ok,"both_years_ok":both_years_ok,"survives":survives,
}))
