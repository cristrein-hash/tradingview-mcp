#!/usr/bin/env python3
"""
_reopt5_scan.py — single-feature discrimination scan over 5ATR candidates.

For each numeric feature, find threshold splits and measure WR on each side, to
discover which features carry signal. RAW-causal. PROHIBITED: R,win,cj,low_idx,low_t,yr,block.
This is DISCOVERY (calibration), not a robustness verdict — verdict comes from the
harness evaluate() with per-year + per-block stability gates.
"""
import json, statistics

from _reopt5_harness import ROWS, BASE_WR

PROHIBITED = {'R','win','cj','low_idx','low_t','yr','block'}

# collect numeric feature keys
keys = [k for k in ROWS[0].keys() if k not in PROHIBITED]

def feat_vals(k):
    return [(r[k], r['win']) for r in ROWS if r.get(k) is not None]

def quantile(sorted_xs, q):
    if not sorted_xs: return None
    i = int(q*(len(sorted_xs)-1))
    return sorted_xs[i]

print(f"BASE_WR={BASE_WR:.2f}  scanning {len(keys)} features\n")

results=[]
for k in keys:
    vals = feat_vals(k)
    if not vals: continue
    xs = sorted(v for v,_ in vals)
    distinct = len(set(xs))
    coverage = len(vals)/len(ROWS)
    if distinct < 2:
        continue
    # candidate thresholds at deciles
    cand = sorted(set(quantile(xs,q) for q in [.1,.2,.25,.3,.4,.5,.6,.7,.75,.8,.9]))
    best=None
    for t in cand:
        ge=[w for v,w in vals if v>=t]
        lt=[w for v,w in vals if v<t]
        if len(ge)>=150:
            wr=100*sum(ge)/len(ge)
            if best is None or abs(wr-BASE_WR)>abs(best[1]-BASE_WR):
                best=('>=%g'%t, wr, len(ge))
        if len(lt)>=150:
            wr=100*sum(lt)/len(lt)
            if best is None or abs(wr-BASE_WR)>abs(best[1]-BASE_WR):
                best=('<%g'%t, wr, len(lt))
    if best:
        results.append((k, best[0], best[1], best[2], coverage, distinct))

# sort by absolute WR deviation from base, prefer side ABOVE base
results.sort(key=lambda r: -(r[2]-BASE_WR))
print("=== features whose best subset has WR ABOVE base (winner-dense) ===")
for k,cond,wr,n,cov,dist in results:
    if wr>BASE_WR:
        print(f"  {k:20s} {cond:14s} WR={wr:5.1f} n={n:5d} cov={cov:.2f} dist={dist}")

print("\n=== features whose best subset has WR BELOW base (loser-dense, CUT candidates) ===")
results.sort(key=lambda r: (r[2]-BASE_WR))
for k,cond,wr,n,cov,dist in results:
    if wr<BASE_WR:
        print(f"  {k:20s} {cond:14s} WR={wr:5.1f} n={n:5d} cov={cov:.2f} dist={dist}")
