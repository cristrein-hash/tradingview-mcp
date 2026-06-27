"""5ATR re-optimization combo hunter (clean pipeline, this session).

Approach:
 1. For each of 47 causal features, scan thresholds in both directions, building
    KEEP-predicates (keep rows satisfying cond) measured as standalone single filters.
 2. Build a candidate predicate pool: only predicates whose KEEP-subset has
    winners_kept_pct >= 85 (i.e. they don't kill winners) -- these are the bricks
    that can stack. Each brick records WR and winners_kept.
 3. Forward selection: start from base, greedily add the brick (AND-combine) that
    maximizes a stability-aware score, up to 3 bricks. Score rewards WR gain +
    streak reduction + per-year/per-block stability, penalizes winner loss below 85%.
 4. Also run a focused exhaustive 2-combo search over a pruned brick set to find
    interactions (weak-alone -> strong-in-combo).
 5. Report top combos with full metrics + robust flag.

RAW-causal. win=R>0. Nulls => predicate FALSE (KEEP filters exclude null rows
ONLY if the predicate references that feature; we instead treat null as 'condition
not evaluable' => row is CUT for KEEP-bricks that reference a null feature).
PROIBIDO usar R/win/cj/low_idx.
"""
import json
import statistics
from itertools import combinations
import _reopt5_lib as L

ROWS = L.load()
N = len(ROWS)

FORB = L.FORBIDDEN
ALLKEYS = [k for k in ROWS[0].keys() if k not in FORB]
FEATS = []
for k in ALLKEYS:
    vals = [r.get(k) for r in ROWS if r.get(k) is not None]
    if len(vals) < N * 0.5:
        continue
    if not all(isinstance(v, (int, float)) for v in vals):
        continue
    if len(set(vals)) < 2:
        continue
    FEATS.append(k)

# sentinel masking for sell_decel (extreme -1e6..-2e6 = "no sell event" sentinel)
SENTINEL = {'sell_decel': lambda v: v <= -1e5}


def feat_val(r, k):
    v = r.get(k)
    if v is None:
        return None
    if k in SENTINEL and SENTINEL[k](v):
        return None
    return v


def make_pred(k, op, thr):
    if op == '>=':
        def p(r):
            v = feat_val(r, k)
            return v is not None and v >= thr
    elif op == '<=':
        def p(r):
            v = feat_val(r, k)
            return v is not None and v <= thr
    p.desc = f"{k}{op}{thr}"
    p.k = k
    return p


def thresholds(k):
    vals = sorted(set(feat_val(r, k) for r in ROWS if feat_val(r, k) is not None))
    if len(vals) <= 12:
        return vals
    # use deciles/ventiles
    qs = [vals[int(len(vals) * q)] for q in
          (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]
    return sorted(set(qs))


def apply_preds(preds):
    return [r for r in ROWS if all(p(r) for p in preds)]


# ---------- Step 1+2: build brick pool ----------
bricks = []  # (pred, m)
for k in FEATS:
    for thr in thresholds(k):
        for op in ('>=', '<='):
            p = make_pred(k, op, thr)
            kept = apply_preds([p])
            if len(kept) < 300:  # need enough sample
                continue
            m = L.metrics(kept, ROWS)
            if m is None:
                continue
            # brick must not destroy winners and should not LOWER WR badly
            if m['winners_kept_pct'] >= 85.0:
                bricks.append((p, m))

# dedupe bricks that produce identical kept-set sizes per feature (keep best WR per feature/op coarse)
print(f"FEATS={len(FEATS)} brick_pool={len(bricks)} (winners_kept>=85% singles)")

# rank bricks by WR for visibility
bricks_sorted = sorted(bricks, key=lambda x: -x[1]['wr_keep'])
print("\nTOP 15 single bricks by WR (winners_kept>=85%):")
for p, m in bricks_sorted[:15]:
    print(f"  {p.desc:28s} n={m['n_keep']:4d} wr={m['wr_keep']:.2f} "
          f"wk={m['winners_kept_pct']:.0f}% lc={m['losers_cut_pct']:.0f}% "
          f"strk{m['streak_keep']} yr={m['by_year']} blk{m['blocks_ok']}")


def score(m):
    """stability-aware score for forward selection."""
    if m is None or m['winners_kept_pct'] < 85.0:
        return -1e9
    s = (m['wr_keep'] - L.BASE_WR) * 3.0          # WR gain
    s += (L.max_losing_streak(ROWS) - m['streak_keep']) * 1.5  # streak cut
    # per-year stability
    yrpen = 0
    for yr in (2024, 2025, 2026):
        v = m['by_year'][yr]
        if v is None or v < L.YEAR_BASE[yr]:
            yrpen += 5
    s -= yrpen
    s += (m['blocks_ok'] - 6) * 1.0
    return s


# ---------- Step 3: forward selection ----------
print("\n" + "=" * 70)
print("FORWARD SELECTION (greedy AND-stack up to 3 bricks)")
# limit candidate bricks to top by score to keep it tractable & meaningful
cand = sorted(bricks, key=lambda x: -score(x[1]))[:120]

chosen = []
chosen_preds = []
cur_kept = ROWS
for depth in range(3):
    best = None
    for p, _ in cand:
        if any(p.desc == cp.desc for cp in chosen_preds):
            continue
        test_preds = chosen_preds + [p]
        kept = apply_preds(test_preds)
        if len(kept) < 300:
            continue
        m = L.metrics(kept, ROWS)
        sc = score(m)
        if best is None or sc > best[0]:
            best = (sc, p, m)
    if best is None:
        break
    sc, p, m = best
    # require improvement
    prev_sc = score(L.metrics(cur_kept, ROWS)) if chosen_preds else -1e9
    if sc <= prev_sc and depth > 0:
        break
    chosen_preds.append(p)
    chosen.append(p.desc)
    cur_kept = apply_preds(chosen_preds)
    print(f"  +{p.desc:28s} -> n={m['n_keep']} wr={m['wr_keep']:.2f} "
          f"wk={m['winners_kept_pct']:.0f}% strk{m['streak_keep']} "
          f"yr={m['by_year']} blk{m['blocks_ok']} score={sc:.1f}")

print("\nForward-selected stack:", " AND ".join(chosen))
L.report("FWD_STACK: " + " AND ".join(chosen), apply_preds(chosen_preds), ROWS)
