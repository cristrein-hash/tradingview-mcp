#!/usr/bin/env python3
"""LAB G — Devil's Advocate audit of the frozen capitulation systems.

Adversarial overlays on the SAME frozen selections (no re-selection, no new
predicate variants — decomposition + costing + robustness only):
  1. NET panel under SB costing (cost_R = 0.80 / g_risk per trade, Lab E convention).
  2. Branch x year decomposition (S2) + branch streaks.
  3. Week-cluster jackknife (drop each week, worst-case sumR).
  4. Risk-size profile of selected trades (late-entry / compressed-R diagnosis for S1).
"""
import json, os, collections
from lab_g_capitulation_systems import ROWS, s1_pass, s2_pass, FROZEN_K

def net_panel(sel, name):
    sel = sorted(sel, key=lambda r: r['cj_t'])
    nets = [r['g_R'] - 0.80 / r['g_risk'] for r in sel]
    n = len(nets); wins = sum(1 for x in nets if x > 0)
    eq = mx = dd = 0.0
    for x in nets:
        eq += x; mx = max(mx, eq); dd = max(dd, mx - eq)
    ls = cls = 0
    for x in nets:
        cls = cls + 1 if x <= 0 else 0; ls = max(ls, cls)
    print(f'[{name} NET-SB] N={n} WR_liq={100*wins/n:.1f}% NET={sum(nets):+.1f} avg={sum(nets)/n:+.3f} '
          f'DD={-dd:.1f} r/DD={sum(nets)/dd if dd else 0:.2f} streak=-{ls}')
    per_yr = collections.defaultdict(float)
    for r, x in zip(sel, nets): per_yr[r['yr']] += x
    print('  per-year NET: ' + ' · '.join(f'{y}:{v:+.1f}' for y, v in sorted(per_yr.items())))

def branch_detail(sel, name):
    for reg in ['BULL', 'RANGE', 'BEAR']:
        sub = sorted([r for r in sel if r['g_v5h'] == reg], key=lambda r: r['cj_t'])
        if not sub: continue
        Rs = [r['g_R'] for r in sub]
        nets = [r['g_R'] - 0.80 / r['g_risk'] for r in sub]
        ls = cls = 0
        for x in Rs:
            cls = cls + 1 if x <= 0 else 0; ls = max(ls, cls)
        yr = collections.defaultdict(lambda: [0, 0.0])
        for r in sub: yr[r['yr']][0] += 1; yr[r['yr']][1] += r['g_R']
        print(f'  [{name}·{reg}] N={len(Rs)} WR={100*sum(1 for x in Rs if x>0)/len(Rs):.1f}% '
              f'sumR={sum(Rs):+.1f} NET={sum(nets):+.1f} streak=-{ls} | '
              + ' · '.join(f'{y}: N{v[0]} {v[1]:+.1f}R' for y, v in sorted(yr.items())))

def week_jackknife(sel, name):
    by_wk = collections.defaultdict(float)
    for r in sel: by_wk[r['g_week']] += r['g_R']
    tot = sum(by_wk.values())
    worst = sorted(by_wk.items(), key=lambda kv: -kv[1])[:3]
    best_drop = tot - worst[0][1] if worst else tot
    print(f'  [{name} jackknife-week] total={tot:+.1f} · minus best wk ({worst[0][0]} {worst[0][1]:+.1f}) = {best_drop:+.1f} '
          f'· top3 wks = {sum(v for _, v in worst):+.1f} ({100*sum(v for _, v in worst)/tot if tot else 0:.0f}% of total)')

def risk_profile(sel, name):
    risks = sorted(r['g_risk'] for r in sel)
    n = len(risks)
    med = risks[n // 2]
    print(f'  [{name} risk] median g_risk={med:.1f} q25={risks[n//4]:.1f} q75={risks[3*n//4]:.1f} '
          f'· med cost_R={0.8/med:.3f}')

if __name__ == '__main__':
    s1 = [r for r in ROWS if s1_pass(r, FROZEN_K)]
    s2 = [r for r in ROWS if s2_pass(r)]
    net_panel(s1, f'S1 VEXA-R k{FROZEN_K}'); branch_detail(s1, 'S1'); week_jackknife(s1, 'S1'); risk_profile(s1, 'S1')
    net_panel(s2, 'S2 TRIPTYCH'); branch_detail(s2, 'S2'); week_jackknife(s2, 'S2'); risk_profile(s2, 'S2')
    # S2 BULL branch alone (decomposition of the frozen spec, not a new predicate)
    s2b = [r for r in s2 if r['g_v5h'] == 'BULL']
    week_jackknife(s2b, 'S2·BULL'); risk_profile(s2b, 'S2·BULL')
