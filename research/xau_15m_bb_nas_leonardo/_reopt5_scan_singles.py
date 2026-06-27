"""Single-feature discrimination scan for 5ATR re-opt.
For each numeric feature, find threshold splits (deciles) and report the
sub-region with highest WR lift + winner retention. Focus: identify which
directions move WR up. RAW-causal: features only, never R/win.
"""
import json
import collections
from _reopt5_lib import load, FORBIDDEN, BASE_WR

rows = load()
n = len(rows)
wins_all = sum(r["win"] for r in rows)

# collect numeric features
feat_vals = collections.defaultdict(list)
for r in rows:
    for k, v in r.items():
        if k in FORBIDDEN:
            continue
        if isinstance(v, (int, float)) and v is not None:
            feat_vals[k].append(v)

# detect constants
print("=== feature inventory ===")
const_feats = []
for k in sorted(feat_vals):
    vals = feat_vals[k]
    uniq = len(set(vals))
    cov = len(vals)
    if uniq <= 1:
        const_feats.append(k)
    print(f"{k:22s} cov={cov:4d} uniq={uniq:4d} min={min(vals):.2f} max={max(vals):.2f}")
print("CONST feats:", const_feats)

print("\n=== single-feature threshold scan (keep-side WR) ===")
# For each feature test keeping >= q and <= q for a grid of quantiles.
import statistics

def qtiles(vals, qs):
    s = sorted(vals)
    out = []
    for q in qs:
        idx = int(q * (len(s) - 1))
        out.append(s[idx])
    return out

results = []
for k in sorted(feat_vals):
    if k in const_feats:
        continue
    # rows where feature present
    present = [r for r in rows if isinstance(r.get(k), (int, float)) and r.get(k) is not None]
    vals = [r[k] for r in present]
    grid = qtiles(vals, [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9])
    grid = sorted(set(round(g,4) for g in grid))
    for thr in grid:
        for op in (">=", "<="):
            if op == ">=":
                kept = [r for r in present if r[k] >= thr]
            else:
                kept = [r for r in present if r[k] <= thr]
            if len(kept) < 200:
                continue
            wk = sum(r["win"] for r in kept)
            wr = 100.0 * wk / len(kept)
            wkp = 100.0 * wk / wins_all
            if wr > BASE_WR + 1.0:  # only show lifts
                results.append((wr, k, op, thr, len(kept), round(wkp,1)))

results.sort(reverse=True)
print(f"{'WR':>6} {'feat':22s} {'op':3s} {'thr':>9} {'n':>5} {'win%':>6}")
for wr, k, op, thr, nn, wkp in results[:60]:
    print(f"{wr:6.2f} {k:22s} {op:3s} {thr:9.3f} {nn:5d} {wkp:6.1f}")
