#!/usr/bin/env python3
"""
Loser-cut (lapidacao) for target E2_discount.

Target membership: dist_ema_atr<0 AND ema_slope_atr>0  (pullback into rising-EMA discount).
Outcome: R_reclaim. winner=outcome>0, loser=outcome<=0.

Goal: REMOVE max losers while keeping >=90% winners, and reduce max-losing-streak.
Filter features must be ORTHOGONAL (do NOT re-use dist_ema_atr / ema_slope_atr, the rule-defining features).
FORBIDDEN (look-ahead / outcome): R_reclaim, R_8atr, near_M8, held8, runner, reclaim_idx, low_idx.

RAW-causal: every feature read is from the reclaim bar / pre-entry; no outcome leakage in the filter.
"""
import json
from collections import Counter
from itertools import combinations

PATH = "entry_dataset.jsonl"
rows = [json.loads(l) for l in open(PATH)]

# --- target membership ---
mem = [r for r in rows if r["dist_ema_atr"] < 0 and r["ema_slope_atr"] > 0]
mem.sort(key=lambda r: r["low_t"])  # chronological for streak

def is_win(r): return r["R_reclaim"] > 0
def is_los(r): return r["R_reclaim"] <= 0

W = [r for r in mem if is_win(r)]
L = [r for r in mem if is_los(r)]

def max_losing_streak(seq):
    best = cur = 0
    for r in seq:
        if is_los(r):
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best

def stats(seq):
    n = len(seq)
    w = sum(1 for r in seq if is_win(r))
    return n, round(100*w/n, 1) if n else 0.0, max_losing_streak(seq)

n0, wr0, ms0 = stats(mem)
print(f"BEFORE  n={n0} WR={wr0} maxstreak={ms0} (winners={len(W)} losers={len(L)})")

# ---------------------------------------------------------------
# Candidate orthogonal predicates. Each is (name, fn). fn True => KEEP the trade.
# We want predicates that are mostly TRUE on winners and FALSE on losers.
# We search single thresholds per numeric feature on the loser/winner separation,
# then evaluate combos.
# ---------------------------------------------------------------
FORBIDDEN = {"R_reclaim","R_8atr","near_M8","held8","runner","reclaim_idx","low_idx",
             "dist_ema_atr","ema_slope_atr","block","low_t","yr"}
numeric_feats = []
for k,v in mem[0].items():
    if k in FORBIDDEN: continue
    if isinstance(v,(int,float)): numeric_feats.append(k)

# For each numeric feature, find direction+threshold that best separates.
# We test "keep if x>=t" and "keep if x<=t" over candidate thresholds (quantiles of losers).
import statistics
def feat_vals(seq,k): return [r[k] for r in seq]

def eval_keep(keep_set):
    kept = [r for r in mem if r in keep_set] if isinstance(keep_set,set) else None
    return kept

def predicate_scan():
    cands = []
    for k in numeric_feats:
        vals = sorted(set(r[k] for r in mem))
        if len(vals) < 2: continue
        # threshold candidates: midpoints
        ths = [(vals[i]+vals[i+1])/2 for i in range(len(vals)-1)]
        # subsample for speed
        if len(ths) > 120:
            step = len(ths)//120
            ths = ths[::step]
        for t in ths:
            for op,fn in (("<=", lambda x,t=t: x<=t), (">=", lambda x,t=t: x>=t)):
                kept = [r for r in mem if fn(r[k])]
                kw = sum(1 for r in kept if is_win(r))
                kl = sum(1 for r in kept if is_los(r))
                if kw == 0: continue
                wkept = 100*kw/len(W)
                lcut = 100*(len(L)-kl)/len(L)
                if wkept >= 90.0 and lcut > 0:
                    cands.append((k,op,round(t,4),wkept,lcut,kw,kl,kept))
    return cands

