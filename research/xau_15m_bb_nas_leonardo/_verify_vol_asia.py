import json
from collections import defaultdict, Counter

rows=[json.loads(l) for l in open('entry_dataset.jsonl')]

# outcome field = R_reclaim (per-trade R)
def R(r): return r['R_reclaim']

# baseline over full corpus
allR=[R(r) for r in rows]
base_avg=sum(allR)/len(allR)
base_wr=100*sum(1 for x in allR if x>0)/len(allR)
print(f'BASE n={len(rows)} avgR={base_avg:.4f} WR={base_wr:.2f}')

# RULE
def sel(r):
    return (r['vol_low_vs_med'] <= 0.9) and (0 <= r['hour'] <= 6)

S=[r for r in rows if sel(r)]
Rs=[R(r) for r in S]
n=len(S)
avg=sum(Rs)/n
wr=100*sum(1 for x in Rs if x>0)/n
print(f'\nRULE n={n} avgR={avg:.4f} WR={wr:.2f}')

# per year
print('\n-- per year (avgR / n / vs base) --')
peryear={}
for yr in (2024,2025,2026):
    sub=[R(r) for r in S if r['yr']==yr]
    if sub:
        a=sum(sub)/len(sub)
        peryear[yr]=(a,len(sub))
        print(f'  y{yr}: avgR={a:.4f} n={len(sub)}')
# year base for reference
print('  -- base per year --')
for yr in (2024,2025,2026):
    sub=[R(r) for r in rows if r['yr']==yr]
    print(f'    y{yr}: base avgR={sum(sub)/len(sub):.4f} n={len(sub)}')

# sign stability across years
signs=set(1 if peryear[y][0]>base_avg else 0 for y in peryear)
all_above=all(peryear[y][0]>base_avg for y in peryear)
all_pos=all(peryear[y][0]>0 for y in peryear)
print(f'\n  all years avgR>0: {all_pos} ; all years > base: {all_above}')

# leave-one-block-out
print('\n-- leave-one-block-out (avgR of rule on remaining blocks) --')
blocks=sorted(set(r['block'] for r in rows))
lobo=[]
for b in blocks:
    sub=[R(r) for r in S if r['block']!=b]
    a=sum(sub)/len(sub)
    lobo.append((b,a,len(sub)))
    print(f'  drop {b}: avgR={a:.4f} n={len(sub)}')
worst_lobo=min(x[1] for x in lobo)
print(f'  worst LOBO avgR={worst_lobo:.4f}')

# also: avgR WITHIN each block (the held-out block itself), to see per-block sign
print('\n-- per-block (the block itself) --')
perblock_signs=[]
for b in blocks:
    sub=[R(r) for r in S if r['block']==b]
    if sub:
        a=sum(sub)/len(sub)
        perblock_signs.append(a)
        print(f'  {b}: avgR={a:.4f} n={len(sub)}')
neg_blocks=sum(1 for a in perblock_signs if a<0)
print(f'  blocks with negative avgR: {neg_blocks}/{len(perblock_signs)}')

# ex-top trades
print('\n-- ex-top-N (remove biggest R winners) --')
Rs_sorted=sorted(Rs, reverse=True)
print('  top10 R:', [round(x,2) for x in Rs_sorted[:10]])
for k in (1,2,3,5):
    rem=Rs_sorted[k:]
    print(f'  ex-top{k}: avgR={sum(rem)/len(rem):.4f} n={len(rem)}')

# contribution: what fraction of total R from top2
total=sum(Rs)
top2=sum(Rs_sorted[:2])
print(f'\n  total R={total:.2f} ; top2 R={top2:.2f} ({100*top2/total:.1f}% of total)')
print(f'  top5 R={sum(Rs_sorted[:5]):.2f} ({100*sum(Rs_sorted[:5])/total:.1f}%)')

# count of winners
nwin=sum(1 for x in Rs if x>0)
print(f'  winners={nwin}/{n}')

# multiple testing context: how does a RANDOM hour-band + vol filter compare?
# quick: shuffle-style null - permute outcomes, recompute rule avgR many times
import random
random.seed(0)
idx_sel=[i for i,r in enumerate(rows) if sel(r)]
nulls=[]
for _ in range(2000):
    samp=random.sample(allR,n)
    nulls.append(sum(samp)/n)
nulls.sort()
p=sum(1 for x in nulls if x>=avg)/len(nulls)
print(f'\n  null (random n={n} draws) mean={sum(nulls)/len(nulls):.4f} p(avgR>=rule)={p:.4f}')
print(f'  null 95pct={nulls[int(0.95*len(nulls))]:.4f} 99pct={nulls[int(0.99*len(nulls))]:.4f}')
