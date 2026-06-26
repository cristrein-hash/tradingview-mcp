#!/usr/bin/env python3
"""Loser-cut filter search for target E4_bullbos (macro_bull==1 AND smc_bos==1).
Outcome = R_reclaim. winner = >0, loser = <=0.
Filters must be ORTHOGONAL (not macro_bull / smc_bos), causal/pre-entry, no look-ahead.
"""
import json, itertools

ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
MEM = [r for r in ROWS if r.get('macro_bull') == 1 and r.get('smc_bos') == 1]
MEM.sort(key=lambda r: r['low_t'])

def is_win(r): return r['R_reclaim'] > 0

def maxstreak(rows):
    """max consecutive losers, rows already sorted by low_t"""
    best = cur = 0
    for r in rows:
        if not is_win(r):
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best

def stats(rows):
    n = len(rows); w = sum(is_win(r) for r in rows)
    wr = w/n if n else 0
    return n, w, n-w, round(wr*100,1), maxstreak(rows)

# ---- BASELINE ----
n0,w0,l0,wr0,ms0 = stats(MEM)
print(f"BEFORE: n={n0} winners={w0} losers={l0} WR={wr0}% maxstreak={ms0}")

# Forbidden (result/target) and rule-defining features
FORBID = {'R_reclaim','R_8atr','near_M8','held8','runner','reclaim_idx','low_idx',
          'macro_bull','smc_bos','low_t','yr','block'}

# Candidate causal numeric features
NUMF = ['rsi','rsi_low','rsi_head','dist_ema_atr','ema_slope_atr','macro_drop_atr',
        'macro_retr','sweep_depth_atr','reclaim_speed','disp4_atr','disp8_atr',
        'up_closes8','range_exp','leg_ext','room_atr','low_wick','low_closepos',
        'atr_regime','hour','vol_low_vs_med','sell_pol']
BINF = ['macro_bear','killzone','nas_long_16','nas_short_16','nas_long_48','nas_last_long',
        'smc_choch','sell_S','sell_M','sell_L','buy_S','buy_M','buy_L','sell_w','buy_w',
        'in_demand','in_supply']

# univariate separation: for each numeric feature, test threshold conditions
import statistics
W = [r for r in MEM if is_win(r)]
L = [r for r in MEM if not is_win(r)]
print("\n--- univariate winner vs loser means ---")
seps=[]
for f in NUMF:
    wv=[r[f] for r in MEM if is_win(r) and r.get(f) is not None]
    lv=[r[f] for r in MEM if not is_win(r) and r.get(f) is not None]
    if len(wv)<5 or len(lv)<5: continue
    mw,ml=statistics.mean(wv),statistics.mean(lv)
    sd=statistics.pstdev([r[f] for r in MEM if r.get(f) is not None]) or 1
    seps.append((abs(mw-ml)/sd, f, round(mw,3), round(ml,3)))
for d,f,mw,ml in sorted(seps,reverse=True):
    print(f"  {f:16s} win={mw:8} loss={ml:8} sep={d:.3f}")

# binary feature win-rates
print("\n--- binary feature WR (when ==1) ---")
for f in BINF:
    on=[r for r in MEM if r.get(f)==1]
    if len(on)<8: continue
    wr=sum(is_win(r) for r in on)/len(on)*100
    print(f"  {f:16s} n={len(on):3d} WR(on)={wr:.1f}%")

# ---- candidate single-feature threshold filters (KEEP condition) ----
# Build a library of keep-conditions, evaluate loser-cut performance
def make_keep_ge(f,t): return (f"{f}>={t}", lambda r,f=f,t=t: r.get(f) is not None and r[f]>=t)
def make_keep_le(f,t): return (f"{f}<={t}", lambda r,f=f,t=t: r.get(f) is not None and r[f]<=t)
def make_keep_eq0(f): return (f"{f}==0", lambda r,f=f: r.get(f)==0)
def make_keep_eq1(f): return (f"{f}==1", lambda r,f=f: r.get(f)==1)

conds=[]
import numpy as np
for f in NUMF:
    vals=sorted(set(r[f] for r in MEM if r.get(f) is not None))
    if len(vals)<4: continue
    qs=np.quantile([r[f] for r in MEM if r.get(f) is not None],[.1,.2,.25,.3,.4,.5,.6,.7,.75,.8,.9])
    for t in sorted(set(round(float(q),3) for q in qs)):
        nm,fn=make_keep_ge(f,t); conds.append((nm,fn))
        nm,fn=make_keep_le(f,t); conds.append((nm,fn))
for f in BINF:
    conds.append(make_keep_eq0(f))
    conds.append(make_keep_eq1(f))

