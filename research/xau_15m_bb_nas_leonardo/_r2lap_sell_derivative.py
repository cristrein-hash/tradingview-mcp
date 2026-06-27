#!/usr/bin/env python3
"""
R2 lapidation — LENS: temporal derivative of selling (sell_decel, flow_accel,
bars_since_sell, sell_skew_mig) + contextual combos.

Operates ONLY on r2_keep==1 (n=2355). win = R>0. Goal: a KEEP-when / CUT-when
filter that raises WR above 68.54, lowers max-losing-streak, keeps >=85% winners,
stable across 2024/2025/2026 (>= per-year base) AND >=6/8 time-blocks not-worse.

Forbidden features: h1_eff, h4_pos (define R2), R, win. RAW-causal only.
"""
import json, itertools

PATH='/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl'
rows=[json.loads(l) for l in open(PATH)]
kept=[r for r in rows if r['r2_keep']==1]
kept.sort(key=lambda r:r['low_t'])

N=len(kept)
W=[r for r in kept if r['R']>0]
WR_BASE=100*len(W)/N

def streak(subset):
    s=sorted(subset,key=lambda r:r['low_t'])
    mls=cur=0
    for r in s:
        if r['R']>0: cur=0
        else: cur+=1; mls=max(mls,cur)
    return mls

# per-year base WR
yr_base={}
for yr in (2024,2025,2026):
    yk=[r for r in kept if r['yr']==yr]
    yr_base[yr]=100*sum(1 for r in yk if r['R']>0)/len(yk)

STREAK_BASE=streak(kept)
TOT_WIN=len(W)

# 8 contiguous time blocks (by low_t order)
blocks=[]
bs=N//8
for i in range(8):
    a=i*bs; b=(i+1)*bs if i<7 else N
    blocks.append(kept[a:b])
block_base=[100*sum(1 for r in bl if r['R']>0)/len(bl) for bl in blocks]

print(f"BASE n={N} WR={WR_BASE:.2f} streak={STREAK_BASE} winners={TOT_WIN}")
print(f"yr_base {yr_base}")
print(f"block_base {[round(x,1) for x in block_base]}\n")

def evaluate(pred, desc):
    keep=[r for r in kept if pred(r)]
    if not keep: return None
    nk=len(keep)
    wk=[r for r in keep if r['R']>0]
    wr=100*len(wk)/nk
    stk=streak(keep)
    wkept=100*len(wk)/TOT_WIN
    lcut=100*(1-(nk-len(wk))/(N-TOT_WIN))  # % of losers cut
    # per-year
    yr_wr={}
    for yr in (2024,2025,2026):
        yk=[r for r in keep if r['yr']==yr]
        yr_wr[yr]=100*sum(1 for r in yk if r['R']>0)/len(yk) if yk else 0.0
    # block not-worse count
    nw=0
    for i,bl in enumerate(blocks):
        blk=[r for r in bl if pred(r)]
        if blk:
            bwr=100*sum(1 for r in blk if r['R']>0)/len(blk)
            if bwr>=block_base[i]-1e-9: nw+=1
        else:
            nw+=1  # empty block = no worse trades present
    robust = (wr>WR_BASE and all(yr_wr[y]>=yr_base[y]-1e-9 for y in (2024,2025,2026))
              and wkept>=85.0 and nw>=6 and stk<STREAK_BASE)
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,2),streak_keep=stk,
                winners_kept_pct=round(wkept,2),losers_cut_pct=round(lcut,2),
                y24=round(yr_wr[2024],2),y25=round(yr_wr[2025],2),y26=round(yr_wr[2026],2),
                blocks_nw=nw,robust=robust)

results=[]

# ---- single-feature scans (lens) ----
# sell_decel >0 = selling decelerating (exhaustion). sentinel <-9e6 means undefined.
for thr in [0.0,0.05,0.1,0.2,0.3]:
    results.append(evaluate(lambda r,t=thr: r['sell_decel']>t and r['sell_decel']<9e6,
                            f"sell_decel>{thr} (decel & defined)"))
# sell_skew_mig >0 = SELL thinning L->S = exhaustion
for thr in [0.0,0.5,1.0,2.0]:
    results.append(evaluate(lambda r,t=thr: r['sell_skew_mig']>t, f"sell_skew_mig>{thr}"))
# flow_accel curvature
for thr in [0,5,10,20]:
    results.append(evaluate(lambda r,t=thr: r['flow_accel']>t, f"flow_accel>{thr}"))
    results.append(evaluate(lambda r,t=thr: r['flow_accel']<-t and t>0, f"flow_accel<-{thr}"))
# bars_since_sell — old sell = sell pressure faded
for thr in [50,100,150,200]:
    results.append(evaluate(lambda r,t=thr: r['bars_since_sell']>t, f"bars_since_sell>{thr}"))
    results.append(evaluate(lambda r,t=thr: r['bars_since_sell']<t, f"bars_since_sell<{thr}"))
