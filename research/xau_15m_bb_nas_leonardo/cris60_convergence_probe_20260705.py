#!/usr/bin/env python3
"""CONVERGÊNCIA 3-LENTES vs rótulo Cris-60 — TESTE ÚNICO PRÉ-DECLARADO (2026-07-05).
Anti-miopia: multi-fatorial (3 sub-estados ortogonais: posição na perna legpos60, exaustão rsi_low,
distância g_ema21_dist), lentes tiradas do topo COERENTE do scan de 72 features (cris60_signature,
null de multiplicidade incluído lá), rótulo = fundos reais do Cris (trajetória por construção),
validação = permutação do rótulo 2000×. 1 look — sem varrer thresholds (usa os cortes de quartil
do scan: legpos60≤0,10 · rsi_low≤39 · ema21_dist<0). Dois objetivos: prec-Cris E hit-3R/NET3."""
import json, bisect, random, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT)); assert len(gt) == 60
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
for u in U:
    u["is_cris60"] = 0
UT = sorted(range(len(U)), key=lambda k: U[k]["t"]); T = [U[k]["t"] for k in UT]
for g in gt:
    j = bisect.bisect_left(T, g["flush_t"] - 7200); best = None
    while j < len(T) and T[j] <= g["flush_t"] + 7200:
        u = U[UT[j]]
        if best is None or abs(u["t"] - g["flush_t"]) < abs(best["t"] - g["flush_t"]):
            best = u
        j += 1
    if best:
        best["is_cris60"] = 1
NC = sum(u["is_cris60"] for u in U); base = NC / len(U)

def fv(u, k, d=None):
    v = u.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

C = [u for u in U if fv(u, "legpos60", 9) <= 0.10 and fv(u, "rsi_low", 99) <= 39 and fv(u, "g_ema21_dist", 9) < 0]
nc = sum(u["is_cris60"] for u in C)
h3 = [u for u in C if R3.get(u["cj_t"], {}).get("R3", -9) >= 3]
nets = [R3[u["cj_t"]]["net3"] for u in C if u["cj_t"] in R3]
weeks = len({u["g_week"] for u in U})
print(f"CONVERGÊNCIA 3 lentes (legpos60≤0,10 & rsi_low≤39 & ema21_dist<0):")
print(f"  N{len(C)} · cris {nc} (prec {100*nc/len(C):.1f}%, lift {nc/len(C)/base:.2f}, recall {nc}/{NC})")
print(f"  hit-3R {100*len(h3)/len(C):.1f}% · NET3 {sum(nets):+.1f} · {len(C)/weeks:.2f}/sem")
random.seed(1)
ids = [id(u) for u in U]; cid = set(id(u) for u in C); ge = 0
for _ in range(2000):
    lab = set(random.sample(ids, NC))
    if len(cid & lab) >= nc:
        ge += 1
print(f"  P(null>=obs) = {ge/2000:.4f}")
json.dump({"n": len(C), "cris": nc, "prec": round(nc / len(C), 4), "recall": round(nc / NC, 3),
           "hit3r": round(len(h3) / len(C), 3), "net3": round(sum(nets), 1),
           "per_week": round(len(C) / weeks, 2), "p_null": ge / 2000},
          open(HERE / "results" / "cris60_convergence_probe_20260705.json", "w"), indent=1)
print("OK → results/cris60_convergence_probe_20260705.json")
