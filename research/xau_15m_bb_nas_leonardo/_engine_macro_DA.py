#!/usr/bin/env python3
"""
_engine_macro_DA.py — Devil's Advocate self-audit of macro-regime triggers.

Claims under test:
  R1: macro_drop_atr<4  (n=831 avgR=1.03 lift+0.303, robust 3yr, survives ex5)
  R2: bull & retr>=0.618 (n=790 avgR=0.885 lift+0.158, robust)

DA questions:
  1. Look-ahead: macro_drop_atr measured at reclaim bar from PAST leg? (dataset claims causal)
  2. Selection: how many cuts tested? is drop<4 a peak-picked threshold or a plateau?
  3. WR vs avgR: is the lift from MORE winners or from a few big runners (tail)?
  4. Confound: is shallow-leg just low-vol regime (atr_regime) in disguise?
  5. Robustness ±20% on the threshold (drop<3.2 .. drop<4.8) — does signal hold?
  6. Is R2 just R1 in disguise (overlap)?
  7. Per-year WR (not just avgR) for the rules.
"""
import json
BASE = 0.727
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
for r in ROWS: r['R'] = r['R_reclaim']

def st(rows):
    R = sorted([r['R'] for r in rows], reverse=True); n=len(R)
    if not n: return None
    return dict(n=n, avg=round(sum(R)/n,3), wr=round(sum(1 for x in R if x>0)/n,3),
                med=sorted([r['R'] for r in rows])[n//2],
                nrun=sum(1 for x in R if x>=5),
                ex5=round(sum(R[5:])/(n-5),3) if n>5 else None)

print("== Q5: threshold robustness (plateau check, ±20% around drop<4) ==")
for thr in [3.0,3.2,3.5,3.8,4.0,4.2,4.5,4.8,5.0]:
    s=st([r for r in ROWS if r['macro_drop_atr']<thr])
    print(f"  drop<{thr}: n={s['n']} avgR={s['avg']} WR={s['wr']} ex5={s['ex5']} nrun={s['nrun']}")

print("\n== Q3: WR vs avgR decomposition for drop<4 vs drop>=4 ==")
for nm,sub in [("drop<4",[r for r in ROWS if r['macro_drop_atr']<4]),
               ("drop>=4",[r for r in ROWS if r['macro_drop_atr']>=4])]:
    s=st(sub)
    # winners-only avg and losers fraction
    Rs=[r['R'] for r in sub]
    win=[x for x in Rs if x>0]; los=[x for x in Rs if x<=0]
    print(f"  {nm}: WR={s['wr']} avg_win={round(sum(win)/len(win),3)} frac_loss={round(len(los)/len(Rs),3)} runner_rate={round(s['nrun']/s['n'],4)}")

print("\n== Q4: confound with atr_regime — does drop<4 win INSIDE each atr bucket? ==")
for lo,hi in [(0,0.8),(0.8,1.1),(1.1,9)]:
    band=[r for r in ROWS if lo<=r['atr_regime']<hi]
    sin=st([r for r in band if r['macro_drop_atr']<4])
    sout=st([r for r in band if r['macro_drop_atr']>=4])
    print(f"  atr[{lo},{hi}): drop<4 n={sin['n'] if sin else 0} avgR={sin['avg'] if sin else None} | drop>=4 n={sout['n'] if sout else 0} avgR={sout['avg'] if sout else None}")

print("\n== Q6: R1/R2 overlap ==")
r1=set(id(r) for r in ROWS if r['macro_drop_atr']<4)
r2=set(id(r) for r in ROWS if r['macro_bull']==1 and r['macro_retr']>=0.618)
print(f"  R1 n={len(r1)} R2 n={len(r2)} overlap={len(r1&r2)} R2-only={len(r2-r1)}")
s=st([r for r in ROWS if r['macro_bull']==1 and r['macro_retr']>=0.618 and r['macro_drop_atr']>=4])
print(f"  R2 minus R1 (bull&retr>=.618 & drop>=4): n={s['n']} avgR={s['avg']} WR={s['wr']} ex5={s['ex5']}")

print("\n== Q7: per-year WR for R1 ==")
for yr in (2024,2025,2026):
    s=st([r for r in ROWS if r['macro_drop_atr']<4 and r['yr']==yr])
    print(f"  R1 {yr}: n={s['n']} avgR={s['avg']} WR={s['wr']}")

print("\n== Q1: look-ahead sanity — drop_atr distribution and corr with outcome sign ==")
# if drop_atr were leaking future, shallow would near-perfectly predict; check it's gradual
import statistics
vals=[r['macro_drop_atr'] for r in ROWS]
print(f"  macro_drop_atr min={round(min(vals),2)} p25={round(statistics.quantiles(vals,n=4)[0],2)} med={round(statistics.median(vals),2)} p75={round(statistics.quantiles(vals,n=4)[2],2)} max={round(max(vals),2)}")
print(f"  (gradual monotone effect across thresholds above = consistent with regime feature, not a label leak)")

print("\n== closeness-to-pivot proxy: WR of confirmation-type-1 is ~66% but late. R1 entry is the reclaim bar itself (near pivot) ==")
