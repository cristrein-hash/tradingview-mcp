#!/usr/bin/env python3
"""Loser-cut search for E5_demand target.
Target members: macro_drop_atr<=3.6 AND in_demand==1. Outcome=R_reclaim.
winner=outcome>0, loser=outcome<=0.
Goal: cut max losers keeping >=90% winners, minimize max-losing-streak.
Forbidden filter features: R_reclaim,R_8atr,near_M8,held8,runner,reclaim_idx,low_idx (look-ahead)
Rule-defining (no reuse, circular): macro_drop_atr, in_demand.
"""
import json, itertools

ROWS=[json.loads(l) for l in open('entry_dataset.jsonl')]
MEM=[r for r in ROWS if r.get('macro_drop_atr',1e9)<=3.6 and r.get('in_demand')==1]
MEM.sort(key=lambda r:r['low_t'])

def is_w(r): return r['R_reclaim']>0
def is_l(r): return r['R_reclaim']<=0

def maxstreak(rows):
    m=c=0
    for r in rows:
        if is_l(r): c+=1; m=max(m,c)
        else: c=0
    return m

def stats(rows):
    n=len(rows); w=sum(is_w(r) for r in rows)
    wr=w/n if n else 0
    return n,w,n-w,wr,maxstreak(rows)

# candidate causal filter features (orthogonal; exclude forbidden + rule-defining)
FORBID={'R_reclaim','R_8atr','near_M8','held8','runner','reclaim_idx','low_idx',
        'macro_drop_atr','in_demand'}
CAND=['rsi','rsi_low','rsi_head','dist_ema_atr','ema_slope_atr','macro_retr',
      'sweep_depth_atr','reclaim_speed','disp4_atr','disp8_atr','up_closes8',
      'range_exp','leg_ext','room_atr','low_wick','low_closepos','atr_regime',
      'hour','killzone','vol_low_vs_med','sell_pol','in_supply']
BIN=['macro_bull','macro_bear','nas_long_16','nas_short_16','nas_long_48',
     'nas_last_long','smc_choch','smc_bos','sell_S','sell_M','sell_L',
     'buy_S','buy_M','buy_L','sell_w','buy_w','killzone','in_supply']

n0,w0,l0,wr0,ms0=stats(MEM)
print(f'BEFORE n={n0} W={w0} L={l0} WR={wr0:.3f} maxstreak={ms0}')

# Build single-feature threshold predicates (keep if pass). We KEEP rows passing, cut rows failing.
import numpy as np
def quantiles(vals):
    vals=sorted(set(vals))
    if len(vals)<=12: return vals
    return list(np.quantile(vals,[i/12 for i in range(1,12)]))

preds=[]  # (desc, keepfn)
for f in CAND:
    vals=[r[f] for r in MEM if f in r and r[f] is not None]
    if not vals: continue
    for t in quantiles(vals):
        preds.append((f'{f}>={t:.4g}', (lambda r,f=f,t=t: r.get(f,-1e9)>=t)))
        preds.append((f'{f}<={t:.4g}', (lambda r,f=f,t=t: r.get(f, 1e9)<=t)))
for f in BIN:
    if any(f in r for r in MEM):
        preds.append((f'{f}==0', (lambda r,f=f: r.get(f,0)==0)))
        preds.append((f'{f}==1', (lambda r,f=f: r.get(f,0)==1)))

WTARGET=0.90*w0

# evaluate single preds
def eval_keep(keepfn):
    kept=[r for r in MEM if keepfn(r)]
    return kept

results=[]
for desc,fn in preds:
    kept=eval_keep(fn)
    n,w,l,wr,ms=stats(kept)
    if w>=WTARGET and l<l0:  # keep >=90% winners, cut some losers
        results.append((desc,[fn],n,w,l,wr,ms))

# combos of 2 and 3 (AND of keep preds)
plist=preds
for combo in itertools.combinations(range(len(plist)),2):
    fns=[plist[i][1] for i in combo]
    keepfn=lambda r,fns=fns: all(fn(r) for fn in fns)
    kept=eval_keep(keepfn)
    n,w,l,wr,ms=stats(kept)
    if w>=WTARGET and l<l0:
        desc=' AND '.join(plist[i][0] for i in combo)
        results.append((desc,fns,n,w,l,wr,ms))

# rank: maximize losers cut, then minimize streak, then maximize WR
results.sort(key=lambda x:(-(l0-x[4]), x[6], -x[5]))

print('\nTOP single+2combo candidates (W>=%.1f):'%WTARGET)
for desc,fns,n,w,l,wr,ms in results[:15]:
    print(f'  cut_L={l0-l:3d} keepW%={w/w0*100:5.1f} streak={ms} | n={n} WR={wr:.3f} | {desc}')

# 3-combos built greedily from best 2-combos to limit blowup
best2=[r for r in results if len(r[1])==2][:40]
res3=[]
for desc2,fns2,_,_,_,_,_ in best2:
    for desc1,fn1 in preds:
        fns=fns2+[fn1]
        keepfn=lambda r,fns=fns: all(fn(r) for fn in fns)
        kept=eval_keep(keepfn)
        n,w,l,wr,ms=stats(kept)
        if w>=WTARGET and l<l0:
            res3.append((desc2+' AND '+desc1,fns,n,w,l,wr,ms))
res3.sort(key=lambda x:(-(l0-x[4]), x[6], -x[5]))
print('\nTOP 3-combos:')
for desc,fns,n,w,l,wr,ms in res3[:10]:
    print(f'  cut_L={l0-l:3d} keepW%={w/w0*100:5.1f} streak={ms} | n={n} WR={wr:.3f} | {desc}')

# --- DEVIL'S ADVOCATE rejection of combo winners ---
# The auto-ranked combos top-out via degenerate near-vacuous thresholds
# (sweep_depth_atr>=-2.996, disp8_atr>=-1.282 are ~always-true) plus a
# sell_pol slice whose apparent gain concentrates in 2025 and LEAVES y2026
# at WR 0.39. Those are selection-bias artifacts, not causal cuts.
# We therefore SELECT the single, year-stable, causal predicate.
import collections
def report(desc, keepfn):
    kept=eval_keep(keepfn)
    n,w,l,wr,ms=stats(kept)
    yw=collections.defaultdict(lambda:[0,0])
    for r in kept:
        yw[r['yr']][0]+=1; yw[r['yr']][1]+=is_w(r)
    ys={y:(yw[y][1]/yw[y][0] if yw[y][0] else 0) for y in (2024,2025,2026)}
    print('\n=== CHOSEN FILTER ===')
    print('desc:',desc)
    print(f'n_after={n} WR_after={wr:.4f} streak_after={ms}')
    print(f'winners_kept_pct={w/w0*100:.2f} losers_cut_pct={(l0-l)/l0*100:.2f}')
    for y in (2024,2025,2026):
        print(f'  y{y}: n={yw[y][0]} WR={ys[y]:.4f}')
    return n,wr,ms,w/w0*100,(l0-l)/l0*100,ys

# sell_w==0 : reclaim bar has NO weak SELL-bubble polarity present.
# Causal: a lingering weak SELL bubble at the demand reclaim = residual
# supply pressure / unfinished distribution => reclaim more likely to fail.
report('sell_w==0  (no weak SELL-bubble polarity at reclaim bar)',
       lambda r: r.get('sell_w',0)==0)
