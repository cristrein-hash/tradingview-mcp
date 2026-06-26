#!/usr/bin/env python3
"""
R2 lapidation — VERIFY top robust contextual cuts.
Re-check the ROBUST winners, dump per-block detail, overlap of cut rows,
and a combined union cut. Operate ONLY on r2_keep==1.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]
KEPT.sort(key=lambda r: r['low_t'])
N0=len(KEPT); W0=sum(r['win'] for r in KEPT); WR0=100*W0/N0
YEARS=sorted(set(r['yr'] for r in KEPT)); BLOCKS=sorted(set(r['block'] for r in KEPT))
YR_BASE={y:100*sum(s['win'] for s in KEPT if s['yr']==y)/sum(1 for s in KEPT if s['yr']==y) for y in YEARS}
BL_BASE={b:100*sum(s['win'] for s in KEPT if s['block']==b)/sum(1 for s in KEPT if s['block']==b) for b in BLOCKS}

def max_streak(rows):
    cur=mx=0
    for r in rows:
        if r['win']==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx
STREAK0=max_streak(KEPT)

def full(name,pred):
    kept=[r for r in KEPT if pred(r)]
    cut=[r for r in KEPT if not pred(r)]
    nk=len(kept); wk=sum(r['win'] for r in kept); wr=100*wk/nk
    streak=max_streak(kept); winners_kept=100*wk/W0
    lt=N0-W0; lc=lt-(nk-wk)
    # cut composition
    cut_w=sum(r['win'] for r in cut); cut_l=len(cut)-cut_w
    yr={}; yr_ok=True
    for y in YEARS:
        sub=[r for r in kept if r['yr']==y]; a=100*sum(s['win'] for s in sub)/len(sub); yr[y]=a
        if a<YR_BASE[y]-1e-9: yr_ok=False
    bnw=0; bd={}
    for b in BLOCKS:
        sub=[r for r in kept if r['block']==b]; a=100*sum(s['win'] for s in sub)/len(sub); bd[b]=a
        if a>=BL_BASE[b]-1e-9: bnw+=1
    robust=(wr>WR0 and yr_ok and winners_kept>=85.0 and bnw>=6 and streak<STREAK0)
    print(f"\n### {name}")
    print(f"  n_keep={nk} WR={wr:.2f} (base {WR0:.2f}) streak={streak} (base {STREAK0})")
    print(f"  cut {len(cut)} rows = {cut_l} losers + {cut_w} winners | winners_kept={winners_kept:.2f}% losers_cut={100*lc/lt:.2f}%")
    print(f"  yr: " + " ".join(f"{y}={yr[y]:.1f}(b{YR_BASE[y]:.1f}){'+' if yr[y]>=YR_BASE[y] else '-'}" for y in YEARS) + f"  yr_ok={yr_ok}")
    print(f"  blk not-worse {bnw}/8: " + " ".join(f"{b[5:]}={bd[b]:.0f}(b{BL_BASE[b]:.0f}){'+' if bd[b]>=BL_BASE[b]-1e-9 else '-'}" for b in BLOCKS))
    print(f"  ROBUST={robust}")
    return set(id(r) for r in cut), robust

# the candidates
preds = {
 "cut(absorb & hivol1.5)": lambda r: not(r['absorption']==1 and r['low_vol_rel']>=1.5),
 "cut(hivol1.5 & young<24)": lambda r: not(r['low_vol_rel']>=1.5 and r['regime_age_h']<24),
 "cut(absorb & young<24)": lambda r: not(r['absorption']==1 and r['regime_age_h']<24),
}
cutsets={}
for nm,p in preds.items():
    cs,rob=full(nm,p); cutsets[nm]=cs

# UNION: cut if absorb&young<24 OR hivol1.5&young<24 OR absorb&hivol1.5
def union_pred(r):
    a=r['absorption']==1; hv=r['low_vol_rel']>=1.5; yg=r['regime_age_h']<24
    bad = (a and yg) or (hv and yg) or (a and hv)
    return not bad
full("UNION: cut [absorb&young | hivol1.5&young | absorb&hivol1.5]", union_pred)

# Tighter union: just absorb&young OR hivol&young (the 'young/unsettled regime' theme = my lens)
def young_pred(r):
    yg=r['regime_age_h']<24
    bad = yg and (r['absorption']==1 or r['low_vol_rel']>=1.5)
    return not bad
full("LENS UNION: cut young<24 & (absorb OR hivol1.5)", young_pred)

# overlap matrix
print("\n=== cut-set overlap (Jaccard) ===")
names=list(cutsets)
for i in range(len(names)):
    for j in range(i+1,len(names)):
        a,b=cutsets[names[i]],cutsets[names[j]]
        inter=len(a&b); uni=len(a|b)
        print(f"  {names[i]} vs {names[j]}: |A|={len(a)} |B|={len(b)} inter={inter} jacc={inter/uni:.2f}")
