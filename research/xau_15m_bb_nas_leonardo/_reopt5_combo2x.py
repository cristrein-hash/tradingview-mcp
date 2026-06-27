"""Exhaustive 2-combo + curated 3-combo search over pruned brick pool.

Goal: find genuinely robust combos (interactions) that raise WR while keeping
>=85% winners, every year >= base, >=6/8 blocks, lower streak.
Also re-test the 8ATR-origin filter families:
  R2  = multi-TF efficiency/position  (h1_/h4_/hd_ eff & pos & trend, path_eff)
  R_B = sell-exhaustion in overheating (rsi high + sell_decel/sell flow + overbought)
RAW-causal. win=R>0.
"""
import _reopt5_lib as L
from itertools import combinations

ROWS = L.load()
N = len(ROWS)
BASE_STREAK = L.max_losing_streak(ROWS)

FORB = L.FORBIDDEN
ALLKEYS = [k for k in ROWS[0].keys() if k not in FORB]
FEATS = []
for k in ALLKEYS:
    vals = [r.get(k) for r in ROWS if r.get(k) is not None]
    if len(vals) < N * 0.5 or not all(isinstance(v, (int, float)) for v in vals) or len(set(vals)) < 2:
        continue
    FEATS.append(k)

SENTINEL = {'sell_decel': lambda v: v <= -1e5}


def fv(r, k):
    v = r.get(k)
    if v is None:
        return None
    if k in SENTINEL and SENTINEL[k](v):
        return None
    return v


def mp(k, op, thr):
    if op == '>=':
        def p(r):
            v = fv(r, k); return v is not None and v >= thr
    else:
        def p(r):
            v = fv(r, k); return v is not None and v <= thr
    p.desc = f"{k}{op}{thr}"; p.k = k
    return p


def thresholds(k):
    vals = sorted(set(fv(r, k) for r in ROWS if fv(r, k) is not None))
    if len(vals) <= 12:
        return vals
    return sorted(set(vals[int(len(vals) * q)] for q in
                  (0.15, 0.3, 0.45, 0.6, 0.75, 0.9)))


def apply(preds):
    return [r for r in ROWS if all(p(r) for p in preds)]


# build brick pool: singles with winners_kept >= 88 (stricter so 2-combos stay >=85)
bricks = []
for k in FEATS:
    for thr in thresholds(k):
        for op in ('>=', '<='):
            p = mp(k, op, thr)
            kept = apply([p])
            if len(kept) < 400:
                continue
            m = L.metrics(kept, ROWS)
            if m and m['winners_kept_pct'] >= 90.0:
                bricks.append((p, m))
print(f"brick_pool(>=90% wk)={len(bricks)}")

# exhaustive 2-combo
results = []
for (p1, _), (p2, _) in combinations(bricks, 2):
    if p1.k == p2.k:
        continue
    kept = apply([p1, p2])
    if len(kept) < 500:
        continue
    m = L.metrics(kept, ROWS)
    if m is None:
        continue
    if m['winners_kept_pct'] >= 85.0 and L.is_robust(m):
        results.append((p1.desc, p2.desc, m))

# sort robust 2-combos by WR then streak reduction
results.sort(key=lambda x: (-x[2]['wr_keep'], x[2]['streak_keep']))
print(f"\nROBUST 2-combos: {len(results)}")
for d1, d2, m in results[:25]:
    print(f"  {d1:26s} & {d2:26s} n={m['n_keep']:4d} wr={m['wr_keep']:.2f} "
          f"wk={m['winners_kept_pct']:.0f}% lc={m['losers_cut_pct']:.0f}% "
          f"strk{BASE_STREAK}->{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}")

# dedupe by feature-pair, keep best per unordered feature pair
best_by_pair = {}
for d1, d2, m in results:
    k1 = d1.split('>=')[0].split('<=')[0]
    k2 = d2.split('>=')[0].split('<=')[0]
    key = tuple(sorted([k1, k2]))
    if key not in best_by_pair or m['wr_keep'] > best_by_pair[key][2]['wr_keep']:
        best_by_pair[key] = (d1, d2, m)
print(f"\nUNIQUE robust feature-pairs: {len(best_by_pair)}")
top_pairs = sorted(best_by_pair.values(), key=lambda x: -x[2]['wr_keep'])[:15]
for d1, d2, m in top_pairs:
    print(f"  {d1:26s} & {d2:26s} wr={m['wr_keep']:.2f} wk={m['winners_kept_pct']:.0f}% "
          f"strk{m['streak_keep']} lc={m['losers_cut_pct']:.0f}%")
