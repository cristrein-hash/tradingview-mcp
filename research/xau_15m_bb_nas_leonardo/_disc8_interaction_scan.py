#!/usr/bin/env python3
"""
_disc8_interaction_scan.py — systematic 2-feature interaction scan.
For every pair of (numeric feature thresholds), find the KEEP region that
maximizes WR while keeping >=85% winners, then require year-stability.
This is the brute search behind the multi-TF contextual lens, but generalized
so we don't miss the real separator.

RAW-causal. win=R>0 only. Order by low_t for streak.
"""
import json, itertools
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])
N = len(ROWS)
TOT_WIN = sum(r['win'] for r in ROWS)
TOT_LOSE = N - TOT_WIN
BASE_WR = TOT_WIN / N
YEARS = [2024, 2025, 2026]
BASE_WR_YR = {}
for y in YEARS:
    sub = [r for r in ROWS if r['yr'] == y]
    BASE_WR_YR[y] = sum(r['win'] for r in sub) / len(sub)

def streak(rows):
    mx=cur=0
    for r in rows:
        if r['win']==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx
BASE_STREAK = streak(ROWS)

NUM = ['h1_trend','h1_dist','h1_pos','h1_eff','h4_trend','h4_dist','h4_pos','h4_eff',
       'hd_trend','hd_dist','hd_pos','hd_eff','dist_demand_atr','dist_supply_atr',
       'n_demand_near','atr_regime','atr_expand','vol_low_vs_med','vol_climax',
       'vpnode_dist_atr','macro_drop_atr','macro_retr','bars_to_8atr','path_eff',
       'rsi','rsi_low','disp4_atr']

# precompute per-feature quantile thresholds (non-null)
def quantiles(vals, qs):
    vals=sorted(vals); out=[]
    for q in qs:
        i=min(len(vals)-1, int(q*len(vals)))
        out.append(vals[i])
    return out

THRS={}
for f in NUM:
    vals=[r[f] for r in ROWS if r[f] is not None]
    if not vals: continue
    THRS[f]=sorted(set(quantiles(vals,[0.2,0.35,0.5,0.65,0.8])))

def eval_keep(kept):
    nk=len(kept)
    if nk<250: return None
    wk=sum(r['win'] for r in kept)
    wr=wk/nk
    wkp=wk/TOT_WIN
    if wkp<0.85: return None
    if wr<=BASE_WR+0.005: return None
    wr_yr={}
    for y in YEARS:
        s=[r for r in kept if r['yr']==y]
        wr_yr[y]=(sum(rr['win'] for rr in s)/len(s), len(s)) if s else (None,0)
    yrs_ok=all(wr_yr[y][0] is not None and wr_yr[y][0]>=BASE_WR_YR[y]-0.005 for y in YEARS)
    return dict(nk=nk,wr=wr,wkp=wkp,strk=streak(kept),
                lcut=(TOT_LOSE-(nk-wk))/TOT_LOSE,
                y=tuple(round(wr_yr[y][0],3) if wr_yr[y][0] is not None else None for y in YEARS),
                yn=tuple(wr_yr[y][1] for y in YEARS),
                yrs_ok=yrs_ok)

# Drop-rule form: cut rows where (fa OP ta) AND (fb OP tb). KEEP the rest.
# We search direction per feature: keep>=t or keep<=t.
results=[]
feats=[f for f in NUM if f in THRS]
for fa, fb in itertools.combinations(feats, 2):
    for ta in THRS[fa]:
        for da in ('ge','le'):
            for tb in THRS[fb]:
                for db in ('ge','le'):
                    def keep(r, fa=fa,ta=ta,da=da, fb=fb,tb=tb,db=db):
                        va=r[fa]; vb=r[fb]
                        # KEEP unless BOTH bad-conditions met. Null => not-bad (keep).
                        bad_a = (va is not None) and ((va<ta) if da=='ge' else (va>ta))
                        bad_b = (vb is not None) and ((vb<tb) if db=='ge' else (vb>tb))
                        return not (bad_a and bad_b)
                    kept=[r for r in ROWS if keep(r)]
                    res=eval_keep(kept)
                    if res and res['yrs_ok']:
                        results.append(((fa,da,ta),(fb,db,tb),res))

results.sort(key=lambda x: (-x[2]['wr'], x[2]['strk']))
print(f"BASE WR={BASE_WR:.4f} streak={BASE_STREAK} | year={ {y:round(BASE_WR_YR[y],3) for y in YEARS} }")
print(f"{len(results)} year-stable drop-rules found. Top 25:")
print()
for (fa,da,ta),(fb,db,tb),res in results[:25]:
    cuta='<' if da=='ge' else '>'
    cutb='<' if db=='ge' else '>'
    print(f"CUT {fa}{cuta}{ta} & {fb}{cutb}{tb} | n={res['nk']:4} wr={res['wr']:.4f} strk={res['strk']:2} "
          f"wkept={res['wkp']:.3f} lcut={res['lcut']:.3f} y={res['y']} yn={res['yn']}")
