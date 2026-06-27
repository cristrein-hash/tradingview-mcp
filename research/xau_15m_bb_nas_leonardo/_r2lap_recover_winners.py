#!/usr/bin/env python3
"""
R2 lapidation phase 3 — the binding constraint is winner-retention, not WR.
SANITY of the frontier: bars_since_sell<50 -> WR77 but keeps 36% winners.
Strategy: find a CUT that removes the loser-dense complement of recent-sell
(i.e. trades with OLD/no recent sell that are losers) while sparing old-sell
winners. Equivalent: KEEP = (recent sell) UNION (orthogonal winner pocket).

Also examine WHERE the recent-sell winners vs old-sell losers live -> contextual
union keeps to climb WR while holding >=85% winners.

ONLY r2_keep==1. Forbidden: h1_eff,h4_pos,R,win.
"""
import json
PATH='/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl'
rows=[json.loads(l) for l in open(PATH)]
kept=[r for r in rows if r['r2_keep']==1]; kept.sort(key=lambda r:r['low_t'])
N=len(kept); TOT_WIN=sum(1 for r in kept if r['R']>0); WR_BASE=100*TOT_WIN/N
def streak(s):
    s=sorted(s,key=lambda r:r['low_t']); mls=cur=0
    for r in s:
        if r['R']>0: cur=0
        else: cur+=1; mls=max(mls,cur)
    return mls
STREAK_BASE=streak(kept)
yr_base={yr:100*sum(1 for r in kept if r['yr']==yr and r['R']>0)/sum(1 for r in kept if r['yr']==yr) for yr in (2024,2025,2026)}
bs=N//8; blocks=[kept[i*bs:((i+1)*bs if i<7 else N)] for i in range(8)]
block_base=[100*sum(1 for r in bl if r['R']>0)/len(bl) for bl in blocks]
def ev(pred,desc):
    keep=[r for r in kept if pred(r)]
    if not keep: return None
    nk=len(keep); wk=[r for r in keep if r['R']>0]; wr=100*len(wk)/nk
    wkept=100*len(wk)/TOT_WIN; lcut=100*((N-TOT_WIN)-(nk-len(wk)))/(N-TOT_WIN)
    yw={yr:(100*sum(1 for r in keep if r['yr']==yr and r['R']>0)/max(1,sum(1 for r in keep if r['yr']==yr))) for yr in (2024,2025,2026)}
    nw=0
    for i,bl in enumerate(blocks):
        blk=[r for r in bl if pred(r)]
        if not blk: nw+=1
        elif 100*sum(1 for r in blk if r['R']>0)/len(blk)>=block_base[i]-1e-9: nw+=1
    rob=(wr>WR_BASE and all(yw[y]>=yr_base[y]-1e-9 for y in (2024,2025,2026)) and wkept>=85 and nw>=6 and streak(keep)<STREAK_BASE)
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,2),streak_keep=streak(keep),
                winners_kept_pct=round(wkept,2),losers_cut_pct=round(lcut,2),
                y24=round(yw[2024],2),y25=round(yw[2025],2),y26=round(yw[2026],2),blocks_nw=nw,robust=rob)

