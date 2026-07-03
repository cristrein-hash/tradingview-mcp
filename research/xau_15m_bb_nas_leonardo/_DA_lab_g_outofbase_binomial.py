#!/usr/bin/env python3
"""DA LAB G — complemento do ATAQUE 2/4: os 21 picks de A FORA da base435.
Binomial dos 21 contra o WR do context-pool (poolA), referência non-swept do pool,
e custo médio em R do Sistema A. Determinístico, só leitura."""
import json, math, statistics as st
from pathlib import Path

HERE = Path(__file__).parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]

def fv(r, k, d=0):
    v = r.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)
            and r["g_knife"] == 0)

A = [r for r in U if sysA(r)]
out = [r for r in A if not r["g_in_base435"]]
poolA = [r for r in U if r["g_v5h"] == "BULL" and r["g_knife"] == 0
         and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)]
p0 = sum(1 for r in poolA if r["g_R"] > 0) / len(poolA)
w = sum(1 for r in out if r["g_R"] > 0)

def tail(n, k, p):
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

print(f"21 fora-da-base: wins brutos {w}/21 ({100*w/21:.1f}%) · P(X>={w}|p_poolA={p0:.3f}) = {tail(21, w, p0):.4f}")
ns = [r for r in poolA if fv(r, "swept_prior_low") != 1]
print(f"poolA non-swept N={len(ns)} WR bruto {100*sum(1 for r in ns if r['g_R']>0)/len(ns):.1f} "
      f"avg_net {st.mean(r['g_R']-0.8/r['g_risk'] for r in ns):+.3f}")
print("A: custo médio em R (SB .80):", round(st.mean(0.8 / r["g_risk"] for r in A), 3),
      "| risco mediano $", st.median(r["g_risk"] for r in A))
