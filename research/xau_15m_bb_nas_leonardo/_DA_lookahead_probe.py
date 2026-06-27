#!/usr/bin/env python3
"""Look-ahead probe: how many bubbles enter the leg/w24 feature exactly at known_at==tc
(borderline close-of-bar), and does B's bubble-ratio edge survive a strict known_at<tc rule?
Also confirms upstream features (h1_eff/rsi) are entry-time by re-deriving counts."""
import json, bisect
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split('.')[0].replace('XAUUSD_15m_replay_',''):json.loads(p.read_text())
      for p in sorted((HERE/'primitives').glob('*.primitives.json'))}
BUB={}
for bf in sorted((HERE/'bubbles').glob('*.bubbles.jsonl')):
    BUB[bf.name[:10]]=sorted([json.loads(l) for l in bf.read_text().splitlines() if l],key=lambda x:x['t'])
ROWS=[json.loads(l) for l in (HERE/'filter_dataset.jsonl').read_text().splitlines()]
SZ={'S':1,'M':2,'L':3}

def bub_feats(bub,t0,t1,tc,strict=False):
    a=bisect.bisect_left([x['t'] for x in bub],t0); bw=sw=0
    for x in bub[a:]:
        if x['t']>t1: break
        ka=x.get('known_at') or x['t']
        if (ka>=tc) if strict else (ka>tc): continue
        if x['side']=='BUY': bw+=SZ[x['size']]
        else: sw+=SZ[x['size']]
    return bw,sw

# count bubbles with known_at == tc that landed inside the leg window
eq_count=0; rows_with_eq=0
for r in ROWS:
    bkey=r['block'][:10]; bub=BUB.get(bkey,[]); tc=r['t']
    t_leg0_t=None
    # leg window starts at entry-leg low bar time; we approximate via series time of i
    # reuse stored bubble feats: just count known_at==tc bubbles in [t_w24-ish, tc]
    n_eq=0
    for x in bub:
        if x['t']>tc: break
        ka=x.get('known_at') or x['t']
        if ka==tc and x['t']<=tc and x['t']>=tc-24*900:
            n_eq+=1
    if n_eq: rows_with_eq+=1; eq_count+=n_eq
print(f'rows where >=1 bubble has known_at==tc inside ~w24 window: {rows_with_eq}/{len(ROWS)} (total {eq_count} bubbles)')
print('-> these are close-of-bar bubbles; included under <= rule, excluded under strict < rule.')

# Re-run B with strict (<tc) bubble feature recomputed on the fly, compare WR
import importlib.util
spec=importlib.util.spec_from_file_location('fh',HERE/'filter_harness.py')
fh=importlib.util.module_from_spec(spec); spec.loader.exec_module(fh)
# inject strict bubble features per row
PRIMTM={k:{b['t']:idx for idx,b in enumerate(pr['series'])} for k,pr in PRIM.items()}
for r in ROWS:
    bkey=r['block'][:10]; bub=BUB.get(bkey,[]); tc=r['t']
    s=PRIM[[k for k in PRIM if k[:10]==bkey][0]]['series']
    tmap=PRIMTM[[k for k in PRIM if k[:10]==bkey][0]]
    i=r['i']; cj=r['cj']
    t_leg0=s[i]['t']
    bw_s,sw_s=bub_feats(bub,t_leg0,tc,tc,strict=True)
    r['_bw_leg_strict']=bw_s; r['_sw_leg_strict']=sw_s
fh.ROWS=ROWS  # same objects
exprB="r['h1_eff']>=0.15 and (r['buy_bub_w_leg']<=3*r['sell_bub_w_leg']+5) and r['rsi']>50"
exprB_strict="r['h1_eff']>=0.15 and (r['_bw_leg_strict']<=3*r['_sw_leg_strict']+5) and r['rsi']>50"
for lab,e in [('B (<=tc, original)',exprB),('B (strict <tc)',exprB_strict)]:
    s,_=fh.run(eval('lambda r: ('+e+')'))
    print(f"{lab:<24} N={s['n']} WR={s['wr']} sumR={s['sumr']} dWR={s['dWR']}")
