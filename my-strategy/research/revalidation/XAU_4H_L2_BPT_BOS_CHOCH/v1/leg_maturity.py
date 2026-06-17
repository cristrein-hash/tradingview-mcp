import json,csv,statistics
from bisect import bisect_right
D="results"
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_bars.jsonl')]; d1.sort(key=lambda b:b['time'])
dt=[b['time'] for b in d1]; dc=[b['close'] for b in d1]
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
SLFIX={'E2','E3','E4','E19','E20','E22','E28','E29','E31','E32','E38','E41'}
TRAP={'E15','E24','E34','E39','E36','E6','E7','E8','E9','E10','E37','E11'}
PREM={'E25','E26','E35'}
def grp(ep): return 'WIN' if ep in WIN else ('SLFIX' if ep in SLFIX else ('TRAP' if ep in TRAP else ('PREM' if ep in PREM else 'REVIEW')))
rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep]; ts=o['time']; i=o['bar_idx']; p=float(matrix[i]['entry_close'])
    j=bisect_right(dt,ts)-1
    if j<60: continue
    lo60=min(dc[j-59:j+1]); hi60=max(dc[j-59:j+1])
    jlo=j-59+dc[j-59:j+1].index(lo60); jhi=j-59+dc[j-59:j+1].index(hi60)
    pct_above_60low=round(100*(p-lo60)/lo60,2)
    days_since_60low=j-jlo
    pct_below_60high=round(100*(hi60-p)/p,2)
    # leg position: 0=at 60d low, 100=at 60d high
    legpos=round(100*(p-lo60)/(hi60-lo60),1) if hi60>lo60 else None
    rows.append({'episode_id':ep,'group':grp(ep),'pct_above_60low':pct_above_60low,
      'days_since_60low':days_since_60low,'pct_below_60high':pct_below_60high,'legpos_0low_100high':legpos})
def show(g):
    sub=[r for r in rows if r['group']==g]
    def med(k): 
        v=[r[k] for r in sub if isinstance(r.get(k),(int,float))]; return round(statistics.median(v),1) if v else None
    print(f"{g:<7}(n={len(sub)}) %above60low:{med('pct_above_60low')}  days_since_60low:{med('days_since_60low')}  %below60high:{med('pct_below_60high')}  legpos:{med('legpos_0low_100high')}")
print("=== LEG MATURITY (60d horizon) by group ===")
for g in ['WIN','SLFIX','TRAP','PREM']: show(g)
print("\n=== hard pairs ===")
for ep in ['E40','E39','E27','E25','E26','E35','E24','E34','E1','E30','E17','E5','E21']:
    r=next((x for x in rows if x['episode_id']==ep),None)
    if r: print(f"  {ep:<4}{r['group']:<6} %above60low:{str(r['pct_above_60low']):<6} days_since_60low:{str(r['days_since_60low']):<4} legpos(0low-100high):{r['legpos_0low_100high']}")
