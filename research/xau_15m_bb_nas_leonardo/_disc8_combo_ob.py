"""Combo search around the OB 'ceiling overhead' axis + regime/TF/path interactions.
Lens: loser when 8ATR spiked into a supply ceiling above (room small) and/or
arrived fast (low bars_to_8atr) with weak demand support. Winner = clear sky above,
grind arrival, fresh demand below.
All keep-rules CUT losers (keep complement). RAW-causal.
"""
from _disc8_lib import load, eval_rule, print_rule, base_stats

rows = load()
n, w, wr, st = base_stats(rows)
print(f"BASE n={n} WR={wr:.4f} streak={st}\n")

# derived
for r in rows:
    r["_room"] = r["dist_supply_atr"] - r["dist_demand_atr"]
    r["_clear_sky"] = 1 if r["dist_supply_atr"] >= 20 else 0  # sentinel = no supply above
    r["_grind"] = 1 if r["bars_to_8atr"] >= 84 else 0          # median split


def g(r, k):
    return r[k] if r[k] is not None else 0


CANDS = {
    # single anchors (context)
    "clear_sky (dist_supply>=20)": lambda r: r["_clear_sky"] == 1,
    "room>=0.44 (supply above demand)": lambda r: r["_room"] >= 0.44,
    "room>=0 (supply not below demand)": lambda r: r["_room"] >= 0,
    "grind (bars_to_8atr>=84)": lambda r: r["_grind"] == 1,
    "dist_supply>=0.5": lambda r: r["dist_supply_atr"] >= 0.5,

    # COMBO: clear sky + grind (no ceiling AND not a spike)
    "clear_sky & grind": lambda r: r["_clear_sky"] == 1 and r["_grind"] == 1,
    "room>=0 & grind": lambda r: r["_room"] >= 0 and r["_grind"] == 1,
    "clear_sky OR grind": lambda r: r["_clear_sky"] == 1 or r["_grind"] == 1,

    # COMBO: ceiling clearance + HTF not topped (h1_pos not at top of range)
    "room>=0 & h1_pos<=0.9": lambda r: r["_room"] >= 0 and g(r, "h1_pos") <= 0.9,
    "clear_sky & h1_pos<=0.9": lambda r: r["_clear_sky"] == 1 and g(r, "h1_pos") <= 0.9,

    # COMBO: ceiling clearance + h4 trend up (HTF supports continuation)
    "room>=0 & h4_trend>=0": lambda r: r["_room"] >= 0 and g(r, "h4_trend") >= 0,
    "clear_sky & h4_trend==1": lambda r: r["_clear_sky"] == 1 and g(r, "h4_trend") == 1,

    # COMBO: cut the WORST cell only -> keep complement of (ceiling AND spike)
    "NOT(ceiling & spike)": lambda r: not (r["_room"] < 0 and r["_grind"] == 0),
    "NOT(ceiling & h1_pos>0.9)": lambda r: not (r["_room"] < 0 and g(r, "h1_pos") > 0.9),

    # demand support: many demand zones near below
    "n_demand_near>=2 & room>=0": lambda r: r["n_demand_near"] >= 2 and r["_room"] >= 0,
}

results = []
for desc, fn in CANDS.items():
    m = eval_rule(rows, fn, desc)
    if m:
        results.append(m)

# sort by wr_keep desc then losers_cut
results.sort(key=lambda m: (-m["wr_keep"], -m["losers_cut_pct"]))
for m in results:
    print_rule(m)
    print()
