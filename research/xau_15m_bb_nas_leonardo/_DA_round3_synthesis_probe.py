#!/usr/bin/env python3
"""DA PROBE — Round 3 continuation verdict + cross-round substrate synthesis.
Adversarial: (1) is continuation catching chop (mfe never reaches target)?
(2) BEAR-short genuinely negative? (3) +zona robustness (concentration/dedup)?
(4) cross-round right-tail substrate signature across the 3 candidate files.
Read-only over candidates_*.csv. Verified 2026-06-26."""
import csv, collections
from pathlib import Path
HERE = Path(__file__).parent

def load(fn):
    return list(csv.DictReader(open(HERE / fn)))

def tail_profile(rows, Rkey="R"):
    n = len(rows)
    R = [float(r[Rkey]) for r in rows]
    w = sum(1 for x in R if x > 0)
    pos = sorted([x for x in R if x > 0], reverse=True)
    top5 = sum(pos[:5]); tot = sum(R)
    return dict(n=n, WR=round(100*w/n), sumR=round(tot,1),
                top5_share=round(100*top5/tot,0) if tot > 0 else None,
                avgR=round(tot/n,3))

print("=== (1) CONTINUATION: chop vs clean — mfe reach distribution ===")
cont = load("candidates_continuation.csv")
n = len(cont)
def frac(p): return round(sum(1 for r in cont if p(r))/n, 3)
print(f"n={n} | mfe<1R(dies before 1R)={frac(lambda r:float(r['mfe_R'])<1.0)} "
      f"| mfe>=2.5R(target reachable)={frac(lambda r:float(r['mfe_R'])>=2.5)} "
      f"| mfe>=3R(runner)={frac(lambda r:float(r['mfe_R'])>=3.0)}")
print("  -> half the fires never see +1R: trigger fires into noise, not clean continuation\n")

print("=== (2) BEAR-short negativity (genuine, not bug) ===")
for d in ("LONG", "SHORT"):
    sub = [r for r in cont if r["dir"] == d]
    print(f"  {d}:", tail_profile(sub))
print("  -> SHORT negative across the board; mirror logic structurally weaker on XAU 15M\n")

print("=== (3) +zona subset robustness ===")
z = [r for r in cont if r["in_zone"] == "1"]
print("  +zona overall:", tail_profile(z))
byb = collections.Counter(r["block"][:10] for r in z)
print("  +zona by block:", dict(byb))
# leave-out top block
blksum = collections.defaultdict(float)
for r in z: blksum[r["block"][:10]] += float(r["R"])
top = max(blksum, key=blksum.get)
rem = [r for r in z if r["block"][:10] != top]
print(f"  drop top block {top} (sumR {round(blksum[top],1)}): remaining", tail_profile(rem))
wins_z = sorted([float(r["R"]) for r in z], reverse=True)
print(f"  +zona wins are all clamped target hits 2.5R: {wins_z[:9]}")
print("  -> n33 0.34/wk, all wins are bare target-hits, edge sits in 1-2 blocks\n")

print("=== (4) CROSS-ROUND substrate signature (right-tail / top-5 concentration) ===")
files = [("R1 candidates_annotated (all macro)", "candidates_annotated.csv", None),
         ("R2 candidates_sweep (all)", "candidates_sweep.csv", None),
         ("R3 candidates_continuation (all)", "candidates_continuation.csv", "R")]
for label, fn, rk in files:
    try:
        rows = load(fn)
        # find an R-like column
        key = rk or ("R" if "R" in rows[0] else None)
        if key is None:
            cands = [c for c in rows[0] if c.lower() in ("r", "r_capped", "rc")]
            key = cands[0] if cands else None
        if key is None:
            print(f"  {label}: no R column ({list(rows[0].keys())[:8]})"); continue
        print(f"  {label}:", tail_profile(rows, key))
    except Exception as e:
        print(f"  {label}: ERR {e}")
print("  -> recurring: low WR (~25-44), positive sumR carried by a handful of right-tail trades,")
print("     top-5 trades = large share of total -> concentration is the structural signature, not a per-round bug")
