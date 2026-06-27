#!/usr/bin/env python3
"""
_engine_eval_novel.py
Evaluate novel RAW features (from entry_dataset_novel.jsonl) + best existing features,
and combinations. Robust = avgR>base in all 3 years AND n>=30 AND not carried by top-2.
"""
import json, os
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
DS=os.path.join(HERE,'entry_dataset_novel.jsonl')
BASE=0.727

rows=[json.loads(l) for l in open(DS)]

def summ(mask,label):
    sel=[r for r in rows if mask(r)]
    n=len(sel)
    if n==0: return None
    R=[r['R_reclaim'] for r in sel]
    avg=sum(R)/n; wr=100*sum(1 for x in R if x>0)/n
    run=100*sum(1 for x in R if x>=5)/n
    yr={}
    for y in (2024,2025,2026):
        ys=[r['R_reclaim'] for r in sel if r['yr']==y]
        yr[y]=(len(ys),(sum(ys)/len(ys)) if ys else None)
    Rs=sorted(R,reverse=True)
    ex=(sum(Rs[2:])/(n-2)) if n>2 else None
    return dict(label=label,n=n,wr=wr,avgR=avg,run=run,y24=yr[2024],y25=yr[2025],y26=yr[2026],lift=avg-BASE,ex=ex)

def robust(o):
    if o is None or o['n']<30: return False
    for y in ('y24','y25','y26'):
        ny,ay=o[y]
        if ny<8 or ay is None or ay<=BASE: return False
    return o['ex'] is not None and o['ex']>BASE

def pr(o):
    if o is None: print('  (empty)'); return False
    rb=robust(o)
    print('  %-50s n=%4d WR=%4.1f%% avgR=%+.3f run=%4.1f%% | y24=%+.2f(%d) y25=%+.2f(%d) y26=%+.2f(%d) | lift=%+.3f exT2=%+.3f R=%s'%(
        o['label'],o['n'],o['wr'],o['avgR'],o['run'],
        o['y24'][1] or 0,o['y24'][0],o['y25'][1] or 0,o['y25'][0],o['y26'][1] or 0,o['y26'][0],
        o['lift'],o['ex'] or 0,rb))
    return rb

print('=== NOVEL single-feature scans ===')
# binary novels
for f in ['rsi_div','retest_lo','absorb_sell','absorb_sellL','in_demand','sweep2','fast_choch']:
    for v in (1,0):
        pr(summ(lambda r,ff=f,vv=v: r.get(ff)==vv, '%s==%d'%(f,v)))

print('--- numeric novels (quantile thresholds) ---')
res=[]
for f in ['decel_ratio','dist_vbp_atr','since_pivot','dz_dist_atr']:
    vals=[r[f] for r in rows if r.get(f) is not None]
    if not vals: continue
    qs=[np.quantile(vals,q) for q in (0.2,0.35,0.5,0.65,0.8)]
    for thr in qs:
        for op,opn in ((lambda v,t=thr: v>=t,'>='),(lambda v,t=thr: v<=t,'<=')):
            o=summ(lambda r,ff=f,oo=op: r.get(ff) is not None and oo(r[ff]),'%s%s%.3f'%(f,opn,thr))
            if o and o['n']>=30: res.append(o)
res.sort(key=lambda o:o['avgR'],reverse=True)
for o in res[:12]: pr(o)

print()
print('=== COMBINATIONS: best existing core (macro_drop_atr<=3.6 / disp4<=-0.6) x novels ===')
core_drop = lambda r: r['macro_drop_atr']<=3.606
core_disp = lambda r: r['disp4_atr']<=-0.649
combos=[
 ('drop<=3.6 & rsi_div', lambda r: core_drop(r) and r.get('rsi_div')==1),
 ('drop<=3.6 & retest_lo', lambda r: core_drop(r) and r.get('retest_lo')==1),
 ('drop<=3.6 & absorb_sell', lambda r: core_drop(r) and r.get('absorb_sell')==1),
 ('drop<=3.6 & sweep2', lambda r: core_drop(r) and r.get('sweep2')==1),
 ('drop<=3.6 & fast_choch', lambda r: core_drop(r) and r.get('fast_choch')==1),
 ('drop<=3.6 & in_demand', lambda r: core_drop(r) and r.get('in_demand')==1),
 ('drop<=3.6 & decel<0.7', lambda r: core_drop(r) and r.get('decel_ratio',9)<0.7),
 ('drop<=3.6 & dist_vbp<=-0.5', lambda r: core_drop(r) and r.get('dist_vbp_atr',9)<=-0.5),
 ('disp4<=-0.65 & rsi_div', lambda r: core_disp(r) and r.get('rsi_div')==1),
 ('disp4<=-0.65 & retest_lo', lambda r: core_disp(r) and r.get('retest_lo')==1),
 ('disp4<=-0.65 & fast_choch', lambda r: core_disp(r) and r.get('fast_choch')==1),
 ('disp4<=-0.65 & sweep2', lambda r: core_disp(r) and r.get('sweep2')==1),
 ('disp4<=-0.65 & in_demand', lambda r: core_disp(r) and r.get('in_demand')==1),
 ('disp4<=-0.65 & dist_vbp<=-0.5', lambda r: core_disp(r) and r.get('dist_vbp_atr',9)<=-0.5),
]
for lab,m in combos: pr(summ(m,lab))
