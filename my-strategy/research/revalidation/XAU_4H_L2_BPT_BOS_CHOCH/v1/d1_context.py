import json,csv,statistics
from collections import Counter
from bisect import bisect_right
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_bars.jsonl')]  # {time, close}
d1.sort(key=lambda b:b['time']); dt=[b['time'] for b in d1]; dc=[b['close'] for b in d1]
def sma(arr,i,p): return sum(arr[i-p+1:i+1])/p if i>=p-1 else None
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
SLFIX={'E2','E3','E4','E19','E20','E22','E28','E29','E31','E32','E38','E41'}
TRAP={'E15','E24','E34','E39','E36','E6','E7','E8','E9','E10','E37','E11'}
PREM={'E25','E26','E35'}
def grp(ep): return 'WIN' if ep in WIN else ('SLFIX' if ep in SLFIX else ('TRAP' if ep in TRAP else ('PREM' if ep in PREM else 'REVIEW')))
rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep]; ts=o['time']; i=o['bar_idx']; p=float(matrix[i]['entry_close'])
    j=bisect_right(dt,ts)-1  # last daily closed <= entry time (causal)
    if j<60: rows.append({'episode_id':ep,'group':grp(ep)}); continue
    s20=sma(dc,j,20); s50=sma(dc,j,50)
    # 1D structure: close vs SMA, 20-day & 50-day slope, position vs recent 20d high/low
    hi20=max(dc[j-19:j+1]); lo20=min(dc[j-19:j+1])
    above50 = dc[j]>s50 if s50 else None
    slope20d = round((dc[j]-dc[j-20])/ (abs(dc[j])*0.01),2)  # in % of price approx
    # 1D recent lower-highs? compare last 3 ~weekly highs (every 5 days)
    near_hi = round((hi20-p)/(abs(p)*0.01),2)  # % below 20d high
    rows.append({'episode_id':ep,'group':grp(ep),'d1_above_sma50':int(above50) if above50 is not None else '',
      'd1_close_vs_sma20_pct':round(100*(dc[j]-s20)/s20,2) if s20 else '',
      'd1_slope20d_pct':round(100*(dc[j]-dc[j-20])/dc[j-20],2),
      'd1_pct_below_20dhigh':round(100*(hi20-p)/p,2),
      'd1_pct_above_20dlow':round(100*(p-lo20)/p,2)})
def show(g):
    sub=[r for r in rows if r['group']==g and 'd1_above_sma50' in r]
    def med(k):
        v=[r[k] for r in sub if isinstance(r.get(k),(int,float))]; return round(statistics.median(v),2) if v else None
    def frac1(k):
        v=[r[k] for r in sub if r.get(k) in (0,1)]; return f"{sum(v)}/{len(v)}" if v else '-'
    print(f"{g:<7}(n={len(sub)}) above_sma50:{frac1('d1_above_sma50')}  med vs_sma20%:{med('d1_close_vs_sma20_pct')}  slope20d%:{med('d1_slope20d_pct')}  below20dHigh%:{med('d1_pct_below_20dhigh')}  above20dLow%:{med('d1_pct_above_20dlow')}")
print("=== 1D CONTEXT by group (causal: last daily closed <= entry) ===")
for g in ['WIN','SLFIX','TRAP','PREM','REVIEW']: show(g)
print("\n=== hard cases E39(trap) vs E40(win), E27(win) vs E25/26/35(prem), E24/E34(top) ===")
for ep in ['E40','E39','E27','E25','E26','E35','E24','E34','E1','E30']:
    r=next(x for x in rows if x['episode_id']==ep)
    print(f"  {ep:<4}{r['group']:<7} above50:{r.get('d1_above_sma50')} vsSMA20%:{r.get('d1_close_vs_sma20_pct')} slope20d%:{r.get('d1_slope20d_pct')} below20dHi%:{r.get('d1_pct_below_20dhigh')} above20dLo%:{r.get('d1_pct_above_20dlow')}")
