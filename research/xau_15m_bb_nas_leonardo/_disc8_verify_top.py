#!/usr/bin/env python3
"""
_disc8_verify_top.py — verify the best drop-rules from the interaction scan
under the FULL robustness battery: WR per year, per 8 blocks, streak before/after,
winners-kept, losers-cut, and a 3-way refinement search seeded on the best base.
RAW-causal. win=R>0. Ordered by low_t.
"""
import json
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])
N = len(ROWS)
TOT_WIN = sum(r['win'] for r in ROWS)
TOT_LOSE = N - TOT_WIN
BASE_WR = TOT_WIN / N
YEARS = [2024, 2025, 2026]
BASE_WR_YR = {y: (lambda s: sum(r['win'] for r in s)/len(s))([r for r in ROWS if r['yr']==y]) for y in YEARS}
BLOCKS = sorted(set(r['block'] for r in ROWS))
BASE_WR_BLK = {b: (lambda s: sum(r['win'] for r in s)/len(s))([r for r in ROWS if r['block']==b]) for b in BLOCKS}

def streak(rows):
    mx=cur=0
    for r in rows:
        if r['win']==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx
BASE_STREAK=streak(ROWS)

def report(name, keep):
    kept=[r for r in ROWS if keep(r)]
    nk=len(kept); wk=sum(r['win'] for r in kept); wr=wk/nk
    print(f"\n### {name}")
    print(f"   n_keep={nk}  wr_keep={wr:.4f} (base {BASE_WR:.4f})  streak {BASE_STREAK}->{streak(kept)}")
    print(f"   winners_kept_pct={wk/TOT_WIN:.4f}  losers_cut_pct={(TOT_LOSE-(nk-wk))/TOT_LOSE:.4f}")
    yr={}
    for y in YEARS:
        s=[r for r in kept if r['yr']==y]; w=sum(r['win'] for r in s)
        yr[y]=(w/len(s),len(s));
        print(f"   y{y}: wr={w/len(s):.4f} (base {BASE_WR_YR[y]:.3f}) n={len(s)}  {'OK' if w/len(s)>=BASE_WR_YR[y] else 'BELOW'}")
    print("   blocks:")
    nbad=0
    for b in BLOCKS:
        s=[r for r in kept if r['block']==b]
        if not s: continue
        w=sum(r['win'] for r in s)/len(s)
        flag='OK' if w>=BASE_WR_BLK[b] else 'below'
        if w<BASE_WR_BLK[b]: nbad+=1
        print(f"     {b}: wr={w:.3f} (base {BASE_WR_BLK[b]:.3f}) n={len(s)} {flag}")
    print(f"   blocks_below_base={nbad}/8")
    return dict(nk=nk,wr=wr,strk=streak(kept),wkp=wk/TOT_WIN,
                lcut=(TOT_LOSE-(nk-wk))/TOT_LOSE,
                y=tuple(round(yr[y][0],4) for y in YEARS), nbad=nbad)

def g(r,k):
    return r.get(k)

# --- Rule 1: cut h1_trend<1 AND h4_eff<0.25  (range-4H without 15M up-trend)
def r1(r):
    bad = (r['h1_trend']<1) and (r['h4_eff'] is not None and r['h4_eff']<0.25)
    return not bad

# --- Rule 2: cut h1_eff<0.2 AND h4_pos<1.02 (no 15M drive AND 4H not extended up)
def r2(r):
    bad = (r['h1_eff']<0.2) and (r['h4_pos'] is not None and r['h4_pos']<1.02)
    return not bad

# --- Rule 3: cut h4_eff<0.35 AND dist_supply_atr<-0.13 (4H range AND price into/above supply)
def r3(r):
    bad = (r['h4_eff'] is not None and r['h4_eff']<0.35) and (r['dist_supply_atr'] is not None and r['dist_supply_atr']<-0.13)
    return not bad

# --- Rule 4: cut h1_pos<1.01 AND macro_retr<1.17 (15M not extended up AND shallow leg retr)
def r4(r):
    bad = (r['h1_pos']<1.01) and (r['macro_retr'] is not None and r['macro_retr']<1.17)
    return not bad

res={}
res['R1']=report('R1: CUT h1_trend<1 & h4_eff<0.25', r1)
res['R2']=report('R2: CUT h1_eff<0.2 & h4_pos<1.02', r2)
res['R3']=report('R3: CUT h4_eff<0.35 & dist_supply_atr<-0.13', r3)
res['R4']=report('R4: CUT h1_pos<1.01 & macro_retr<1.17', r4)

# --- 3-way: stack R1 + an extra cut to push WR with minimal winner loss
print("\n\n=== 3-WAY refinements on R1 ===")
def r1b(r):
    if not r1(r): return False  # already cut
    # extra: also cut if at HTF top (hd_pos>0.85) AND h4 range
    if r['hd_pos'] is not None and r['hd_pos']>0.85 and (r['h4_eff'] is not None and r['h4_eff']<0.3):
        return False
    return True
report('R1+top: R1 AND not(hd_pos>0.85 & h4_eff<0.3)', r1b)

def r1c(r):
    if not r1(r): return False
    # extra: cut also h4_eff<0.25 alone when supply very close (<0)
    if r['h4_eff'] is not None and r['h4_eff']<0.25 and r['dist_supply_atr'] is not None and r['dist_supply_atr']<0:
        return False
    return True
report('R1+supply: R1 AND not(h4_eff<0.25 & dist_supply<0)', r1c)
