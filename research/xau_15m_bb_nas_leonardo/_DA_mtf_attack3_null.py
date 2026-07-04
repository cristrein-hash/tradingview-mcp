#!/usr/bin/env python3
"""DA ATAQUE 3 — multiplicidade (57 lentes + 15 pares sobre N35).
Null de rotulagem: 200 reps de 35 pseudo-trades do universo com mesmo perfil temporal
(1 controle sorteado a ±10d de cada trade real, sem reposição), pipeline INTEGRAL do mapa
(lentes → cands cov>=60%+lift>=1.3 → top-6 → pares cov>=50% → MELHOR lift de par).
Reporta P(melhor par >= 8.20x | H0) e a distribuição. Seed fixa (determinístico)."""
import json, random
import _DA_mtf_common as C

cache = json.load(open(C.SCRATCH / "ctx_orig_shift0.json"))
CT = cache["ct"]  # 1107 controles, cada um com _cj_t
OBS_PAIR = 8.2
tr_ts = [t["t"] for t in C.TR]
rng = random.Random(42)
REPS = 200

best_pairs, best_singles = [], []
for rep in range(REPS):
    used = set()
    pseudo = []
    for tt in tr_ts:
        for radius in (10 * 86400, 20 * 86400, 40 * 86400):
            pool = [i for i, o in enumerate(CT) if i not in used and abs(o["_cj_t"] - tt) <= radius]
            if pool: break
        i = rng.choice(pool); used.add(i); pseudo.append(CT[i])
    ps_ts = [o["_cj_t"] for o in pseudo]
    ctrls = [o for i, o in enumerate(CT) if i not in used and min(abs(o["_cj_t"] - t) for t in ps_ts) > 24 * 900]
    lifts, cands, best = C.pipeline(pseudo, ctrls)
    finite = [x[3] for x in best if x[3] != float("inf")]
    infs = [x for x in best if x[3] == float("inf")]
    bp = (float("inf") if infs else (max(finite) if finite else 0.0))
    bs = max((c[4] for c in cands), default=0.0)
    best_pairs.append(bp); best_singles.append(bs)
    if (rep + 1) % 50 == 0: print(f"  rep {rep+1}/{REPS}")

fin = sorted(x for x in best_pairs if x != float("inf"))
n_inf = len(best_pairs) - len(fin)
ge = sum(1 for x in best_pairs if x >= OBS_PAIR)
print(f"\nNULL {REPS} reps — MELHOR lift de par por rep:")
if fin:
    print(f"  mediana={fin[len(fin)//2]:.2f}x p90={fin[int(0.9*len(fin))]:.2f}x p95={fin[int(0.95*len(fin))]:.2f}x max finito={fin[-1]:.2f}x | inf (ctrl=0): {n_inf}")
print(f"  P(melhor par >= {OBS_PAIR}x | H0) = {ge}/{REPS} = {ge/REPS:.3f}")
bs_f = sorted(best_singles)
print(f"MELHOR lift single por rep: mediana={bs_f[len(bs_f)//2]:.2f}x p95={bs_f[int(0.95*len(bs_f))]:.2f}x max={bs_f[-1]:.2f}x")
print(f"  (observado nos 35 reais: melhor single qualificado 2.68x [15M supply_far3atr]; melhor par 8.20x)")
n_nopair = sum(1 for x in best_pairs if x == 0.0)
print(f"  reps sem par qualificado (cov>=50% em top-6): {n_nopair}/{REPS}")
json.dump({"best_pairs": [str(x) for x in best_pairs], "best_singles": best_singles},
          open(C.SCRATCH / "attack3_null_results.json", "w"))
