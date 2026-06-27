#!/usr/bin/env python3
"""
R2 lapidation phase 2 — WINNER-RETENTION frontier.

Phase 1 showed: strong-WR cuts (bars_since_sell<50 -> WR77) sacrifice winners.
Loser-targeted CUT framings (cut active/escalating sell) keep ~85-93% winners but
barely lift WR. Here we tighten CUT-when filters that surgically remove losers
where selling is STILL ACTIVE/ESCALATING (lens) without touching winners, and
layer contextual session/recency conditions.

ONLY r2_keep==1. win=R>0. Forbidden: h1_eff,h4_pos,R,win.
robust = wr>68.54 AND per-year>=year-base AND winners_kept>=85% AND blocks_nw>=6 AND streak<24.
"""
import json

PATH='/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl'
rows=[json.loads(l) for l in open(PATH)]
kept=[r for r in rows if r['r2_keep']==1]
kept.sort(key=lambda r:r['low_t'])
N=len(kept); W=[r for r in kept if r['R']>0]; WR_BASE=100*len(W)/N; TOT_WIN=len(W)

def streak(s):
    s=sorted(s,key=lambda r:r['low_t']); mls=cur=0
    for r in s:
        if r['R']>0: cur=0
        else: cur+=1; mls=max(mls,cur)
    return mls
STREAK_BASE=streak(kept)
yr_base={yr:100*sum(1 for r in kept if r['yr']==yr and r['R']>0)/sum(1 for r in kept if r['yr']==yr) for yr in (2024,2025,2026)}
bs=N//8
blocks=[kept[i*bs:((i+1)*bs if i<7 else N)] for i in range(8)]
block_base=[100*sum(1 for r in bl if r['R']>0)/len(bl) for bl in blocks]

def ev(pred,desc):
    keep=[r for r in kept if pred(r)]
    if not keep: return None
    nk=len(keep); wk=[r for r in keep if r['R']>0]; wr=100*len(wk)/nk
    wkept=100*len(wk)/TOT_WIN
    lcut=100*((N-TOT_WIN)-(nk-len(wk)))/(N-TOT_WIN)
    yw={yr:(100*sum(1 for r in keep if r['yr']==yr and r['R']>0)/max(1,sum(1 for r in keep if r['yr']==yr))) for yr in (2024,2025,2026)}
    nw=0
    for i,bl in enumerate(blocks):
        blk=[r for r in bl if pred(r)]
        if not blk: nw+=1
        elif 100*sum(1 for r in blk if r['R']>0)/len(blk) >= block_base[i]-1e-9: nw+=1
    rob=(wr>WR_BASE and all(yw[y]>=yr_base[y]-1e-9 for y in (2024,2025,2026)) and wkept>=85 and nw>=6 and streak(keep)<STREAK_BASE)
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,2),streak_keep=streak(keep),
                winners_kept_pct=round(wkept,2),losers_cut_pct=round(lcut,2),
                y24=round(yw[2024],2),y25=round(yw[2025],2),y26=round(yw[2026],2),
                blocks_nw=nw,robust=rob)

print(f"BASE n={N} WR={WR_BASE:.2f} streak={STREAK_BASE} wins={TOT_WIN} yr_base={ {k:round(v,1) for k,v in yr_base.items()} }")
print(f"block_base {[round(x,1) for x in block_base]}\n")

DEF=lambda r: r['sell_decel']>-9e6  # sell_decel defined
results=[]

# Loser signature = selling ACTIVE/ESCALATING. Define adversely & CUT it.
# "active" = recent sell (bars_since_sell small) ; "escalating" = sell_decel<=0 (accelerating) or flow_accel<0
# Tune the recency cutoff for the CUT so we excise the worst loser pocket but spare winners.
for rec in [20,30,40,50,60]:
    results.append(ev(lambda r,c=rec: not (DEF(r) and r['sell_decel']<=0 and r['bars_since_sell']<c),
                      f"CUT: sell accel(<=0) & bars_since_sell<{rec}"))
# escalating via flow_accel curvature strongly negative + recent
for fa in [0,-5,-10]:
    for rec in [40,60]:
        results.append(ev(lambda r,f=fa,c=rec: not (r['flow_accel']<f and r['bars_since_sell']<c),
                          f"CUT: flow_accel<{fa} & bars_since_sell<{rec}"))
# combine: cut only when BOTH accel & negative curvature & recent (most specific loser pocket)
for rec in [40,60,80]:
    results.append(ev(lambda r,c=rec: not (DEF(r) and r['sell_decel']<=0 and r['flow_accel']<0 and r['bars_since_sell']<c),
                      f"CUT: accel & flow<0 & recent<{rec}"))
# cut when sell thickening (skew<0) AND escalating
results.append(ev(lambda r: not (r['sell_skew_mig']<0 and r['flow_accel']<0 and DEF(r) and r['sell_decel']<=0),
                  "CUT: skew<0 & flow<0 & accel"))
# Deadzone session context cut (low-quality time) intersect active sell
results.append(ev(lambda r: not (r['is_deadzone']==1 and DEF(r) and r['sell_decel']<=0),
                  "CUT: deadzone & sell accel"))
results.append(ev(lambda r: not (r['is_deadzone']==1 and r['flow_accel']<0),
                  "CUT: deadzone & flow_accel<0"))
# keep-when wide: keep unless (deadzone OR escalating-recent)
results.append(ev(lambda r: not (r['is_deadzone']==1 or (DEF(r) and r['sell_decel']<=0 and r['bars_since_sell']<40)),
                  "CUT: deadzone OR (accel & recent<40)"))

# session positive framings (keep windows) intersect mild lens
lon=lambda r:r['is_london_open']==1; ny=lambda r:r['is_ny_overlap']==1
results.append(ev(lambda r: lon(r) or ny(r), "KEEP: london_open | ny_overlap"))
results.append(ev(lambda r: not r['is_deadzone']==1, "KEEP: not deadzone"))
results.append(ev(lambda r: (lon(r) or ny(r)) and not (DEF(r) and r['sell_decel']<=0 and r['bars_since_sell']<40),
                  "KEEP:(lon|ny) & not(accel&recent<40)"))

# absorption-positive cut of escalating sell: absorption present means sell got eaten -> keep;
# absorption absent AND escalating recent sell -> cut
results.append(ev(lambda r: not (r['absorption']==0 and DEF(r) and r['sell_decel']<=0 and r['bars_since_sell']<40),
                  "CUT: no-absorption & accel & recent<40"))

# regime_age context: very young regime + escalating sell = trap
results.append(ev(lambda r: not (r['regime_age_h']<24 and DEF(r) and r['sell_decel']<=0 and r['bars_since_sell']<40),
                  "CUT: young regime<24h & accel & recent<40"))

results=[x for x in results if x]
results.sort(key=lambda x:(-(x['robust']), -x['wr_keep']))
print("RESULTS (sorted robust then WR):")
for x in results:
    flag='*ROBUST*' if x['robust'] else ''
    print(f"  WR{x['wr_keep']:.1f} n{x['n_keep']:4d} stk{x['streak_keep']:2d} wkept{x['winners_kept_pct']:.0f}% lcut{x['losers_cut_pct']:.0f}% [{x['y24']:.0f}/{x['y25']:.0f}/{x['y26']:.0f}] nw{x['blocks_nw']} {flag} :: {x['desc']}")

import json as J
J.dump(results, open('/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_r2lap_winner_retention_results.json','w'), indent=1)
