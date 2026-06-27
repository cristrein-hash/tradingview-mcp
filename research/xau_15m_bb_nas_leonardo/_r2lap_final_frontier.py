#!/usr/bin/env python3
"""
R2 lapidation phase 4 — FINAL frontier at the 85%-winner-retention boundary.
Goal: among filters keeping >=85% winners, find any that lift WR>68.54, drop
streak<24, and stay >= per-year base + >=6/8 blocks. Wide net of contextual
unions anchored on recency + curvature + session + buy_L_recent (orthogonal to
the sell-derivative lens). RAW-causal, r2_keep==1 only.
"""
import json,itertools
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
    nw=sum(1 for i,bl in enumerate(blocks) if (lambda blk: (not blk) or 100*sum(1 for r in blk if r['R']>0)/len(blk)>=block_base[i]-1e-9)([r for r in bl if pred(r)]))
    stk=streak(keep)
    rob=(wr>WR_BASE and all(yw[y]>=yr_base[y]-1e-9 for y in (2024,2025,2026)) and wkept>=85 and nw>=6 and stk<STREAK_BASE)
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,2),streak_keep=stk,
                winners_kept_pct=round(wkept,2),losers_cut_pct=round(lcut,2),
                y24=round(yw[2024],2),y25=round(yw[2025],2),y26=round(yw[2026],2),blocks_nw=nw,robust=rob)

results=[]
# atoms (orthogonal winner-rich pockets identified earlier)
A_rec=lambda c: (lambda r,k=c: r['bars_since_sell']<k)
A_flow=lambda t: (lambda r,k=t: abs(r['flow_accel'])>k)
A_buyL=lambda r: r['buy_L_recent']==1
A_lon=lambda r: r['is_london_open']==1
A_absorb=lambda r: r['absorption']==1
# scan unions keeping recency loose enough for >=85% retention
for rec in [100,120,150,170,200]:
    for ft in [10,15,20]:
        for extra,lab in [(lambda r:False,''),(A_buyL,'|buyL'),(A_lon,'|lon'),
                          (A_absorb,'|absorb'),(lambda r:A_buyL(r) or A_lon(r),'|buyL|lon')]:
            p=lambda r,c=rec,t=ft,e=extra: r['bars_since_sell']<c or abs(r['flow_accel'])>t or e(r)
            results.append(ev(p,f"recent<{rec} | |flow|>{ft}{lab}"))
# CUT-complement framing: cut deep-old + flat-curvature + no winner flag (loser pocket)
for rec in [150,170,200]:
    for ft in [10,15]:
        results.append(ev(lambda r,c=rec,t=ft: not (r['bars_since_sell']>=c and abs(r['flow_accel'])<=t and r['buy_L_recent']==0 and r['absorption']==0),
                          f"CUT: old>={rec} & |flow|<={ft} & no-buyL & no-absorb"))

results=[x for x in results if x]
# keep only >=85% retention rows for the report, plus best overall
ret85=[x for x in results if x['winners_kept_pct']>=85]
ret85.sort(key=lambda x:(-(x['robust']),-x['wr_keep'],-x['winners_kept_pct']))
print(f"BASE WR={WR_BASE:.2f} streak={STREAK_BASE} yr_base={ {k:round(v,1) for k,v in yr_base.items()} }")
print(f"\n>=85% WINNER-RETENTION rows ({len(ret85)}):")
for x in ret85[:25]:
    flag='*ROBUST*' if x['robust'] else ''
    print(f"  WR{x['wr_keep']:.1f} n{x['n_keep']:4d} stk{x['streak_keep']:2d} wkept{x['winners_kept_pct']:.0f}% lcut{x['losers_cut_pct']:.0f}% [{x['y24']:.0f}/{x['y25']:.0f}/{x['y26']:.0f}] nw{x['blocks_nw']} {flag} :: {x['desc']}")

allres=sorted(results,key=lambda x:-x['wr_keep'])
print(f"\nTop WR overall (any retention):")
for x in allres[:8]:
    print(f"  WR{x['wr_keep']:.1f} n{x['n_keep']:4d} stk{x['streak_keep']:2d} wkept{x['winners_kept_pct']:.0f}% lcut{x['losers_cut_pct']:.0f}% [{x['y24']:.0f}/{x['y25']:.0f}/{x['y26']:.0f}] nw{x['blocks_nw']} :: {x['desc']}")
import json as J
J.dump(results, open('/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_r2lap_final_frontier_results.json','w'), indent=1)
