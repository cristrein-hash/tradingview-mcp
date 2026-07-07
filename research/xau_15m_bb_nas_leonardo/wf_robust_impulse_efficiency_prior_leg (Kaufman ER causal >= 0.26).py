#!/usr/bin/env python3
"""ROBUSTEZ / NULL de multiplicidade-winner-curse para o candidato
'impulse_efficiency_prior_leg (Kaufman ER causal >= 0.26)'.

Feature JA passou lookahead (CAUSAL_CLEAN). keep_ns estrito-causal = dado (52 entries).
Objetivo deste script: sob permutacao/rotacao dos OUTCOMES dos 96 entries, com que
frequencia um filtro do MESMO tamanho (N_kept) atinge hit3r >= observado.
null_p = P(null >= obs).
"""
import sys, random
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score

KEEP = [1,2,3,6,7,8,12,13,14,18,20,22,24,28,30,31,37,38,40,41,42,43,52,53,54,61,63,64,65,66,
        68,69,70,71,72,73,74,75,76,77,78,80,81,85,86,87,88,90,91,92,95,96]
keepset = set(KEEP)

# ordena por t para preservar estrutura temporal nas rotacoes
E = sorted(ENTRIES, key=lambda e: e["t"])
outs = [e["out"] for e in E]                 # vetor de outcomes na ordem temporal
in_keep = [e["n"] in keepset for e in E]     # mascara do keep-set FIXO (feature nao depende de outcome)
Nk = sum(in_keep)
obs_w = sum(o for o, k in zip(outs, in_keep) if k)
obs_hit = obs_w / Nk
base_w = sum(outs); base = base_w / len(outs)
print(f"N total={len(outs)} base winners={base_w} base hit3r={base:.3f}")
print(f"keep-set FIXO N_kept={Nk} winners_kept={obs_w} obs_hit3r={obs_hit:.4f}")

# -------- NULL 1: ROTACOES CICLICAS dos outcomes (preserva clustering temporal) --------
# keep-set (definido pela feature ER) e FIXO; rotacionamos o vetor de outcomes.
# um filtro do mesmo tamanho (Nk) => contamos winners que caem no keep-set.
def hit_for_rotation(k):
    w = 0
    n = len(outs)
    for idx in range(n):
        if in_keep[idx] and outs[(idx + k) % n]:
            w += 1
    return w / Nk

rot_hits = [hit_for_rotation(k) for k in range(len(outs))]
rot_ge = sum(1 for h in rot_hits if h >= obs_hit - 1e-9)
rot_p = rot_ge / len(rot_hits)
print(f"\n[ROTACOES ciclicas n={len(rot_hits)}] >=obs: {rot_ge}  null_p_rot={rot_p:.4f}")
print(f"  rot null hit3r: min={min(rot_hits):.3f} med={sorted(rot_hits)[len(rot_hits)//2]:.3f} max={max(rot_hits):.3f}")

# -------- NULL 2: PERMUTACOES ALEATORIAS dos outcomes (resolucao fina) --------
# equivalente a sortear um subconjunto aleatorio de tamanho Nk (hipergeometrico) =
# 'com que frequencia um filtro do MESMO tamanho atinge hit3r >= obs' sob rotulos random.
random.seed(20260707)
NPERM = 100000
ge = 0
for _ in range(NPERM):
    random.shuffle(outs)
    w = sum(o for o, k in zip(outs, in_keep) if k)
    if w / Nk >= obs_hit - 1e-9:
        ge += 1
perm_p = ge / NPERM
print(f"\n[PERMUTACOES aleatorias n={NPERM}] >=obs: {ge}  null_p_perm={perm_p:.5f}")

# -------- decisao de robustez --------
sc = score(KEEP)
poison_ok = sc["winners_cut"] < sc["losers_cut"]
y25w, y25n = map(int, sc["y2025"].split("/"))
y26w, y26n = map(int, sc["y2026"].split("/"))
BASE = base
y25r = y25w / y25n if y25n else 0
y26r = y26w / y26n if y26n else 0
both_years_ok = (y25r > BASE) and (y26r > BASE)
null_p = perm_p                                  # primario = permutacao (resolucao fina)
survives = (null_p < 0.1) and poison_ok and both_years_ok and (Nk >= 20)

print("\n==== VEREDITO ROBUSTEZ ====")
print(f"null_p (perm) = {null_p:.5f}  | null_p_rot = {rot_p:.4f}")
print(f"poison_ok = {poison_ok}  (winners_cut={sc['winners_cut']} < losers_cut={sc['losers_cut']})")
print(f"y2025 {sc['y2025']}={y25r:.3f} vs base {BASE:.3f} -> {y25r>BASE}")
print(f"y2026 {sc['y2026']}={y26r:.3f} vs base {BASE:.3f} -> {y26r>BASE}")
print(f"both_years_ok = {both_years_ok}")
print(f"N_kept = {Nk} (>=20 = {Nk>=20})")
print(f"SURVIVES = {survives}")
