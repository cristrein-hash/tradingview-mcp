#!/usr/bin/env python3
"""Lab B r2 — MARKET STRUCTURE AGENT — Step 1: base calibration (LOOK LEDGER: Look0 aggregate baseline only).

- Filter base: g_in_base435==1 & g_v5h!='BEAR' (expect N=435)
- NET-SB = g_R - 0.80/g_risk
- Look0: reproduce baseline aggregates (NET, WR_liq, DD, streak, runners) — aggregate only, no structural cross-tab.
- Calibration (NO outcome): quantiles of structural fields ON THE BASE distribution (prior P3: universe quantiles are vacuous on base).
- Join maturation features (room_above, ext_ema, pos20) by t; report join coverage.
"""
import json, math
from collections import Counter

DIR = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{DIR}/results/lab_g_candidates.jsonl')]
base = [r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR']
print(f"universe={len(rows)} base={len(base)}")

for r in base:
    r['net'] = r['g_R'] - 0.80 / r['g_risk']

# ---- Look0: aggregate baseline reproduction ----
base_sorted = sorted(base, key=lambda r: r['t'])
nets = [r['net'] for r in base_sorted]
sumnet = sum(nets)
wr = 100.0 * sum(1 for n in nets if n > 0) / len(nets)
# DD on cumulative net
cum = peak = 0.0; dd = 0.0
for n in nets:
    cum += n; peak = max(peak, cum); dd = min(dd, cum - peak)
# max loss streak (net<=0)
stk = cur = 0
for n in nets:
    if n <= 0: cur += 1; stk = max(stk, cur)
    else: cur = 0
print(f"LOOK0: sumNET={sumnet:+.1f} WR_liq={wr:.1f} DD={dd:.1f} maxLossStreak={stk}")
for thr in (3, 4, 5, 6):
    print(f"  runners net>={thr}: {sum(1 for n in nets if n >= thr)}")

# ---- join maturation ----
mat = json.load(open(f'{DIR}/base4_maturation_features.json'))
mt = {m['t']: m for m in mat}
joined = sum(1 for r in base if r['t'] in mt)
print(f"maturation join by t: {joined}/{len(base)}")
for r in base:
    m = mt.get(r['t'])
    if m:
        r['room_above'] = m.get('room_above'); r['ext_ema'] = m.get('ext_ema')
        r['pos20'] = m.get('pos20'); r['mfe'] = m.get('mfe'); r['stopped'] = m.get('stopped')

# ---- calibration: BASE quantiles of structural fields (no outcome) ----
def q(vals, p):
    v = sorted(x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x)))
    if not v: return None
    i = p * (len(v) - 1); lo = int(i)
    return v[lo] + (i - lo) * (v[min(lo + 1, len(v) - 1)] - v[lo]) if lo + 1 < len(v) else v[lo]

fields = ['n_supply_overhead', 'clean_sky_atr', 'h1n_clean_sky_atr', 'h4n_clean_sky_atr',
          'legpos60', 'legpos90', 'g_box96', 'g_box480', 'dist_demand_atr', 'n_demand_near',
          'h1_pos', 'h4_pos', 'g_ema21_dist', 'g_ema50_dist', 'g_atr_spike',
          'room_above', 'ext_ema', 'pos20']
print("\nBASE quantiles (q10/q25/q50/q75/q80/q90) + missing:")
for f in fields:
    vals = [r.get(f) for r in base]
    miss = sum(1 for v in vals if v is None)
    qs = [q(vals, p) for p in (0.10, 0.25, 0.50, 0.75, 0.80, 0.90)]
    qss = ' '.join('None' if x is None else f'{x:.3f}' for x in qs)
    print(f"  {f:22s} miss={miss:3d}  {qss}")

print("\ncategorical/int distributions on base:")
for f in ['n_supply_overhead', 'n_demand_near', 'in_demand', 'g_v5h', 'h1_trend', 'h4_trend', 'h1n_trend', 'h4n_trend']:
    print(f"  {f}: {Counter(str(r.get(f)) for r in base).most_common(8)}")
