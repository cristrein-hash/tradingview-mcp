#!/usr/bin/env python3
"""VERIFICACAO INDEPENDENTE do classificador de fase final (FaseD INTERSECT FSM4) no kit (2026-07-07).
Confirma metricas + loser-targets cortados + null multiplicidade-consciente. Script salvo (nao inline)."""
import json, sys
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import score, ENTRIES
FINAL=[2,3,4,7,8,9,10,12,13,14,15,16,20,23,27,30,35,36,37,39,40,44,45,46,48,51,52,53,55,61,62,64,71,74,75,76,77,78,82,84,87,88,90,93]
LOSER_TARGETS=[21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
WINNER_KEYS=[1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]
m=score(FINAL)
print("=== CONFIRMACAO score(FINAL) ==="); print(json.dumps(m,indent=1))
keep=set(FINAL); alln=set(e["n"] for e in ENTRIES); cut=alln-keep
lt_cut=sorted(set(LOSER_TARGETS)&cut); lt_kept=sorted(set(LOSER_TARGETS)&keep)
wk_kept=sorted(set(WINNER_KEYS)&keep); wk_cut=sorted(set(WINNER_KEYS)&cut)
print(f"\nloser-targets CORTADOS {len(lt_cut)}/22: {lt_cut}")
print(f"loser-targets SOBREVIVEM {len(lt_kept)}/22: {lt_kept}")
print(f"winner-keys MANTIDOS {len(wk_kept)}/22: {wk_kept}")
print(f"winner-keys CORTADOS (custo) {len(wk_cut)}/22: {wk_cut}")
# null exato hipergeometrico: P(X>=winners_kept | 96, 52 winners, N_kept)
from math import comb
N=len(ENTRIES); K=sum(e["out"] for e in ENTRIES); n=m["N_kept"]; x=m["winners_kept"]
p=sum(comb(K,i)*comb(N-K,n-i) for i in range(x,min(K,n)+1))/comb(N,n)
print(f"\nnull hipergeometrico exato P(winners_kept>={x} | N{N},W{K},n{n}) = {p:.4f}")
# multiplicidade: o combo foi best-of-11 de features best-of-grid. correcao ingenua para K_looks
for Klooks in (3,6,11,20):
    print(f"  sob {Klooks} looks (Sidak 1-(1-p)^K): {1-(1-p)**Klooks:.3f}")
print("\nOK")
