#!/usr/bin/env python3
"""Relatório Stage-B: estatísticas descritivas dos candidatos (sem regra/threshold/backtest). Lê candidates_stageB.csv
(gerado do RAW via primitives). Verified 2026-06-25."""
import csv, statistics as st, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "candidates_stageB.csv")))
n = len(rows)
def f(r, k):
    try: return float(r[k])
    except Exception: return None
ts = sorted(int(r["entry_t"]) for r in rows)
d0, d1 = dt.datetime.utcfromtimestamp(ts[0]), dt.datetime.utcfromtimestamp(ts[-1])
weeks = (ts[-1] - ts[0]) / (7 * 86400); months = (ts[-1] - ts[0]) / (30.4 * 86400)
nl = sum(1 for r in rows if r["dir"] == "LONG"); ns = n - nl
print(f"=== STAGE-B — RELATÓRIO DE CANDIDATOS ===")
print(f"TOTAL candidatos = {n}")
print(f"cobertura: {d0:%Y-%m-%d} → {d1:%Y-%m-%d} ({weeks:.0f} semanas / {months:.0f} meses)")
print(f"frequência BRUTA: {n/weeks:.1f}/semana | {n/months:.1f}/mês  (alvo final 1-3/sem é PÓS-seleção, não agora)")
print(f"direção: LONG {nl} ({100*nl/n:.0f}%) | SHORT {ns} ({100*ns/n:.0f}%)")
print("\nper-bloco:")
from collections import Counter
bc = Counter(r["block"] for r in rows)
for b in sorted(bc): print(f"  {b}: {bc[b]}")
print("\n=== distribuições de features (sanity, sem threshold) ===")
def dist(k, fmt="{:.2f}"):
    vs = [f(r, k) for r in rows if f(r, k) is not None]
    if not vs: print(f"  {k:>20}: —"); return
    qs = st.quantiles(vs, n=4)
    print(f"  {k:>20}: min {fmt.format(min(vs))} | q1 {fmt.format(qs[0])} | med {fmt.format(qs[1])} | q3 {fmt.format(qs[2])} | max {fmt.format(max(vs))}")
for k in ["zone_width_atr","zone_age_bars","mitig_count","penetration_pct","bars_in_zone","arrival_atr","nas_dist_ema_atr","dist_edge_atr","nas_count_in_zone","smc_bos_choch_50","rsi","hour_utc"]:
    dist(k)
def boolc(k):
    c = Counter(r[k] for r in rows); print(f"  {k:>22}: {dict(c)}")
print("\n=== categóricos ===")
for k in ["setup_vs_flow","zone_virgin","acceptance_beyond_mid","nas_before_touch","zone_pre_existing","last_smc","op_flow","dow"]:
    boolc(k)
print("\n=== campos mapeados ao RAW (todas as colunas) ===")
print("  ", list(rows[0].keys()))
