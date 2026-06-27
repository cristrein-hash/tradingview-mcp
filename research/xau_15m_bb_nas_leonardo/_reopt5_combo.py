"""Combo CUT search for 5ATR re-opt.
A row is CUT only if it satisfies ALL conditions in a combo (loser-dense
pocket = AND of conditions). Keep the complement. This finds small pockets
that are loser-dense, preserving winners.
Also supports KEEP-combos (keep only rows satisfying ALL = positive selection).
Each candidate evaluated under full robustness gate.
RAW-causal: features only, never R/win/cj/low_idx.

Lens priority (PERNA/regime): deep-leg vs shallow-leg, daily/h4 position.
"""
import itertools
import collections
from _reopt5_lib import load, metrics, is_robust, report, BASE_WR, YEAR_BASE

rows = load()
wins_all = sum(r["win"] for r in rows)

# ---- Build atomic CUT predicates (cut = likely loser pocket) ----
# Each predicate: (label, fn) where fn(r)->True means "this row is in the cut region".
# Rows with null feature value => predicate False (not cut) to be safe.
def ge(k, t):
    return (f"{k}>={t}", lambda r,k=k,t=t: r.get(k) is not None and r[k] >= t)
def le(k, t):
    return (f"{k}<={t}", lambda r,k=k,t=t: r.get(k) is not None and r[k] <= t)

# Candidate cut atoms drawn from scan_cut + lens. These describe LOSER-dense traits:
#  - shallow leg / not done bottoming: macro_retr low, bars_to_base low, path_eff high, bars_since_lowest low
#  - chasing high in range: h1_pos low(early), hd_eff low(no daily trend), h4_pos low
#  - weak momentum context
CUT_ATOMS = [
    le("h1_pos", 0.76), le("h1_pos", 0.52), le("h1_pos", 0.65),
    le("h1_dist", 1.85), le("h1_dist", 0.60),
    le("hd_eff", 0.12), le("hd_eff", 0.06),
    le("dist_supply_atr", -0.26),  # entering INTO supply overhead close
    ge("macro_bear", 1.0),
    le("vpnode_dist_atr", 1.71), le("vpnode_dist_atr", 0.11),
    le("disp4_atr", 1.0), le("disp4_atr", 0.44),
    le("rsi", 57.8), le("rsi", 51.6),
    le("path_eff", 0.06), ge("path_eff", 0.92),
    le("bars_to_base", 7.0), le("bars_to_base", 14.0),
    le("bars_since_lowest", 14.0), le("bars_since_lowest", 6.0),
    le("h4_pos", 0.48), le("h4_pos", 0.40),
    le("h4_dist", 0.42),
    le("macro_retr", 0.45), le("macro_retr", 0.39),
    le("low_closepos", 0.20),
    ge("regime_age_h", 120.5),
    ge("smc_bos", 3.0),
    le("vol_climax", 0.79),
    ge("flow_accel", 30.0),
    le("dist_demand_atr", -0.10),  # already pierced demand
]

def eval_cut(atom_fns):
    """atom_fns: list of predicate fns; cut if ALL true. keep complement."""
    kept = [r for r in rows if not all(f(r) for f in atom_fns)]
    return kept

def desc(atoms):
    return "CUT(" + " AND ".join(a[0] for a in atoms) + ")"

candidates = []

# singles already known; focus pairs and triples
labels = list(range(len(CUT_ATOMS)))

print(">>> scanning PAIRS")
for i, j in itertools.combinations(labels, 2):
    a = [CUT_ATOMS[i], CUT_ATOMS[j]]
    fns = [x[1] for x in a]
    kept = eval_cut(fns)
    if len(kept) < 2400:  # don't cut too much
        continue
    m = metrics(kept, rows)
    if m and m["winners_kept_pct"] >= 85.0 and m["wr_keep"] > BASE_WR + 0.4:
        candidates.append((m["wr_keep"], desc(a), kept, m))

print(">>> scanning TRIPLES (filtered atoms)")
# To keep triples tractable, only combine atoms that as a pair already cut some losers
for i, j, k in itertools.combinations(labels, 3):
    a = [CUT_ATOMS[i], CUT_ATOMS[j], CUT_ATOMS[k]]
    fns = [x[1] for x in a]
    kept = eval_cut(fns)
    if len(kept) < 2500:
        continue
    m = metrics(kept, rows)
    if m and m["winners_kept_pct"] >= 85.0 and m["wr_keep"] > BASE_WR + 0.6:
        candidates.append((m["wr_keep"], desc(a), kept, m))

candidates.sort(key=lambda x: -x[0])
print(f"\n=== TOP combos (winners>=85%, WR>base) : {len(candidates)} found ===")
robusts = []
for wr, d, kept, m in candidates[:40]:
    rob = is_robust(m)
    flag = "ROBUST" if rob else ""
    print(f"WR={wr:.2f} n={m['n_keep']} win%={m['winners_kept_pct']} "
          f"lcut%={m['losers_cut_pct']} streak={m['streak_base']}->{m['streak_keep']} "
          f"yr={m['by_year']} blk={m['blocks_ok']}/8 {flag}  {d}")
    if rob:
        robusts.append((wr, d, kept, m))

print(f"\n=== {len(robusts)} ROBUST combos ===")
for wr, d, kept, m in robusts:
    print(f"WR={wr:.2f} {d}")
