#!/usr/bin/env python3
"""LAB B r2 — ROUND 4 (final): classificação completa das 36 loss-runs por assinatura ex-ante
(ceiling-CONV2 vs anti-estrutura conv==0 vs temporal-puro) + por-ano do conv==0 + overlap classes.
Looks L#22..L#24."""
import json, statistics
from collections import Counter, defaultdict

SB = 0.80
D = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{D}/results/lab_g_candidates.jsonl')]
base = sorted([r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR'],
              key=lambda r: r['t'])
for r in base: r['net'] = r['g_R'] - SB / r['g_risk']

def q(vals, p):
    vs = sorted(v for v in vals if v is not None)
    return vs[min(len(vs) - 1, int(p * len(vs)))]

Q = dict(supply_q75=q([r['n_supply_overhead'] for r in base], .75),
         sky_q25=q([r['clean_sky_atr'] for r in base], .25),
         leg60_q75=q([r['legpos60'] for r in base], .75),
         leg90_q75=q([r['legpos90'] for r in base], .75),
         box96_q80=q([r['g_box96'] for r in base], .80),
         box480_q80=q([r['g_box480'] for r in base], .80),
         h1sky_q25=q([r['h1n_clean_sky_atr'] for r in base], .25),
         h4sky_q25=q([r['h4n_clean_sky_atr'] for r in base], .25),
         e21_q75=q([r['g_ema21_dist'] for r in base], .75),
         e50_q75=q([r['g_ema50_dist'] for r in base], .75),
         e50_q50=q([r['g_ema50_dist'] for r in base], .50),
         h1pos_q50=q([r['h1_pos'] for r in base], .50))
for r in base:
    L = dict(A=r['n_supply_overhead'] >= Q['supply_q75'],
             B=r['clean_sky_atr'] <= Q['sky_q25'],
             C=r['legpos60'] >= Q['leg60_q75'] and r['legpos90'] >= Q['leg90_q75'],
             D=r['g_box96'] >= Q['box96_q80'] and r['g_box480'] >= Q['box480_q80'],
             E=(r['h1n_clean_sky_atr'] is not None and r['h1n_clean_sky_atr'] <= Q['h1sky_q25']
                and r['h4n_clean_sky_atr'] is not None and r['h4n_clean_sky_atr'] <= Q['h4sky_q25']),
             F=r['g_ema21_dist'] >= Q['e21_q75'] and r['g_ema50_dist'] >= Q['e50_q75'])
    r['conv'] = sum(L.values())
    r['deadmid'] = (r['conv'] == 0 and r['g_ema50_dist'] <= Q['e50_q50']
                    and r['h1_pos'] is not None and r['h1_pos'] <= Q['h1pos_q50'])

runs, cur = [], []
for i, r in enumerate(base):
    if r['net'] < 0: cur.append(i)
    else:
        if len(cur) >= 3: runs.append(cur)
        cur = []
if len(cur) >= 3: runs.append(cur)

print('== L#22 TAXONOMIA das 36 loss-runs (>=2/3 membros na classe) ==')
tax = Counter()
loss_by_tax = Counter()
for run in runs:
    mem = [base[i] for i in run]
    f_ceil = sum(1 for r in mem if r['conv'] >= 2) / len(mem)
    f_anti = sum(1 for r in mem if r['conv'] == 0) / len(mem)
    lossR = sum(r['net'] for r in mem)
    kind = ('CEILING' if f_ceil >= 2/3 else
            'ANTI_STRUCT' if f_anti >= 2/3 else
            'MIXED/TEMPORAL')
    tax[kind] += 1
    loss_by_tax[kind] += lossR
print('  runs:', dict(tax))
print('  dor NET por taxonomia:', {k: round(v, 1) for k, v in loss_by_tax.items()})
tot = sum(loss_by_tax.values())
print(f'  dor total nas runs: {tot:+.1f} · % com assinatura ex-ante (CEILING+ANTI): '
      f'{100*(loss_by_tax["CEILING"]+loss_by_tax["ANTI_STRUCT"])/tot:.0f}%')

print('\n== L#23 conv==0 por-ano (cohort) ==')
yr = defaultdict(lambda: [0, 0.0, 0])
for r in base:
    if r['conv'] == 0:
        yr[r['yr']][0] += 1; yr[r['yr']][1] += r['net']
        if r['g_R'] >= 3: yr[r['yr']][2] += 1
print('  ano:(N, sumNET, runners) =', {k: (v[0], round(v[1], 1), v[2]) for k, v in sorted(yr.items())})

print('\n== L#24 overlap DEADMID x membros das runs quebradas + regime ==')
dm = [r for r in base if r['deadmid']]
reg = Counter(r['g_v5h'] for r in dm)
print(f'  DEADMID N={len(dm)} regimes={dict(reg)}')
# streak sob SKIP deadmid
net_skip = [r['net'] for r in base if not r['deadmid']]
stk = wst = 0
for x in net_skip:
    if x < 0: stk += 1; wst = max(wst, stk)
    else: stk = 0
print(f'  worst streak sob SKIP DEADMID: {wst} (baseline 8)')
net_skip0 = [r['net'] for r in base if r['conv'] != 0]
stk = wst = 0
for x in net_skip0:
    if x < 0: stk += 1; wst = max(wst, stk)
    else: stk = 0
print(f'  worst streak sob SKIP conv==0: {wst} (baseline 8)')
print('\nLOOKS LEDGER: total acumulado 24.')