# Diagnose: among OLD-sell trades (bars_since_sell>=50), what separates win/loss?
old=[r for r in kept if r['bars_since_sell']>=50]
ow=[r for r in old if r['R']>0]
print(f"OLD-sell(>=50): n={len(old)} WR={100*len(ow)/len(old):.1f} (loser-dense complement)")
recent=[r for r in kept if r['bars_since_sell']<50]
print(f"RECENT-sell(<50): n={len(recent)} WR={100*sum(1 for r in recent if r['R']>0)/len(recent):.1f}\n")
# within OLD: which orthogonal feature flags the winners (to UNION back in)?
for f,cond,lab in [
  ('flow_accel',lambda r:r['flow_accel']>20,'flow_accel>20'),
  ('flow_accel',lambda r:abs(r['flow_accel'])>20,'|flow_accel|>20'),
  ('absorption',lambda r:r['absorption']==1,'absorption'),
  ('is_ny_overlap',lambda r:r['is_ny_overlap']==1,'ny_overlap'),
  ('is_london_open',lambda r:r['is_london_open']==1,'london'),
  ('buy_L_recent',lambda r:r['buy_L_recent']==1,'buy_L_recent'),
  ('naslong_after_smc',lambda r:r['naslong_after_smc']==1,'naslong_after_smc'),
  ('buy_after_smc',lambda r:r['buy_after_smc']==1,'buy_after_smc'),
]:
    sub=[r for r in old if cond(r)]
    if sub: print(f"  OLD & {lab}: n={len(sub)} WR={100*sum(1 for r in sub if r['R']>0)/len(sub):.1f}")
print()

results=[]
RS=lambda r: r['bars_since_sell']<50  # the WR77 core
# UNION: keep recent-sell OR (old-sell with winner-rich flag) -> recover winners
results.append(ev(lambda r: RS(r) or r['flow_accel']>20, "recent<50 | flow_accel>20"))
results.append(ev(lambda r: RS(r) or abs(r['flow_accel'])>20, "recent<50 | |flow_accel|>20"))
results.append(ev(lambda r: RS(r) or r['absorption']==1, "recent<50 | absorption"))
results.append(ev(lambda r: RS(r) or r['buy_L_recent']==1, "recent<50 | buy_L_recent"))
results.append(ev(lambda r: RS(r) or r['naslong_after_smc']==1, "recent<50 | naslong_after_smc"))
results.append(ev(lambda r: RS(r) or (r['flow_accel']>20 or r['absorption']==1), "recent<50 | (flow>20|absorb)"))
# loosen recency to recover winners while holding WR
for c in [80,100,120,150]:
    results.append(ev(lambda r,k=c: r['bars_since_sell']<k, f"bars_since_sell<{c}"))
# recency UNION strong-curvature(either sign) UNION buy_L_recent
results.append(ev(lambda r: r['bars_since_sell']<80 or abs(r['flow_accel'])>20 or r['buy_L_recent']==1,
                  "recent<80 | |flow|>20 | buy_L_recent"))
results.append(ev(lambda r: r['bars_since_sell']<100 or abs(r['flow_accel'])>20,
                  "recent<100 | |flow|>20"))
# CUT framing of complement: cut OLD-sell losers lacking any winner flag
results.append(ev(lambda r: not (r['bars_since_sell']>=100 and r['flow_accel']<=20 and r['absorption']==0 and r['buy_L_recent']==0),
                  "CUT: old>=100 & flow<=20 & no-absorb & no-buyL"))
results.append(ev(lambda r: not (r['bars_since_sell']>=80 and abs(r['flow_accel'])<=20 and r['absorption']==0),
                  "CUT: old>=80 & |flow|<=20 & no-absorb"))
results.append(ev(lambda r: not (r['bars_since_sell']>=120 and abs(r['flow_accel'])<=10),
                  "CUT: old>=120 & |flow|<=10"))

results=[x for x in results if x]
results.sort(key=lambda x:(-(x['robust']),-(x['winners_kept_pct']>=85),-x['wr_keep']))
print("RESULTS:")
for x in results:
    flag='*ROBUST*' if x['robust'] else ('~85+' if x['winners_kept_pct']>=85 else '')
    print(f"  WR{x['wr_keep']:.1f} n{x['n_keep']:4d} stk{x['streak_keep']:2d} wkept{x['winners_kept_pct']:.0f}% lcut{x['losers_cut_pct']:.0f}% [{x['y24']:.0f}/{x['y25']:.0f}/{x['y26']:.0f}] nw{x['blocks_nw']} {flag} :: {x['desc']}")
import json as J
J.dump(results, open('/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_r2lap_recover_winners_results.json','w'), indent=1)
