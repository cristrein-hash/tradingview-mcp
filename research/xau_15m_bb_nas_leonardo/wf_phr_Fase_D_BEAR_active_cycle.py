#!/usr/bin/env python3
"""ROBUSTNESS AUDIT — Fase-D BEAR-active cycle-phase classifier (XAU 15M LONG 3R).
NULL test: does a filter selecting N=73 of 96 achieve hit3r>=obs by chance?
Two nulls: (A) permute outcomes (breaks all structure), (B) rotate outcomes in
time order (preserves win/loss autocorrelation clustering). keep-mask FIXED.
"""
import sys, random
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score

KEEP = [2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,20,21,22,23,25,27,28,29,30,31,34,35,36,37,38,39,40,41,42,43,44,45,46,48,51,52,53,54,55,57,58,59,60,61,62,63,64,67,69,71,72,73,74,75,76,77,78,82,83,84,87,88,90,91,92,93,94,96]
keepset = set(KEEP)

# order entries by n (== chronological build order)
ents = sorted(ENTRIES, key=lambda e: e["n"])
outs = [e["out"] for e in ents]
mask = [e["n"] in keepset for e in ents]
Nkept = sum(mask)
obs_hit = sum(o for o, m in zip(outs, mask) if m) / Nkept
base = sum(outs) / len(outs)
print(f"obs: N_kept={Nkept} hit3r_kept={obs_hit:.4f} base={base:.4f}")

def hit_under(shuffled):
    return sum(o for o, m in zip(shuffled, mask) if m) / Nkept

TRIALS = 50000
rng = random.Random(20260707)

# NULL A: full permutation
geA = 0
for _ in range(TRIALS):
    sh = outs[:]; rng.shuffle(sh)
    if hit_under(sh) >= obs_hit - 1e-9: geA += 1
null_pA = geA / TRIALS

# NULL B: circular rotation (preserves temporal clustering)
L = len(outs)
geB = 0
for _ in range(TRIALS):
    k = rng.randrange(L)
    sh = outs[k:] + outs[:k]
    if hit_under(sh) >= obs_hit - 1e-9: geB += 1
null_pB = geB / TRIALS

# rotation has only L distinct outcomes -> also do exact enumeration
geB_exact = 0
for k in range(L):
    sh = outs[k:] + outs[:k]
    if hit_under(sh) >= obs_hit - 1e-9: geB_exact += 1
null_pB_exact = geB_exact / L

null_p = max(null_pA, null_pB_exact)  # conservative

sc = score(KEEP)
w25, n25 = map(int, sc["y2025"].split("/"))
w26, n26 = map(int, sc["y2026"].split("/"))
r25, r26 = w25/n25, w26/n26
poison_ok = sc["winners_cut"] < sc["losers_cut"]
both_years_ok = (r25 > base) and (r26 > base)
survives = (null_p < 0.1) and poison_ok and both_years_ok and Nkept >= 20

print(f"NULL A permute:  p={null_pA:.4f}")
print(f"NULL B rotate MC:p={null_pB:.4f}  exact({L})={null_pB_exact:.4f}")
print(f"null_p (max/conservative) = {null_p:.4f}")
print(f"y2025 {r25:.4f} >base {r25>base} | y2026 {r26:.4f} >base {r26>base}")
print(f"poison_ok={poison_ok} both_years_ok={both_years_ok} N>=20={Nkept>=20}")
print(f"SURVIVES={survives}")
