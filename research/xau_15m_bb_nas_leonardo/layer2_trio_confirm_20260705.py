#!/usr/bin/env python3
"""LAYER 2 — confirmação única declarada do TRIO h1up & rsi40-60 & quiet30 (2026-07-05).
Materialização do heredoc (guard). Painel completo + streak distribucional + null 4000×.
Resultado registado: N323 hit3R 35,6% +93,2 DD−15,7 stk−11 2,94/sem · P(null)=0,013 ·
streak q50 11 P(>5)=1,00 · recall estrito 1/33 — lift real sobre a base (30,3%) mas NÃO são os
fundos do Cris e o perfil de streak é inoperável FN; o valor está na FAMÍLIA h1up (FDR P=0,002,
N859 +194,6, recall 9/33) como semente de discriminação para a próxima iteração."""
import json, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
TRIO = [u for u in BASE if fv(u, "h1_trend", 0) == 1 and 40 <= fv(u, "rsi_low", -1) <= 60
        and u["_q30"] is not None and u["_q30"] <= 1.0]
p = panel(TRIO, "TRIO h1up&rsi4060&quiet30")
nets = [R3[u["cj_t"]]["net3"] for u in sorted(TRIO, key=lambda x: x["cj_t"])]
random.seed(3); q = []
for _ in range(2000):
    sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
    for x in sq:
        c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
    q.append(m2)
q.sort()
print(f"  streak distribucional: q50 {q[1000]} q95 {q[int(0.95*2000)]} P(>5) {sum(1 for x in q if x>5)/2000:.2f}")
H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BASE]
obs = sum(1 for u in TRIO if R3[u["cj_t"]]["R3"] >= 3) / len(TRIO)
ge = sum(1 for _ in range(4000) if sum(random.sample(H0, len(TRIO))) / len(TRIO) >= obs)
print(f"  P(null>=obs) = {ge/4000:.4f}")
json.dump({"trio": p, "p_null": ge / 4000, "stk_q95": q[int(0.95 * 2000)]},
          open(HERE / "results" / "layer2_trio_confirm_20260705.json", "w"), indent=1, default=str)
