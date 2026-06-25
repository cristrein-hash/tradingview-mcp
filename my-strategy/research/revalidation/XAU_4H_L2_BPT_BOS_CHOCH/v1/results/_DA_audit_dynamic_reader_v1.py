#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of l2_bpt_dynamic_reader_v1 (read-only, no file modification).
SANITY_PROBE: CI + sub-state separation + null reconstruction on the saved reading CSV.
verified-at: 2026-06-22. Reproducible artifact (not part of the reader under review)."""
import csv, math, random
from collections import Counter

ROWS = list(csv.DictReader(open("results/l2_bpt_dynamic_reader_v1_reading.csv")))
def f(v):
    try: return float(v)
    except: return None
N = len(ROWS)
runner = lambda r: f(r['mfe_R']) >= 5
loser  = lambda r: f(r['mfe_R']) < 2
nR = sum(runner(r) for r in ROWS); nL = sum(loser(r) for r in ROWS)
base = nR / N

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z*z/n
    c = p + z*z/(2*n); m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return ((c-m)/d, (c+m)/d)

print("="*72); print("DA AUDIT — dynamic reader v1")
print(f"N={N}  base runner_rate={base*100:.2f}% (nR={nR} nL={nL})")
print("why:", dict(Counter(r['why'] for r in ROWS)))
print("new_pol:", dict(Counter(r['new_pol'] for r in ROWS)))

print("\n--- Q5/Q6 per-bucket runner separation ---")
for why in ('LEGITIMATE_BEAR_BUY','REVERSAL_RUNNER','MARKUP_CONTINUATION',
            'BEAR_PULLBACK_TRAP','TOP_TRAP_AVOID','AMBIGUOUS'):
    sub=[r for r in ROWS if r['why']==why]; n=len(sub)
    rr=sum(runner(r) for r in sub); sl=sum(f(r['letrun']) for r in sub)
    lo,hi=wilson(rr,n)
    print(f"  {why:22s} n={n:3d} run={rr:2d} rate={(100*rr/n if n else 0):5.1f}% "
          f"lift={(rr/n/base if n else 0):.2f} Wilson95=[{lo*100:4.1f},{hi*100:4.1f}] sumR={sl:6.1f}")

print("\n--- Q2 NEW_TAKE confidence interval ---")
take=[r for r in ROWS if r['new_pol']=='TAKE']
k=sum(runner(r) for r in take); n=len(take)
lo,hi=wilson(k,n)
print(f"NEW_TAKE n={n} runners={k} rate={100*k/n:.1f}% Wilson95=[{lo*100:.1f},{hi*100:.1f}]  base={base*100:.1f}%")
print(f"  -> base {base*100:.1f}% is {'INSIDE' if lo<=base<=hi else 'OUTSIDE'} the CI")

# Fisher-ish: hypergeometric tail p(>= k runners in n draws from N with nR runners)
def hyper_tail(k,n,nR,N):
    from math import comb
    tot=comb(N,n); p=0.0
    for x in range(k, min(n,nR)+1):
        p += comb(nR,x)*comb(N-nR,n-x)/tot
    return p
print(f"  hypergeometric p(>= {k} runners in {n} draws) = {hyper_tail(k,n,nR,N):.3f}")

print("\n--- Q3 mislabel correction vs shuffle ---")
sw=sum(int(r['skip_winner_recovered']) for r in ROWS)
lc=sum(int(r['loser_take_cut']) for r in ROWS)
# universe of skip-winners and loser-takes per engine policy
eng_skip=lambda r: r['eng_pol'] in ('SKIP','REVIEW','REVIEW_RISK')
eng_take=lambda r: r['eng_pol']=='TAKE'
tot_skip_win=sum(1 for r in ROWS if runner(r) and eng_skip(r))
tot_loser_take=sum(1 for r in ROWS if loser(r) and eng_take(r))
print(f"skip-winners recovered: {sw} of {tot_skip_win} ({100*sw/tot_skip_win:.0f}%)")
print(f"loser-takes cut:        {lc} of {tot_loser_take} ({100*lc/tot_loser_take:.0f}%)")
def sumlet(pred): return round(sum(f(r['letrun']) for r in ROWS if pred(r)),1)
nt=sumlet(lambda r:r['new_pol']=='TAKE'); et=sumlet(eng_take)
print(f"sumR_letrun NEW_TAKE={nt}  ENG_TAKE={et}  delta={nt-et:+.1f}R "
      f"(NEW n={n}, ENG n={sum(1 for r in ROWS if eng_take(r))})")

print("\n--- Q6 TAKE composition (single sub-reader dominance?) ---")
takewhy=Counter(r['why'] for r in take)
print("TAKE why:", dict(takewhy))
br=takewhy.get('LEGITIMATE_BEAR_BUY',0)
print(f"  sub-reader-7 share of TAKE = {br}/{n} = {100*br/n:.0f}%")

print("\n--- Q2 null reconstruction (does sign survive vs random same-size draw) ---")
rng=random.Random(3); mfev=[f(r['mfe_R']) for r in ROWS]; obs=k/n; ge=0; NP=20000
for _ in range(NP):
    idx=list(range(N)); rng.shuffle(idx); s=idx[:n]
    if sum(1 for j in s if mfev[j]>=5)/n >= obs: ge+=1
print(f"p(rand runner_rate >= {obs*100:.1f}%) = {ge/NP:.3f}")
print("="*72)