# absorption
results.append(evaluate(lambda r: r['absorption']==1, "absorption==1"))
# buy_sell_ratio4
for thr in [4,5,6]:
    results.append(evaluate(lambda r,t=thr: r['buy_sell_ratio4']>=t, f"buy_sell_ratio4>={thr}"))

# ---- 2-feature combos (contextual) ----
sd = lambda r: r['sell_decel']>0.05 and r['sell_decel']<9e6   # decel defined
ssk= lambda r: r['sell_skew_mig']>0.0                          # thinning
fa = lambda r: r['flow_accel']>0                               # positive curvature
bss= lambda r: r['bars_since_sell']>100                        # sell faded
ab = lambda r: r['absorption']==1
bsr= lambda r: r['buy_sell_ratio4']>=5

combos2=[
 (lambda r: sd(r) and ssk(r), "sell_decel>0.05 & sell_skew_mig>0"),
 (lambda r: sd(r) and fa(r), "sell_decel>0.05 & flow_accel>0"),
 (lambda r: sd(r) and bss(r), "sell_decel>0.05 & bars_since_sell>100"),
 (lambda r: ssk(r) and fa(r), "sell_skew_mig>0 & flow_accel>0"),
 (lambda r: ssk(r) and bss(r), "sell_skew_mig>0 & bars_since_sell>100"),
 (lambda r: sd(r) and ab(r), "sell_decel>0.05 & absorption"),
 (lambda r: ssk(r) and ab(r), "sell_skew_mig>0 & absorption"),
 (lambda r: fa(r) and ab(r), "flow_accel>0 & absorption"),
 (lambda r: sd(r) and bsr(r), "sell_decel>0.05 & buy_sell_ratio4>=5"),
 (lambda r: ssk(r) and bsr(r), "sell_skew_mig>0 & buy_sell_ratio4>=5"),
 (lambda r: bss(r) and bsr(r), "bars_since_sell>100 & buy_sell_ratio4>=5"),
 (lambda r: sd(r) and not ssk(r) and fa(r), "decel>0.05 & skew<=0 & flow_accel>0"),
]
for p,d in combos2: results.append(evaluate(p,d))

# ---- 3-feature combos ----
combos3=[
 (lambda r: sd(r) and ssk(r) and fa(r), "decel>0.05 & skew>0 & flow_accel>0"),
 (lambda r: sd(r) and ssk(r) and bss(r), "decel>0.05 & skew>0 & bars_since_sell>100"),
 (lambda r: sd(r) and fa(r) and bsr(r), "decel>0.05 & flow_accel>0 & ratio4>=5"),
 (lambda r: ssk(r) and fa(r) and bsr(r), "skew>0 & flow_accel>0 & ratio4>=5"),
 (lambda r: sd(r) and ab(r) and fa(r), "decel>0.05 & absorption & flow_accel>0"),
 (lambda r: (sd(r) or ssk(r)) and fa(r) and bsr(r), "(decel|skew) & flow_accel>0 & ratio4>=5"),
]
for p,d in combos3: results.append(evaluate(p,d))

# ---- CUT-when framing: cut active/escalating selling ----
# loser hypothesis: selling still active/escalating -> sell_decel<=0 (accel) AND recent sell
cut_active = lambda r: not (r['sell_decel']<=0 and r['sell_decel']>-9e6 and r['bars_since_sell']<100)
results.append(evaluate(cut_active,"CUT: sell accel(<=0) & recent sell(<100)"))
cut2 = lambda r: not (r['sell_decel']<=0 and r['sell_decel']>-9e6 and r['flow_accel']<0)
results.append(evaluate(cut2,"CUT: sell accel & flow_accel<0"))
cut3 = lambda r: not (r['sell_skew_mig']<0 and r['bars_since_sell']<100)
results.append(evaluate(cut3,"CUT: skew<0(thickening) & recent sell"))

results=[x for x in results if x]
# print all, sort by wr then winners_kept
results.sort(key=lambda x:(-x['wr_keep'], -x['winners_kept_pct']))
print("ALL (sorted by WR):")
for x in results:
    flag='ROBUST' if x['robust'] else ''
    print(f"  WR{x['wr_keep']:.1f} n{x['n_keep']:4d} stk{x['streak_keep']:2d} "
          f"wkept{x['winners_kept_pct']:.0f}% lcut{x['losers_cut_pct']:.0f}% "
          f"[{x['y24']:.0f}/{x['y25']:.0f}/{x['y26']:.0f}] nw{x['blocks_nw']} {flag} :: {x['desc']}")

print("\nROBUST ONLY:")
rob=[x for x in results if x['robust']]
for x in rob:
    print(f"  WR{x['wr_keep']:.1f} n{x['n_keep']} stk{x['streak_keep']} wkept{x['winners_kept_pct']:.0f}% lcut{x['losers_cut_pct']:.0f}% [{x['y24']}/{x['y25']}/{x['y26']}] nw{x['blocks_nw']} :: {x['desc']}")
if not rob: print("  (none)")

# dump json for downstream
import json as J
open('/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/_r2lap_sell_derivative_results.json','w').write(J.dumps(results,indent=1))