def eval_keep(keepfn, rows=MEM):
    kept=[r for r in rows if keepfn(r)]
    n,w,l,wr,ms=stats(kept)
    wk = w/w0*100 if w0 else 0   # winners kept pct
    lc = (l0-l)/l0*100 if l0 else 0  # losers cut pct
    return n,w,l,wr,ms,wk,lc

print("\n--- single-condition filters keeping >=90% winners, sorted by losers_cut ---")
results=[]
for nm,fn in conds:
    n,w,l,wr,ms,wk,lc=eval_keep(fn)
    if wk>=90 and lc>0:
        results.append((lc,ms,wr,wk,nm,n,w,l))
for lc,ms,wr,wk,nm,n,w,l in sorted(results,reverse=True)[:20]:
    print(f"  keep[{nm:20s}] n={n:3d} WR={wr:.1f}% loser_cut={lc:.1f}% win_kept={wk:.1f}% maxstreak={ms}")

# ---- 2-3 feature combos (AND of keep conditions) on the best singles ----
# take top singles that cut losers, try ANDing
top_singles=[(nm,fn) for nm,fn in conds]
best_singles=sorted(results,reverse=True)[:14]
sel=[(r[4]) for r in best_singles]
cond_map=dict(conds)
print("\n--- 2-combo AND filters keeping >=90% winners ---")
combo_results=[]
names=[r[4] for r in best_singles]
for a,b in itertools.combinations(names,2):
    fa,fb=cond_map[a],cond_map[b]
    keep=lambda r,fa=fa,fb=fb: fa(r) and fb(r)
    n,w,l,wr,ms,wk,lc=eval_keep(keep)
    if wk>=90 and lc>0:
        combo_results.append((lc,ms,wr,wk,f"{a} AND {b}",n,w,l))
for lc,ms,wr,wk,nm,n,w,l in sorted(combo_results,reverse=True)[:15]:
    print(f"  {nm:40s} n={n:3d} WR={wr:.1f}% cut={lc:.1f}% kept={wk:.1f}% ms={ms}")

# ---- pick best: maximize loser_cut with >=90% winners kept, tiebreak lower maxstreak ----
allcand=[(lc,-ms,wr,wk,nm,n,w,l,'single') for lc,ms,wr,wk,nm,n,w,l in results] + \
        [(lc,-ms,wr,wk,nm,n,w,l,'combo') for lc,ms,wr,wk,nm,n,w,l in combo_results]
if allcand:
    allcand.sort(reverse=True)
    best=allcand[0]
    lc,negms,wr,wk,nm,n,w,l,typ=best
    ms=-negms
    print("\n=== BEST FILTER ===")
    print(f"desc: keep {nm}")
    print(f"n_after={n} WR_after={wr}% maxstreak_after={ms} winners_kept={wk:.1f}% losers_cut={lc:.1f}%")
    # rebuild kept rows for the best filter
    if typ=='single':
        keepfn=cond_map[nm]
    else:
        a,b=nm.split(' AND ')
        keepfn=lambda r,fa=cond_map[a],fb=cond_map[b]: fa(r) and fb(r)
    kept=[r for r in MEM if keepfn(r)]
    for y in (2024,2025,2026):
        yr=[r for r in kept if r['yr']==y]
        if yr:
            ywr=sum(is_win(r) for r in yr)/len(yr)*100
            print(f"  y{y}: n={len(yr)} WR={ywr:.1f}%")
        else:
            print(f"  y{y}: n=0")
else:
    print("\n=== NO FILTER cuts losers keeping >=90% winners ===")

# ---- DEVIL'S ADVOCATE AUDIT on the chosen lens: buy_L>=1 (presence of LARGE buy bubbles) ----
# buy_L is a COUNT, not a flag. Cut = any LARGE buy-bubble present at reclaim.
print("\n--- DA AUDIT: cut group buy_L>=1 (LARGE buy bubbles present) ---")
cut=[r for r in MEM if r['buy_L']>=1]
cw=sum(is_win(r) for r in cut); cl=len(cut)-cw
print(f"  CUT group: n={len(cut)} W={cw} L={cl} WR={cw/len(cut)*100:.1f}%")
from collections import defaultdict
dd=defaultdict(lambda:[0,0])
for r in cut: dd[r['yr']][0 if is_win(r) else 1]+=1
for y in sorted(dd): print(f"    cut y{y}: W={dd[y][0]} L={dd[y][1]} (WR={dd[y][0]/(dd[y][0]+dd[y][1])*100:.0f}%)")
# honesty: WR delta and streak are within noise; year sign flips
print("  NOTE: WR shift 49.0->49.6% is within sampling noise (n=431, ~200 thresholds tested).")
print("  Cut group is NOT uniformly bad across years (2025 WR=52%), so edge is fragile/non-stationary.")
