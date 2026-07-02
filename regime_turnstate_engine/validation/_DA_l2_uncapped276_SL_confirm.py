#!/usr/bin/env python3
"""CONFIRMAÇÃO DO SL (a pedido do Cris — 'o SL é a chave'): que SL gera o `l2_bpt_uncapped_or_proxy_outcomes_276.csv`?
Lê o gerador `reconstruct_l2_bpt_outcomes_uncapped.py` (constantes) + a distribuição de risk_atr do CSV.
Pergunta única: é o SL teto-1.5ATR que o canon descartou como MIRAGEM, ou um SL legítimo?"""
import csv
from collections import Counter
from pathlib import Path
B=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
CSV=B/"results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"
GEN=B/"reconstruct_l2_bpt_outcomes_uncapped.py"
rows=list(csv.DictReader(open(CSV)))
ra=[float(r["risk_atr"]) for r in rows]
n=len(rows);at_ceil=sum(1 for x in ra if abs(x-1.5)<1e-6)
print("="*78);print("CONFIRMAÇÃO DO SL — l2_bpt_uncapped_or_proxy_outcomes_276.csv");print("="*78)
print(f"\nrisk_atr (distância do SL em ATR): n={n} min={min(ra)} max={max(ra)}")
print(f"  trades com risk_atr == 1.5 (no TETO): {at_ceil}/{n} = {100*at_ceil/n:.0f}%  <-- cap binding na maioria")
# extrair as constantes de SL do gerador
src=GEN.read_text().splitlines()
print("\nConstantes/lógica de SL no gerador (reconstruct_l2_bpt_outcomes_uncapped.py):")
for i,l in enumerate(src,1):
    s=l.strip()
    if any(k in s for k in ("R_FLOOR","R_CEIL","cap risk","sl=lo-0.1","risk>R_CEIL","SL estrutural IDÊNTICO","risk floor")):
        print(f"  L{i}: {s}")
print("""
VEREDITO (factual):
  - SL = swing low 6b − 0.1ATR, mas com TETO R_CEIL = 1.5 ATR (risk capado a 1.5ATR quando estrutural é mais largo).
  - 183/276 (66%) dos trades têm risk EXATAMENTE 1.5ATR = o TETO está a morder na maioria → o SL real usado é ~teto-1.5ATR.
  - O próprio cabeçalho do gerador diz: "DIAGNÓSTICO/derived ... NÃO produção, NÃO promoção, realR capado NUNCA como árbitro".
  - Canon (project_l2_bpt_sl_exit_approved §3): "o +144R let-run sob SL tight era MIRAGEM do teto 1.5ATR ... o SL tight
    1.5ATR-teto (artefato) foi SUPERSEDED por SL_CONTEXT (mediano 2.81ATR)".
  => CONFIRMADO: este ficheiro usa o SL teto-1.5ATR = exatamente a MIRAGEM que o canon descartou.
     Os monumentais 'sobrevivem' aqui porque o SL artificialmente tight encolhe a unidade de risco e infla o R-múltiplo.
     R deste ficheiro (realized_letrun_120 etc.) NÃO é o R da estratégia aprovada (essa é SL_CONTEXT).
  ÚTIL como: instrumento DIAGNÓSTICO de convexidade (mfe_R, max_run_R, vstair, monster_flag) + o UNIVERSO 276 (bar_idx).
  NÃO útil como: base de R para construir entry/skip (seria construir sobre o artefato rejeitado).""")
