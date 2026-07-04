#!/usr/bin/env python3
"""Lab B r2 — MARKET STRUCTURE AGENT — Step 2: FROZEN LENSES + structural map.

LOOK LEDGER (declared):
  Look0 (step1): aggregate baseline only. No structural-outcome cross-tab seen.
  FREEZE POINT: the five lens predicates below were written BEFORE running this
    script, i.e. before ANY structural-outcome look on the base. Thresholds are
    quantiles of the BASE distribution (step1 calibration output) — declared as
    calibration per prior P3 (universe quantiles are vacuous on base).
  Look1 (this script, part B): structural bucket map WR/avgNET/sumNET/runners by
    base-quintile of each field. EXPLORATORY — anything derived from it is
    CALIBRATION status, not a frozen test.
  Look2 (this script, part A): evaluation of frozen lenses L1..L5.

FROZEN PREDICATES (thresholds = base quantiles, step1):
  L1_LID_LOCAL   : clean_sky_atr <= 0.08 (q25) AND n_supply_overhead >= 16 (q50)
  L2_LID_MTF     : h1n_clean_sky_atr < 99 AND h1n_clean_sky_atr <= 0.39 (q25 raw incl. sentinel)
                   AND clean_sky_atr <= 0.23 (q50)
  L3_TOPLEG_EXT  : legpos90 >= 0.746 (q80) AND g_ema50_dist >= 2.415 (q75)
  L4_CEIL480_LID : g_box480 >= 0.933 (q75) AND clean_sky_atr <= 0.23 (q50)
  L5_NOROOM_LID  : room_above <= base-q25(room_above) AND clean_sky_atr <= 0.23 (q50)
                   (room_above only in convergence — prior #2)

Frozen evaluation criteria:
  SKIP-grade  : flagged sumNET < 0 AND flagged runners(g_R>=3) <= 3 of 53, robust per-year sign.
  REVIEW/size : flagged avgNET clearly below rest but sumNET > 0 or runners material.
  Else        : context-class only (no action).
Runner preservation is first-class: report runner retention of base-minus-flagged.
"""
import json, math
from collections import defaultdict

DIR = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{DIR}/results/lab_g_candidates.jsonl')]
base = [r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR']
mat = {m['t']: m for m in json.load(open(f'{DIR}/base4_maturation_features.json'))}
for r in base:
    m = mat.get(r['cj_t'], {})
    r['room_above'] = m.get('room_above'); r['ext_ema'] = m.get('ext_ema')
    r['pos20'] = m.get('pos20'); r['mfe'] = m.get('mfe')
    r['net'] = r['g_R'] - 0.80 / r['g_risk']
    r['runner'] = 1 if r['g_R'] >= 3 else 0
base.sort(key=lambda r: r['t'])
N = len(base); TOT = sum(r['net'] for r in base); RUN = sum(r['runner'] for r in base)

def q(vals, p):
    v = sorted(x for x in vals if x is not None)
    i = p * (len(v) - 1); lo = int(i)
    return v[lo] + (i - lo) * (v[min(lo + 1, len(v) - 1)] - v[lo]) if lo + 1 < len(v) else v[lo]

ROOM_Q25 = q([r['room_above'] for r in base], 0.25)
print(f"base N={N} sumNET={TOT:+.1f} runners={RUN}  room_above q25(base)={ROOM_Q25:.3f} "
      f"(q10={q([r['room_above'] for r in base],0.10):.3f} q50={q([r['room_above'] for r in base],0.50):.3f})")

def stats(sub):
    if not sub: return dict(n=0)
    nets = [r['net'] for r in sub]
    return dict(n=len(sub), wr=100 * sum(1 for x in nets if x > 0) / len(nets),
                avg=sum(nets) / len(nets), s=sum(nets), run=sum(r['runner'] for r in sub))

def dd_stk(sub):
    cum = peak = 0.0; dd = 0.0; stk = cur = 0
    for r in sub:
        cum += r['net']; peak = max(peak, cum); dd = min(dd, cum - peak)
        if r['net'] <= 0: cur += 1; stk = max(stk, cur)
        else: cur = 0
    return dd, stk

LENSES = {
 'L1_LID_LOCAL':  lambda r: r['clean_sky_atr'] <= 0.08 and r['n_supply_overhead'] >= 16,
 'L2_LID_MTF':    lambda r: r['h1n_clean_sky_atr'] < 99 and r['h1n_clean_sky_atr'] <= 0.39 and r['clean_sky_atr'] <= 0.23,
 'L3_TOPLEG_EXT': lambda r: r['legpos90'] >= 0.746 and r['g_ema50_dist'] >= 2.415,
 'L4_CEIL480_LID':lambda r: r['g_box480'] >= 0.933 and r['clean_sky_atr'] <= 0.23,
 'L5_NOROOM_LID': lambda r: r['room_above'] is not None and r['room_above'] <= ROOM_Q25 and r['clean_sky_atr'] <= 0.23,
}

print("\n=== Look2: FROZEN LENSES ===")
print(f"{'lens':16s} {'nF':>4} {'cov%':>5} | flagged: WR avgNET sumNET run | rest: WR avgNET | SKIP-> sumNET DD stk runKeep")
for name, fn in LENSES.items():
    flag = [r for r in base if fn(r)]; rest = [r for r in base if not fn(r)]
    f, s = stats(flag), stats(rest)
    dd, stk = dd_stk(rest)
    print(f"{name:16s} {f['n']:4d} {100*f['n']/N:5.1f} | {f.get('wr',0):4.1f} {f.get('avg',0):+5.2f} {f.get('s',0):+6.1f} {f.get('run',0):3d} "
          f"| {s['wr']:4.1f} {s['avg']:+5.2f} | {s['s']:+6.1f} {dd:5.1f} -{stk} {s['run']}/{RUN}")
    yr = defaultdict(list)
    for r in flag: yr[r['yr']].append(r)
    per = '  '.join(f"{y}:n{len(v)} s{sum(x['net'] for x in v):+.1f}" for y, v in sorted(yr.items()))
    print(f"                 per-year flagged: {per}")

print("\n=== Look1: STRUCTURAL MAP (base quintiles per field; N/WR/avgNET/sumNET/runners) ===")
FIELDS = ['n_supply_overhead', 'clean_sky_atr', 'h1n_clean_sky_atr', 'h4n_clean_sky_atr',
          'legpos60', 'legpos90', 'g_box96', 'g_box480', 'g_ema21_dist', 'g_ema50_dist',
          'h1_pos', 'h4_pos', 'dist_demand_atr', 'n_demand_near', 'room_above', 'ext_ema', 'pos20', 'g_atr_spike']
for f in FIELDS:
    sub = [r for r in base if r.get(f) is not None]
    cuts = [q([r[f] for r in sub], p) for p in (0.2, 0.4, 0.6, 0.8)]
    buckets = [[] for _ in range(5)]
    for r in sub:
        b = sum(1 for c in cuts if r[f] > c)
        buckets[b].append(r)
    line = []
    for i, bk in enumerate(buckets):
        st = stats(bk)
        line.append(f"Q{i+1}[n{st['n']:3d} wr{st.get('wr',0):3.0f} av{st.get('avg',0):+4.2f} s{st.get('s',0):+6.1f} r{st.get('run',0):2d}]")
    print(f"{f:20s} cuts={['%.2f'%c for c in cuts]}\n  {' '.join(line)}")
