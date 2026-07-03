#!/usr/bin/env python3
"""DIAGNÓSTICO (2026-07-03): qual regra de SL reproduz os R salvos em l1_approved34.json
(base do l1_FINAL_regime_gated.json N24 +45,2R)?

Resultado (reproduzível): regra **v1 (zona_OB_low − 0,1·ATR)** bate **34/34** (sumR +35,2 = painel v1
do l1_sl_structural_test.md); regra nova aprovada (max(zona,swing6)−0,1·ATR) bate só 32/34.
⇒ Os outcomes do FINAL-24 (+45,2R · 18W · 75%) foram computados sob a REGRA V1, não sob a regra
nova da APPROVED_REFINEMENT_2026_06_16 (+41,0R nos 34). Conflito documentado.

RESOLUÇÃO (Cris 2026-07-03): **REGRA V1 = OFICIAL** ("artefato V1 é o aprovado"). A regra
max(zona,swing6) fica como estudo in-sample não-oficial. Correção registrada no topo de
APPROVED_REFINEMENT_2026_06_16.md + memória (project_l1_refinement card).
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
L1 = REPO / "my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION"
sys.path.insert(0, str(L1)); sys.path.insert(0, str(REPO / "my-strategy/core"))
import scanner

A34 = json.load(open(REPO / "my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_approved34.json"))
S = scanner.build_series()

def idx_of(ts):
    et = int(datetime.strptime(ts, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp())
    i = S.idx.get(et)
    return i if i is not None else min(range(S.N), key=lambda k: abs(S.T[k] - et))

def walk(i, entry, sl, target, mx=60):
    for k in range(i + 1, min(i + 1 + mx, S.N)):
        if S.L[k] <= sl: return -1.0
        if S.H[k] >= target: return 3.0
    e = min(i + mx, S.N - 1)
    return round((S.C[e] - entry) / (entry - sl), 2)

print("approved34: n", len(A34), "sumR", round(sum(t['R'] for t in A34), 1),
      "wins", sum(1 for t in A34 if t['R'] > 0))
ok = {"v1": 0, "new": 0}
for t in A34:
    i = idx_of(t["ts"]); entry = S.C[i]; atr = S.ATR14[i]
    dz = scanner.demand_zone(S, i)
    zlo = (dz[1] if dz else S.EMA21[i - 1]); sw6 = min(S.L[max(0, i - 5):i + 1])
    for tag, sl in [("v1", zlo - 0.1 * atr), ("new", max(zlo, sw6) - 0.1 * atr)]:
        if entry - sl <= 0: continue
        if abs(walk(i, entry, sl, entry + 3 * (entry - sl)) - t["R"]) <= 0.02:
            ok[tag] += 1
print(f"match: regra v1 = {ok['v1']}/34 · regra nova = {ok['new']}/34")
