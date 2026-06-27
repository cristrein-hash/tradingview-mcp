"""_reopt5_multitf_stack.py — MULTI-TF lens re-derivation of R2 axis for 5ATR.

R2 axis (8ATR origin = multi-TF efficiency/position). Re-derived for 5ATR:
  LOSER = 15M entry with NO drive (weak h1 structure) into HTF range/topo/down.

This script focuses the search on the MULTI-TF feature family
(h1_/h4_/hd_ {trend,dist,pos,eff}) and threshold-scans each as a CUT-when-
loser-dense pocket, then stacks the strongest with ORTHOGONAL context cuts.

A STACK = union of CUT rules: a row is removed if it matches ANY rule.
Robust gate (shared lib): wr_keep>60.49, >=year base each yr, winners_kept>=85%,
>=6/8 blocks non-worse. We also want streak DOWN.

PROIBIDO R/win/cj/low_idx. RAW-causal (all features = bars already closed).
"""
import itertools
from _reopt5_lib import (load, metrics, is_robust, report, BASE_WR, YEAR_BASE)

rows = load()


def le(k, t):
    return (f"{k}<={t}", lambda r, k=k, t=t: r.get(k) is not None and r[k] <= t)


def eq(k, v):
    return (f"{k}=={v}", lambda r, k=k, v=v: r.get(k) == v)


