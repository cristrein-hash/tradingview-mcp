#!/usr/bin/env python3
"""PASSO B — refinar conv≤1 p/ NÃO cortar em bull-forte (parar de descartar winners). Identifica os discards POSITIVOS
sob let-run e seu contexto CAUSAL (regime v3, weekly_slope, macro phase), testa refinamentos (preserve-se-bull) e
re-mede na régua oficial: positivos resgatados vs losers re-admitidos + sumR/maxDD/streak/runners. Calibracao 276. Verified 2026-06-25."""
import csv
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
COST = 0.35
REG = {int(r["bar_idx"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_regua_structural.csv"))}
TAB = {int(r["b"]): r for r in csv.DictReader(open(V1 / "results/l2_bpt_conv_bear_overlap_table.csv"))}
MB = {}
for r in csv.DictReader(open(V1 / "results/l2_bpt_full276_macro_bear_v3_decisions.csv")):
    try: MB[int(float(r["bar_idx"]))] = r
    except Exception: pass
def fnum(x, d=None):
    try: return float(x)
    except Exception: return d

rows = []
for b, t in TAB.items():
    if b not in REG: continue
    lr = float(REG[b]["letrun_struct"]); wk = fnum((MB.get(b) or {}).get("weekly_slope"))
    rows.append({"b": b, "dt": t["dt"], "net": lr - COST, "letrun": lr, "mfe": float(REG[b]["mfe_struct"]),
                 "rm_conv": int(t["rm_conv"]), "rm_bear": int(t["rm_bear"]), "rm_blr": int(t["rm_blr"]),
                 "regime": t["regime"], "wk": wk, "wk_bull": 1 if (wk is not None and wk > 0) else 0})
R = {r["b"]: r for r in rows}
def stats(rs):
    n = len(rs)
    if not n: return dict(n=0, sumR=0, maxDD=0, streak=0)
    cum = peak = mdd = ls = best = 0
    for r in sorted(rs, key=lambda x: x["b"]):
        cum += r["net"]; peak = max(peak, cum); mdd = max(mdd, peak - cum)
        ls = 0 if r["net"] > 0 else ls + 1; best = max(best, ls)
    return dict(n=n, sumR=round(sum(r["net"] for r in rs), 1), maxDD=round(mdd, 1), streak=best)
RUN = lambda r: r["letrun"] >= 5.0

# (1) discards do conv≤1 + os POSITIVOS
conv = [r for r in rows if r["rm_conv"] == 1]
print(f"conv≤1 = {len(conv)} cortes. POSITIVOS descartados (letrun>0):")
for r in sorted([x for x in conv if x["letrun"] > 0], key=lambda x: -x["letrun"]):
    print(f"  #{r['b']} {r['dt']} regime={r['regime']:>10} wk_slope={r['wk']} letrun={r['letrun']:+.2f}")
print("  (negativos cortados corretamente:", sum(1 for r in conv if r["letrun"] <= 0), ")")

base = stats(rows); nrun = sum(1 for r in rows if RUN(r))
print(f"\nBASELINE 245: sumR={base['sumR']:+} maxDD={base['maxDD']} streak={base['streak']} runners={nrun}")

# (2) refinamentos: cut só se NÃO bull-forte
REFINES = {
    "R0 conv≤1 (puro)": lambda r: r["rm_conv"] == 1,
    "R1 conv≤1 & regime!=BULL": lambda r: r["rm_conv"] == 1 and r["regime"] != "BULL",
    "R2 conv≤1 & NOT wk_bull": lambda r: r["rm_conv"] == 1 and r["wk_bull"] == 0,
    "R3 conv≤1 & regime==BEAR": lambda r: r["rm_conv"] == 1 and r["regime"] == "BEAR",
}
print("\n=== refinamentos do conv (cut-rule) — re-medidos na régua oficial ===")
print(f"{'rule':>26} | {'n_cut':>5} | {'+resgatados':>11} | {'−readmit':>9} | {'run_cut':>7} | {'base após sumR/maxDD/streak':>27}")
for name, f in REFINES.items():
    cut = [r for r in rows if f(r)]; kept = [r for r in rows if not f(r)]
    # vs R0: o que R0 cortava e este NÃO corta = preservados
    r0 = set(r["b"] for r in rows if r["rm_conv"] == 1); now = set(r["b"] for r in cut)
    preserved = r0 - now
    pos_resc = sum(1 for b in preserved if R[b]["letrun"] > 0); neg_read = sum(1 for b in preserved if R[b]["letrun"] <= 0)
    rc = sum(1 for r in cut if RUN(r)); k = stats(kept)
    print(f"{name:>26} | {len(cut):>5} | {pos_resc:>11} | {neg_read:>9} | {rc:>7} | {k['sumR']:>+8}/{k['maxDD']}/{k['streak']}")

# (3) o melhor refinamento ∪ bear_leg_refined
print("\n=== combinado (refinamento ∪ bear_leg_refined) na régua oficial ===")
for name, f in REFINES.items():
    union = lambda r, f=f: f(r) or r["rm_blr"] == 1
    kept = [r for r in rows if not union(r)]; cut = [r for r in rows if union(r)]
    rc = sum(1 for r in cut if RUN(r)); k = stats(kept)
    print(f"  {name:>26} ∪ blr → sumR={k['sumR']:+} maxDD={k['maxDD']} streak={k['streak']} runners_cut={rc} (n_cut={len(cut)})")
print("\nCalibracao 276 (canon). Régua oficial SL_CONTEXT+let-run. Risk-shaping, não alpha.")
