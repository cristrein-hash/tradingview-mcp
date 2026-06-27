#!/usr/bin/env python3
"""DA feasibility probe for proposed feature 'sweep_reclaim_signature'.

Question: can we causally compute, from RAW 15M, a sweep+reclaim of the
nearest EQL (LONG) / EQH (SHORT) SMC level before each NAS-in-zone candidate?

Checks: (1) timestamp-unit consistency between candidates.nas_t and
smc_events.t / series.t; (2) how many candidates have a matching EQ level
within W bars; (3) of those, how many show sweep+reclaim (<=2 bars).
Saved (not inline) per output-orphan guard.
"""
import json, csv, glob

ROOT = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = list(csv.DictReader(open(f'{ROOT}/candidates_annotated.csv')))

# --- timestamp sanity ---
cand_blocks = set(r['block'] for r in rows)
d0 = json.load(open(glob.glob(f'{ROOT}/primitives/*.json')[0]))
print('sample cand block :', next(iter(cand_blocks)))
print('sample prim block :', d0['block'])
print('sample nas_t      :', rows[0]['nas_t'])
print('sample series t    :', d0['series'][0]['t'], '..', d0['series'][-1]['t'])
print('sample smc t       :', d0['smc_events'][0]['t'])

# block keys: candidates use the .jsonl.gz suffix, primitives use 'block' too?
def norm(k):
    # normalize to date-range core, e.g. '2024-08-25_to_2024-11-25'
    k = k.replace('XAUUSD_15m_replay_', '').replace('.jsonl.gz', '')
    k = k.replace('_rerun_customOBbaseline', '')
    return k

prim = {}
for f in glob.glob(f'{ROOT}/primitives/*.json'):
    d = json.load(open(f))
    prim[norm(d['block'])] = d
cand_norm = set(norm(b) for b in cand_blocks)
print('prim keys match cand keys?', cand_norm.issubset(set(prim.keys())))
print('cand norm sample:', sorted(cand_norm)[:3])
print('prim norm sample:', sorted(prim.keys())[:3])

BAR = 900  # 15m in seconds
W = 96     # 1 day lookback
EPS = 0.0003

# detect timestamp scale: are series timestamps seconds or ms?
span = d0['series'][-1]['t'] - d0['series'][0]['t']
print('series span/nbars (sec/bar est):', span / max(1, len(d0['series']) - 1))

have = 0
sweep = 0
reclaim_lags = []
for r in rows:
    d = prim.get(norm(r['block']))
    if not d:
        continue
    eq = sorted((e['t'], e['text'], e['price']) for e in d['smc_events']
                if e['text'] in ('EQH', 'EQL'))
    ser = {b['t']: b for b in d['series']}
    ts = sorted(ser.keys())
    nas_t = int(r['nas_t'])
    side = r['dir']
    want = 'EQL' if side == 'LONG' else 'EQH'
    lo = nas_t - W * BAR
    cand = [e for e in eq if lo <= e[0] <= nas_t and e[1] == want]
    if not cand:
        continue
    have += 1
    lvl = cand[-1][2]
    window = [ser[t] for t in ts if lo <= t <= nas_t]
    for i, b in enumerate(window):
        breached = (side == 'LONG' and b['l'] < lvl * (1 - EPS)) or \
                   (side == 'SHORT' and b['h'] > lvl * (1 + EPS))
        if breached:
            for k in range(0, 3):
                if i + k < len(window):
                    c = window[i + k]['c']
                    if (side == 'LONG' and c > lvl) or (side == 'SHORT' and c < lvl):
                        sweep += 1
                        reclaim_lags.append(k)
                        break
            break

print(f'\ncandidates total            : {len(rows)}')
print(f'with matching EQ in {W} bars : {have}')
print(f'  of those, sweep+reclaim   : {sweep}')
if reclaim_lags:
    from collections import Counter
    print('  reclaim_lag dist          :', dict(Counter(reclaim_lags)))
