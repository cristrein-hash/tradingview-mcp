#!/usr/bin/env python3
"""PROBE — viabilidade da lente ANINHAMENTO MULTI-TF de valor (discount-of-discount) p/ ideação de features.
Confirma, do RAW 15M exclusivo (primitives/*.json), que dá pra derivar buckets 1D/semanal causalmente
(floor(t/period), último bucket FECHADO) e mede a distribuição da posição da barra 15M dentro do range
do DIA ANTERIOR (discount/mid/premium). NÃO é backtest — é grounding pras propostas de feature.
Causal: cada barra 15M consome só buckets HTF já fechados (bisect_right sobre t_end). Verified 2026-06-26."""
import json, bisect, statistics as st
from pathlib import Path

PRIM = sorted((Path(__file__).parent / "primitives").glob("*.primitives.json"))
bars = {}
for p in PRIM:
    for b in json.loads(p.read_text())["series"]:
        bars[b["t"]] = b
ts = sorted(bars)
print("15M bars", len(ts))

def buckets(period):
    bk = {}
    for t in ts:
        b = bars[t]; k = t // period
        if k not in bk:
            bk[k] = {"h": b["h"], "l": b["l"], "c": b["c"], "o": b["o"], "k": k}
        else:
            z = bk[k]; z["h"] = max(z["h"], b["h"]); z["l"] = min(z["l"], b["l"]); z["c"] = b["c"]
    return [bk[k] for k in sorted(bk)]

D = buckets(86400); W = buckets(604800)
print("1D buckets", len(D), "  weekly buckets", len(W))

dr = [d["h"] - d["l"] for d in D if d["h"] > d["l"]]
print("daily range USD median", round(st.median(dr), 1),
      "p10", round(sorted(dr)[len(dr) // 10], 1), "p90", round(sorted(dr)[len(dr) * 9 // 10], 1))
wr = [w["h"] - w["l"] for w in W if w["h"] > w["l"]]
print("weekly range USD median", round(st.median(wr), 1))

# posição da barra 15M dentro do range do DIA ANTERIOR (causal: último daily FECHADO)
dends = [(d["k"] + 1) * 86400 for d in D]
cnt = {"disc": 0, "mid": 0, "prem": 0, "na": 0}
for t in ts:
    ki = bisect.bisect_right(dends, t) - 1
    if ki < 0:
        cnt["na"] += 1; continue
    d = D[ki]; rng = d["h"] - d["l"]
    if rng <= 0:
        cnt["na"] += 1; continue
    pos = (bars[t]["c"] - d["l"]) / rng
    cnt["disc" if pos < 0.333 else ("prem" if pos > 0.667 else "mid")] += 1
print("15M bars by position in PRIOR-DAY range:", cnt)
