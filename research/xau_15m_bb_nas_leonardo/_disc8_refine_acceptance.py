#!/usr/bin/env python3
"""
_disc8_refine_acceptance.py — Discovery part 3. Refine the dominant axis found in
part 2: ACCEPTANCE TIME (bars_to_8atr). Fast spikes to 8ATR are exhaustion losers;
slow-grind acceptance are winners. This is a vol/volume-CONTEXTUAL read: a move
that took many bars to extend 8ATR was ACCEPTED by volume (grind = repeated
auction acceptance), not a low-liquidity spike.

Goal: maximize losers_cut while keeping winners_kept>=0.85 AND robust across 3yr
AND lowering max-losing-streak. Tune the fast-spike cut with secondary context
(path_eff steep, vpnode at/below POC, low macro_retr, h1_pos low).

robust=True only if WR>base AND >=base each year AND winners_kept>=0.85.
RULES: win=R>0, no R/win feature, chronological streak.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
TOT_WIN = sum(r['win'] for r in ROWS); TOT_LOSS = N - TOT_WIN
YR_BASE = {y: (lambda s: sum(x['win'] for x in s)/len(s))([r for r in ROWS if r['yr']==y]) for y in (2024,2025,2026)}

def streak(rows):
    mx=cur=0
    for r in rows:
        if r['win']==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx
BASE_STREAK=streak(ROWS)

def ev(name,pred,minn=80):
    keep=[r for r in ROWS if pred(r)]
    if len(keep)<minn: return None
    nk=len(keep); wk=sum(r['win'] for r in keep); wr=wk/nk
    wkp=wk/TOT_WIN; lc=(TOT_LOSS-(nk-wk))/TOT_LOSS
    yr={y:(lambda s: sum(x['win'] for x in s)/len(s) if s else None)([r for r in keep if r['yr']==y]) for y in (2024,2025,2026)}
    robust=(wr>BASE_WR and wkp>=0.85 and all(yr[y] is not None and yr[y]>=YR_BASE[y] for y in (2024,2025,2026)))
    return dict(name=name,n_keep=nk,wr=round(wr,4),strk=streak(keep),wkp=round(wkp,4),
                lc=round(lc,4),y24=round(yr[2024],4),y25=round(yr[2025],4),y26=round(yr[2026],4),robust=robust)

RES=[]
def t(name,pred,minn=80):
    r=ev(name,pred,minn)
    if r: RES.append(r)

# sweep fast-spike threshold
for thr in (20,25,31,40,50):
    t(f"CUT(bars<{thr})", lambda r,thr=thr: r['bars_to_8atr']>=thr)
# fast spike + steep (exhaustion blowoff)
for thr in (31,40,50):
    for pe in (0.4,0.5,0.6):
        t(f"CUT(bars<{thr} & path_eff>{pe})",
          lambda r,thr=thr,pe=pe: not (r['bars_to_8atr']<thr and r['path_eff']>pe))
# fast spike + low retr (shallow pullback before spike = weak)
for thr in (31,40,50):
    t(f"CUT(bars<{thr} & macro_retr<1.0)",
      lambda r,thr=thr: not (r['bars_to_8atr']<thr and r['macro_retr']<1.0))
# fast spike + below value (vpnode<=0) OR at POC
for thr in (31,40,50):
    t(f"CUT(bars<{thr} & vpnode<=2)",
      lambda r,thr=thr: not (r['bars_to_8atr']<thr and r['vpnode_dist_atr']<=2.0))
# fast spike + h1 not trending up / pos low
for thr in (31,40,50):
    t(f"CUT(bars<{thr} & h1_pos<1.05)",
      lambda r,thr=thr: not (r['bars_to_8atr']<thr and r['h1_pos']<1.05))
# combined exhaustion read: fast AND steep AND shallow-pullback
for thr in (40,50,62):
    t(f"CUT(bars<{thr} & path_eff>0.5 & macro_retr<1.0)",
      lambda r,thr=thr: not (r['bars_to_8atr']<thr and r['path_eff']>0.5 and r['macro_retr']<1.0))
# fast AND (steep OR shallow)  -- broader exhaustion net
for thr in (40,50,62):
    t(f"CUT(bars<{thr} & (path_eff>0.55 OR macro_retr<0.9))",
      lambda r,thr=thr: not (r['bars_to_8atr']<thr and (r['path_eff']>0.55 or r['macro_retr']<0.9)))
# fast AND rsi extreme high (overbought spike)
for thr in (40,50):
    t(f"CUT(bars<{thr} & rsi>78)",
      lambda r,thr=thr: not (r['bars_to_8atr']<thr and r['rsi']>78))
# two-stage: cut fast-steep AND also rsi>80 always
t("CUT(bars<40 & path_eff>0.5) & CUT(rsi>80)",
  lambda r: not (r['bars_to_8atr']<40 and r['path_eff']>0.5) and r['rsi']<=80)

RES.sort(key=lambda x:(-x['robust'],-x['lc'],-x['wr']))
print(f"BASE_WR={BASE_WR:.4f} STREAK={BASE_STREAK} YR_BASE={ {y:round(v,3) for y,v in YR_BASE.items()} }")
print("rob wr    nk   strk wk%   lc%   y24  y25  y26  name")
for r in RES:
    print(f"{'Y' if r['robust'] else '.'}  {r['wr']:.3f} {r['n_keep']:4d} {r['strk']:4d} "
          f"{r['wkp']:.2f}  {r['lc']:.2f}  {r['y24']:.2f} {r['y25']:.2f} {r['y26']:.2f}  {r['name']}")
