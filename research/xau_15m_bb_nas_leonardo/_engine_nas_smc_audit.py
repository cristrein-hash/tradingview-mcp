#!/usr/bin/env python3
"""
_engine_nas_smc_audit.py — Devil's Advocate / robustness audit of the leading
NAS/SMC candidates from _engine_nas_smc.py.

Robustness redefined per spec intent: avgR > PER-YEAR base in all 3 years
(yearly bases differ: 2024=0.691, 2025=0.797, 2026=0.603), n>=30,
and not carried by top-2 trades (ex-top2 still > global base 0.727).

Also runs:
  - ex-top2 AND ex-top3 stability
  - WR vs base WR (45.4%)
  - "closer than 8ATR" proxy: near_M8 rate inside the rule (target context only,
    NOT used as feature) — higher near_M8 means edge realizes nearer the pivot.
  - block-level concentration (how many distinct blocks carry the rule).
"""
import json

ROWS = [json.loads(l) for l in open("entry_dataset.jsonl")]
GBASE = 0.727
YBASE = {2024: 0.691, 2025: 0.797, 2026: 0.603}
WRBASE = 0.454


def audit(desc, rs):
    n = len(rs)
    R = sorted([r["R_reclaim"] for r in rs], reverse=True)
    avg = sum(R) / n
    wr = sum(1 for x in R if x > 0) / n
    run = sum(1 for x in R if x >= 5) / n
    extop2 = sum(R[2:]) / (n - 2)
    extop3 = sum(R[3:]) / (n - 3)
    nm8 = sum(r["near_M8"] for r in rs) / n
    nblocks = len(set(r["block"] for r in rs))
    yr = {}
    beats_year = True
    for y in (2024, 2025, 2026):
        sub = [r["R_reclaim"] for r in rs if r["yr"] == y]
        ay = sum(sub) / len(sub) if sub else None
        yr[y] = (len(sub), round(ay, 3) if ay is not None else None)
        if ay is None or len(sub) < 5 or ay <= YBASE[y]:
            beats_year = False
    robust = (n >= 30 and beats_year and extop2 > GBASE)
    print(f"{desc}")
    print(f"  n={n} WR={round(wr,3)}(base.454) avgR={round(avg,3)} lift={round(avg-GBASE,3)} "
          f"run={round(run,3)} nearM8={round(nm8,3)}(base.223) blocks={nblocks}")
    print(f"  y24={yr[2024]}(b.691) y25={yr[2025]}(b.797) y26={yr[2026]}(b.603) "
          f"beats_yearly_base={beats_year}")
    print(f"  exTop2={round(extop2,3)} exTop3={round(extop3,3)} top3R={[round(x,2) for x in R[:3]]}")
    print(f"  >>> ROBUST(yearly)={robust}\n")
    return robust


print("=== LEADING CANDIDATES — yearly-base robustness audit ===\n")

audit("C1: smc_bos==1 (most recent BOS)",
      [r for r in ROWS if r["smc_bos"] == 1])

audit("C2: nas_long_16>=2 AND smc_choch in(1,2)",
      [r for r in ROWS if r["nas_long_16"] >= 2 and r["smc_choch"] in (1, 2)])

audit("C3: nas_long_48>=2 AND macro_bull==1",
      [r for r in ROWS if r["nas_long_48"] >= 2 and r["macro_bull"] == 1])

audit("C4: smc_choch==2",
      [r for r in ROWS if r["smc_choch"] == 2])

# Try to strengthen smc_bos==1 with NAS confirmation (clean directional)
print("=== smc_bos==1 refined with NAS lens ===\n")
audit("C5: smc_bos==1 AND nas_short_16==0",
      [r for r in ROWS if r["smc_bos"] == 1 and r["nas_short_16"] == 0])
audit("C6: smc_bos==1 AND nas_last_long==1",
      [r for r in ROWS if r["smc_bos"] == 1 and r["nas_last_long"] == 1])
audit("C7: smc_bos==1 AND nas_long_48>=2",
      [r for r in ROWS if r["smc_bos"] == 1 and r["nas_long_48"] >= 2])
audit("C8: smc_bos==1 AND smc_choch in(1,2)",
      [r for r in ROWS if r["smc_bos"] == 1 and r["smc_choch"] in (1, 2)])
audit("C9: smc_bos==1 AND smc_choch==2",
      [r for r in ROWS if r["smc_bos"] == 1 and r["smc_choch"] == 2])

# nas_long_16>=2 + choch refined
print("=== nas_long cluster refinements ===\n")
audit("C10: nas_long_16>=2 AND smc_choch==2",
      [r for r in ROWS if r["nas_long_16"] >= 2 and r["smc_choch"] == 2])
audit("C11: nas_long_16>=3 AND smc_choch in(1,2)",
      [r for r in ROWS if r["nas_long_16"] >= 3 and r["smc_choch"] in (1, 2)])

# macro_bull combos cleaner
print("=== macro_bull anchored (NAS-confirmed) ===\n")
audit("C12: macro_bull==1 AND smc_bos==1",
      [r for r in ROWS if r["macro_bull"] == 1 and r["smc_bos"] == 1])
audit("C13: macro_bull==1 AND nas_long_48>=2 AND smc_bos==1",
      [r for r in ROWS if r["macro_bull"] == 1 and r["nas_long_48"] >= 2 and r["smc_bos"] == 1])
