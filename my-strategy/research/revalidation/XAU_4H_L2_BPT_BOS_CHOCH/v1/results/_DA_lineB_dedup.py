#!/usr/bin/env python3
"""LINHA B — dedup serial do pool (1566 barras coladas) em FUNDOS DISTINTOS. Agrupa barras dentro de 12 barras (mesma
queda) num episódio; representante = barra de menor close (o fundo real). Verified 2026-06-25."""
import json, datetime as dt
from pathlib import Path
from collections import Counter
V1 = Path(__file__).resolve().parents[1]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
pool = json.load(open(V1 / "results/l2_bpt_lineB_candidate_pool.json"))
pool.sort(key=lambda x: x["i"])
GAP = 12
groups = []; cur = []
for f in pool:
    if cur and f["i"] - cur[-1]["i"] > GAP:
        groups.append(cur); cur = []
    cur.append(f)
if cur: groups.append(cur)
# representante = PRIMEIRA barra que dispara o sinal (CAUSAL — sem olhar o futuro do grupo)
eps = [g[0] for g in groups]
def yr(f): return dt.datetime.utcfromtimestamp(int(F[f["i"]]["ts_epoch"])).year
print(f"pool barras = {len(pool)}  →  FUNDOS DISTINTOS (dedup {GAP} barras) = {len(eps)}")
print("por ano:", dict(sorted(Counter(yr(f) for f in eps).items())))
print("tamanho médio do grupo:", round(len(pool) / len(groups), 1), "barras")
json.dump([e["i"] for e in eps], open(V1 / "results/l2_bpt_lineB_distinct_bottoms.json", "w"))
print(f"salvo -> results/l2_bpt_lineB_distinct_bottoms.json ({len(eps)} fundos)")
