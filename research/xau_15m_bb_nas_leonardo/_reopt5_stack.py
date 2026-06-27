"""Final STACK evaluation for 5ATR re-opt.
A STACK = union of 1-3 CUT rules (a row is removed if it matches ANY rule).
Each rule may itself be an AND-combo of atoms (loser-dense pocket).
We test the best non-degenerate rules individually and stacked, under the
full robustness gate, prioritizing streak reduction + WR lift + winner keep.

Themes (orthogonal):
  A = R2 multi-TF efficiency/position: cut entries with weak h1 structure
      (h1_pos<=0.65 = early/low in h1 swing, not yet thrust) -> single strongest
  B = leg-stage: cut not-done-bottoming (path_eff>=0.92 fast clean drop still
      falling) -> orthogonal to A (path vs structure)
  C = location: cut entering INTO daily-down with no daily efficiency
      (hd_eff<=0.12) -> daily-context
We seek a stack that combines orthogonal cuts to cut MORE losers while
staying >=85% winners and lowering streak.
RAW-causal.
"""
import itertools
from _reopt5_lib import load, metrics, is_robust, report, BASE_WR

rows = load()

def le(k,t): return (f"{k}<={t}", lambda r,k=k,t=t: r.get(k) is not None and r[k]<=t)
def ge(k,t): return (f"{k}>={t}", lambda r,k=k,t=t: r.get(k) is not None and r[k]>=t)

# Non-degenerate orthogonal RULES (each = AND of atoms). A row matches rule if ALL atoms true.
RULES = {
    "A_h1pos": [le("h1_pos",0.65)],                       # weak h1 structure / early
    "A_h1dist": [le("h1_dist",1.85)],                     # close to h1 ema (no thrust)
    "B_path_falling": [ge("path_eff",0.92), le("bars_to_base",14.0)],  # fast clean drop, just made low
    "C_hd_eff": [le("hd_eff",0.12)],                      # no daily trend efficiency
    "D_vpnode": [le("vpnode_dist_atr",1.71)],             # sitting on vp node (chop)
    "E_h4dist": [le("h4_dist",0.42)],                     # at h4 ema, no h4 thrust
    "F_into_supply": [le("dist_supply_atr",-0.26)],       # closing into overhead supply
    "G_intodemand": [le("dist_demand_atr",-0.1)],         # pierced demand
    "H_bottoming_young": [le("bars_to_base",14.0), le("bars_since_lowest",14.0)],
}

def matches(rule, r):
    return all(f(r) for _,f in rule)

def apply_stack(rule_keys):
    kept = [r for r in rows if not any(matches(RULES[k], r) for k in rule_keys)]
    return kept

def label(rule_keys):
    parts=[]
    for k in rule_keys:
        parts.append(k+"["+ " & ".join(a for a,_ in RULES[k]) +"]")
    return "STACK_CUT( " + " OR ".join(parts) + " )"

# 1) singles
print("########## SINGLE RULES ##########")
single_m={}
for k in RULES:
    kept=apply_stack([k])
    m=report(label([k]), kept, rows)
    single_m[k]=(kept,m)

# 2) pairs and triples (union)
print("\n########## STACKS (pairs/triples) ##########")
best=[]
keys=list(RULES)
for combo in list(itertools.combinations(keys,2))+list(itertools.combinations(keys,3)):
    kept=apply_stack(list(combo))
    m=metrics(kept,rows)
    if m and m["winners_kept_pct"]>=85.0 and m["wr_keep"]>BASE_WR:
        best.append((m,combo,kept))

# sort: prioritize streak reduction then WR
best.sort(key=lambda x:(x[0]["streak_keep"], -x[0]["wr_keep"]))
print("\n--- best stacks sorted by (streak asc, WR desc) ---")
for m,combo,kept in best[:25]:
    rob=is_robust(m)
    print(f"WR={m['wr_keep']:.2f} n={m['n_keep']} win%={m['winners_kept_pct']} "
          f"lcut%={m['losers_cut_pct']} streak={m['streak_base']}->{m['streak_keep']} "
          f"yr={m['by_year']} blk={m['blocks_ok']}/8 {'ROBUST' if rob else ''}  "
          f"{ ' OR '.join(combo) }")

# 3) full report on the most promising robust stacks (max WR among robust + min streak among robust)
print("\n########## FINAL: top robust by WR ##########")
robs=[(m,combo,kept) for m,combo,kept in best if is_robust(m)]
robs_by_wr=sorted(robs,key=lambda x:-x[0]["wr_keep"])
for m,combo,kept in robs_by_wr[:5]:
    report(label(list(combo)), kept, rows)

print("\n########## FINAL: top robust by streak reduction ##########")
robs_by_streak=sorted(robs,key=lambda x:(x[0]["streak_keep"],-x[0]["wr_keep"]))
seen=set()
for m,combo,kept in robs_by_streak[:5]:
    report(label(list(combo)), kept, rows)
