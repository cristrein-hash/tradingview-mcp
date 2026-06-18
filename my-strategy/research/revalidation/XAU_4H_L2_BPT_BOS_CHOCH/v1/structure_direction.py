import json,csv,statistics
from bisect import bisect_right
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_bars.jsonl')]; d1.sort(key=lambda b:b['time'])
dt=[b['time'] for b in d1]; dc=[b['close'] for b in d1]
K=5; ph=[False]*N; pl=[False]*N
for j in range(K,N-K):
    if H[j]>max(H[j-K:j]) and H[j]>max(H[j+1:j+K+1]): ph[j]=True
    if L[j]<min(L[j-K:j]) and L[j]<min(L[j+1:j+K+1]): pl[j]=True
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
SLFIX={'E2','E3','E4','E19','E20','E22','E28','E29','E31','E32','E38','E41'}
TRAP={'E15','E24','E34','E39','E36','E6','E7','E8','E9','E10','E37','E11'}
PREM={'E25','E26','E35'}
def grp(ep): return 'WIN' if ep in WIN else ('SLFIX' if ep in SLFIX else ('TRAP' if ep in TRAP else ('PREM' if ep in PREM else 'REVIEW')))
def structure_dir(i):
    # last 2 confirmed pivot highs and lows (j<=i-5). Bull structure = HH+HL; Bear = LH+LL
    lows=[(j,L[j]) for j in range(K,i-K+1) if pl[j]][-2:]
    highs=[(j,H[j]) for j in range(K,i-K+1) if ph[j]][-2:]
    hh = highs[-1][1]>highs[-2][1] if len(highs)>=2 else None
    hl = lows[-1][1]>lows[-2][1] if len(lows)>=2 else None
    # most recent structural break before i: did price close below last pivot low (bear BOS) more recently than close above last pivot high (bull BOS)?
    last_bear=None; last_bull=None
    if len(lows)>=1:
        ref_low=lows[-1][1]
        for k in range(i,max(K,i-30),-1):
            if C[k]<ref_low: last_bear=k; break
    if len(highs)>=1:
        ref_high=highs[-1][1]
        for k in range(i,max(K,i-30),-1):
            if C[k]>ref_high: last_bull=k; break
    if last_bear and (not last_bull or last_bear>last_bull): brk='BEAR'
    elif last_bull and (not last_bear or last_bull>=last_bear): brk='BULL'
    else: brk='none'
    return hh,hl,brk
rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep]; i=o['bar_idx']; ts=o['time']; p=float(matrix[i]['entry_close'])
    j=bisect_right(dt,ts)-1
    lo60=min(dc[j-59:j+1]); hi60=max(dc[j-59:j+1]); legpos=round(100*(p-lo60)/(hi60-lo60),1) if hi60>lo60 else None
    hh,hl,brk=structure_dir(i)
    rows.append({'episode_id':ep,'group':grp(ep),'legpos':legpos,'recent_break':brk,
      'HH':int(hh) if hh is not None else '','HL':int(hl) if hl is not None else ''})
print("=== recent_break (most recent BULL vs BEAR structural break before entry) by group ===")
from collections import Counter
for g in ['WIN','SLFIX','TRAP','PREM']:
    gg=[r for r in rows if r['group']==g]
    c=Counter(r['recent_break'] for r in gg)
    print(f"  {g:<7} {dict(c)}  eps_BEAR={[r['episode_id'] for r in gg if r['recent_break']=='BEAR']}")
print("\n=== KEY: within HIGH-legpos, does recent_break=BEAR isolate the top-traps from winners? ===")
hi=[r for r in rows if r['legpos'] and r['legpos']>75]
for g in ['WIN','TRAP']:
    gg=[r for r in hi if r['group']==g]
    bear=[r['episode_id'] for r in gg if r['recent_break']=='BEAR']
    print(f"  {g:<7} n={len(gg)}  BEAR-break: {len(bear)} -> {bear}")
print("\n=== hard pairs ===")
for ep in ['E40','E39','E24','E34','E15','E27','E30','E5','E13','E21','E23']:
    r=next(x for x in rows if x['episode_id']==ep)
    print(f"  {ep:<4}{r['group']:<6} legpos:{str(r['legpos']):<6} recent_break:{r['recent_break']:<5} HH:{r['HH']} HL:{r['HL']}")
