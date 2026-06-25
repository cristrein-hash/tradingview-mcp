#!/usr/bin/env python3
"""DA robustness audit for the conv<=1 / bear_leg_refined skip claim on the OFFICIAL let-run regua.

Joins:
  - results/l2_bpt_conv_bear_overlap_table.csv  -> which trades each group removes (rm_conv/rm_bear/rm_blr), by bar_idx 'b'
  - results/l2_bpt_regua_structural.csv         -> letrun_struct per bar_idx (official let-run exit, pre-cost)

Cost convention: official regua applies 0.35R cost. The regua csv letrun_struct is PRE-cost; baseline
sumR reported (+52.5) is POST-cost on 245. We reconcile both and run:
  J) jackknife: drop single most-positive removed loser from each skip group
  N) near-runner sensitivity: runner threshold letrun in {3,5,8}; recount runners_cut
  O) overlap/additivity of conv<=1 vs bear_leg_refined unions
  P) per-period P1(2020-22)/P2(2023-26) decomposition of sumR delta + maxDD
  R) random-loser control: avg over random sets of ~23 negative-letrun trades, compare sumR gain vs conv<=1
  5) #5826 leave-one-out: does conv<=1 still beat BEAR without that single trade
Calibration on 276 (canon): labels calibrate; nothing becomes a gate/validation.
Verified 2026-06-25.
"""
import csv, statistics, random
from pathlib import Path

V1 = Path(__file__).resolve().parents[1]
ov = {int(r['b']): r for r in csv.DictReader(open(V1/"results/l2_bpt_conv_bear_overlap_table.csv"))}
reg = {int(r['bar_idx']): r for r in csv.DictReader(open(V1/"results/l2_bpt_regua_structural.csv"))}

COST = 0.35
# Traded set on official regua = bars present in regua csv (245 after TOP_EXHAUSTION no_trade)
traded = sorted(reg.keys())
def letrun(b):  # pre-cost let-run R
    return float(reg[b]['letrun_struct'])
def lr_net(b):
    return letrun(b) - COST

# date -> period
def period(b):
    dt = ov[b]['dt'] if b in ov else ''
    y = int(dt[:4]) if dt[:4].isdigit() else 0
    return 'P1' if y <= 2022 else 'P2'

def curve_stats(bars):
    bs = [b for b in bars if b in reg]
    order = sorted(bs, key=lambda b: ov[b]['dt'] if b in ov else str(b))
    cum=peak=mdd=ls=best=0
    for b in order:
        r = lr_net(b); cum += r; peak=max(peak,cum); mdd=max(mdd,peak-cum)
        ls = 0 if r>0 else ls+1; best=max(best,ls)
    n=len(bs)
    return dict(n=n, sumR=round(sum(lr_net(b) for b in bs),1),
                WR=round(100*sum(1 for b in bs if lr_net(b)>0)/n,1) if n else 0,
                maxDD=round(mdd,1), streak=best)

# membership sets from flags
S = {
 'conv':  [b for b in traded if b in ov and ov[b]['rm_conv']=='1'],
 'bear':  [b for b in traded if b in ov and ov[b]['rm_bear']=='1'],
 'blr':   [b for b in traded if b in ov and ov[b]['rm_blr']=='1'],
}
base = curve_stats(traded)
print(f"== BASELINE (let-run, cost {COST}) ==")
print(f"  n={base['n']} sumR={base['sumR']} WR={base['WR']} maxDD={base['maxDD']} streak={base['streak']}")
print(f"  runners(letrun>=5) baseline = {sum(1 for b in traded if letrun(b)>=5)}\n")

def keep(removed):
    rs=set(removed); return [b for b in traded if b not in rs]

print("== group sizes & removed-trade letrun profile ==")
for k,v in S.items():
    lrs=sorted((round(letrun(b),2) for b in v))
    print(f"  {k}: n={len(v)} removed_letrun={lrs}")
print()

# union conv<=1 U bear_leg_refined
union_cb = sorted(set(S['conv'])|set(S['blr']))
inter_cb = sorted(set(S['conv'])&set(S['blr']))
print(f"== OVERLAP conv<=1 vs blr: |conv|={len(S['conv'])} |blr|={len(S['blr'])} |union|={len(union_cb)} |inter|={len(inter_cb)} inter={inter_cb}\n")

