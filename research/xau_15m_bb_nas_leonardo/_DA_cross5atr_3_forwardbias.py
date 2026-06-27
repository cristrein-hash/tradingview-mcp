#!/usr/bin/env python3
"""DA POINT 3 — FORWARD BIAS. Prove the tier is realized leg power (FUTURE) and CANNOT
be an entry filter. For each matched BOT entry, show the M8 reversal timestamp the tier
came from and the leg_atr (the post-entry leg). If the reversal == the anchor bar and the
leg_atr is the move AFTER entry, the tier is unknowable at entry. Quantify: at entry time
(low_t), how far in the future is the reversal-defining info? leg_atr is by definition the
size of the leg the entry is trying to ride, i.e. the OUTCOME. State look-ahead verdict."""
import csv, bisect
from pathlib import Path
from filter_harness import ROWS, dedup
HERE=Path(__file__).parent; BAR=900; W=3
REV=[{**r,"t":int(r["t"]),"leg_atr":float(r["leg_atr"])} for r in csv.DictReader(open(HERE/"reversal_power.csv"))]
REVt=sorted(REV,key=lambda r:r["t"]); RT=[r["t"] for r in REVt]
def nearest_rev(t):
    k=bisect.bisect_left(RT,t); best=None
    for j in (k-1,k,k+1):
        if 0<=j<len(REVt):
            d=abs(REVt[j]["t"]-t)
            if best is None or d<best[0]: best=(d,REVt[j])
    return best
base=dedup(ROWS)
matched=[]
for r in base:
    nb=nearest_rev(r["low_t"])
    if nb and nb[0]<=W*BAR and nb[1]["kind"]=="BOT":
        matched.append((r,nb[1]))
print(f"matched BOT entries: {len(matched)}")
print("tier is assigned from leg_atr / power_score of the reversal. leg_atr = size of the")
print("leg that STARTS at the BOT and extends FORWARD (out_atr in true_reversals). Unknowable at entry.")
print("\nentry_low_t   rev_t      Δbars  rev_leg_atr  tier   entry_R   win")
for r,rev in sorted(matched,key=lambda x:x[0]["low_t"])[:40]:
    db=(rev["t"]-r["low_t"])/BAR
    print(f"{r['low_t']}  {rev['t']}  {db:>5.0f}  {rev['leg_atr']:>10.1f}  {rev['tier']:<7}{r['R']:>+6.2f}  {r['win']}")
# correlation: does tier (forward) predict R? trivially yes (that's the tautology)
import statistics as st
by_tier={}
for r,rev in matched: by_tier.setdefault(rev["tier"],[]).append(r["R"])
print("\navg entry-R by FORWARD tier (tautological — leg power IS the outcome):")
for t in ["MONSTRO","FORTE","MEDIO","FRACO"]:
    v=by_tier.get(t,[])
    if v: print(f"  {t:<8} n={len(v)} avgR={st.mean(v):+.2f}")
print("\nVERDICT: tier requires the post-entry leg -> cannot gate entries. Diagnostic ONLY.")
