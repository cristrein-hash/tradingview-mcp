import json,csv,statistics
D="results"
# outcome_proxy_failure_audit.csv: baseline lift table
rows=[
 {'metric':'pct_reach_+2ATR_36bars','all_bars':'67.3%','base_candidates':'66.6%','lift':'0.99x','verdict':'NO EDGE — equals base rate'},
 {'metric':'pct_reach_+3ATR_36bars','all_bars':'52.4%','base_candidates':'52.6%','lift':'1.00x','verdict':'NO EDGE — equals base rate'},
 {'metric':'candidates','all_bars':'9815','base_candidates':'2965','lift':'','verdict':'candidates = serial signals'},
 {'metric':'unique_episodes(gap>6)','all_bars':'','base_candidates':'276','lift':'','verdict':'true structural count ~276 not 2965'},
 {'metric':'cand_per_episode_mean','all_bars':'','base_candidates':'10.7','lift':'','verdict':'heavy duplication in legs'},
]
with open(f"{D}/l2_bpt_outcome_proxy_failure_audit.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# unknown_strong_vs_bom.csv: median feature comparison
q={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
ana={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_pruned_base_v2_outcome_anatomy.csv"))}
def fl(x):
    try:return float(x)
    except:return None
bom=[cid for cid,r in ana.items() if r['label']=='BOM']
us=[cid for cid,r in ana.items() if r['label']=='UNKNOWN' and r['anatomy_class'] in('STRONG_CONTINUATION','GOOD_CONTINUATION')]
def med(ids,feat,tbl):
    v=[fl(tbl[i].get(feat)) for i in ids if i in tbl and fl(tbl[i].get(feat)) is not None]
    return round(statistics.median(v),2) if v else None
feats=['dist_4h_supply_low_atr','supply_dist_from_polarity_atr','dist_4h_demand_top_atr',
       'demand_dist_from_polarity_atr','reclaim_close_dist_from_demand_atr']
cmp=[]
for fe in feats:
    cmp.append({'feature':fe,'BOM_median':med(bom,fe,q),'UNKNOWN_STRONG_median':med(us,fe,q),
      'note':'BOM cleaner supply context (farther)'})
# add anatomy mfe medians
for fe in ['mfe_atr_36','mae_atr_36','cret_atr_36']:
    cmp.append({'feature':fe,'BOM_median':med(bom,fe,ana),'UNKNOWN_STRONG_median':med(us,fe,ana),'note':'forward anatomy'})
with open(f"{D}/l2_bpt_unknown_strong_vs_bom.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(cmp[0].keys())); w.writeheader(); w.writerows(cmp)
# reclass distribution
import collections
rc=collections.Counter()
for r in csv.DictReader(open(f"{D}/l2_bpt_unknown_strong_reclassification.csv")): rc[r['reclass']]+=1
print("reclass dist:",dict(rc))
print("wrote proxy_failure_audit + unknown_strong_vs_bom")
