#!/usr/bin/env python3
"""PASSO 1 FUNDACAO — re-medir os 5 grupos de skip na REGUA OFICIAL (SL_CONTEXT + let-run, custo 0.35R).
Por grupo: n_cut, runners_cut (letrun>=5R realizado), winners_cut (net>0), sumR_removido, efeito em sumR/streak/maxDD.
Teste-chave: conv<=1-skip vs BEAR-skip sob let-run (a preservacao do #5826 compensa?). Calibracao 276 (canon). Verified 2026-06-25."""
import csv
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
COST = 0.35
REG = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_regua_structural.csv"))}
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}
# join: so trades com regua oficial (245 traded; 31 TOP_EXH no_trade ja excluidos pelo SL)
rows = []
for b, t in TAB.items():
    if b not in REG: continue
    lr = float(REG[b]["letrun_struct"]); mfe = float(REG[b]["mfe_struct"])
    rows.append({"b": b, "dt": t["dt"], "net": lr - COST, "letrun": lr, "mfe": mfe,
                 "rm_conv": int(t["rm_conv"]), "rm_bear": int(t["rm_bear"]), "rm_blr": int(t["rm_blr"]),
                 "regime": t["regime"]})
rows.sort(key=lambda r: r["b"])
print(f"join regua oficial ∩ grupos = {len(rows)} traded (de 276; 31 TOP_EXH no_trade pelo SL)\n")

def stats(rs):
    n = len(rs)
    if not n: return dict(n=0, sumR=0, WR=0, maxDD=0, streak=0)
    cum = peak = mdd = ls = best = 0
    for r in sorted(rs, key=lambda x: x["b"]):
        cum += r["net"]; peak = max(peak, cum); mdd = max(mdd, peak - cum)
        ls = 0 if r["net"] > 0 else ls + 1; best = max(best, ls)
    return dict(n=n, sumR=round(sum(r["net"] for r in rs), 1), WR=round(100 * sum(1 for r in rs if r["net"] > 0) / n),
                maxDD=round(mdd, 1), streak=best)

RUN = lambda r: r["letrun"] >= 5.0   # runner realizado sob let-run estrutural
base = stats(rows); nrun = sum(1 for r in rows if RUN(r))
print(f"BASELINE (todos {base['n']}, let-run oficial): sumR={base['sumR']:+} WR={base['WR']}% maxDD={base['maxDD']} streak={base['streak']} | runners(letrun>=5R)={nrun}\n")

GROUPS = {
    "A conv<=1": lambda r: r["rm_conv"] == 1,
    "B conv<=1 ∩ BEAR": lambda r: r["rm_conv"] == 1 and r["rm_bear"] == 1,
    "C conv<=1 \\ BEAR": lambda r: r["rm_conv"] == 1 and r["rm_bear"] == 0,
    "E bear_leg_refined": lambda r: r["rm_blr"] == 1,
}
print("=== SKIP GROUPS na regua oficial (remover o grupo) ===")
print(f"{'grupo':>20} | {'n_cut':>5} | {'runners_cut':>11} | {'win_cut':>7} | {'sumR_removido':>13} | {'base apos: sumR/streak/maxDD':>28}")
for name, f in GROUPS.items():
    g = [r for r in rows if f(r)]; kept = [r for r in rows if not f(r)]
    rc = sum(1 for r in g if RUN(r)); wc = sum(1 for r in g if r["net"] > 0)
    srem = round(sum(r["net"] for r in g), 1); k = stats(kept)
    print(f"{name:>20} | {len(g):>5} | {rc:>11} | {wc:>7} | {srem:>+13} | {k['sumR']:>+8}/{k['streak']}/{k['maxDD']}")

# Grupo D = preserve (BEAR corta, conv preserva): valor que conv ADICIONA mantendo D
D = [r for r in rows if r["rm_bear"] == 1 and r["rm_conv"] == 0]
print(f"\n=== GRUPO D (BEAR\\conv, conv PRESERVA) — valor da preservacao sob let-run ===")
print(f"  n={len(D)} | runners(letrun>=5R) preservados={sum(1 for r in D if RUN(r))} | sumR preservado={sum(r['net'] for r in D):+.1f}")
for r in sorted(D, key=lambda x: -x["letrun"]):
    print(f"    #{r['b']} {r['dt']} regime={r['regime']} letrun={r['letrun']:+.1f} mfe={r['mfe']:.1f} {'<<RUNNER' if RUN(r) else ''}")

# TESTE-CHAVE: conv<=1-skip vs BEAR-skip sob let-run
print("\n=== TESTE-CHAVE: conv<=1-skip vs BEAR-skip (regua oficial let-run) ===")
conv_kept = stats([r for r in rows if r["rm_conv"] == 0]); conv_rc = sum(1 for r in rows if r["rm_conv"] == 1 and RUN(r))
bear_kept = stats([r for r in rows if r["rm_bear"] == 0]); bear_rc = sum(1 for r in rows if r["rm_bear"] == 1 and RUN(r))
print(f"  conv<=1 skip → base sumR={conv_kept['sumR']:+} streak={conv_kept['streak']} maxDD={conv_kept['maxDD']} | runners_cut={conv_rc}")
print(f"  BEAR    skip → base sumR={bear_kept['sumR']:+} streak={bear_kept['streak']} maxDD={bear_kept['maxDD']} | runners_cut={bear_rc}")
# combinado conv ∪ bear_leg_refined
comb = stats([r for r in rows if not (r["rm_conv"] == 1 or r["rm_blr"] == 1)])
comb_rc = sum(1 for r in rows if (r["rm_conv"] == 1 or r["rm_blr"] == 1) and RUN(r))
print(f"  conv<=1 ∪ bear_leg_refined skip → base sumR={comb['sumR']:+} streak={comb['streak']} maxDD={comb['maxDD']} | runners_cut={comb_rc}")
print("\nCalibracao 276 (canon). letrun=régua oficial aprovada; nada vira gate novo sem validação.")
