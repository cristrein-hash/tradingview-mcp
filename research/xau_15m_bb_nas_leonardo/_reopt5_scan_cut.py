"""Scan for loser-dense regions to CUT (keep complement).
This is the route to >=85% winner retention: cut a small region that is
mostly losers. For each numeric feature + each binary, find the single-sided
cut whose KEPT complement maximizes WR while keeping >=85% winners.
RAW-causal: features only.
"""
import collections
from _reopt5_lib import load, FORBIDDEN, BASE_WR

rows = load()
wins_all = sum(r["win"] for r in rows)
n = len(rows)

def qtiles(vals, qs):
    s = sorted(vals)
    return [s[int(q*(len(s)-1))] for q in qs]

feat_vals = collections.defaultdict(list)
for r in rows:
    for k, v in r.items():
        if k in FORBIDDEN: continue
        if isinstance(v,(int,float)) and v is not None:
            feat_vals[k].append(v)

results = []
for k in sorted(feat_vals):
    vals = feat_vals[k]
    if len(set(vals)) <= 1: continue
    present = [r for r in rows if isinstance(r.get(k),(int,float)) and r.get(k) is not None]
    grid = sorted(set(round(g,4) for g in qtiles(vals,[0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9,0.95])))
    for thr in grid:
        for op in (">=","<="):  # CUT this region; keep complement (incl. nulls of other feats stay)
            if op==">=":
                cut=[r for r in present if r[k]>=thr]
            else:
                cut=[r for r in present if r[k]<=thr]
            # keep = everything not in cut (cut only defined on present; rows with null on k are kept)
            cut_ids=set(id(r) for r in cut)
            kept=[r for r in rows if id(r) not in cut_ids]
            if len(kept)<1500: continue  # keep majority
            wk=sum(r['win'] for r in kept)
            wr=100.0*wk/len(kept)
            wkp=100.0*wk/wins_all
            if wkp>=85.0 and wr>BASE_WR+0.3:
                results.append((wr,wkp,k,op,thr,len(kept)))

results.sort(reverse=True)
print(f"{'WRkeep':>6} {'win%':>5} {'feat':22s} cut{'op':3s} {'thr':>9} {'nkeep':>5}")
for wr,wkp,k,op,thr,nn in results[:50]:
    print(f"{wr:6.2f} {wkp:5.1f} {k:22s} cut{op:3s} {thr:9.3f} {nn:5d}")
