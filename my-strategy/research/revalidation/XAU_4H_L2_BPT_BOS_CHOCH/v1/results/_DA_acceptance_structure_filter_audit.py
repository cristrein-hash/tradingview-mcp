#!/usr/bin/env python3
"""DA AUDIT — candidate filter "skip f3_acceptance_state in {HOLDING_SUPPORT,BROKE_SUPPORT} AND f4_structure_state==STRUCTURE_UP"
over the MACRO_RANGE-regime L2/BPT subset (user's n=70). Reproduces the reported numbers + runs the
multiple-testing and per-year robustness checks. Causality of f3/f4 is verified by CODE READING of the
generator l2_bpt_dspa_path_features.py (window [i-LB,i], pivots confirmed j+3<=i) — see report, not this script.
Inputs (all in-sample on 276): path features + outcomes + macro_reader_leg (=RANGE membership).
Reproducible/committed. DIAGNOSTIC ONLY (no OOS/cross-asset)."""
import csv, itertools, random
from collections import Counter, defaultdict

D = "."  # run from results/
feat = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
outc = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
leg  = {int(r['bar_idx']): r['macro_reader_leg'] for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv"))}
# let-run / uncapped outcome (user said "let-run, R post-cost", DD-17.8 => uncapped ruler)
unc  = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}

import os
MODE = os.environ.get("RULER","letrun")  # "capped" or "letrun"
def R(b):
    if MODE=="capped": return float(outc[b]['realR'])
    v = unc[b].get('realized_letrun_120') or unc[b].get('realized_letrun_60')
    return float(v)
def yr(b): return outc[b]['datetime'][:4]

# ---- RANGE-regime universe (user's n=70) ----
RANGE = [b for b in outc if leg.get(b) == 'MACRO_RANGE' and b in feat]

def stats(bars):
    if not bars: return dict(N=0, WR=0, sumR=0, avgR=0, DD=0)
    rs = [R(b) for b in bars]
    wins = sum(1 for x in rs if x > 0)
    # max drawdown on cumulative R (order by bar_idx = chronological)
    cum = 0; peak = 0; dd = 0
    for b in sorted(bars):
        cum += R(b); peak = max(peak, cum); dd = min(dd, cum - peak)
    return dict(N=len(bars), WR=round(100*wins/len(bars),1), sumR=round(sum(rs),1),
                avgR=round(sum(rs)/len(rs),3), DD=round(dd,1))

def keep_combined(b):
    f3 = feat[b]['f3_acceptance_state']; f4 = feat[b]['f4_structure_state']
    skip = (f3 in ('HOLDING_SUPPORT','BROKE_SUPPORT')) and (f4 == 'STRUCTURE_UP')
    return not skip
def keep_f3(b):
    return feat[b]['f3_acceptance_state'] not in ('HOLDING_SUPPORT','BROKE_SUPPORT')
def keep_f4(b):
    return feat[b]['f4_structure_state'] != 'STRUCTURE_UP'

print("="*80)
print("POINT 0 — reproduce reported numbers on RANGE (MACRO_RANGE) subset")
print(f"  BASE                :", stats(RANGE))
print(f"  skip f3 HOLD/BROKE  :", stats([b for b in RANGE if keep_f3(b)]))
print(f"  skip f4 STRUCTURE_UP:", stats([b for b in RANGE if keep_f4(b)]))
kept = [b for b in RANGE if keep_combined(b)]
print(f"  COMBINED (kept)     :", stats(kept))
print(f"  cut trades          : {len(RANGE)-len(kept)}  (of {len(RANGE)})")

# ---- POINT 3 — per-year ----
print("\n" + "="*80)
print("POINT 3 — per-year: BASE vs COMBINED-filter (RANGE subset)")
years = sorted(set(yr(b) for b in RANGE))
print(f"  {'year':6} {'baseN':>6} {'baseR':>8} {'baseWR':>7} | {'keptN':>6} {'keptR':>8} {'keptWR':>7} {'cut':>4}")
for y in years:
    by = [b for b in RANGE if yr(b)==y]
    ky = [b for b in by if keep_combined(b)]
    sb, sk = stats(by), stats(ky)
    print(f"  {y:6} {sb['N']:>6} {sb['sumR']:>8} {sb['WR']:>7} | {sk['N']:>6} {sk['sumR']:>8} {sk['WR']:>7} {sb['N']-sk['N']:>4}")

# ---- POINT 2 — multiple testing: how many 2-of-K categorical splits beat this? ----
# Enumerate all binary "skip" rules from single categorical features (each level = candidate skip),
# and all 2-feature AND combinations, then rank by resulting sumR and by WR on the kept set.
# This estimates the selection advantage of picking the best 2-of-many after seeing outcomes.
print("\n" + "="*80)
print("POINT 2 — multiple-testing / selection inflation")
cat_cols = ['f1_flush' , 'f1_swept_low_reclaim','f2_flush_state','f3_acceptance_state','f4_structure_state',
            'f4_BOS','f4_CHoCH','f5_range_pos_4h','f5_range_pos_1d','f6_svp_state','f7_regime_traj']
