import json,csv,statistics
from collections import Counter,defaultdict
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen); H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
def mfe36(i):
    e=min(i+36,N-1)
    if e<=i or not ATR[i]: return None
    return (max(H[i+1:e+1])-C[i])/ATR[i]
# ---- baseline: STRONG/GOOD rate over ALL bars vs candidates ----
allm=[mfe36(i) for i in range(2*14,N-37)]; allm=[x for x in allm if x is not None]
base_all_strong=sum(1 for x in allm if x>=3)/len(allm)
base_all_good=sum(1 for x in allm if x>=2)/len(allm)
ana={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_pruned_base_v2_outcome_anatomy.csv"))}
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_pruned_base_v2_demand_supply_quality.csv".replace('pruned_base_v2_demand','v2_2_pruned_base_v2_demand')))} if False else {r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
cand=list(ana.values())
def fl(x):
    try:return float(x)
    except:return None
cand_m=[fl(r['mfe_atr_36']) for r in cand if fl(r['mfe_atr_36']) is not None]
cand_strong=sum(1 for x in cand_m if x>=3)/len(cand_m)
cand_good=sum(1 for x in cand_m if x>=2)/len(cand_m)
print("=== BASELINE: STRONG/GOOD rate (pure forward MFE36) ===")
print(f"  ALL bars      : >=3ATR {base_all_strong:.1%}  >=2ATR {base_all_good:.1%}  (n={len(allm)})")
print(f"  base candidates: >=3ATR {cand_strong:.1%}  >=2ATR {cand_good:.1%}  (n={len(cand_m)})")
print(f"  => lift candidate vs all: x{cand_good/base_all_good:.2f} (>=2ATR)")

# ---- episode clustering: group candidates with entry-bar gap <=6 ----
idxs=sorted(int(r['candidate_id'][1:]) for r in cand)
episodes=[]; cur=[idxs[0]]
for a,b in zip(idxs,idxs[1:]):
    if b-a<=6: cur.append(b)
    else: episodes.append(cur); cur=[b]
episodes.append(cur)
cpe=[len(e) for e in episodes]
print(f"\n=== CLUSTERING ===")
print(f"  candidates {len(idxs)} -> unique episodes (gap>6) {len(episodes)} | cand/episode med {statistics.median(cpe)} max {max(cpe)} mean {sum(cpe)/len(episodes):.1f}")
# STRONG per episode
id2cls={int(r['candidate_id'][1:]):r['anatomy_class'] for r in cand}
id2lab={int(r['candidate_id'][1:]):r['label'] for r in cand}
strong_eps=sum(1 for e in episodes if any(id2cls[i] in ('STRONG_CONTINUATION','GOOD_CONTINUATION') for i in e))
print(f"  episodes with >=1 STRONG/GOOD: {strong_eps}/{len(episodes)}")

# ---- UNKNOWN_STRONG duplicate of BOM? within +-12 bars of a BOM entry ----
bom_idx=[int(r['candidate_id'][1:]) for r in cand if id2lab[int(r['candidate_id'][1:])]=='BOM']
us=[int(r['candidate_id'][1:]) for r in cand if id2lab[int(r['candidate_id'][1:])]=='UNKNOWN' and id2cls[int(r['candidate_id'][1:])] in ('STRONG_CONTINUATION','GOOD_CONTINUATION')]
def near_bom(i,w=12): return any(abs(i-b)<=w for b in bom_idx)
dup=sum(1 for i in us if near_bom(i))
# same-episode-as-BOM
bom_eps=set(); 
for k,e in enumerate(episodes):
    if any(id2lab[i]=='BOM' for i in e): bom_eps.add(k)
us_in_bom_ep=sum(1 for i in us if any(i in e for k,e in enumerate(episodes) if k in bom_eps))
print(f"\n=== UNKNOWN_STRONG analysis (n={len(us)}) ===")
print(f"  within +-12 bars of a BOM entry: {dup} ({100*dup/len(us):.0f}%)")
print(f"  sharing an episode with a BOM: {us_in_bom_ep} ({100*us_in_bom_ep/len(us):.0f}%)")
# L2-likeness via demand/supply quality
def l2like(cid):
    q=qual.get(cid)
    if not q: return False
    return q['demand_category'] in ('DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG') and q['supply_category'] not in ('SUPPLY_FRESH_DANGEROUS','SUPPLY_NEAR_AND_REJECTING')
us_l2=sum(1 for i in us if l2like('C%d'%i))
print(f"  L2-like (demand-supporting/origin + supply not dangerous): {us_l2} ({100*us_l2/len(us):.0f}%)")
print(f"  NOT L2-like (generic bull follow-through): {len(us)-us_l2} ({100*(len(us)-us_l2)/len(us):.0f}%)")

# ---- BOM vs UNKNOWN_STRONG quick compare ----
def med_feat(ids,feat,src):
    vals=[]
    for i in ids:
        r=(qual if src=='q' else id2cls).get('C%d'%i) if src=='q' else None
        if src=='q':
            v=fl((qual.get('C%d'%i) or {}).get(feat))
            if v is not None: vals.append(v)
    return round(statistics.median(vals),2) if vals else None
print(f"\n=== BOM vs UNKNOWN_STRONG (median) ===")
for feat in ['dist_4h_supply_low_atr','supply_dist_from_polarity_atr','dist_4h_demand_top_atr','reclaim_close_dist_from_demand_atr']:
    print(f"  {feat:<36} BOM {med_feat(bom_idx,feat,'q')}  US {med_feat(us,feat,'q')}")

# write small outputs
with open(f"{D}/l2_bpt_episode_cluster_analysis.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(['episode_id','n_candidates','has_BOM','has_STRONG','first_ts','span_bars'])
    for k,e in enumerate(episodes):
        ts=frozen[e[0]]['ts_epoch']
        w.writerow([k,len(e),int(any(id2lab[i]=='BOM' for i in e)),int(any(id2cls[i] in('STRONG_CONTINUATION','GOOD_CONTINUATION') for i in e)),ts,e[-1]-e[0]])
import datetime
with open(f"{D}/l2_bpt_unknown_strong_reclassification.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(['candidate_id','near_BOM_12b','shares_BOM_episode','l2_like','reclass'])
    for i in us:
        nb=near_bom(i); se=any(i in e for k,e in enumerate(episodes) if k in bom_eps); l2=l2like('C%d'%i)
        rc='DUPLICATE_SIGNAL_IN_BULL_LEG' if (nb or se) else ('TRUE_L2_CONTINUATION_CANDIDATE' if l2 else 'GENERIC_BULL_FOLLOW_THROUGH')
        w.writerow(['C%d'%i,int(nb),int(se),int(l2),rc])
print("\nwrote cluster + reclassification CSVs")
