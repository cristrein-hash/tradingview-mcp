#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of the conv<=1 ELIMINATION candidate.
Read-only. Operates on results/l2_bpt_elimination_sweep.json (already computed, causal).
Recomputes removed-set composition, jackknife on the +13R claim, threshold/cutoff perturbation
(conv<=0 vs conv<=1 vs conv<=2), streak fragility, and the BEAR-confound (is conv<=1 just regime BEAR
in disguise?). NOT a new backtest — adversarial re-aggregation of an existing result. Verified 2026-06-24."""
import json

rows = json.load(open("results/l2_bpt_elimination_sweep.json"))
rows.sort(key=lambda r: r["dt"])

def stats(rs):
    n = len(rs); w = sum(1 for r in rs if r["realR"] > 0)
    sumR = sum(r["realR"] for r in rs)
    ls = mls = 0
    for r in rs:
        if r["realR"] < 0: ls += 1; mls = max(mls, ls)
        else: ls = 0
    return n, w, (w / n if n else 0.0), sumR, mls

bn, bw, bwr, bsum, bmls = stats(rows)
nrun = sum(1 for r in rows if r["mfe"] >= 10)
print(f"BASELINE n={bn} W={bw} WR={bwr:.1%} sumR={bsum:+.1f} streak={bmls} runners={nrun}\n")

def rule_conv(thr): return lambda r: r["conv"] <= thr

# ---- conv<=1 removed-set composition ----
rem = [r for r in rows if r["conv"] <= 1]
kept = [r for r in rows if not r["conv"] <= 1]
remwin = [r for r in rem if r["realR"] > 0]
remloss = [r for r in rem if r["realR"] < 0]
remrun = [r for r in rem if r["mfe"] >= 10]
print(f"conv<=1 removed n={len(rem)}  winners={len(remwin)} losers={len(remloss)} runners={len(remrun)}")
print(f"  removed sumR={sum(r['realR'] for r in rem):+.2f} (kept gain={-sum(r['realR'] for r in rem):+.2f})")
print(f"  removed BEAR={sum(1 for r in rem if r['is_bear']==1)} of {len(rem)}  conv0={sum(1 for r in rem if r['conv']==0)} conv1={sum(1 for r in rem if r['conv']==1)}")
print(f"  KEPT: {stats(kept)}\n")

# ---- BEAR confound: does conv<=1 add anything beyond 'regime BEAR'? ----
bear = [r for r in rows if r["is_bear"] == 1]
nonbear_lowconv = [r for r in rem if r["is_bear"] == 0]
print(f"CONFOUND: BEAR set n={len(bear)} sumR={sum(r['realR'] for r in bear):+.2f} losers={sum(1 for r in bear if r['realR']<0)}")
print(f"  conv<=1 AND non-BEAR n={len(nonbear_lowconv)} sumR={sum(r['realR'] for r in nonbear_lowconv):+.2f} "
      f"losers={sum(1 for r in nonbear_lowconv if r['realR']<0)} winners={sum(1 for r in nonbear_lowconv if r['realR']>0)}")
print(f"  -> isolated lift of conv (the non-BEAR part) is the real test of voices 1/3/4\n")

# ---- threshold perturbation ----
print("THRESHOLD SWEEP (kept stats):")
for thr in (-1, 0, 1, 2):
    k = [r for r in rows if not (r["conv"] <= thr)]
    rmv = [r for r in rows if r["conv"] <= thr]
    rr = sum(1 for r in rmv if r["mfe"] >= 10)
    n, w, wr, s, m = stats(k)
    print(f"  conv<={thr}: removed={len(rmv)} runRem={rr} -> n={n} WR={wr:.1%} sumR={s:+.1f} streak={m}")
print()

# ---- jackknife the +13R: drop each removed loser one at a time, recompute kept sumR ----
base_kept_sum = stats(kept)[3]
print(f"JACKKNIFE on +13R claim (kept sumR baseline-of-rule={base_kept_sum:+.2f}):")
# If we FAIL to remove the single worst loser (it stays in kept), how much of the +13R survives?
worst = sorted(rem, key=lambda r: r["realR"])  # most negative first
for r in worst[:3]:
    keptp = kept + [r]
    print(f"  if {r['dt']} (realR={r['realR']:+.2f}) NOT removed: kept sumR={stats(keptp)[3]:+.2f}")
# remove the BEST removed winner from the 'gain' (i.e., we wrongly cut a winner) - already counted
print(f"  6 winners wrongly cut total realR=+{sum(r['realR'] for r in remwin):.2f} "
      f"(these are LOST gains, the rule is NET +13 only because 17 losers outweigh them)\n")

# ---- streak fragility ----
print("STREAK: baseline=7, conv<=1 kept=6. Locate the streak-7 run in baseline and check if the breaking trade is one removed by the rule.")
ls = 0; run = []; runs = []
for r in rows:
    if r["realR"] < 0:
        ls += 1; run.append(r)
    else:
        if ls >= 6: runs.append(list(run))
        ls = 0; run = []
if ls >= 6: runs.append(list(run))
for rn in runs:
    dts = [(x["dt"], round(x["realR"], 2), x["conv"], x["is_bear"]) for x in rn]
    removed_in = sum(1 for x in rn if x["conv"] <= 1)
    print(f"  losing run len={len(rn)} removed-by-rule={removed_in}: {dts}")
