"""
_reopt5_streak_attack.py — can any predicate break the 30-loser cluster (2026-02-25)
while keeping >=85% winners? Report per-predicate: streak after, winners kept, wr, and
how many of the 30 cluster-losers it cuts.
"""
from _reopt5_harness import ROWS, evaluate, max_losing_streak, BASE_WINS, BASE_WR
SENT=-10000000.0
def nz(v): return v is not None and v!=SENT

# rebuild the 30 cluster ids
s=sorted(ROWS,key=lambda r:r['low_t'])
cur=0;start=0;best=(0,0,0)
for i,r in enumerate(s):
    if r['win']==0:
        if cur==0:start=i
        cur+=1
        if cur>best[0]:best=(cur,start,i)
    else:cur=0
ln,a,b=best
cluster=set(id(r) for r in s[a:b+1])

preds={
 'cut_chop(h1_trend==0)': lambda r: not (r['h1_trend']==0),
 'keep_trend_up':         lambda r: r['h1_trend']==1,
 'cut_loweff(<0.12)':     lambda r: not (nz(r['path_eff']) and r['path_eff']<0.12),
 'cut_loweff(<0.20)':     lambda r: not (nz(r['path_eff']) and r['path_eff']<0.20),
 'cut_loweff(<0.30)':     lambda r: not (nz(r['path_eff']) and r['path_eff']<0.30),
 'keep_eff>=0.20':        lambda r: nz(r['path_eff']) and r['path_eff']>=0.20,
 'cut_regime_young<8':    lambda r: not (nz(r['regime_age_h']) and r['regime_age_h']<8),
 'keep_disp4>=2':         lambda r: nz(r['disp4_atr']) and r['disp4_atr']>=2.0,
 'keep_closepos>=0.5':    lambda r: nz(r['low_closepos']) and r['low_closepos']>=0.5,
 'cut_brate>=5':          lambda r: not (nz(r['buy_sell_ratio4']) and r['buy_sell_ratio4']>=5),
 'keep_atr_norm<=1.4':    lambda r: nz(r['atr_regime']) and r['atr_regime']<=1.4,
}
print(f"cluster size={ln}  base WR {BASE_WR:.2f}  base winners {BASE_WINS}")
print(f"{'pred':28s} {'streak':>7} {'wr':>6} {'win%':>6} {'clust_cut':>9} {'n_keep':>7}")
for name,fn in preds.items():
    keep=[r for r in ROWS if fn(r)]
    streak=max_losing_streak(keep)
    wk=sum(r['win'] for r in keep)
    winpct=100*wk/BASE_WINS
    wr=100*wk/len(keep) if keep else 0
    clust_cut=sum(1 for r in s[a:b+1] if not fn(r))
    print(f"{name:28s} {streak:7d} {wr:6.2f} {winpct:6.1f} {clust_cut:9d} {len(keep):7d}")