def report(name, removed):
    removed=sorted(set(removed))
    after=curve_stats(keep(removed))
    rc0=sum(1 for b in traded if letrun(b)>=5)
    rc_after=sum(1 for b in keep(removed) if letrun(b)>=5)
    removed_sum=round(sum(lr_net(b) for b in removed),1)
    runners_cut={t: sum(1 for b in removed if letrun(b)>=t) for t in (3,5,8)}
    near=[round(letrun(b),2) for b in removed if 3<=letrun(b)<5]
    print(f"-- SKIP {name} (n={len(removed)}) --")
    print(f"   after: sumR={after['sumR']} (Δ{after['sumR']-base['sumR']:+.1f}) WR={after['WR']} maxDD={after['maxDD']} streak={after['streak']}")
    print(f"   removed_sumR(net)={removed_sum}  runners_cut by thr{{3,5,8}}={runners_cut}  near-runners[3,5)={near}")
    # jackknife: drop single most-positive removed loser
    if removed:
        mp=max(removed, key=lambda b: lr_net(b))
        jk=report_quiet(removed, drop=mp)
        print(f"   jackknife(drop most-+ removed b={mp} letrun={letrun(mp):.2f}): sumR after = {jk}")
    return after

def report_quiet(removed, drop):
    removed=[b for b in removed if b!=drop]
    return curve_stats(keep(removed))['sumR']

A=report("conv<=1", S['conv'])
B=report("BEAR", S['bear'])
U=report("conv<=1 U blr", union_cb)
E=report("blr (bear_leg_refined)", S['blr'])
print()

# per-period decomposition for the union
print("== PER-PERIOD (union conv<=1 U blr) ==")
for P in ('P1','P2'):
    bp=[b for b in traded if period(b)==P]
    rem=[b for b in union_cb if period(b)==P]
    b_before=curve_stats(bp); b_after=curve_stats([b for b in bp if b not in set(union_cb)])
    print(f"  {P}: before sumR={b_before['sumR']} maxDD={b_before['maxDD']} | after sumR={b_after['sumR']} maxDD={b_after['maxDD']} | removed_in_period={len(rem)}")
print()

# #5826 leave-one-out in conv-vs-bear
TARGET=5826
print(f"== #{TARGET} leave-one-out (conv beats BEAR?) ==")
present = TARGET in reg
print(f"  {TARGET} in regua={present}  letrun={letrun(TARGET) if present else 'NA'}  rm_conv={ov.get(TARGET,{}).get('rm_conv')} rm_bear={ov.get(TARGET,{}).get('rm_bear')}")
# conv preserves 5826 (rm_conv=0), BEAR removes it (rm_bear=1) per group D. Compare keep-sets excluding 5826 entirely.
conv_keep=set(keep(S['conv'])); bear_keep=set(keep(S['bear']))
for tag,ks in (("conv",conv_keep),("BEAR",bear_keep)):
    full=curve_stats(sorted(ks))
    noT=curve_stats(sorted(ks-{TARGET}))
    print(f"  {tag}: sumR_full={full['sumR']}  sumR_no{TARGET}={noT['sumR']}")
print()

# random-loser control
print("== RANDOM-LOSER CONTROL vs conv<=1 ==")
negs=[b for b in traded if letrun(b)<0]
k=len(S['conv'])
random.seed(7)
gains=[]; runners_hit=[]
for _ in range(2000):
    samp=random.sample(negs,k)
    gains.append(curve_stats(keep(samp))['sumR']-base['sumR'])
    runners_hit.append(sum(1 for b in samp if letrun(b)>=5))
gains.sort()
conv_gain=A['sumR']-base['sumR']
pct=100*sum(1 for g in gains if g>=conv_gain)/len(gains)
print(f"  random {k}-loser filters: gain median={statistics.median(gains):+.1f} p90={gains[int(0.9*len(gains))]:+.1f} max={gains[-1]:+.1f}")
print(f"  conv<=1 gain={conv_gain:+.1f} -> {pct:.1f}% of random loser-filters match/exceed it")
print(f"  random runners_cut>=1 happens in {100*sum(1 for r in runners_hit if r>=1)/len(runners_hit):.0f}% of draws (conv cuts 0)")
print("\nCalibration 276 (canon). Nothing here becomes a gate/validation.")
PY = None
PY
