import json,csv,statistics
from bisect import bisect_right
from collections import defaultdict
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);C=[r['close'] for r in frozen];V=[r.get('volume') or 0 for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))} if False else {int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_bars.jsonl')]; d1.sort(key=lambda b:b['time'])
dt=[b['time'] for b in d1]; dc=[b['close'] for b in d1]
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
SLFIX={'E2','E3','E4','E19','E20','E22','E28','E29','E31','E32','E38','E41'}
TRAP={'E15','E24','E34','E39','E36','E6','E7','E8','E9','E10','E37','E11'}
PREM={'E25','E26','E35'}
def grp(ep): return 'WIN' if ep in WIN else ('SLFIX' if ep in SLFIX else ('TRAP' if ep in TRAP else ('PREM' if ep in PREM else 'REVIEW')))
def fl(x):
    try:return float(x)
    except:return None
rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep]; i=o['bar_idx']; ts=o['time']; p=float(matrix[i]['entry_close']); q=qual.get(o['candidate_id'],{})
    # legpos 60d
    j=bisect_right(dt,ts)-1
    lo60=min(dc[j-59:j+1]); hi60=max(dc[j-59:j+1]); legpos=round(100*(p-lo60)/(hi60-lo60),1) if hi60>lo60 else None
    d1slope=round(100*(dc[j]-dc[j-20])/dc[j-20],2)
    # exhaustion indicators at entry
    nas_short=fl(matrix[i]['nas_short_10']) or 0
    sell_bub=fl(matrix[i]['sell_bub_10']) or 0
    large_sell=fl(matrix[i]['large_sell_10']) or 0
    rsi=fl(matrix[i]['rsi'])
    volr=round(V[i]/(sum(V[i-20:i])/20),2) if i>=20 and sum(V[i-20:i])>0 else None
    # composite exhaustion score (climax of distribution)
    exh=0
    if nas_short>=6: exh+=1
    if large_sell>=1: exh+=1
    if rsi and rsi>=68: exh+=1
    if volr and volr>=1.5: exh+=1
    rows.append({'episode_id':ep,'group':grp(ep),'legpos':legpos,'d1slope20':d1slope,
      'nas_short':nas_short,'sell_bub':sell_bub,'large_sell':large_sell,'rsi':rsi,'vol_ratio':volr,'exh_score':exh})

# strata by legpos
def strat(lp):
    return 'HIGH(>75)' if (lp is not None and lp>75) else ('MID(50-75)' if (lp is not None and lp>=50) else 'LOW(<50)')
print("=== INTERACTION legpos × exhaustion (by group within leg-position strata) ===")
for s in ['LOW(<50)','MID(50-75)','HIGH(>75)']:
    sub=[r for r in rows if strat(r['legpos'])==s]
    print(f"\n--- {s}  (n={len(sub)}) ---")
    for g in ['WIN','SLFIX','TRAP','PREM','REVIEW']:
        gg=[r for r in sub if r['group']==g]
        if not gg: continue
        eh=statistics.median([r['exh_score'] for r in gg])
        nas=statistics.median([r['nas_short'] for r in gg]); rsis=[r['rsi'] for r in gg if r['rsi']]
        print(f"   {g:<7} n={len(gg)}  exh_score_med={eh}  nas_short_med={nas}  rsi_med={round(statistics.median(rsis),0) if rsis else '-'}  eps={[r['episode_id'] for r in gg]}")

# Candidate discriminator: TRAP_FLAG = HIGH legpos AND exhaustion present
print("\n=== CANDIDATE RULE: flag = (legpos>75 AND exh_score>=2)  -> would-be TRAP ===")
def flag(r): return (r['legpos'] is not None and r['legpos']>75 and r['exh_score']>=2)
from collections import Counter
for g in ['WIN','SLFIX','TRAP','PREM']:
    gg=[r for r in rows if r['group']==g]; f=[r['episode_id'] for r in gg if flag(r)]
    print(f"  {g:<7} flagged {len(f)}/{len(gg)}  -> {f}")
print("\n=== RECALL-GATE: do the 9 winners survive (NOT flagged)? ===")
win_flagged=[r['episode_id'] for r in rows if r['group']=='WIN' and flag(r)]
print(f"  winners flagged (BAD if any): {win_flagged or 'NONE — recall preserved 9/9'}")

# hard pairs
print("\n=== hard pairs ===")
for ep in ['E40','E39','E24','E34','E27','E30','E1','E5','E21','E23','E17','E13']:
    r=next(x for x in rows if x['episode_id']==ep)
    print(f"  {ep:<4}{r['group']:<6} legpos:{str(r['legpos']):<6} exh:{r['exh_score']} nas:{r['nas_short']} largeSell:{r['large_sell']} rsi:{r['rsi']} vol:{r['vol_ratio']} flag:{int(flag(r))}")
with open(f"{D}/l2_bpt_legpos_exhaustion.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())+['trap_flag']); w.writeheader()
    for r in rows: r2=dict(r); r2['trap_flag']=int(flag(r)); w.writerow(r2)
