#!/usr/bin/env python3
"""
_r2lap_loser_cut.py
R2-KEPT subset (r2_keep==1) lapidation, CUT-WHEN orientation.

The flow-takeover lens (_r2lap_flow_takeover.py) showed bars_since_buycross is a
sparse-recent feature (median 99): keep-when-recent retains too few winners.
So pivot to CUT-WHEN loser signatures that remove a SMALL slice of mostly-losers
while keeping >=85% winners. Lens stays flow-takeover: the loser signature is
"too far past the cross AND weak buy flow" + contextual confluence.

Gate (robust): wr_keep>68.54 AND y24>=66.05 AND y25>=70.91 AND y26>=65.19
AND winners_kept_pct>=85 AND >=6/8 blocks not-worse AND streak_keep<24.
RAW-causal, as-of-bar.
"""
import json, itertools

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = sorted([r for r in ROWS if r['r2_keep'] == 1], key=lambda r: r['low_t'])
N = len(KEPT); WINS = sum(r['win'] for r in KEPT); WR_BASE = 100*WINS/N
BLOCKS = sorted(set(r['block'] for r in KEPT))
YEAR_BASE = {yr: 100*sum(x['win'] for x in KEPT if x['yr']==yr)/max(1,len([x for x in KEPT if x['yr']==yr])) for yr in (2024,2025,2026)}
BLOCK_BASE = {b: 100*sum(x['win'] for x in KEPT if x['block']==b)/len([x for x in KEPT if x['block']==b]) for b in BLOCKS}

def streak(rows):
    s=m=0
    for r in rows:
        if r['win']==0: s+=1; m=max(m,s)
        else: s=0
    return m
STREAK_BASE = streak(KEPT)

def evaluate(keep_fn, desc):
    kept=[r for r in KEPT if keep_fn(r)]
    if not kept: return None
    n=len(kept); wk=sum(r['win'] for r in kept); wr=100*wk/n
    wkp=100*wk/WINS
    lt=N-WINS; lk=n-wk; lcut=100*(lt-lk)/lt if lt else 0
    yr_wr={}; yr_ok=True
    for yr in (2024,2025,2026):
        g=[r for r in kept if r['yr']==yr]
        if g:
            w=100*sum(x['win'] for x in g)/len(g); yr_wr[yr]=w
            if w<YEAR_BASE[yr]-1e-9: yr_ok=False
        else: yr_wr[yr]=None; yr_ok=False
    nb=0
    for b in BLOCKS:
        g=[r for r in kept if r['block']==b]
        if g and 100*sum(x['win'] for x in g)/len(g) >= BLOCK_BASE[b]-1e-9: nb+=1
    rob=(wr>WR_BASE+1e-9 and yr_ok and wkp>=85.0 and nb>=6 and streak(kept)<STREAK_BASE)
    return dict(desc=desc,n_keep=n,wr_keep=round(wr,2),streak_keep=streak(kept),
                winners_kept_pct=round(wkp,2),losers_cut_pct=round(lcut,2),
                y24=round(yr_wr[2024],2) if yr_wr[2024] is not None else None,
                y25=round(yr_wr[2025],2) if yr_wr[2025] is not None else None,
                y26=round(yr_wr[2026],2) if yr_wr[2026] is not None else None,
                blocks_not_worse=nb,robust=rob)

print(f"BASE n={N} WR={WR_BASE:.2f} strk={STREAK_BASE} y24={YEAR_BASE[2024]:.2f} y25={YEAR_BASE[2025]:.2f} y26={YEAR_BASE[2026]:.2f}")

# First: WR among losers/winners by single-feature buckets to find cheap loser slices.
def cut_quality(name, cut_fn):
    cut=[r for r in KEPT if cut_fn(r)]
    if not cut: return None
    n=len(cut); w=sum(r['win'] for r in cut)
    return (name, n, round(100*w/n,1), n-w, w)  # desc, n_cut, WR_in_cut, losers_cut, winners_lost

