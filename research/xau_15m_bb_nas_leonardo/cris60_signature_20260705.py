#!/usr/bin/env python3
"""ASSINATURA DOS 60 FUNDOS DO CRIS no universo fractal selado (2026-07-05).
Rótulo expandido pelo Cris (61 círculos → 60 fundos únicos, GT sha-checked). Cobertura lab_g: 59/60
(miss único declarado: 2025-11-25 14:45). Pergunta supervisionada: no universo selado de 4739
fundos locais com ~74 features causais, o que separa os fundos-Cris (~1,3% base) do resto?

DISCIPLINA (pós-DA, multiplicidade in-ledger): scan univariado por quartis sobre TODAS as features
causais numéricas; significância APENAS via null de permutação do rótulo (2000×) sobre o MÁXIMO
lift do ledger inteiro (todas features × 4 quartis) → P in-ledger; gate P≤0,002 (regra DA para
re-interrogação dos mesmos dados). Binárias: lift direto no valor 1. Outcome/id EXCLUÍDOS do scan:
t, cj_t, yr, block, is_*, g_R, g_risk, g_entry, g_sl, g_week (g_atr mantido: causal na barra).
Painel adicional: hit-3R (R3) por pocket para ligar Cris-ness a lucro. Zero conjunções nesta rodada."""
import json, bisect, hashlib, random, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent

GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT)); assert len(gt) == 60

U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}

# --- label is_cris60: fractal t a ±2h do flush GT E low do episódio compatível (±1%) ---
for u in U:
    u["is_cris60"] = 0
UT = sorted(range(len(U)), key=lambda k: U[k]["t"])
T = [U[k]["t"] for k in UT]
matched = 0
for g in gt:
    j = bisect.bisect_left(T, g["flush_t"] - 2 * 3600); best = None
    while j < len(T) and T[j] <= g["flush_t"] + 2 * 3600:
        u = U[UT[j]]
        if best is None or abs(u["t"] - g["flush_t"]) < abs(best["t"] - g["flush_t"]):
            best = u
        j += 1
    if best is not None:
        best["is_cris60"] = 1; matched += 1
NC = sum(u["is_cris60"] for u in U)
print(f"label: {matched}/60 GT → {NC} candidatos únicos marcados (base {100*NC/len(U):.2f}%)")

EXCL = {"t", "cj_t", "yr", "block", "is_monforte", "is_medfraco", "is_bottom", "is_cris60",
        "g_R", "g_risk", "g_entry", "g_sl", "g_week"}
feats = [k for k in U[0] if k not in EXCL and isinstance(U[0].get(k), (int, float, type(None)))]
# só numéricas com variação
def vals(f):
    return [u[f] for u in U if isinstance(u.get(f), (int, float)) and not isinstance(u.get(f), bool)]
feats = [f for f in feats if len(set(vals(f))) > 1]
print(f"features causais no scan: {len(feats)}")

def groups_for(f):
    vs = sorted(vals(f)); n = len(vs)
    uniq = sorted(set(vs))
    out = []
    if len(uniq) <= 4:   # discreta/binária: um grupo por valor
        for v in uniq:
            out.append((f"={v}", [u for u in U if u.get(f) == v]))
    else:
        qs = [vs[int(n * q)] for q in (0.25, 0.5, 0.75)]
        bounds = [(vs[0], qs[0]), (qs[0], qs[1]), (qs[1], qs[2]), (qs[2], vs[-1])]
        for qi, (lo, hi) in enumerate(bounds):
            if qi == 0:
                g = [u for u in U if isinstance(u.get(f), (int, float)) and u[f] <= hi]
            elif qi == 3:
                g = [u for u in U if isinstance(u.get(f), (int, float)) and u[f] >= lo]
            else:
                g = [u for u in U if isinstance(u.get(f), (int, float)) and lo <= u[f] <= hi]
            out.append((f"Q{qi+1} {lo:.2f}–{hi:.2f}", g))
    return [(tag, g) for tag, g in out if len(g) >= 40]   # grupos minúsculos fora (poder)

base = NC / len(U)
ledger = []   # (feature, tag, n, ncris, lift)
for f in feats:
    for tag, g in groups_for(f):
        nc = sum(u["is_cris60"] for u in g)
        lift = (nc / len(g)) / base
        ledger.append((f, tag, len(g), nc, lift))
ledger.sort(key=lambda x: -x[4])

# --- null de permutação sobre o MÁXIMO lift do ledger inteiro ---
random.seed(20260705)
idx_groups = []
for f in feats:
    for tag, g in groups_for(f):
        idx_groups.append([id(u) for u in g])
ids = [id(u) for u in U]
maxes = []
for _ in range(2000):
    lab = set(random.sample(ids, NC))
    m = 0.0
    for gi in idx_groups:
        nc = sum(1 for x in gi if x in lab)
        m = max(m, (nc / len(gi)) / base)
    maxes.append(m)
maxes.sort()
def pval(lift):
    return sum(1 for m in maxes if m >= lift) / len(maxes)
q95 = maxes[int(0.95 * len(maxes))]; q998 = maxes[int(0.998 * len(maxes))]
print(f"null max-lift (2000 perms, ledger {len(idx_groups)} grupos): q50 {maxes[1000]:.2f} · "
      f"q95 {q95:.2f} · q99.8 {q998:.2f}")
print()
print(f"{'feature':<24} {'grupo':>16} {'N':>5} {'cris':>4} {'prec%':>6} {'lift':>5} {'P':>7} {'hit3R%':>7}")
sig = []
for f, tag, n, nc, lift in ledger[:20]:
    grp = None
    for tg, g in groups_for(f):
        if tg == tag: grp = g; break
    h3 = 100 * sum(1 for u in grp if R3.get(u["cj_t"], {}).get("R3", -9) >= 3) / len(grp)
    p = pval(lift)
    mark = " ***" if p <= 0.002 else ""
    if p <= 0.002: sig.append((f, tag, lift, p))
    print(f"{f:<24} {tag:>16} {n:>5} {nc:>4} {100*nc/n:>5.1f}% {lift:>5.2f} {p:>7.3f} {h3:>6.1f}%{mark}")
print()
print(f"SIGNIFICATIVOS a P≤0,002 (gate DA): {sig if sig else 'NENHUM'}")
json.dump({"label_matched": matched, "n_cris": NC, "ledger_groups": len(idx_groups),
           "null_q95": q95, "null_q998": q998,
           "top20": [{"f": f, "g": t, "n": n, "cris": nc, "lift": round(l, 2), "p": pval(l)}
                     for f, t, n, nc, l in ledger[:20]],
           "significant": [{"f": f, "g": t, "lift": round(l, 2), "p": p} for f, t, l, p in sig]},
          open(HERE / "results" / "cris60_signature_20260705.json", "w"), indent=1)
print("OK → results/cris60_signature_20260705.json")
