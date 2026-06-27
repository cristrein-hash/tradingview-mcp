"""Cadence/silence lens. max_silence is constant(21) -> dead. Use proxies:
bars_since_sell (recency of sell flow), buy_sell_ratio4 (one-sidedness),
flow_accel (curvature). Hypothesis: recent active two-sided flow that is NOT
one-sided-overbought = coiled spring (winner); stale/one-sided = chop (loser).
KEEP-when filters (we cut the chop).
"""
from _r2lap_lib import load, evaluate, report

k = load()

tests = []

# C1: recent sell flow (active battle)
tests.append(("C1 keep bars_since_sell<=40", lambda r: r['bars_since_sell'] <= 40))
# C2: not one-sided overbought
tests.append(("C2 keep buy_sell_ratio4<=5", lambda r: r['buy_sell_ratio4'] <= 5))
# C3: combo recent sell AND not one-sided
tests.append(("C3 keep bss<=40 AND bsr4<=5", lambda r: r['bars_since_sell'] <= 40 and r['buy_sell_ratio4'] <= 5))
# C4: recent sell OR not one-sided (looser, keep more winners)
tests.append(("C4 keep bss<=40 OR bsr4<=5", lambda r: r['bars_since_sell'] <= 40 or r['buy_sell_ratio4'] <= 5))
# C5: cut only the worst chop: stale sell AND one-sided overbought
tests.append(("C5 cut (bss>40 AND bsr4>5)", lambda r: not (r['bars_since_sell'] > 40 and r['buy_sell_ratio4'] > 5)))
# C6: cut flat-curvature chop too: also require not flat flow
tests.append(("C6 cut (bss>40 AND bsr4>5) and cut flat flow_accel in(-2..0)",
              lambda r: not (r['bars_since_sell'] > 40 and r['buy_sell_ratio4'] > 5) and not (-2 <= r['flow_accel'] <= 0)))
# C7: cut one-sided OR flat
tests.append(("C7 cut (bsr4>5 OR flat flow)", lambda r: not (r['buy_sell_ratio4'] > 5 or (-2 <= r['flow_accel'] <= 0))))

print("BASE WR=68.54 streak=24  yr base 24=66.05 25=70.91 26=65.19\n")
for desc, fn in tests:
    report(evaluate(k, fn, desc))
    print()
