#!/usr/bin/env python3
"""LAYER 2 — conjunção calibrada nos QUANTIS dos 14 GT (2026-07-05, plano de memória).
Correção de cálculo: cortes tirados da DISTRIBUIÇÃO dos próprios GT-estritos h1up (bandas q10-q90
deles), não do gap de medianas. Pré-declarado: features = legpos60, g_atr_spike, g_ema21_dist,
g_sweep_depth, n_supply_overhead; conjunção = todas dentro da banda GT-q10..q90 (one-sided onde a
direção é óbvia). + réplica com bandas q25-q75 (mais apertada). Painel + recall estrito + null."""
import json, random, bisect as bs
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
gt = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
BSs = sorted(BASE, key=lambda u: u["cj_t"]); BT = [u["cj_t"] for u in BSs]
for u in BASE:
    u["_gt"] = 0
for g in gt:
    j = bs.bisect_left(BT, g["flush_t"] - 8 * 3600)
    while j < len(BT) and BT[j] <= g["flush_t"] + 8 * 3600:
        u = BSs[j]
        if abs((u["g_sl"] + 0.1 * u["g_atr"]) - g["flush_low"]) <= (u.get("g_atr") or 5.0):
            u["_gt"] = 1
        j += 1
H1 = [u for u in BASE if fv(u, "h1_trend", 0) == 1]
GTm = [u for u in H1 if u["_gt"]]
print(f"GT-estritos h1up: {len(GTm)}")
FE = ["legpos60", "g_atr_spike", "g_ema21_dist", "g_sweep_depth", "n_supply_overhead"]
def qs(f, lo, hi):
    v = sorted(fv(u, f) for u in GTm if fv(u, f) is not None)
    return v[int(lo * (len(v) - 1))], v[int(hi * (len(v) - 1))]
for tag, lo, hi in (("q10-q90", 0.10, 0.90), ("q25-q75", 0.25, 0.75)):
    bands = {f: qs(f, lo, hi) for f in FE}
    print(f"\nBANDAS {tag}: " + " · ".join(f"{f} [{a:.2f},{b:.2f}]" for f, (a, b) in bands.items()))
    # one-sided óbvios: legpos <=hi · spike >=lo · ema21 <=hi · sweep >=lo · supply <=hi
    sel = [u for u in H1
           if fv(u, "legpos60", 9) <= bands["legpos60"][1]
           and fv(u, "g_atr_spike", 0) >= bands["g_atr_spike"][0]
           and fv(u, "g_ema21_dist", 9) <= bands["g_ema21_dist"][1]
           and fv(u, "g_sweep_depth", -9) >= bands["g_sweep_depth"][0]
           and fv(u, "n_supply_overhead", 99) <= bands["n_supply_overhead"][1]]
    p = panel(sel, f"GTQ {tag}", MISS_BULL)
    if not sel:
        continue
    print(f"    recall vs 56 totais: {strict_recall(sel, MISS_ALL)}/56 · GT dentro: {sum(u['_gt'] for u in sel)}")
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in H1]
    obs = sum(1 for u in sel if R3[u["cj_t"]]["R3"] >= 3) / len(sel)
    random.seed(11)
    ge = sum(1 for _ in range(4000) if sum(random.sample(H0, len(sel))) / len(sel) >= obs)
    print(f"    P(null>=obs vs família h1up) = {ge/4000:.4f}")
    nets = [R3[u["cj_t"]]["net3"] for u in sorted(sel, key=lambda x: x["cj_t"])]
    q = []
    for _ in range(2000):
        sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
        for x in sq:
            c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
        q.append(m2)
    q.sort()
    print(f"    streak: q95 {q[int(0.95*2000)]} P(>5) {sum(1 for x in q if x>5)/2000:.2f}")
