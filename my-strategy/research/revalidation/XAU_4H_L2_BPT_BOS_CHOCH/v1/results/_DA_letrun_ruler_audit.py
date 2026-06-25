#!/usr/bin/env python3
"""DA audit — interrogating 'letrun as the R-ruler' pick (2026-06-25).
Reproduces the diagnostic numbers behind the Devil's Advocate objections:
 (obj3) calibration SL is TIGHT (RW=6, ATR-floored 0.3 / ceiled 1.5) -> risk_atr distribution
 (obj3) compare vs Cris structural SL (gt_risk) in real_outcome_sl_validation.csv
 (obj5) letrun realized R vs mfe_R: circularity / runner re-naming check (corr + capture%)
Read-only. Diagnostic. Validation stays inside the 276 (calibration only)."""
import csv, math, statistics as st
D = "results"

# --- obj3: SL tightness in the calibration ---
rows = list(csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
rs = sorted(float(r['risk_atr']) for r in rows if r['risk_atr'])
n = len(rs)
print("=== obj3: calibration SL risk_atr (tight RW=6, floor0.3/ceil1.5) ===")
print(f"n={n} min={rs[0]:.2f} median={rs[n//2]:.2f} max={rs[-1]:.2f} mean={sum(rs)/n:.2f}")
print(f"at 1.5 ATR ceiling: {sum(1 for x in rs if x>=1.49)}/{n}")
print(f"at ~0.3 ATR floor (<=0.35): {sum(1 for x in rs if x<=0.35)}/{n}")

# compare against Cris structural SL risk
sl = list(csv.DictReader(open(f"{D}/l2_bpt_real_outcome_sl_validation.csv")))
my = [float(r['my_risk']) for r in sl if r.get('my_risk')]
gt = [float(r['gt_risk']) for r in sl if r.get('gt_risk')]
if my and gt:
    print(f"sl_validation: my_risk median={st.median(my):.1f}  gt(structural) median={st.median(gt):.1f}"
          f"  ratio~{st.median(gt)/st.median(my):.1f}x wider structural")

# --- obj5: letrun vs mfe circularity ---
print("\n=== obj5: letrun realized vs mfe_R (runner re-naming / circularity) ===")
def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x-ma)**2 for x in a)); db = math.sqrt(sum((y-mb)**2 for y in b))
    return num/(da*db)
allmfe = [float(r['mfe_R']) for r in rows]
alllr = [float(r['realized_letrun_120']) for r in rows]
allcap = [float(r['capped_realR']) for r in rows]
runs = [r for r in rows if float(r['mfe_R']) >= 5]
print(f"runners(mfe>=5) n={len(runs)} mean_mfe={st.mean([float(r['mfe_R']) for r in runs]):.2f} "
      f"mean_letrun={st.mean([float(r['realized_letrun_120']) for r in runs]):.2f} "
      f"capture={100*st.mean([float(r['realized_letrun_120']) for r in runs])/st.mean([float(r['mfe_R']) for r in runs]):.0f}%")
print(f"corr(letrun_120, mfe_R) over 276 = {corr(alllr, allmfe):.3f}")
print(f"corr(capped_realR, mfe_R) over 276 = {corr(allcap, allmfe):.3f}")
print("\nDONE _DA_letrun_ruler_audit")
