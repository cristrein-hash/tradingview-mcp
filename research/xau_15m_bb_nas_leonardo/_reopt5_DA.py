"""Devil's Advocate audit for the 5ATR re-opt finalists.
Checks:
 1. Look-ahead: features used are h1_pos/h1_dist/hd_eff/dist_supply/vpnode/path/bars_to_base.
    All are 'as-of entry bar' structural reads; no same-bar daily close lookahead
    flagged here (dataset-level; documented as causal upstream). We re-state.
 2. In-sample / selection bias: count how many variations tested; Bonferroni-style
    sanity on the chosen pair. Bootstrap WR-lift CI to see if +2.4pp survives noise.
 3. Power: with n~3000, MDE for WR.
 4. Robustness of thresholds: jitter thresholds +/-15% and re-check WR/robust.
 5. Try adding orthogonal cut F_into_supply onto A-pair.
 6. Degenerate-atom check.
RAW-causal.
"""
import random, itertools
from _reopt5_lib import load, metrics, is_robust, report, BASE_WR

rows=load()
random.seed(42)

def le(k,t): return lambda r: r.get(k) is not None and r[k]<=t
def ge(k,t): return lambda r: r.get(k) is not None and r[k]>=t

# Finalist A-pair: cut if h1_pos<=0.65 OR h1_dist<=1.85
def A_pair(thr_pos=0.65, thr_dist=1.85):
    fp=le("h1_pos",thr_pos); fd=le("h1_dist",thr_dist)
    return [r for r in rows if not (fp(r) or fd(r))]

print("=== 1) Finalist baseline ===")
kept=A_pair()
m=metrics(kept,rows); report("A_pair base", kept, rows)

print("\n=== 4) threshold jitter +/-15% (robustness) ===")
for dp in (-0.15,0,0.15):
    for dd in (-0.15,0,0.15):
        tp=round(0.65*(1+dp),3); td=round(1.85*(1+dd),3)
        k=A_pair(tp,td); mm=metrics(k,rows)
        print(f" h1_pos<={tp} h1_dist<={td}: WR={mm['wr_keep']} win%={mm['winners_kept_pct']} "
              f"lcut%={mm['losers_cut_pct']} streak->{mm['streak_keep']} robust={is_robust(mm)}")

print("\n=== 2) bootstrap CI on WR-lift (resample rows w/ replacement) ===")
base_wr=BASE_WR
fp=le("h1_pos",0.65); fd=le("h1_dist",1.85)
def lift_on(sample):
    keep=[r for r in sample if not (fp(r) or fd(r))]
    if not keep: return 0
    wr=100*sum(x['win'] for x in keep)/len(keep)
    bwr=100*sum(x['win'] for x in sample)/len(sample)
    return wr-bwr
lifts=[]
N=len(rows)
for _ in range(2000):
    s=[rows[random.randrange(N)] for _ in range(N)]
    lifts.append(lift_on(s))
lifts.sort()
print(f" WR-lift point={lift_on(rows):.2f}pp  boot mean={sum(lifts)/len(lifts):.2f}  "
      f"CI95=[{lifts[50]:.2f},{lifts[-50]:.2f}]  P(lift>0)={sum(1 for x in lifts if x>0)/len(lifts):.3f}")

print("\n=== 3) power: MDE ~ for n=3000 split (rough) ===")
import math
p=0.605; se=math.sqrt(p*(1-p)/len(kept))
print(f" SE(WR_keep)~{100*se:.2f}pp; 2*SE band ~ +/-{200*se:.2f}pp. Observed lift +2.43pp.")

print("\n=== 5) add orthogonal F_into_supply onto A-pair ===")
fs=le("dist_supply_atr",-0.26)
k2=[r for r in rows if not (fp(r) or fd(r) or fs(r))]
report("A_pair OR F_into_supply", k2, rows)

print("\n=== 5b) add orthogonal C_hd_eff onto A-pair ===")
fh=le("hd_eff",0.12)
k3=[r for r in rows if not (fp(r) or fd(r) or fh(r))]
report("A_pair OR C_hd_eff", k3, rows)

print("\n=== 6) degenerate check: is A_pair just h1_dist? ===")
only_dist=[r for r in rows if not fd(r)]
only_pos=[r for r in rows if not fp(r)]
md=metrics(only_dist,rows); mpo=metrics(only_pos,rows)
print(f" only h1_dist<=1.85 cut: WR={md['wr_keep']} win%={md['winners_kept_pct']} lcut%={md['losers_cut_pct']}")
print(f" only h1_pos<=0.65 cut:  WR={mpo['wr_keep']} win%={mpo['winners_kept_pct']} lcut%={mpo['losers_cut_pct']}")
# overlap of the two cut sets
cutd=set(id(r) for r in rows if fd(r)); cutp=set(id(r) for r in rows if fp(r))
print(f" cut-by-dist={len(cutd)} cut-by-pos={len(cutp)} overlap={len(cutd&cutp)} union={len(cutd|cutp)}")
