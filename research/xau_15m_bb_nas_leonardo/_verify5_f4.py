import json
rows=[json.loads(l) for l in open('dataset_5atr.jsonl')]

def keep(r):
    return r['rsi']>=53.0 and r['disp4_atr']>=0.77 and r['sell_skew_mig']<=0.65

def wr(rs):
    n=len(rs); w=sum(x['win'] for x in rs)
    return (n, w, 100*w/n if n else 0.0)

def maxstreak(rs):
    # max consecutive losers in chronological order
    mx=cur=0
    for x in rs:
        if x['win']==0:
            cur+=1; mx=max(mx,cur)
        else:
            cur=0
    return mx

# chronological order: by block then by low_t
rows_sorted=sorted(rows, key=lambda r:(r['block'], r['low_t']))

base=rows_sorted
kept=[r for r in base if keep(r)]

bn,bw,bwr=wr(base)
kn,kw,kwr=wr(kept)
print(f"BASE   n={bn} wins={bw} WR={bwr:.2f} maxLossStreak={maxstreak(base)}")
print(f"KEEP   n={kn} wins={kw} WR={kwr:.2f} maxLossStreak={maxstreak(kept)}")
print(f"deltaWR=+{kwr-bwr:.2f}pp")

total_winners=sum(r['win'] for r in base)
winners_kept=sum(r['win'] for r in kept)
print(f"winners_kept_pct={100*winners_kept/total_winners:.1f}  ({winners_kept}/{total_winners})")
total_losers=bn-bw
losers_kept=kn-kw
print(f"losers_cut_pct={100*(total_losers-losers_kept)/total_losers:.1f}")

print("\n--- BY YEAR (base WR -> keep WR, deltapp) ---")
worse_year=[]
for y in sorted(set(r['yr'] for r in base)):
    yb=[r for r in base if r['yr']==y]
    yk=[r for r in yb if keep(r)]
    _,_,ybwr=wr(yb); _,_,ykwr=wr(yk)
    flag='' if ykwr>=ybwr else '  <<< WORSE'
    print(f"  {y}: base={ybwr:.2f}  keep={ykwr:.2f}  d={ykwr-ybwr:+.2f}  (n_keep={len(yk)}){flag}")
    if ykwr<ybwr: worse_year.append(y)

print("\n--- BY BLOCK (base WR -> keep WR) ---")
worse_blocks=0
for b in sorted(set(r['block'] for r in base)):
    bb=[r for r in base if r['block']==b]
    bk=[r for r in bb if keep(r)]
    _,_,bbwr=wr(bb); _,_,bkwr=wr(bk)
    flag='' if bkwr>=bbwr else '  <<< WORSE'
    if bkwr<bbwr: worse_blocks+=1
    print(f"  {b}: base={bbwr:.2f}  keep={bkwr:.2f}  d={bkwr-bbwr:+.2f}  (n_keep={len(bk)}){flag}")

print(f"\nworse_years={worse_year}  worse_blocks={worse_blocks}/8")

# Cherry-pick: +/-20% neighborhood collapse on each threshold
print("\n--- NEIGHBORHOOD +/-20% (cherry-pick check) ---")
def keep_p(r,t_rsi,t_disp,t_skew):
    return r['rsi']>=t_rsi and r['disp4_atr']>=t_disp and r['sell_skew_mig']<=t_skew
import itertools
for nm,(lo,hi,which) in {
    'rsi':( 53.0*0.8,53.0*1.2,'rsi'),
    'disp4_atr':(0.77*0.8,0.77*1.2,'disp'),
    'sell_skew_mig':(0.65*0.8,0.65*1.2,'skew')}.items():
    for t in (lo,53.0 if which=='rsi' else (0.77 if which=='disp' else 0.65),hi):
        if which=='rsi': k=[r for r in base if keep_p(r,t,0.77,0.65)]
        elif which=='disp': k=[r for r in base if keep_p(r,53.0,t,0.65)]
        else: k=[r for r in base if keep_p(r,53.0,0.77,t)]
        _,_,w=wr(k)
        print(f"  {nm}={t:.3f}: WR={w:.2f} n={len(k)} d=+{w-bwr:.2f}")