# ---------- 1) THRESHOLD SCAN each multi-TF feature as a single CUT ----------
# scan a grid; report the single-cut robust ones with best WR + streak.
MTF_SCAN = {
    "h1_pos": [0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95],
    "h1_eff": [0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
    "h1_dist": [1.0, 1.5, 1.85, 2.2, 2.5, 3.0],
    "h4_pos": [0.3, 0.45, 0.6, 0.7, 0.8],
    "h4_eff": [0.05, 0.10, 0.15, 0.20],
    "h4_dist": [0.0, 0.42, 1.0, 2.0],
    "hd_pos": [0.3, 0.45, 0.6, 0.7],
    "hd_eff": [0.05, 0.10, 0.12, 0.16, 0.20],
    "hd_dist": [-2.0, 0.0, 2.0],
}

print("########## MULTI-TF SINGLE-CUT THRESHOLD SCAN ##########")
print("(CUT rows where feature <= t; keep rest)")
single_robust = []
for k, grid in MTF_SCAN.items():
    for t in grid:
        nm, fn = le(k, t)
        kept = [r for r in rows if not fn(r)]
        m = metrics(kept, rows)
        if m and m["wr_keep"] > BASE_WR and m["winners_kept_pct"] >= 85.0:
            rob = is_robust(m)
            tag = "ROBUST" if rob else ""
            print(f"  CUT {nm:14s} WR={m['wr_keep']:.2f} n={m['n_keep']} "
                  f"win%={m['winners_kept_pct']} lcut%={m['losers_cut_pct']} "
                  f"streak={m['streak_base']}->{m['streak_keep']} "
                  f"yr={m['by_year']} blk={m['blocks_ok']}/8 {tag}")
            if rob:
                single_robust.append((nm, fn, m))

# also the categorical trend cuts
print("\n--- trend categorical cuts ---")
TREND_CUTS = {
    "h1_down": eq("h1_trend", -1),
    "h4_range": eq("h4_trend", 0),
    "hd_down": eq("hd_trend", -1),
    "hd_range": eq("hd_trend", 0),
}
for nm, (lbl, fn) in TREND_CUTS.items():
    kept = [r for r in rows if not fn(r)]
    m = metrics(kept, rows)
    if m:
        rob = is_robust(m)
        print(f"  CUT {nm:10s} WR={m['wr_keep']:.2f} n={m['n_keep']} win%={m['winners_kept_pct']} "
              f"lcut%={m['losers_cut_pct']} streak={m['streak_base']}->{m['streak_keep']} "
              f"blk={m['blocks_ok']}/8 {'ROBUST' if rob else ''}")

# ---------- 2) ORTHOGONAL STACKS: strong h1-structure cut + context ----------
# Define named rules (each = AND of atoms). Row matches rule if all atoms true.
RULES = {
    # A-family: weak 15M structure / no drive (the R2 core)
    "A_h1pos65": [le("h1_pos", 0.65)],
    "A_h1pos70": [le("h1_pos", 0.70)],
    "A_h1eff15": [le("h1_eff", 0.15)],
    "A_h1dist185": [le("h1_dist", 1.85)],
    # B-family: HTF range/topo (orthogonal TF)
    "B_h4dist": [le("h4_dist", 0.42)],
    "B_hd_eff": [le("hd_eff", 0.12)],
    "B_h4range_notup": [eq("h4_trend", 0)],
    # C-family: location (into supply / pierced demand)
    "C_into_supply": [le("dist_supply_atr", -0.26)],
    "C_vpnode": [le("vpnode_dist_atr", 1.71)],
    # combo-atom rules (interaction): no-drive AND htf-range
    "AB_noeff_h4range": [le("h1_eff", 0.15), eq("h4_trend", 0)],
    "AB_weak_into_supply": [le("h1_pos", 0.65), le("dist_supply_atr", -0.26)],
}


def matches(rule, r):
    return all(f(r) for _, f in rule)


def apply_stack(keys):
    return [r for r in rows if not any(matches(RULES[k], r) for k in keys)]


def label(keys):
    return "CUT( " + " OR ".join(
        k + "[" + " & ".join(a for a, _ in RULES[k]) + "]" for k in keys) + " )"


print("\n\n########## ORTHOGONAL STACKS (pairs + triples) ##########")
keys = list(RULES)
cands = []
for r_ in (1, 2, 3):
    for combo in itertools.combinations(keys, r_):
        kept = apply_stack(list(combo))
        m = metrics(kept, rows)
        if m and m["winners_kept_pct"] >= 85.0 and m["wr_keep"] > BASE_WR:
            cands.append((m, combo))

# rank by WR desc among robust; then by streak
robs = [(m, c) for m, c in cands if is_robust(m)]
robs_by_wr = sorted(robs, key=lambda x: -x[0]["wr_keep"])
robs_by_streak = sorted(robs, key=lambda x: (x[0]["streak_keep"], -x[0]["wr_keep"]))

print(f"\n--- {len(robs)} ROBUST stacks. Top 15 by WR ---")
for m, c in robs_by_wr[:15]:
    print(f"WR={m['wr_keep']:.2f} n={m['n_keep']} win%={m['winners_kept_pct']} "
          f"lcut%={m['losers_cut_pct']} streak={m['streak_base']}->{m['streak_keep']} "
          f"yr={m['by_year']} blk={m['blocks_ok']}/8   {' OR '.join(c)}")

print(f"\n--- Top 10 ROBUST by streak reduction ---")
for m, c in robs_by_streak[:10]:
    print(f"streak={m['streak_base']}->{m['streak_keep']} WR={m['wr_keep']:.2f} "
          f"n={m['n_keep']} win%={m['winners_kept_pct']} lcut%={m['losers_cut_pct']} "
          f"blk={m['blocks_ok']}/8   {' OR '.join(c)}")

print("\n\n########## FINAL DETAIL: best robust by WR + best by streak ##########")
seen = set()
finalists = []
if robs_by_wr:
    finalists.append(robs_by_wr[0])
if robs_by_streak:
    finalists.append(robs_by_streak[0])
# add best WR among the 3-rule stacks for max loser-cut
robs_triples = sorted([x for x in robs if len(x[1]) == 3], key=lambda x: -x[0]["wr_keep"])
if robs_triples:
    finalists.append(robs_triples[0])
for m, c in finalists:
    key = tuple(c)
    if key in seen:
        continue
    seen.add(key)
    report(label(list(c)), apply_stack(list(c)), rows)
