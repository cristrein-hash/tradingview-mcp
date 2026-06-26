#!/usr/bin/env python3
"""
R2 lapidation — COMBO stage. Contextual cut: only drop a row when several
orthogonal "bad" signs align, to preserve >=85% winners.
Imports evaluate/show machinery from the single-feature script by re-defining
here (self-contained, RAW-causal). Operate ONLY on r2_keep==1.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]
KEPT.sort(key=lambda r: r['low_t'])
N0 = len(KEPT); W0 = sum(r['win'] for r in KEPT); WR0 = 100*W0/N0
YEARS = sorted(set(r['yr'] for r in KEPT))
BLOCKS = sorted(set(r['block'] for r in KEPT))
YR_BASE = {y: 100*sum(s['win'] for s in KEPT if s['yr']==y)/sum(1 for s in KEPT if s['yr']==y) for y in YEARS}
BL_BASE = {b: 100*sum(s['win'] for s in KEPT if s['block']==b)/sum(1 for s in KEPT if s['block']==b) for b in BLOCKS}


def max_streak(rows):
    cur = mx = 0
    for r in rows:
        if r['win']==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx

STREAK0 = max_streak(KEPT)


def evaluate(name, pred):
    kept = [r for r in KEPT if pred(r)]
    if not kept: return None
    nk=len(kept); wk=sum(r['win'] for r in kept); wr=100*wk/nk
    streak=max_streak(kept); winners_kept=100*wk/W0
    losers_total=N0-W0; losers_cut=losers_total-(nk-wk); losers_cut_pct=100*losers_cut/losers_total
    yr_after={}; yr_ok=True
    for y in YEARS:
        sub=[r for r in kept if r['yr']==y]
        if not sub: yr_after[y]=None; yr_ok=False; continue
        a=100*sum(s['win'] for s in sub)/len(sub); yr_after[y]=a
        if a<YR_BASE[y]-1e-9: yr_ok=False
    blocks_notworse=0
    for b in BLOCKS:
        sub=[r for r in kept if r['block']==b]
        if not sub: continue
        a=100*sum(s['win'] for s in sub)/len(sub)
        if a>=BL_BASE[b]-1e-9: blocks_notworse+=1
    robust=(wr>WR0 and yr_ok and winners_kept>=85.0 and blocks_notworse>=6 and streak<STREAK0)
    return dict(name=name,n_keep=nk,wr_keep=round(wr,2),streak_keep=streak,
                winners_kept_pct=round(winners_kept,2),losers_cut_pct=round(losers_cut_pct,2),
                y24=round(yr_after.get(2024,0),2),y25=round(yr_after.get(2025,0),2),
                y26=round(yr_after.get(2026,0),2),blocks_notworse=blocks_notworse,robust=robust)


def show(res):
    if res is None: return
    flag='ROBUST' if res['robust'] else ('near' if res['wr_keep']>WR0 and res['winners_kept_pct']>=85 and res['streak_keep']<STREAK0 else '')
    print(f"{res['name']:<54} n={res['n_keep']:<5} WR={res['wr_keep']:<6} strk={res['streak_keep']:<3} "
          f"winK%={res['winners_kept_pct']:<6} losC%={res['losers_cut_pct']:<6} "
          f"y24={res['y24']:<6} y25={res['y25']:<6} y26={res['y26']:<6} blk={res['blocks_notworse']}/8 {flag}")

print(f"BASELINE n={N0} WR={WR0:.2f} streak={STREAK0} | yr_base {[round(YR_BASE[y],1) for y in YEARS]}")
print()

# Define "bad sign" predicates (return True if this row shows a loser-prone trait)
def bad_absorb(r): return r['absorption']==1
def bad_hivol(r): return r['low_vol_rel']>=1.5
def bad_hivol12(r): return r['low_vol_rel']>=1.2
def bad_deadzone(r): return r['is_deadzone']==1
def bad_young(r): return r['regime_age_h']<24       # not fresh-enough turn settling
def bad_lowclose(r): return r['low_closepos']<0.4
def bad_buyLrecent(r): return r['buy_L_recent']==1  # surprisingly loser-prone single
def bad_skew(r): return r['sell_skew_mig']<=0       # no exhaustion thinning

print("=== CONTEXTUAL CUT: drop row only if >=K bad signs ===")
sign_funcs = [bad_absorb, bad_hivol, bad_deadzone, bad_young, bad_lowclose]
def nbad(r): return sum(f(r) for f in sign_funcs)
for K in [2,3]:
    show(evaluate(f"keep nbad(absorb,hivol1.5,dead,young<24,lowclose<.4)<{K}", lambda r,k=K: nbad(r)<k))

# Variant pools
poolA=[bad_absorb,bad_hivol12,bad_deadzone,bad_young,bad_lowclose]
def nbadA(r): return sum(f(r) for f in poolA)
for K in [2,3]:
    show(evaluate(f"keep nbadA(absorb,hivol1.2,dead,young,lowclose)<{K}", lambda r,k=K: nbadA(r)<k))

poolB=[bad_absorb,bad_hivol,bad_deadzone,bad_lowclose,bad_skew]
def nbadB(r): return sum(f(r) for f in poolB)
for K in [2,3]:
    show(evaluate(f"keep nbadB(absorb,hivol1.5,dead,lowclose,skew)<{K}", lambda r,k=K: nbadB(r)<k))

print()
print("=== PAIR cuts: cut only when BOTH conditions (targeted loser pocket) ===")
# Cut absorption AND high-vol together (climax-absorb in chaos)
show(evaluate("cut(absorb & hivol1.5)", lambda r: not(bad_absorb(r) and bad_hivol(r))))
show(evaluate("cut(absorb & hivol1.2)", lambda r: not(bad_absorb(r) and bad_hivol12(r))))
show(evaluate("cut(absorb & deadzone)", lambda r: not(bad_absorb(r) and bad_deadzone(r))))
show(evaluate("cut(absorb & lowclose<.4)", lambda r: not(bad_absorb(r) and bad_lowclose(r))))
show(evaluate("cut(hivol1.5 & deadzone)", lambda r: not(bad_hivol(r) and bad_deadzone(r))))
show(evaluate("cut(hivol1.5 & young<24)", lambda r: not(bad_hivol(r) and bad_young(r))))
show(evaluate("cut(hivol1.5 & lowclose<.4)", lambda r: not(bad_hivol(r) and bad_lowclose(r))))
show(evaluate("cut(deadzone & young<24)", lambda r: not(bad_deadzone(r) and bad_young(r))))
show(evaluate("cut(deadzone & lowclose<.4)", lambda r: not(bad_deadzone(r) and bad_lowclose(r))))
show(evaluate("cut(absorb & young<24)", lambda r: not(bad_absorb(r) and bad_young(r))))
show(evaluate("cut(buyLrecent & young<24)", lambda r: not(bad_buyLrecent(r) and bad_young(r))))
show(evaluate("cut(absorb & buyLrecent)", lambda r: not(bad_absorb(r) and bad_buyLrecent(r))))
show(evaluate("cut(hivol1.5 & buyLrecent)", lambda r: not(bad_hivol(r) and bad_buyLrecent(r))))

print()
print("=== TRIPLE cuts ===")
show(evaluate("cut(absorb & hivol1.2 & young<24)", lambda r: not(bad_absorb(r) and bad_hivol12(r) and bad_young(r))))
show(evaluate("cut(absorb & deadzone & lowclose<.4)", lambda r: not(bad_absorb(r) and bad_deadzone(r) and bad_lowclose(r))))
show(evaluate("cut(hivol1.5 & deadzone & lowclose<.4)", lambda r: not(bad_hivol(r) and bad_deadzone(r) and bad_lowclose(r))))

print()
print("=== KEEP-when (positive contextual) ===")
def good_calm(r): return r['low_vol_rel']<=1.2
def good_noabsorb(r): return r['absorption']==0
def good_mature(r): return r['regime_age_h']>=24
def good_session(r): return r['is_deadzone']==0
show(evaluate("keep calm & noabsorb", lambda r: good_calm(r) and good_noabsorb(r)))
show(evaluate("keep noabsorb & mature(age>=24)", lambda r: good_noabsorb(r) and good_mature(r)))
show(evaluate("keep calm & mature", lambda r: good_calm(r) and good_mature(r)))
show(evaluate("keep noabsorb & !deadzone", lambda r: good_noabsorb(r) and good_session(r)))
show(evaluate("keep calm OR noabsorb (cut absorb&hivol)", lambda r: good_calm(r) or good_noabsorb(r)))
