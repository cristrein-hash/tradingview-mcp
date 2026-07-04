#!/usr/bin/env python3
"""Lab B r2 — Step 3: characterize Look1-derived cells (CALIBRATION status, declared) + streak anatomy.

LOOK LEDGER: Look3. Candidates derived from Look1 map (NOT frozen tests):
  C1_H4MIDLID : h4n_clean_sky_atr in [0.38, 0.92)  — only negative cell in map (s=-3.0, n87)
                -> robustness: boundary sweep grid, per-year, DD/streak impact of SKIP.
  C2_EARLYLEG : legpos60 <= 0.25 AND g_ema21_dist <= 0.16 — bottom-of-structure convergence
                (both weak-WR cells; check if it taxes runners — ext_emaQ1 is runner-rich).
  CLASS_QUICKPOP : room_above <= 1.11 (base q20) — high WR / runner-poor context class (F4 route).
  CLASS_KNIFE    : g_ema21_dist <= 0.16 (base q20) — low WR / runner-rich context class (F4 route).
Streak anatomy: structural composition of all loss-runs >=4 vs base mean (z-scores).
"""
import json, math
from collections import defaultdict

DIR = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{DIR}/results/lab_g_candidates.jsonl')]
base = [r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR']
mat = {m['t']: m for m in json.load(open(f'{DIR}/base4_maturation_features.json'))}
for r in base:
    m = mat.get(r['cj_t'], {})
    r['room_above'] = m.get('room_above')
    r['net'] = r['g_R'] - 0.80 / r['g_risk']
    r['runner'] = 1 if r['g_R'] >= 3 else 0
base.sort(key=lambda r: r['t'])
N = len(base); RUN = sum(r['runner'] for r in base)

def stats(sub):
    if not sub: return dict(n=0, wr=0, avg=0, s=0, run=0)
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

print("=== C1_H4MIDLID boundary sweep (h4n_clean_sky_atr in [lo,hi)) ===")
print("lo,hi -> nF WR avgNET sumNET run | SKIP-> sum DD stk runKeep")
for lo in (0.30, 0.38, 0.45):
    for hi in (0.80, 0.92, 1.10):
        fl = [r for r in base if lo <= r['h4n_clean_sky_atr'] < hi]
        rest = [r for r in base if not (lo <= r['h4n_clean_sky_atr'] < hi)]
        f, s = stats(fl), stats(rest); dd, stk = dd_stk(rest)
        print(f"[{lo:.2f},{hi:.2f}) n{f['n']:3d} wr{f['wr']:3.0f} av{f['avg']:+5.2f} s{f['s']:+6.1f} r{f['run']:2d} | {s['s']:+6.1f} {dd:5.1f} -{stk} {s['run']}/{RUN}")
fl = [r for r in base if 0.38 <= r['h4n_clean_sky_atr'] < 0.92]
yr = defaultdict(list)
for r in fl: yr[r['yr']].append(r)
print("C1 per-year:", {y: f"n{len(v)} s{sum(x['net'] for x in v):+.1f} r{sum(x['runner'] for x in v)}" for y, v in sorted(yr.items())})

print("\n=== C2_EARLYLEG convergence ===")
for name, fn in [
    ('legpos60<=0.25 alone', lambda r: r['legpos60'] <= 0.25),
    ('ema21<=0.16 alone   ', lambda r: r['g_ema21_dist'] <= 0.16),
    ('C2 AND              ', lambda r: r['legpos60'] <= 0.25 and r['g_ema21_dist'] <= 0.16),
    ('legpos90<=0.34 alone', lambda r: r['legpos90'] <= 0.34),
    ('C2b lp90 AND ema21  ', lambda r: r['legpos90'] <= 0.34 and r['g_ema21_dist'] <= 0.16),
]:
    fl = [r for r in base if fn(r)]; rest = [r for r in base if not fn(r)]
    f, s = stats(fl), stats(rest); dd, stk = dd_stk(rest)
    print(f"{name} n{f['n']:3d} wr{f['wr']:3.0f} av{f['avg']:+5.2f} s{f['s']:+6.1f} r{f['run']:2d} | SKIP-> {s['s']:+6.1f} {dd:5.1f} -{stk} {s['run']}/{RUN}")

print("\n=== CONTEXT CLASSES (no skip; route to F4/management) ===")
for name, fn in [
    ('QUICKPOP room<=1.11', lambda r: r['room_above'] is not None and r['room_above'] <= 1.11),
    ('KNIFE ema21<=0.16  ', lambda r: r['g_ema21_dist'] <= 0.16),
    ('OVERLAP both       ', lambda r: r['room_above'] is not None and r['room_above'] <= 1.11 and r['g_ema21_dist'] <= 0.16),
]:
    fl = [r for r in base if fn(r)]
    f = stats(fl)
    gr = [r['g_R'] for r in fl]
    med = sorted(gr)[len(gr)//2] if gr else 0
    print(f"{name} n{f['n']:3d} wr{f['wr']:3.0f} av{f['avg']:+5.2f} s{f['s']:+6.1f} r{f['run']:2d} medR{med:+.2f}")

print("\n=== STREAK ANATOMY: loss-runs >=4, structural z-profile vs base ===")
FIELDS = ['n_supply_overhead','clean_sky_atr','h4n_clean_sky_atr','legpos60','legpos90',
          'g_box96','g_box480','g_ema21_dist','g_ema50_dist','h1_pos','h4_pos','room_above','g_atr_spike']
mu, sd = {}, {}
for f in FIELDS:
    vals = [r[f] for r in base if r.get(f) is not None and r[f] != 99]
    mu[f] = sum(vals)/len(vals)
    sd[f] = (sum((v-mu[f])**2 for v in vals)/len(vals))**0.5
runs, cur = [], []
for r in base:
    if r['net'] <= 0: cur.append(r)
    else:
        if len(cur) >= 4: runs.append(cur)
        cur = []
if len(cur) >= 4: runs.append(cur)
members = [r for run in runs for r in run]
print(f"loss-runs>=4: {len(runs)} runs, {len(members)} members; dates: {[ (run[0]['block'], len(run)) for run in runs ]}")
print("z-scores of members vs base (|z|>0.3 marked):")
for f in FIELDS:
    vals = [r[f] for r in members if r.get(f) is not None and r[f] != 99]
    if not vals or sd[f] == 0: continue
    z = (sum(vals)/len(vals) - mu[f]) / sd[f]
    mark = ' <<<' if abs(z) > 0.3 else ''
    print(f"  {f:20s} z={z:+.2f}{mark}")
# how many streak members carry C1 flag?
c1 = sum(1 for r in members if 0.38 <= r['h4n_clean_sky_atr'] < 0.92)
print(f"streak members flagged C1_H4MIDLID: {c1}/{len(members)}")
# 2-week clustering of members
wk = defaultdict(int)
for r in members: wk[r['g_week']] += 1
print("streak members per g_week:", dict(sorted(wk.items())))
