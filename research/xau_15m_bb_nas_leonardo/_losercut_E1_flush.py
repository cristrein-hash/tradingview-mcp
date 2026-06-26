#!/usr/bin/env python3
"""Loser-cut (lapidacao) for target E1_flush.
Members = rsi_low>=48.5 AND disp4_atr<-0.898. Outcome = R_reclaim.
Forbidden as filter: R_reclaim,R_8atr,near_M8,held8,runner,reclaim_idx,low_idx (look-ahead/target)
Rule-defining (circular, do NOT reuse): rsi_low, disp4_atr.
Goal: cut max losers keeping >=90% winners, minimize max-losing-streak.
"""
import json, itertools

rows = [json.loads(l) for l in open('entry_dataset.jsonl')]
mem = [r for r in rows if r['rsi_low'] >= 48.5 and r['disp4_atr'] < -0.898]
mem.sort(key=lambda r: r['low_t'])

FORBIDDEN = {'R_reclaim','R_8atr','near_M8','held8','runner','reclaim_idx','low_idx','low_t','block','yr'}
RULE = {'rsi_low','disp4_atr'}

def is_win(r): return r['R_reclaim'] > 0

def stats(sub):
    n=len(sub); w=sum(1 for r in sub if is_win(r))
    wr = w/n if n else 0
    streak=mx=0
    for r in sub:
        if is_win(r): streak=0
        else: streak+=1; mx=max(mx,streak)
    return n, w, wr, mx

def yr_wr(sub):
    out={}
    for y in (2024,2025,2026):
        s=[r for r in sub if r['yr']==y]
        out[y]= (sum(1 for r in s if is_win(r))/len(s)) if s else None
    return out

N0,W0,WR0,MX0 = stats(mem)
L0 = N0-W0
print(f"BEFORE n={N0} winners={W0} losers={L0} WR={WR0:.3f} maxstreak={MX0}")

# candidate features
feats=[k for k in mem[0] if k not in FORBIDDEN and k not in RULE and isinstance(mem[0][k],(int,float))]

# For a "keep" condition, we EXCLUDE rows failing the predicate.
# We want predicate kept-set to retain >=90% winners and maximize losers cut.
# Try threshold predicates per feature in both directions.
import numpy as np

def eval_keep(keepmask):
    sub=[r for i,r in enumerate(mem) if keepmask[i]]
    n,w,wr,mx=stats(sub)
    winners_kept = w/W0
    losers_cut = (L0-(n-w))/L0 if L0 else 0
    return sub,n,w,wr,mx,winners_kept,losers_cut

# build single-feature threshold candidates
cands=[]  # (desc, keepmask)
for f in feats:
    vals=sorted(set(r[f] for r in mem))
    # candidate cut points: quantiles
    qs=[np.quantile([r[f] for r in mem], q) for q in np.linspace(0.05,0.95,19)]
    for t in sorted(set(round(x,4) for x in qs)):
        for op,fn in (('>=',lambda r,f=f,t=t: r[f]>=t),('<=',lambda r,f=f,t=t: r[f]<=t)):
            km=[fn(r) for r in mem]
            if sum(km)<10: continue
            cands.append((f'{f}{op}{t}', km, f))

# filter to those keeping >=90% winners, score by losers_cut then streak
good=[]
for desc,km,f in cands:
    sub,n,w,wr,mx,wk,lc=eval_keep(km)
    if wk>=0.90 and lc>0:
        good.append((lc, -mx, wr, desc, km, f, n, w, wk))
good.sort(key=lambda x:(-x[0], x[1], -x[2]))

print("\n=== TOP single-feature loser-cuts (winners_kept>=90%) ===")
for g in good[:12]:
    lc,negmx,wr,desc,km,f,n,w,wk=g
    print(f"  {desc:28s} n={n} WR={wr:.3f} streak={-negmx} winkept={wk:.3f} loscut={lc:.3f}")

# combos of 2-3 orthogonal features (different base feature), AND of keep predicates
best_singles={}
for g in good:
    f=g[5]
    if f not in best_singles: best_singles[f]=g  # already sorted best-first
single_list=list(best_singles.values())

