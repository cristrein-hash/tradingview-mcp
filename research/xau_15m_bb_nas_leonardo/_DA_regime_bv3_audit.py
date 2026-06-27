#!/usr/bin/env python3
"""Devil's Advocate audit of test_regime_bv3.py (Cris 2026-06-27).
Checks: (1) causality prior-day vs same-day mapping; (2) reproduce 4 rows;
(3) n21 BEAR block detail + binomial CI; (4) sub-signals macro_broken/stage_n/v2_state.
RAW-causal, in-sample only."""
import json, bisect, datetime as dt, collections, math
from pathlib import Path
from filter_harness import ROWS, dedup, stats

BV3 = Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl")
cls = [json.loads(l) for l in BV3.read_text().splitlines() if l.strip()]
byday = {dt.date.fromisoformat(r["ts"]): r for r in cls}
days = sorted((d, byday[d]) for d in byday)
DD = [d for d, _ in days]

def asof(t, lag=1):
    ed = dt.datetime.utcfromtimestamp(t).date()
    if lag == 1:
        k = bisect.bisect_left(DD, ed) - 1      # strictly prior closed day
    else:
        k = bisect.bisect_right(DD, ed) - 1     # <= entry date (same-day, look-ahead)
    return days[k][1] if k >= 0 else None

base = dedup([r for r in ROWS if r['h1_eff'] is not None and r['h1_eff'] >= 0.15])
for c in base:
    rp = asof(c['t'], 1); rs = asof(c['t'], 0)
    c['p'] = rp; c['s'] = rs

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (round(100*(c-h), 1), round(100*(c+h), 1))

print("=== (1) PRIOR vs SAMEDAY mapping ===")
for tag, key in (("PRIOR", "p"), ("SAMEDAY", "s")):
    g = [c for c in base if c[key]['v3_state'] == 'BEAR']
    w = sum(x['win'] for x in g); sm = sum(x['R'] for x in g)
    lo, hi = wilson(w, len(g))
    print(f"  {tag} BEAR block: n={len(g)} WR={100*w/len(g):.1f}% (Wilson {lo}-{hi}) sumR={sm:+.1f}")
diff = [c for c in base if c['p']['v3_state'] != c['s']['v3_state']]
print(f"  entries where prior!=sameday state: {len(diff)}/{len(base)}")

print("\n=== (3) n21 BEAR block detail ===")
g = sorted([c for c in base if c['p']['v3_state'] == 'BEAR'], key=lambda x: x['t'])
for c in g:
    d = dt.datetime.utcfromtimestamp(c['t']).strftime('%Y-%m-%d')
    print(f"  {d} block={c['block']} R={c['R']:+.2f} win={c['win']} yr={c['yr']}")
w = sum(x['win'] for x in g)
print(f"  total: n={len(g)} W={w} L={len(g)-w} sumR={sum(x['R'] for x in g):+.1f} Wilson_WR={wilson(w,len(g))}")
# how concentrated is the +6.1R? remove biggest winner
gr = sorted(g, key=lambda x: -x['R'])
print(f"  sumR without top winner ({gr[0]['R']:+.2f}): {sum(x['R'] for x in g)-gr[0]['R']:+.1f}")

print("\n=== (5) sub-signals on the 211 ===")
for c in base:
    c['mb'] = c['p'].get('macro_broken'); c['sn'] = c['p'].get('stage_n'); c['v2'] = c['p'].get('v2_state_final')
# macro_broken
for val in (True, False):
    g = [c for c in base if c['mb'] == val]
    if g:
        w = sum(x['win'] for x in g)
        print(f"  macro_broken={val!s:<5} n={len(g):>3} WR={100*w/len(g):.1f}% sumR={sum(x['R'] for x in g):+.1f}")
# v2_state_final
for st in sorted(set(c['v2'] for c in base)):
    g = [c for c in base if c['v2'] == st]
    w = sum(x['win'] for x in g)
    print(f"  v2_state={st:<12} n={len(g):>3} WR={100*w/len(g):.1f}% sumR={sum(x['R'] for x in g):+.1f}")
# stage_n buckets
print("  stage_n distribution:", dict(collections.Counter(c['sn'] for c in base)))