print("\n=== CUT-SLICE QUALITY (low WR-in-cut = good loser slice) ===")
cuts = [
 ("buycross>200", lambda r: r['bars_since_buycross']>200),
 ("buycross>300", lambda r: r['bars_since_buycross']>300),
 ("buycross>400", lambda r: r['bars_since_buycross']>400),
 ("ratio4<=2", lambda r: r['buy_sell_ratio4']<=2.0),
 ("ratio4<=1", lambda r: r['buy_sell_ratio4']<=1.0),
 ("ratio4==0", lambda r: r['buy_sell_ratio4']==0.0),
 ("closepos<0.2", lambda r: r['low_closepos']<0.2),
 ("closepos<0.3", lambda r: r['low_closepos']<0.3),
 ("deadzone", lambda r: r['is_deadzone']==1),
 ("sell_decel<0(big)", lambda r: r['sell_decel']<-1),
 ("flow_accel<-20", lambda r: r['flow_accel']<-20),
 ("flow_accel<-40", lambda r: r['flow_accel']<-40),
 ("sell_skew<0", lambda r: r['sell_skew_mig']<0),
 ("buycross>300 & ratio4<=2", lambda r: r['bars_since_buycross']>300 and r['buy_sell_ratio4']<=2.0),
 ("buycross>300 & closepos<0.3", lambda r: r['bars_since_buycross']>300 and r['low_closepos']<0.3),
 ("ratio4<=2 & closepos<0.3", lambda r: r['buy_sell_ratio4']<=2.0 and r['low_closepos']<0.3),
 ("deadzone & ratio4<=2", lambda r: r['is_deadzone']==1 and r['buy_sell_ratio4']<=2.0),
 ("deadzone & buycross>300", lambda r: r['is_deadzone']==1 and r['bars_since_buycross']>300),
 ("ratio4<=2 & sell_skew<0", lambda r: r['buy_sell_ratio4']<=2.0 and r['sell_skew_mig']<0),
 ("closepos<0.3 & flow_accel<-20", lambda r: r['low_closepos']<0.3 and r['flow_accel']<-20),
 ("ratio4<=2 & flow_accel<-20", lambda r: r['buy_sell_ratio4']<=2.0 and r['flow_accel']<-20),
 ("buycross>400 & ratio4<=2", lambda r: r['bars_since_buycross']>400 and r['buy_sell_ratio4']<=2.0),
 ("ratio4<=1 & closepos<0.3", lambda r: r['buy_sell_ratio4']<=1.0 and r['low_closepos']<0.3),
]
for name,fn in cuts:
    cq=cut_quality(name,fn)
    if cq: print(f"  {cq[0]:<34} n_cut={cq[1]:>4} WRin={cq[2]:>5} losers_cut={cq[3]:>4} winners_lost={cq[4]:>4}")

# Now evaluate KEEP = not(cut) as full filters
results=[]
for name,fn in cuts:
    results.append(evaluate(lambda r,f=fn: not f(r), f"CUT {name}"))

# layered cuts (cut if ANY of several weak-loser conditions)
def anycut(r):
    return (r['bars_since_buycross']>300 and r['buy_sell_ratio4']<=2.0) or \
           (r['buy_sell_ratio4']<=1.0) or \
           (r['low_closepos']<0.25 and r['flow_accel']<-20)
results.append(evaluate(lambda r: not anycut(r), "CUT union(late&weak | ratio<=1 | weaklow&decel)"))

def anycut2(r):
    return (r['buy_sell_ratio4']<=2.0 and r['low_closepos']<0.3) or \
           (r['is_deadzone']==1 and r['buy_sell_ratio4']<=2.0)
results.append(evaluate(lambda r: not anycut2(r), "CUT union(weak&lowclose | dead&weak)"))

def anycut3(r):
    return (r['buy_sell_ratio4']<=2.0 and r['sell_skew_mig']<0) or \
           (r['buy_sell_ratio4']<=1.0) or \
           (r['low_closepos']<0.25 and r['flow_accel']<-20)
results.append(evaluate(lambda r: not anycut3(r), "CUT union(weak&skewneg | ratio<=1 | weaklow&decel)"))

results=[r for r in results if r]
results.sort(key=lambda r:(r['robust'],r['wr_keep'],r['winners_kept_pct']),reverse=True)

print("\n=== KEEP=not(cut) FILTERS ===")
print(f"{'desc':<52}{'n':>5}{'WR':>7}{'strk':>5}{'wkept%':>8}{'lcut%':>7}{'y24':>7}{'y25':>7}{'y26':>7}{'blk':>4}{'rob':>5}")
for r in results:
    print(f"{r['desc']:<52}{r['n_keep']:>5}{r['wr_keep']:>7}{r['streak_keep']:>5}"
          f"{r['winners_kept_pct']:>8}{r['losers_cut_pct']:>7}"
          f"{str(r['y24']):>7}{str(r['y25']):>7}{str(r['y26']):>7}{r['blocks_not_worse']:>4}{str(r['robust']):>5}")

print(f"\nROBUST: {sum(1 for r in results if r['robust'])}")
for r in results:
    if r['robust']: print(json.dumps(r))
