#!/usr/bin/env python3
"""DA VETOR C — multiplicidade e poder estatístico dos achados de hoje (camada macro).
Conta de looks (enumerada por leitura dos 9 scripts de hoje) + binomial/hipergeométrica exata
para GTQ∩banda (4/8) e DF∩banda (10/24)."""
import json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
R3 = [json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")]
hits = sum(1 for r in R3 if r["R3"] >= 3)
base = hits / len(R3)
print(f"base universo: {hits}/{len(R3)} = {100*base:.1f}% hit3R")

def binom_ge(k, n, p):
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))

def hyper_ge(k, N, K, n):
    # P(X>=k) tirando n de N com K sucessos
    return sum(math.comb(K, i) * math.comb(N-K, n-i) / math.comb(N, n)
               for i in range(k, min(K, n)+1))

print("\nGTQ∩banda: 4/8 (50%) vs alternativas de null:")
print(f"  vs base universo {100*base:.1f}%      P(X>=4|8)  = {binom_ge(4,8,base):.3f}")
print(f"  vs GTQ-18 própria (8/18=44,4%) P(X>=4|8)  = {binom_ge(4,8,8/18):.3f}")
print(f"  hipergeométrica (subset 8 de 18 c/ 8 wins) P(X>=4) = {hyper_ge(4,18,8,8):.3f}")
print("\nDF∩banda: 10/24 (41,7%):")
print(f"  vs base universo {100*base:.1f}%      P(X>=10|24) = {binom_ge(10,24,base):.3f}")
print(f"  vs DF-40 própria (14/40=35%)   P(X>=10|24) = {binom_ge(10,24,14/40):.3f}")
print(f"  hipergeométrica (subset 24 de 40 c/ 14 wins) P(X>=10) = {hyper_ge(10,40,14,24):.3f}")

LOOKS_OUTCOME = [
    ("macro_level_test_entry FASE B", 4),
    ("macro_retrace_gate (r6/r8 × G1-G4)", 8),
    ("macro_composite_engine C1-C6", 6),
    ("needle_v2 (agulha + 5 ablações)", 6),
    ("gtq_retrace_cross (GTQ∩banda, DF∩banda)", 2),
]
LOOKS_STRUCT = [
    ("macro_demand_zone_engine 12 configs + best-of", 13),
    ("macro_demand_zone_v2 8 configs + união", 9),
    ("gt_structural_distance 5 famílias × 2 thresholds", 10),
    ("gt_macro_leg_retrace 3r × (4 feats + 3 bandas)", 21),
    ("macro_level_test FASE A 4w × 2 fam", 8),
    ("needle_v2 banda q10-q90 nova", 1),
    ("banda [0.5,1.3] nunca testada no diag (silenciosa)", 1),
]
no = sum(x[1] for x in LOOKS_OUTCOME); ns = sum(x[1] for x in LOOKS_STRUCT)
print(f"\nLOOKS de hoje: outcome = {no} · estrutura/calibração = {ns} · total = {no+ns}")
for nm, k in LOOKS_OUTCOME + LOOKS_STRUCT:
    print(f"  {k:>3}  {nm}")
p1 = binom_ge(4, 8, base)
print(f"\nSidak p/ melhor-de-{no} looks outcome: 1-(1-p)^{no} com p={p1:.3f} → {1-(1-p1)**no:.3f}")
print(f"p necessário p/ sobreviver Bonferroni {no} looks a 5%: {0.05/no:.4f}")
