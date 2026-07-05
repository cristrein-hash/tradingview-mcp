#!/usr/bin/env python3
"""LAYER 2 — composição única pré-declarada: DEEP-FLUSH dentro de h1up (2026-07-05).
Do perfil GT-vs-vizinhos (mapa, não teste): assinatura dos fundos do Cris na família h1up =
flush violento à base da perna, abaixo da EMA21, em demanda. 1 LOOK:
  L2-DF: h1_trend==1 & legpos60<=0.20 & g_atr_spike>=1.3 & g_ema21_dist<0
  (sobre a base v3: ctx pré-perna + demanda + reclaim>=1, ex-CASCEX)
Painel completo + recall estrito + null 4000× vs base + streak distribucional."""
import json, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
DF = [u for u in BASE if fv(u, "h1_trend", 0) == 1 and fv(u, "legpos60", 9) <= 0.20
      and fv(u, "g_atr_spike", 0) >= 1.3 and fv(u, "g_ema21_dist", 9) < 0]
p = panel(DF, "L2-DF h1up&base&spike&subEMA", MISS_BULL)
p_all = None
if DF:
    # recall também vs TODOS os 56 (não só BULL)
    print(f"  recall vs 56 totais: {strict_recall(DF, MISS_ALL)}/56")
nets = [R3[u["cj_t"]]["net3"] for u in sorted(DF, key=lambda x: x["cj_t"])]
random.seed(9); q = []
for _ in range(2000):
    sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
    for x in sq:
        c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
    q.append(m2)
q.sort()
print(f"  streak distribucional: q50 {q[1000]} q95 {q[int(0.95*2000)]} P(>5) {sum(1 for x in q if x>5)/2000:.2f}")
H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BASE]
obs = sum(1 for u in DF if R3[u["cj_t"]]["R3"] >= 3) / len(DF)
ge = sum(1 for _ in range(4000) if sum(random.sample(H0, len(DF))) / len(DF) >= obs)
print(f"  P(null>=obs vs base) = {ge/4000:.4f}")
print("\n  membros (p/ visual):")
for u in sorted(DF, key=lambda x: x["cj_t"]):
    r3 = R3[u["cj_t"]]
    print(f"   {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} "
          f"{'WIN ' if r3['R3']>=3 else 'loss'} net {r3['net3']:+.2f} GT={u.get('_gt','?')}")
json.dump({"panel": p, "p_null": ge / 4000, "stk_q95": q[int(0.95 * 2000)]},
          open(HERE / "results" / "layer2_h1up_deepflush_20260705.json", "w"), indent=1, default=str)
