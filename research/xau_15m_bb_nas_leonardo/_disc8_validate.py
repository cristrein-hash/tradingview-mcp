"""Validate top rules for robustness: per-block beat-base, leave-one-block-out,
not-carried-by-few. Plus try to rescue winners via path_eff/macro contextual add.
robust=true requires WR>base in ALL 3 yrs AND not carried by <=2 blocks.
"""
from _disc8_lib import load, eval_rule, base_stats

rows = load()
n, w, BASE, st = base_stats(rows)
print(f"BASE WR={BASE:.4f} streak={st}\n")
for r in rows:
    r["_room"] = r["dist_supply_atr"] - r["dist_demand_atr"]


def g(r, k):
    return r[k] if r[k] is not None else 0


def per_year_ok(m):
    yb = {2024: 0.6234, 2025: 0.6900, 2026: 0.6385}
    return all(m["yr"][y][0] is not None and m["yr"][y][0] >= yb[y] for y in (2024, 2025, 2026))


def loo_block(rows, fn):
    """leave-one-block-out: min WR_keep across removing each block."""
    blocks = sorted(set(r["block"] for r in rows))
    out = []
    for b in blocks:
        sub = [r for r in rows if r["block"] != b]
        kept = [r for r in sub if fn(r)]
        if kept:
            out.append((b, sum(x["win"] for x in kept) / len(kept), len(kept)))
    return out


RULES = {
    "room>=0 & grind84": lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 84,
    "room>=0 & grind60": lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 60,
    # contextual rescue attempts: add path_eff or macro to recover winners w/o WR loss
    "room>=0 & grind60 & path_eff<=0.5": lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 60 and r["path_eff"] <= 0.5,
    "room>=0 & (grind60 OR macro_retr>=1.0)": lambda r: r["_room"] >= 0 and (r["bars_to_8atr"] >= 60 or r["macro_retr"] >= 1.0),
    "room>=0 & (grind60 OR n_demand_near>=5)": lambda r: r["_room"] >= 0 and (r["bars_to_8atr"] >= 60 or r["n_demand_near"] >= 5),
}

for desc, fn in RULES.items():
    m = eval_rule(rows, fn, desc)
    ok_yr = per_year_ok(m)
    loo = loo_block(rows, fn)
    loo_min = min(loo, key=lambda x: x[1]) if loo else None
    # carried-by-few: drop best block, does WR stay > base?
    blk_wr = [(b, v[0], v[1]) for b, v in m["blk"].items() if v[0] is not None]
    print(f"RULE: {desc}")
    print(f"  n_keep={m['n_keep']} wr={m['wr_keep']} streak={m['streak_keep']} "
          f"winners_kept={m['winners_kept_pct']} losers_cut={m['losers_cut_pct']}")
    print(f"  yr24={m['yr'][2024]} yr25={m['yr'][2025]} yr26={m['yr'][2026]}  per_year_ok={ok_yr}")
    nb = sum(1 for _, wrr, _ in blk_wr if wrr > BASE)
    print(f"  blocks>base: {nb}/{len(blk_wr)}  loo_min_block={loo_min}")
    print(f"  block detail: {[(b, round(wrr,2), nn) for b,wrr,nn in blk_wr]}")
    print()
