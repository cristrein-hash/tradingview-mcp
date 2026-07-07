#!/usr/bin/env python3
"""NULL robustness audit — 4-STATE CYCLE-PHASE MACHINE (A/B/C/D) — XAU 15M LONG 3R.
Filtro fixo (strict keep_ns, N=54). H0: outcomes sao aleatorios (independentes da regra do filtro).
Dois nulls: (a) PERMUTA global dos 96 outcomes; (b) ROTACAO circular (preserva autocorrelacao/blocos).
null_p = P(hit3r do MESMO conjunto de 54 posicoes >= obs) sob H0.
"""
import sys, random
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score

KEEP = [1,2,3,4,6,7,8,9,10,12,13,14,15,16,18,20,23,26,27,30,33,35,36,37,39,40,44,45,46,48,
        50,51,52,53,55,61,62,64,68,71,74,75,76,77,78,80,82,84,87,88,89,90,93,95]
keep = set(KEEP)

# entries em ORDEM TEMPORAL (por t da barra de decisao j)
ents = sorted(ENTRIES, key=lambda e: e["t"])
outs = [e["out"] for e in ents]                       # sequencia temporal de outcomes
kept_mask = [1 if e["n"] in keep else 0 for e in ents]  # quais posicoes o filtro mantem
Nk = sum(kept_mask)
tot_w = sum(outs)
obs_w = sum(o for o, m in zip(outs, kept_mask) if m)
obs_hit = obs_w / Nk
print(f"N_entries={len(ents)} total_winners={tot_w} N_kept={Nk} obs_winners_kept={obs_w} obs_hit3r={obs_hit:.4f}")

ITERS = 50000
rng = random.Random(20260707)

def hit_kept(seq):
    return sum(s for s, m in zip(seq, kept_mask) if m)

# (a) PERMUTA global — quebra qualquer estrutura, hipergeometrico
ge_perm = 0
for _ in range(ITERS):
    seq = outs[:]; rng.shuffle(seq)
    if hit_kept(seq) >= obs_w: ge_perm += 1
p_perm = (ge_perm + 1) / (ITERS + 1)

# (b) ROTACAO circular — preserva blocos de vitorias/derrotas (autocorrelacao temporal)
n = len(outs)
ge_rot = 0
for _ in range(ITERS):
    k = rng.randrange(1, n)
    seq = outs[k:] + outs[:k]
    if hit_kept(seq) >= obs_w: ge_rot += 1
p_rot = (ge_rot + 1) / (ITERS + 1)

# null_p conservador = pior (maior) dos dois
null_p = max(p_perm, p_rot)

# gates
sc = score(KEEP)
poison_ok = sc["winners_cut"] < sc["losers_cut"]
y25w, y25n = map(int, sc["y2025"].split("/"))
y26w, y26n = map(int, sc["y2026"].split("/"))
base = tot_w / len(ents)
r25 = y25w / y25n; r26 = y26w / y26n
both_years_ok = (r25 > base) and (r26 > base)
survives = (null_p < 0.10) and poison_ok and both_years_ok and (Nk >= 20)

print(f"null_p_permute={p_perm:.4f}  null_p_rotate={p_rot:.4f}  null_p(conserv)={null_p:.4f}")
print(f"poison: winners_cut={sc['winners_cut']} losers_cut={sc['losers_cut']} -> poison_ok={poison_ok}")
print(f"years: base={base:.4f} 2025={r25:.4f}({sc['y2025']}) 2026={r26:.4f}({sc['y2026']}) -> both_years_ok={both_years_ok}")
print(f"N_kept={Nk} -> N_ok={Nk>=20}")
print(f"SURVIVES={survives}")
