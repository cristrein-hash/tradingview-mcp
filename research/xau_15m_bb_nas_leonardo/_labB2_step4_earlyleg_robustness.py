#!/usr/bin/env python3
"""Lab B r2 — Step 4: EARLYLEG lens robustness (CALIBRATION status, Look1-derived; declared Look4).

Tests:
  E1: legpos60 <= thr, thr in {0.20, 0.25, 0.30} — SKIP vs HALF-SIZE impact on sum/DD/streak/runners.
  E2: convergent legpos60<=0.25 AND h1_pos<=0.61.
  E3: per-year + per-block sign of benefit (jackknife-style) for E1@0.25 SKIP.
  E4: overlap of E1 flags with streak members (does it eat the pain clusters?).
  C1 half-size comparison (h4n mid-lid) for completeness.
"""
import json
from collections import defaultdict

DIR = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{DIR}/results/lab_g_candidates.jsonl')]
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

def report(name, flagfn, mode):
    if mode == 'SKIP':
        nets = [r['net'] for r in base if not flagfn(r)]
        runk = sum(r['runner'] for r in base if not flagfn(r))
    else:  # HALF
        nets = [r['net'] * (0.5 if flagfn(r) else 1.0) for r in base]
        runk = RUN  # runners still taken, half size
    s, dd, stk = curve(nets)
    nf = sum(1 for r in base if flagfn(r))
    rf = sum(r['runner'] for r in base if flagfn(r))
    print(f"{name:34s} {mode:4s} nF={nf:3d} rF={rf:2d} -> sum{s:+7.1f} DD{dd:6.1f} stk-{stk} runKeep {runk}/{RUN}")

print("baseline                                sum+233.6 DD -14.2 stk-8")
for thr in (0.20, 0.25, 0.30):
    fn = (lambda t: (lambda r: r['legpos60'] <= t))(thr)
    report(f"E1 legpos60<={thr}", fn, 'SKIP')
    report(f"E1 legpos60<={thr}", fn, 'HALF')
fnE2 = lambda r: r['legpos60'] <= 0.25 and r['h1_pos'] <= 0.61
report("E2 lp60<=0.25 AND h1_pos<=0.61", fnE2, 'SKIP')
report("E2 lp60<=0.25 AND h1_pos<=0.61", fnE2, 'HALF')
fnC1 = lambda r: 0.38 <= r['h4n_clean_sky_atr'] < 0.92
report("C1 h4nlid [0.38,0.92)", fnC1, 'SKIP')
report("C1 h4nlid [0.38,0.92)", fnC1, 'HALF')

print("\nE3 per-year / per-block, E1@0.25 flagged subset (what SKIP removes):")
fn25 = lambda r: r['legpos60'] <= 0.25
for key in ('yr', 'block'):
    agg = defaultdict(lambda: [0, 0.0, 0])
    for r in base:
        if fn25(r):
            a = agg[r[key]]; a[0] += 1; a[1] += r['net']; a[2] += r['runner']
    print(f"  by {key}: " + '  '.join(f"{k}:n{v[0]} s{v[1]:+.1f} r{v[2]}" for k, v in sorted(agg.items())))

print("\nE4 streak-eating: members of loss-runs>=4 flagged by E1@0.25")
runs, cur = [], []
for r in base:
    if r['net'] <= 0: cur.append(r)
    else:
        if len(cur) >= 4: runs.append(cur);
        cur = []
if len(cur) >= 4: runs.append(cur)
members = [r for run in runs for r in run]
flg = sum(1 for r in members if fn25(r))
print(f"  flagged {flg}/{len(members)} streak-members ({100*flg/len(members):.0f}%) vs base coverage {100*sum(1 for r in base if fn25(r))/len(base):.0f}%")
per_run = [(run[0]['block'], len(run), sum(1 for r in run if fn25(r))) for run in runs]
print("  per-run (block, len, flagged):", per_run)

print("\nE1@0.25 flagged runners detail (identity of the 5 runners we would lose on SKIP):")
for r in base:
    if fn25(r) and r['runner']:
        print(f"  t={r['t']} block={r['block']} g_R={r['g_R']:+.2f} net={r['net']:+.2f} legpos60={r['legpos60']:.2f} h1_pos={r['h1_pos']:.2f}")
