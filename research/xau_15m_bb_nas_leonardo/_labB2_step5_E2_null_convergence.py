#!/usr/bin/env python3
"""Lab B r2 — Step 5: E2 lens (legpos60<=a AND h1_pos<=b) — grid wiggle, per-block convergence,
null benchmark (random equal-size removals), streak-run coverage. Declared Look5 (calibration).
"""
import json, random
from collections import defaultdict

# NOTE 2026-07-04: results/lab_g_candidates.jsonl became a broken self-referential
# symlink at 04:01 (sibling agent activity). Using session-scratchpad backup (4499 rows,
# base 435 verified identical: sumNET +233.6).
SRC = ('/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/'
       'd1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/derivados_sandbox/'
       'backup_candidates/lab_g_candidates.jsonl')
rows = [json.loads(l) for l in open(SRC)]
base = [r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR']
for r in base:
    r['net'] = r['g_R'] - 0.80 / r['g_risk']
    r['runner'] = 1 if r['g_R'] >= 3 else 0
base.sort(key=lambda r: r['t'])
RUN = sum(r['runner'] for r in base)

def curve(nets):
    cum = peak = 0.0; dd = 0.0; stk = cur = 0
    for n in nets:
        cum += n; peak = max(peak, cum); dd = min(dd, cum - peak)
        if n <= 0: cur += 1; stk = max(stk, cur)
        else: cur = 0
    return cum, dd, stk

print("=== E2 grid wiggle (SKIP) — baseline sum+233.6 DD-14.2 stk-8 ===")
for a in (0.20, 0.25, 0.30):
    for b in (0.55, 0.61, 0.65, 0.70):
        fn = lambda r: r['legpos60'] <= a and r['h1_pos'] <= b
        rest = [r['net'] for r in base if not fn(r)]
        s, dd, stk = curve(rest)
        nf = sum(1 for r in base if fn(r)); rf = sum(r['runner'] for r in base if fn(r))
        rk = RUN - rf
        print(f"a={a:.2f} b={b:.2f} nF={nf:3d} rF={rf} -> sum{s:+7.1f} DD{dd:6.1f} stk-{stk} runKeep {rk}/{RUN}")

fn = lambda r: r['legpos60'] <= 0.25 and r['h1_pos'] <= 0.61
print("\n=== E2@0.25/0.61 flagged: per-year, per-block ===")
for key in ('yr', 'block'):
    agg = defaultdict(lambda: [0, 0.0, 0])
    for r in base:
        if fn(r):
            a_ = agg[r[key]]; a_[0] += 1; a_[1] += r['net']; a_[2] += r['runner']
    print(f"  by {key}: " + '  '.join(f"{k}:n{v[0]} s{v[1]:+.1f} r{v[2]}" for k, v in sorted(agg.items())))

print("\n=== NULL: 2000 random removals of n=42, benchmark (sum>=+233.6 AND DD>=-11.0 AND stk<=6) ===")
random.seed(42)
hits_all = hits_dd = hits_sum = hits_stk = 0
for _ in range(2000):
    idx = set(random.sample(range(len(base)), 42))
    rest = [base[i]['net'] for i in range(len(base)) if i not in idx]
    s, dd, stk = curve(rest)
    if s >= 233.6: hits_sum += 1
    if dd >= -11.0: hits_dd += 1
    if stk <= 6: hits_stk += 1
    if s >= 233.6 and dd >= -11.0 and stk <= 6: hits_all += 1
print(f"  P(sum>=base)={hits_sum/2000:.3f} P(DD>=-11.0)={hits_dd/2000:.3f} P(stk<=6)={hits_stk/2000:.3f} P(all)={hits_all/2000:.4f}")

print("\n=== E2 coverage of loss-runs>=4 ===")
runs, cur = [], []
for r in base:
    if r['net'] <= 0: cur.append(r)
    else:
        if len(cur) >= 4: runs.append(cur)
        cur = []
if len(cur) >= 4: runs.append(cur)
members = [r for run in runs for r in run]
flg = sum(1 for r in members if fn(r))
print(f"  flagged {flg}/{len(members)} streak-members ({100*flg/len(members):.0f}%) vs coverage {100*sum(1 for r in base if fn(r))/len(base):.1f}%")
print("  per-run flagged:", [(run[0]['block'], len(run), sum(1 for r in run if fn(r))) for run in runs])

print("\n=== E2 HALF-size variant metrics ===")
nets = [r['net'] * (0.5 if fn(r) else 1.0) for r in base]
s, dd, stk = curve(nets)
print(f"  HALF: sum{s:+.1f} DD{dd:.1f} stk-{stk} runKeep {RUN}/{RUN} (runners at half size: {sum(r['runner'] for r in base if fn(r))})")

print("\n=== E2 flagged loser anatomy: worst 10 by net ===")
fl = sorted([r for r in base if fn(r)], key=lambda r: r['net'])[:10]
for r in fl:
    print(f"  {r['block']} net={r['net']:+.2f} lp60={r['legpos60']:.2f} h1_pos={r['h1_pos']:.2f} box96={r['g_box96']:.2f} v5h={r['g_v5h']}")
