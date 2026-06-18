import json,csv,statistics
from bisect import bisect_right
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];C=[r['close'] for r in frozen];V=[r.get('volume') or 0 for r in frozen];RS=[r.get('rsi') for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_bars.jsonl')]; d1.sort(key=lambda b:b['time'])
dt=[b['time'] for b in d1]; dc=[b['close'] for b in d1]
SELL={'plot_6','plot_8','plot_10'}
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
SLFIX={'E2','E3','E4','E19','E20','E22','E28','E29','E31','E32','E38','E41'}
TRAP={'E15','E24','E34','E39','E36','E6','E7','E8','E9','E10','E37','E11'}
PREM={'E25','E26','E35'}
def grp(ep): return 'WIN' if ep in WIN else ('SLFIX' if ep in SLFIX else ('TRAP' if ep in TRAP else ('PREM' if ep in PREM else 'REVIEW')))
def rsi_bear_div(i,look=12):
    # price higher-high vs RSI lower-high over lookback (classic bearish divergence)
    seg_h=[(j,H[j],RS[j]) for j in range(max(0,i-look),i+1) if RS[j] is not None]
    if len(seg_h)<6: return 0
    # two halves: recent high vs prior high
    mid=len(seg_h)//2
    prior=max(seg_h[:mid],key=lambda x:x[1]); recent=max(seg_h[mid:],key=lambda x:x[1])
    return 1 if (recent[1]>prior[1] and recent[2]<prior[2]) else 0
def sell_climax(i,look=10):
    bubs=frozen[i].get('bubbles_recent') or []
    return sum(1 for b in bubs if b.get('plot_id') in SELL and b.get('bars_ago') is not None and 0<=b['bars_ago']<=look)
rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep]; i=o['bar_idx']; ts=o['time']; p=float(matrix[i]['entry_close'])
    j=bisect_right(dt,ts)-1
    lo60=min(dc[j-59:j+1]); hi60=max(dc[j-59:j+1]); legpos=round(100*(p-lo60)/(hi60-lo60),1) if hi60>lo60 else None
    rows.append({'episode_id':ep,'group':grp(ep),'legpos':legpos,
      'rsi_bear_div':rsi_bear_div(i),'sell_climax':sell_climax(i),'rsi':RS[i]})
print("=== WITHIN HIGH-legpos (>75): separate the 4 top-traps from valid? ===")
hi=[r for r in rows if r['legpos'] and r['legpos']>75]
print(f"  n in HIGH stratum: {len(hi)}")
for g in ['WIN','SLFIX','TRAP','PREM','REVIEW']:
    gg=[r for r in hi if r['group']==g]
    if not gg: continue
    bd=sum(r['rsi_bear_div'] for r in gg); sc=statistics.median([r['sell_climax'] for r in gg])
    print(f"  {g:<7} n={len(gg)}  rsi_bear_div={bd}/{len(gg)}  sell_climax_med={sc}  eps={[r['episode_id'] for r in gg]}")
print("\n=== the 4 HIGH-legpos traps individually ===")
for ep in ['E15','E24','E34','E39']:
    r=next(x for x in rows if x['episode_id']==ep)
    print(f"  {ep:<4} legpos:{r['legpos']} rsi_bear_div:{r['rsi_bear_div']} sell_climax:{r['sell_climax']} rsi:{r['rsi']}")
print("\n=== the 6 HIGH-legpos winners individually (must NOT look like traps) ===")
for ep in ['E5','E13','E21','E23','E27','E30']:
    r=next(x for x in rows if x['episode_id']==ep)
    print(f"  {ep:<4} legpos:{r['legpos']} rsi_bear_div:{r['rsi_bear_div']} sell_climax:{r['sell_climax']} rsi:{r['rsi']}")
print("\n=== E39 vs E40 (the decisive pair) ===")
for ep in ['E40','E39']:
    r=next(x for x in rows if x['episode_id']==ep)
    print(f"  {ep:<4}{r['group']:<6} legpos:{r['legpos']} rsi_bear_div:{r['rsi_bear_div']} sell_climax:{r['sell_climax']} rsi:{r['rsi']}")
