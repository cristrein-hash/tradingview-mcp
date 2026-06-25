#!/usr/bin/env python3
"""Para cada WINNER cortado pela camada conv≤1 ∪ bear_leg_refined, busca o proximo trade PRESERVADO (nao cortado) e
ve se ele captura o mesmo move (recovery). Quantifica o CUSTO LIQUIDO REAL de cortar winners. Régua oficial let-run.
Calibracao 276. Verified 2026-06-25."""
import csv, datetime as dt
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
COST = 0.35; BAR = 14400; WIN_BARS = 60   # janela "mesmo move" ~10 dias
F = __import__("json")
frozen_ts = {}
for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl"):
    pass
import json
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
REG = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_regua_structural.csv"))}
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}
def cut(b): t = TAB.get(b, {}); return t.get("rm_conv") == "1" or t.get("rm_blr") == "1"
def net(b): return float(REG[b]["letrun_struct"]) - COST
def dts(b): return dt.datetime.utcfromtimestamp(int(F[b]["ts_epoch"]))

traded = sorted(REG.keys())
cut_winners = [b for b in traded if cut(b) and net(b) > 0]
print(f"WINNERS cortados pela camada (net>0): {len(cut_winners)}\n")
gross = 0; recovered = 0; recov_R = 0
for b in cut_winners:
    gross += net(b)
    nxt = [x for x in traded if x > b and not cut(x)]
    near = [x for x in nxt if (int(F[x]['ts_epoch']) - int(F[b]['ts_epoch'])) <= WIN_BARS * BAR]
    # proximo preservado (qualquer) + proximo preservado WINNER na janela
    np = nxt[0] if nxt else None
    win_near = next((x for x in near if net(x) > 0), None)
    gap = (dts(np) - dts(b)).days if np else None
    rec = win_near is not None and net(win_near) >= net(b)
    if rec: recovered += 1; recov_R += net(b)
    line = f"  #{b} {dts(b):%Y-%m-%d} net={net(b):+.2f} → próx preservado #{np} ({gap}d, net={net(np):+.2f})" if np else f"  #{b} (sem trade depois)"
    if win_near:
        line += f" | winner preservado na janela: #{win_near} net={net(win_near):+.2f} {'✓RECUPERA' if rec else '(menor)'}"
    else:
        line += " | NENHUM winner preservado em ~10d → custo NÃO recuperado"
    print(line)
print(f"\nRESUMO: custo bruto winners cortados = {gross:+.2f}R | recuperados (winner preservado ≥ em ~10d) = {recovered}/{len(cut_winners)} (≈{recov_R:+.2f}R)")
print(f"CUSTO LÍQUIDO REAL aprox = {gross - recov_R:+.2f}R (vs bruto {gross:+.2f}R)")
print("\nCalibracao 276 (canon). 'Recupera' = próximo move pego por trade preservado; aproximacao, nao prova.")
