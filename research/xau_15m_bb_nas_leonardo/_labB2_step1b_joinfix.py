#!/usr/bin/env python3
"""Lab B r2 — Step 1b: fix maturation join + runner definition check (no structural-outcome look)."""
import json

DIR = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{DIR}/results/lab_g_candidates.jsonl')]
base = [r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR']
mat = json.load(open(f'{DIR}/base4_maturation_features.json'))

print("cand t sample:", [base[i]['t'] for i in range(3)], type(base[0]['t']))
print("mat  t sample:", [mat[i]['t'] for i in range(3)], type(mat[0]['t']))
print("mat gid sample:", [mat[i]['gid'] for i in range(3)])
print("cand block sample:", [base[i].get('block') for i in range(3)])
print("mat block sample:", [mat[i].get('block') for i in range(3)])
print("cand cj_t sample:", [base[i].get('cj_t') for i in range(3)])
print("mat cj sample:", [mat[i].get('cj') for i in range(3)])

# try joins
ct = {r['t'] for r in base}
print("join on t:", len(ct & {m['t'] for m in mat}))
print("join on cand.cj_t = mat.t:", len({r.get('cj_t') for r in base} & {m['t'] for m in mat}))
print("join on cand.t = mat.cj:", len(ct & {m.get('cj') for m in mat}))
print("join on cand.g_entry vs mat.entry (values):", len({r.get('g_entry') for r in base} & {m.get('entry') for m in mat}))

# runner def check: 53
for expr, fn in [("g_R>=3", lambda r: r['g_R'] >= 3), ("g_R>=4", lambda r: r['g_R'] >= 4),
                 ("g_R>=5", lambda r: r['g_R'] >= 5), ("g_R>3", lambda r: r['g_R'] > 3),
                 ("net>=2.5", lambda r: (r['g_R'] - .8 / r['g_risk']) >= 2.5)]:
    print(expr, sum(1 for r in base if fn(r)))
