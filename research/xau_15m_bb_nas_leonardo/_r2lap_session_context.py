#!/usr/bin/env python3
"""
_r2lap_session_context.py
The only feature that separates the 24-streak losers is session (deadzone /
ny_overlap). Test session keep-when filters + session x flow-takeover combos
against the full robust gate. RAW-causal, as-of-bar.
"""
import json
ROWS=[json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT=sorted([r for r in ROWS if r['r2_keep']==1],key=lambda r:r['low_t'])
N=len(KEPT);WINS=sum(r['win'] for r in KEPT);WR_BASE=100*WINS/N
BLOCKS=sorted(set(r['block'] for r in KEPT))
YB={yr:100*sum(x['win'] for x in KEPT if x['yr']==yr)/len([x for x in KEPT if x['yr']==yr]) for yr in(2024,2025,2026)}
BB={b:100*sum(x['win'] for x in KEPT if x['block']==b)/len([x for x in KEPT if x['block']==b]) for b in BLOCKS}
def streak(rows):
    s=m=0
    for r in rows:
        if r['win']==0:s+=1;m=max(m,s)
        else:s=0
    return m
SB=streak(KEPT)
def ev(fn,desc):
    k=[r for r in KEPT if fn(r)]
    if not k:return None
    n=len(k);wk=sum(r['win'] for r in k);wr=100*wk/n;wkp=100*wk/WINS
    lt=N-WINS;lcut=100*(lt-(n-wk))/lt
    yw={};yok=True
    for yr in(2024,2025,2026):
        g=[r for r in k if r['yr']==yr]
        if g:
            w=100*sum(x['win'] for x in g)/len(g);yw[yr]=w
            if w<YB[yr]-1e-9:yok=False
        else:yw[yr]=None;yok=False
    nb=sum(1 for b in BLOCKS if [x for x in k if x['block']==b] and 100*sum(x['win'] for x in k if x['block']==b)/len([x for x in k if x['block']==b])>=BB[b]-1e-9)
    rob=(wr>WR_BASE+1e-9 and yok and wkp>=85 and nb>=6 and streak(k)<SB)
    return dict(desc=desc,n_keep=n,wr_keep=round(wr,2),streak_keep=streak(k),
                winners_kept_pct=round(wkp,2),losers_cut_pct=round(lcut,2),
                y24=round(yw[2024],2) if yw[2024] else None,y25=round(yw[2025],2) if yw[2025] else None,
                y26=round(yw[2026],2) if yw[2026] else None,blocks_not_worse=nb,robust=rob)
print(f"BASE WR={WR_BASE:.2f} strk={SB} y24={YB[2024]:.2f} y25={YB[2025]:.2f} y26={YB[2026]:.2f}")
R=[]
R.append(ev(lambda r:r['is_deadzone']==0,"keep not-deadzone"))
R.append(ev(lambda r:r['is_ny_overlap']==1 or r['is_london_open']==1,"keep ny_overlap OR london"))
R.append(ev(lambda r:not(r['is_deadzone']==1 and r['buy_sell_ratio4']>3),"CUT deadzone&strongbuy(latebull-trap)"))
R.append(ev(lambda r:not(r['is_deadzone']==1 and r['sell_skew_mig']>0),"CUT deadzone&sell_skew>0"))
R.append(ev(lambda r:not(r['is_deadzone']==1 and r['bars_since_buycross']>200),"CUT deadzone&latecross"))
R.append(ev(lambda r:not(r['is_deadzone']==1 and r['is_ny_overlap']==0 and r['is_london_open']==0 and r['buy_sell_ratio4']>3),"CUT deadzone&nosession&strongbuy"))
R.append(ev(lambda r:not(r['is_deadzone']==1 and r['low_closepos']<0.6 and r['buy_sell_ratio4']>3),"CUT deadzone&midclose&strongbuy"))
R=[r for r in R if r]
R.sort(key=lambda r:(r['robust'],r['wr_keep'],r['winners_kept_pct']),reverse=True)
print(f"{'desc':<46}{'n':>5}{'WR':>7}{'strk':>5}{'wkept%':>8}{'lcut%':>7}{'y24':>7}{'y25':>7}{'y26':>7}{'blk':>4}{'rob':>5}")
for r in R:
    print(f"{r['desc']:<46}{r['n_keep']:>5}{r['wr_keep']:>7}{r['streak_keep']:>5}{r['winners_kept_pct']:>8}{r['losers_cut_pct']:>7}{str(r['y24']):>7}{str(r['y25']):>7}{str(r['y26']):>7}{r['blocks_not_worse']:>4}{str(r['robust']):>5}")
print(f"\nROBUST: {sum(1 for r in R if r['robust'])}")
for r in R:
    if r['robust']:print(json.dumps(r))
