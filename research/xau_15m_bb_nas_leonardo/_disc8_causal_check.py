"""Causal sanity: is 'room>=0' just the clear-sky sentinel (supply==99)?
Split room>=0 into REAL supply-above (0.07<=dist_supply<20) vs sentinel(>=20).
Both should lift if the read ('ceiling not overhead') is causal, not an artifact.
Also re-verify max-losing-streak via explicit chronological scan.
"""
from _disc8_lib import load, base_stats, max_losing_streak

rows = load()
n, w, BASE, st = base_stats(rows)
print(f"BASE WR={BASE:.4f} streak={st}")
for r in rows:
    r["_room"] = r["dist_supply_atr"] - r["dist_demand_atr"]
    r["_sentinel"] = 1 if r["dist_supply_atr"] >= 20 else 0


def grp(name, sel):
    s = [r for r in rows if sel(r)]
    if not s:
        print(f"  {name}: empty"); return
    print(f"  {name:48s} n={len(s):4d} WR={sum(x['win'] for x in s)/len(s):.3f}")


print("\n=== decompose room>=0 by sentinel ===")
grp("room>=0 & REAL supply above (0.07<=ds<20)", lambda r: r["_room"] >= 0 and 0.07 <= r["dist_supply_atr"] < 20)
grp("room>=0 & sentinel (ds>=20 clear sky)", lambda r: r["_room"] >= 0 and r["_sentinel"] == 1)
grp("room<0 (ceiling: supply below demand)", lambda r: r["_room"] < 0)
grp("room>=0 & grind60 & REAL supply", lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 60 and 0.07 <= r["dist_supply_atr"] < 20)
grp("room>=0 & grind60 & sentinel", lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 60 and r["_sentinel"] == 1)

print("\n=== streak re-verify (explicit) on final rule ===")
def streak_explicit(keep_fn):
    kept = [r for r in rows if keep_fn(r)]  # rows already low_t sorted
    seq = [r["win"] for r in kept]
    mx = cur = 0
    for v in seq:
        cur = cur + 1 if v == 0 else 0
        mx = max(mx, cur)
    return len(kept), mx

for d, fn in [
    ("ALL", lambda r: True),
    ("room>=0 & grind84", lambda r: r["_room"] >= 0 and r["bars_to_8atr"] >= 84),
    ("room>=0 & (grind60 OR n_demand_near>=5)", lambda r: r["_room"] >= 0 and (r["bars_to_8atr"] >= 60 or r["n_demand_near"] >= 5)),
]:
    nk, mxs = streak_explicit(fn)
    print(f"  {d:42s} n={nk:4d} streak={mxs}  (lib={max_losing_streak([r for r in rows if fn(r)])})")