cat_cols = [c for c in cat_cols if c in feat[RANGE[0]]]
# build atomic skip-predicates: (col==level)
preds = []
for c in cat_cols:
    for lv in sorted(set(feat[b][c] for b in RANGE)):
        preds.append((c, lv, lambda b,c=c,lv=lv: feat[b][c]==lv))
# single-level skips + 2-level AND skips
def eval_skip(is_skip):
    kb = [b for b in RANGE if not is_skip(b)]
    if len(kb) < 12: return None  # min sample guard
    return stats(kb), len(kb)
results = []
# singles
for (c,lv,p) in preds:
    e = eval_skip(p)
    if e: results.append((f"{c}=={lv}", e[0]['sumR'], e[0]['WR'], e[1]))
# pairs (AND)
for (c1,l1,p1),(c2,l2,p2) in itertools.combinations(preds,2):
    if c1==c2: continue
    e = eval_skip(lambda b,p1=p1,p2=p2: p1(b) and p2(b))
    if e: results.append((f"{c1}=={l1} & {c2}=={l2}", e[0]['sumR'], e[0]['WR'], e[1]))
n_looks = len(results)
base = stats(RANGE)
our = stats(kept)
by_sumR = sorted(results, key=lambda x:-x[1])
by_wr   = sorted([r for r in results if r[3]>=20], key=lambda x:-x[2])  # WR only meaningful at n>=20
print(f"  effective looks (single+AND skip rules, n_kept>=12): {n_looks}")
print(f"  our COMBINED rule: sumR={our['sumR']} WR={our['WR']} N={our['N']}")
rank_sumR = 1+sum(1 for r in results if r[1] > our['sumR'])
print(f"  our rule rank by sumR: {rank_sumR} of {n_looks}")
print(f"  TOP-8 rules by sumR (many will be as good/better => selection is easy here):")
for name,s,w,n in by_sumR[:8]:
    print(f"     sumR={s:>6} WR={w:>5} N={n:>4}  {name}")
print(f"  TOP-6 by WR (n_kept>=20):")
for name,s,w,n in by_wr[:6]:
    print(f"     WR={w:>5} sumR={s:>6} N={n:>4}  {name}")

# permutation null: shuffle realR across RANGE, re-pick BEST 2-of-K rule, record its sumR gain.
# gives the distribution of "best selected rule" sumR under no real edge.
print("\n  PERMUTATION NULL (shuffle realR, re-pick BEST rule by sumR each draw):")
random.seed(7)
rvals = [R(b) for b in RANGE]
bars_sorted = list(RANGE)
best_null = []
NPERM = 400
for _ in range(NPERM):
    perm = rvals[:]; random.shuffle(perm)
    rmap = dict(zip(bars_sorted, perm))
    def Rp(b): return rmap[b]
    best = -1e9
    for (c,lv,p) in preds:
        kb = [b for b in RANGE if not p(b)]
        if len(kb) < 12: continue
        s = sum(Rp(b) for b in kb)
        if s > best: best = s
    for (c1,l1,p1),(c2,l2,p2) in itertools.combinations(preds,2):
        if c1==c2: continue
        kb = [b for b in RANGE if not (p1(b) and p2(b))]
        if len(kb) < 12: continue
        s = sum(Rp(b) for b in kb)
        if s > best: best = s
    best_null.append(best)
best_null.sort()
import statistics
p95 = best_null[int(0.95*len(best_null))]
p50 = statistics.median(best_null)
ge = sum(1 for x in best_null if x >= our['sumR'])/len(best_null)
print(f"    base sumR (no filter)      = {base['sumR']}")
print(f"    null best-rule sumR median = {round(p50,1)} | p95 = {round(p95,1)}")
print(f"    our observed kept sumR     = {our['sumR']}")
print(f"    P(null best-rule sumR >= our) = {round(ge,3)}   (selection-adjusted p-value)")

# ---- POINT 4 — 2025 chop residual ----
print("\n" + "="*80)
print("POINT 4 — does it solve the chop over-trading? (2025 RANGE)")
for y in ['2024','2025']:
    by = [b for b in RANGE if yr(b)==y]
    ky = [b for b in by if keep_combined(b)]
    losers_kept = [b for b in ky if R(b)<=0]
    print(f"  {y}: base {stats(by)['N']}tr {stats(by)['sumR']}R -> kept {stats(ky)['N']}tr {stats(ky)['sumR']}R  (losers remaining kept={len(losers_kept)})")
print("\nDONE. In-sample on 276 (phase10 boxes + features same universe). No OOS/cross-asset.")