def combine(masks):
    return [all(m[i] for m in masks) for i in range(len(mem))]

combo_results=[]
single_keys=[g[3] for g in good]  # all good single predicates
# limit combo search to top good predicates by losers_cut for tractability
top_for_combo = good[:60]
for r in (2,3):
    for combo in itertools.combinations(top_for_combo,r):
        fs={c[5] for c in combo}
        if len(fs)<r: continue  # require orthogonal (distinct base features)
        km=combine([c[4] for c in combo])
        if sum(km)<10: continue
        sub,n,w,wr,mx,wk,lc=eval_keep(km)
        if wk>=0.90 and lc>0:
            desc=' AND '.join(c[3] for c in combo)
            combo_results.append((lc,-mx,wr,desc,n,w,wk,mx))
combo_results.sort(key=lambda x:(-x[0],x[1],-x[2]))

print("\n=== TOP combo loser-cuts (winners_kept>=90%, orthogonal) ===")
for cr in combo_results[:12]:
    lc,negmx,wr,desc,n,w,wk,mx=cr
    print(f"  WR={wr:.3f} streak={mx} winkept={wk:.3f} loscut={lc:.3f} n={n} | {desc}")

# choose best overall: prefer highest losers_cut with winners_kept>=0.90, tiebreak lower streak then higher WR
pool=[]
for g in good:
    lc,negmx,wr,desc,km,f,n,w,wk=g
    pool.append((lc,-negmx*-1,wr,desc,km,n,w,wk,-negmx))  # keep mask
# unify scoring
def score_entry(km):
    sub,n,w,wr,mx,wk,lc=eval_keep(km)
    return lc,mx,wr,n,w,wk,sub

best=None
for desc,km,f in [(g[3],g[4],g[5]) for g in good]:
    lc,mx,wr,n,w,wk,sub=score_entry(km)
    key=(lc, -mx, wr)
    if best is None or key>best[0]:
        best=(key,desc,km,lc,mx,wr,n,w,wk,sub)
# also consider combos
for cr in combo_results:
    pass

print("\n=== CHOSEN (single, most robust) ===")
# Chosen = low_closepos<=0.7922 : best loser-cut among single features keeping >=90% winners.
# Rationale: low_closepos (close position within the reclaim bar's range, 0=low,1=high)
# is ORTHOGONAL to the rule features (rsi_low level, disp4_atr displacement magnitude).
# A reclaim bar that closes high in its range (>0.79) = exhaustion/blowoff into the close
# with no follow-through buyers => loser. Closing in lower 3/4 of range = absorption with
# room => winner. Causal, available at the reclaim bar, no look-ahead.
sub=[r for r in mem if r['low_closepos']<=0.7922]
n,w,wr,mx=stats(sub); wk=w/W0; lc=(L0-(n-w))/L0; yw=yr_wr(sub)
print('desc: low_closepos<=0.7922')
print(f'AFTER n={n} winners={w} losers={n-w} WR={wr:.3f} maxstreak={mx}')
print(f'winners_kept={wk:.3f} losers_cut={lc:.3f}')
print('yr WR:', {y:(round(v,3) if v is not None else None) for y,v in yw.items()})

# ---- DEVIL'S ADVOCATE / robustness materialized ----
print("\n=== DA: threshold robustness (low_closepos) ===")
for t in [0.75,0.77,0.7922,0.81,0.83]:
    s=[r for r in mem if r['low_closepos']<=t]
    nn,ww,wwr,mmx=stats(s)
    print(f'  t={t}: n={nn} WR={wwr:.3f} streak={mmx} winkept={ww/W0:.3f} loscut={(L0-(nn-ww))/L0:.3f}')

print("\n=== DA: combo (lower streak) low_closepos<=0.7922 AND leg_ext<=0.769 AND sell_L<=0 ===")
combo=[r for r in mem if r['low_closepos']<=0.7922 and r['leg_ext']<=0.769 and r['sell_L']<=0.0]
nn,ww,wwr,mmx=stats(combo)
print(f'  n={nn} WR={wwr:.3f} streak={mmx} winkept={ww/W0:.3f} loscut={(L0-(nn-ww))/L0:.3f} yr={yr_wr(combo)}')
