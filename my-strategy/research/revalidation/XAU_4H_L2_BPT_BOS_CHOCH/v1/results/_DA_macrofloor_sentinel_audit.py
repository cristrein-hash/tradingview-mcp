#!/usr/bin/env python3
"""Devil's-Advocate audit for the macro_floor hypothesis (XAU 4H L2/BPT).

Verifies the two load-bearing data claims the DA could not take on faith:
 1. The distDem=-1.00 value for #3949 — is it a missing-value sentinel?
    How many of the 276 carry the sentinel, and does it leak into
    near_dem / macro_floor as a *true* (<=1.0 ATR) flag?
 2. macro_floor coverage / inversion sanity: of trades flagged
    macro_floor==True via dist<=1.0, how many are sentinel-driven?

Reproducible companion to the DA verdict. No mutation of inputs.
verified at: 2026-06-25
"""
import csv, collections, os

MAT = os.path.join(os.path.dirname(__file__), "l2_bpt_trade_qualification_matrix.csv")
rows = list(csv.DictReader(open(MAT)))
DC = "dist_4h_demand_low_atr"
OC = "demand_origin_of_leg"
HC = "has_4h_demand"

def fnum(v):
    try:
        return float(v)
    except Exception:
        return None

print(f"total rows: {len(rows)}")

# --- 1. sentinel audit on dist_4h_demand_low_atr ---
unparseable = [r for r in rows if fnum(r[DC]) is None]
negs = collections.Counter()
le1_true = 0          # would set near_dem / macro_floor ON
le1_negative = 0      # ON *because* value is negative (sentinel-like)
for r in rows:
    x = fnum(r[DC])
    if x is None:
        continue
    if x < 0:
        negs[round(x, 2)] += 1
    if x <= 1.0:
        le1_true += 1
        if x < 0:
            le1_negative += 1

print(f"unparseable (blank/NA) dist values: {len(unparseable)}")
print(f"negative dist values (sentinel candidates): {sum(negs.values())} -> {dict(negs)}")
print(f"rows with dist<=1.0 (near_dem ON): {le1_true}")
print(f"  of those, ON because dist<0 (sentinel leak): {le1_negative}")

# has_4h_demand gate: does a real demand zone exist at all?
no_dem = [r for r in rows if str(r.get(HC, "")).strip().lower() in ("0", "false", "")]
print(f"rows with has_4h_demand falsey: {len(no_dem)}")
# of the negative-dist rows, how many actually lack a demand zone?
neg_rows = [r for r in rows if (fnum(r[DC]) is not None and fnum(r[DC]) < 0)]
neg_no_dem = [r for r in neg_rows if str(r.get(HC, "")).strip().lower() in ("0", "false", "")]
print(f"  of negative-dist rows, has_4h_demand falsey: {len(neg_no_dem)} / {len(neg_rows)}")

# --- 2. macro_floor recomputation two ways ---
def truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes")

mf_naive = 0   # dem_origin OR dist<=1.0  (negative counts as <=1.0  -> BUG path)
mf_guard = 0   # dem_origin OR (0<=dist<=1.0)  (sentinel excluded)
for r in rows:
    x = fnum(r[DC])
    org = truthy(r.get(OC, ""))
    if org or (x is not None and x <= 1.0):
        mf_naive += 1
    if org or (x is not None and 0.0 <= x <= 1.0):
        mf_guard += 1
print(f"macro_floor (naive, dist<=1.0 incl negatives): {mf_naive}")
print(f"macro_floor (guarded, 0<=dist<=1.0):           {mf_guard}")
print(f"delta from sentinel contamination: {mf_naive - mf_guard}")

# spot-check the named episodes if present (col name for id?)
idcol = next((c for c in rows[0] if c.lower() in ("id", "trade_id", "signal_id", "tid")), None)
print(f"id column: {idcol}")
if idcol:
    want = {"5826", "3949", "3118", "1661", "1901", "2737", "5555", "5627", "9628"}
    for r in rows:
        if str(r[idcol]) in want:
            print(f"  #{r[idcol]} dist={r[DC]} demOrigin={r.get(OC)} has_dem={r.get(HC)}")
