import json,csv,statistics
from collections import defaultdict,Counter
D="results"
rows=json.load(open('/tmp/dsq_rows.json'))
FRAG=['GT13B','GT17A','GT23','GT24']
def fl(x):
    try: return float(x)
    except: return None
# event-level aggregation (per gt_id): median of numeric, mode of categories
def by_event(label):
    ev=defaultdict(list)
    for r in rows:
        if r['label']==label and r['gt_id']: ev[r['gt_id']].append(r)
    return ev
bom_ev=by_event('BOM'); nao_ev=by_event('NAO')
NUM=['dist_4h_demand_top_atr','dist_4h_supply_low_atr','dist_d1_demand_atr','dist_d1_supply_atr',
     'demand_dist_from_polarity_atr','supply_dist_from_polarity_atr','quality_score_exploratory']
BIN=['has_4h_demand_below','demand_4h_touched_on_retest','demand_4h_below_polarity','demand_4h_origin_of_leg_cand',
     'has_4h_supply_overhead','supply_4h_broken_before_entry','supply_4h_rejected_before_entry','supply_4h_blocks_target_2ATR']
def ev_num(ev,feat):  # per-event median across its candidates, then list over events
    out=[]
    for g,rs in ev.items():
        vals=[fl(r[feat]) for r in rs if fl(r[feat]) is not None]
        if vals: out.append(statistics.median(vals))
    return out
def ev_bin(ev,feat):  # event positive if ANY candidate has flag=1
    return [1 if any(int(r[feat])==1 for r in rs) else 0 for g,rs in ev.items()]

cmp_rows=[]
def med(l): return round(statistics.median(l),2) if l else None
for feat in NUM:
    b=ev_num(bom_ev,feat); n=ev_num(nao_ev,feat)
    cmp_rows.append({'feature':feat,'type':'numeric_atr','BOM_median':med(b),'NAO_median':med(n),
      'BOM_min':round(min(b),2) if b else None,'BOM_max':round(max(b),2) if b else None,
      'NAO_min':round(min(n),2) if n else None,'NAO_max':round(max(n),2) if n else None,
      'note':'event-level median; small-n (BOM=%d,NAO=%d)'%(len(b),len(n))})
for feat in BIN:
    b=ev_bin(bom_ev,feat); n=ev_bin(nao_ev,feat)
    cmp_rows.append({'feature':feat,'type':'binary_event','BOM_median':f"{sum(b)}/{len(b)}",'NAO_median':f"{sum(n)}/{len(n)}",
      'BOM_min':'','BOM_max':'','NAO_min':'','NAO_max':'','note':'event present in >=1 candidate'})
with open(f"{D}/l2_bpt_v2_2_bom_nao_demand_supply_comparison.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(cmp_rows[0].keys())); w.writeheader(); w.writerows(cmp_rows)

print("=== BOM vs NAO (event-level) ===")
for r in cmp_rows: print(f"  {r['feature']:<34}{r['type']:<14} BOM {str(r['BOM_median']):>8}  NAO {str(r['NAO_median']):>8}")

# category distributions
print("\n=== categories (event-level dominant) ===")
def cat_dist(ev,key):
    c=Counter()
    for g,rs in ev.items():
        c[Counter(r[key] for r in rs).most_common(1)[0][0]]+=1
    return dict(c)
for key in ['demand_category','supply_category','polarity_category']:
    print(f"  {key}: BOM {cat_dist(bom_ev,key)} | NAO {cat_dist(nao_ev,key)}")

# UNKNOWN ranking by category + quality score
unk=[r for r in rows if r['label']=='UNKNOWN']
def urank(r):
    q=int(r['quality_score_exploratory'])
    if 'NO' in r['feature_availability']: return 'UNKNOWN_NEEDS_VISUAL'
    if r['supply_category'] in ('SUPPLY_FRESH_DANGEROUS','SUPPLY_NEAR_AND_REJECTING') or r['polarity_category']=='POLARITY_UNDER_SUPPLY_PRESSURE':
        return 'UNKNOWN_NAO_LIKE_SUPPLY_PRESSURE'
    if q>=2 and r['demand_category'] in ('DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG'):
        return 'UNKNOWN_BOM_LIKE_DEMAND_SUPPLY'
    if r['supply_category'] in ('CLEAN_SKY','SUPPLY_FAR_ENOUGH'):
        return 'UNKNOWN_CLEAN_BUT_UNPROVEN'
    return 'UNKNOWN_LOW_PRIORITY'
rk=Counter()
for r in unk: r['unknown_rank']=urank(r); rk[r['unknown_rank']]+=1
with open(f"{D}/l2_bpt_v2_2_unknown_demand_supply_ranking.csv","w",newline="") as f:
    flds=['candidate_id','timestamp','source','unknown_rank','demand_category','supply_category','polarity_category','quality_score_exploratory','dist_4h_supply_low_atr','dist_4h_demand_top_atr']
    w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore'); w.writeheader(); w.writerows(unk)
print("\n=== UNKNOWN ranking ==="); 
for k,v in rk.most_common(): print(f"  {k}: {v}")

# fragile profile
frag=[r for r in rows if r['gt_id'] in FRAG and r['label']=='BOM']
with open(f"{D}/l2_bpt_v2_2_fragile_bom_demand_supply_profile.csv","w",newline="") as f:
    flds=['gt_id','candidate_id','timestamp','demand_category','supply_category','polarity_category','dist_4h_demand_top_atr','dist_4h_supply_low_atr','has_4h_demand_below','supply_4h_broken_before_entry','quality_score_exploratory']
    w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore'); w.writeheader(); w.writerows(sorted(frag,key=lambda r:r['gt_id']))
print("\n=== fragile BOM ===")
for r in sorted(frag,key=lambda r:r['gt_id']):
    print(f"  {r['gt_id']:<7} dem={r['demand_category']:<26} sup={r['supply_category']:<26} pol={r['polarity_category']:<28} q={r['quality_score_exploratory']}")

# reason atlas v4: each category as a reason with BOM/NAO/UNKNOWN event/cand counts
atlas=[]
allcats={'demand':set(r['demand_category'] for r in rows),'supply':set(r['supply_category'] for r in rows),'polarity':set(r['polarity_category'] for r in rows)}
def evcount(ev,key,cat): return sum(1 for g,rs in ev.items() if Counter(r[key] for r in rs).most_common(1)[0][0]==cat)
for side,key in [('demand','demand_category'),('supply','supply_category'),('polarity','polarity_category')]:
    for cat in sorted(allcats[side]):
        b=evcount(bom_ev,key,cat); n=evcount(nao_ev,key,cat); u=sum(1 for r in unk if r[key]==cat)
        role='visual_priority' if (b>=2 and n==0) else ('soft_warning' if (n>=b and n>0) else 'tag')
        atlas.append({'reason_id':cat,'reason_name':cat,'side':side,'description':cat.replace('_',' ').lower(),
          'BOM_count':f"{b}/{len(bom_ev)}",'NAO_count':f"{n}/{len(nao_ev)}",'UNKNOWN_count':u,
          'role':role,'confidence':'low(BOM_ev=%d,NAO_ev=%d)'%(len(bom_ev),len(nao_ev)),
          'causal_status':'causal (as-of-bar OB boxes; age UNAVAILABLE)','notes':'HYPOTHESIS_ONLY/TAG_ONLY; small-n'})
with open(f"{D}/l2_bpt_v2_2_reason_atlas_distance_quality_v4.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(atlas[0].keys())); w.writeheader(); w.writerows(atlas)
print(f"\nReason Atlas v4: {len(atlas)} reasons")