singles = predicate_scan()
# rank by losers cut desc, then winners kept desc
singles.sort(key=lambda c:(-c[4], -c[3]))
print("\nTOP SINGLE predicates (winners_kept>=90%):")
for c in singles[:12]:
    k,op,t,wk,lc,kw,kl,kept = c
    n,wr,ms = stats(kept)
    print(f"  {k}{op}{t}: keep n={n} WR={wr} streak={ms} | win_kept={wk:.1f}% los_cut={lc:.1f}%")

# ---------------------------------------------------------------
# Combo search: combine 2-3 single predicates (AND). Keep if ALL keep-predicates true.
# Use the surviving singles pool.
# ---------------------------------------------------------------
pool = singles[:40]  # best singles as building blocks
def kept_of(c):
    return c[7]
best_combos = []
# represent each predicate as a frozenset of kept indices
idx = {id(r):i for i,r in enumerate(mem)}
def kept_ids(c): return frozenset(idx[id(r)] for r in c[7])

pred_sets = [(c, kept_ids(c)) for c in pool]
allids = frozenset(range(len(mem)))
win_ids = frozenset(i for i,r in enumerate(mem) if is_win(r))
los_ids = frozenset(i for i,r in enumerate(mem) if is_los(r))

def combo_eval(ids):
    kw = len(ids & win_ids); kl = len(ids & los_ids)
    if kw==0: return None
    wkept = 100*kw/len(W); lcut=100*(len(L)-kl)/len(L)
    return wkept,lcut,kw,kl

seen = set()
for r in range(1,4):
    for combo in combinations(range(len(pred_sets)), r):
        ids = allids
        for j in combo: ids = ids & pred_sets[j][1]
        ev = combo_eval(ids)
        if ev is None: continue
        wkept,lcut,kw,kl = ev
        if wkept < 90.0: continue
        key = ids
        if key in seen: continue
        seen.add(key)
        descs = " AND ".join(f"{pred_sets[j][0][0]}{pred_sets[j][0][1]}{pred_sets[j][0][2]}" for j in combo)
        kept = [mem[i] for i in sorted(ids)]
        n,wr,ms = stats(kept)
        best_combos.append((lcut,wkept,wr,ms,n,descs,ids))

# rank: maximize losers cut, then winners kept, then lower streak, then higher WR
best_combos.sort(key=lambda x:(-x[0], -x[1], x[3], -x[2]))
print("\nTOP COMBOS (winners_kept>=90%, ranked by losers_cut then streak):")
for lcut,wkept,wr,ms,n,descs,ids in best_combos[:15]:
    print(f"  [{descs}] keep n={n} WR={wr} streak={ms} | win_kept={wkept:.1f}% los_cut={lcut:.1f}%")

# ---------------------------------------------------------------
# Pick BEST: maximize losers cut with winners_kept>=90 AND lowest streak.
# Tie-break favor lower streak then higher losers_cut.
# ---------------------------------------------------------------
def year_wr(kept):
    out={}
    for y in (2024,2025,2026):
        sub=[r for r in kept if r["yr"]==y]
        if sub:
            wr=round(100*sum(1 for r in sub if is_win(r))/len(sub),1)
            out[y]=(len(sub),wr)
        else: out[y]=(0,None)
    return out

if best_combos:
    # choose by composite: prioritize streak reduction then losers cut
    chosen = sorted(best_combos, key=lambda x:(x[3], -x[0], -x[1]))[0]
    lcut,wkept,wr,ms,n,descs,ids = chosen
    kept = [mem[i] for i in sorted(ids)]
    n2,wr2,ms2 = stats(kept)
    yw = year_wr(kept)
    print("\n=== CHOSEN FILTER ===")
    print("desc:", descs)
    print(f"AFTER n={n2} WR={wr2} maxstreak={ms2}")
    print(f"winners_kept={wkept:.1f}%  losers_cut={lcut:.1f}%")
    for y in (2024,2025,2026):
        nn,wy=yw[y]; print(f"  y{str(y)[2:]}: n={nn} WR={wy}")
else:
    print("\nNENHUM filtro corta loser mantendo >=90% winners.")
