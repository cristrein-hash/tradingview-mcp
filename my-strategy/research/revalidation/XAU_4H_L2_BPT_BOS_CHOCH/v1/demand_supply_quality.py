#!/usr/bin/env python3
"""L2/BPT v2.2 PRUNED_BASE_V2 — demand/supply DISTANCE-QUALITY model (causal, RAW-derived).
Replaces binary presence with distance + touched + broken + polarity-relation features.
Custom OB v11 boxes as-of-bar (causal). age/freshness via x1/x2 = UNAVAILABLE (ordinal, not
temporal) -> mitigation approximated by price-touch in prior window. No SL in v2.2 -> structural
SL / R-targets UNAVAILABLE -> ATR-proxy targets (labeled). NO backtest/PnL/filter/plot/prod/SLIM.
"""
import json, csv, gzip, statistics
import os
from datetime import datetime, timezone
from bisect import bisect_right
from collections import Counter, defaultdict

D = os.environ.get("L2_OUT_DIR", "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
RAW = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
GZ_4H = [f"{RAW}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",
         f"{RAW}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
GZ_4H = [os.environ["L2_GZ_4H"]] if os.environ.get("L2_GZ_4H") else GZ_4H
GZ_1D = f"{RAW}/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz"
COB="OB Detector"; WIN=12  # retest/touch window (bars before entry)

frozen=[json.loads(l) for l in open(os.environ.get('L2_RAW_FEATURES','/tmp/raw_features_2020_2026.jsonl'))]
N=len(frozen); ts_by_idx={i:frozen[i]['ts_epoch'] for i in range(N)}
idx_by_ts={frozen[i]['ts_epoch']:i for i in range(N)}
H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR4=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR4[i]=sum(trs[i-14:i])/14

base=[r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
def label(r): return 'BOM' if r['GT_match']=='yes' else ('NAO' if r['NAO_match']=='yes' else 'UNKNOWN')

# 4H boxes as-of-bar
boxes4h={}
for gz in GZ_4H:
    with gzip.open(gz,'rt') as f:
        for line in f:
            try: d=json.loads(line)
            except: continue
            ov=d.get('ohlcv') or []
            if not ov: continue
            cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
            if not cob: continue
            dem=[];sup=[]
            for b in (cob.get('all_boxes') or []):
                hi,lo,tx=b.get('high'),b.get('low'),(b.get('text') or '').upper()
                if hi is None: continue
                (dem if tx=='DEMAND' else sup if tx=='SUPPLY' else []).append((hi,lo))
            boxes4h[ov[-1]['time']]=(dem,sup)

# 1D demand/supply timeline + ATR_D1
d1t=[];d1dem=[];d1sup=[];daily=[]
with gzip.open(GZ_1D,'rt') as f:
    for line in f:
        try: d=json.loads(line)
        except: continue
        rcd=d.get('replay_current_date')
        if rcd is None: continue
        cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
        dem=[];sup=[]
        if cob:
            for b in (cob.get('all_boxes') or []):
                tx=(b.get('text') or '').upper(); hi=b.get('high'); lo=b.get('low')
                if hi is None: continue
                (dem if tx=='DEMAND' else sup if tx=='SUPPLY' else []).append((hi,lo))
        d1t.append(rcd); d1dem.append(dem); d1sup.append(sup)
        ov=d.get('ohlcv') or []
        if ov: daily.append((ov[-1]['time'],ov[-1]['high'],ov[-1]['low'],ov[-1]['close']))
daily=sorted(set(daily)); dts=[x[0] for x in daily]; datr={}; trs=[]
for k in range(1,len(daily)):
    trs.append(max(daily[k][1]-daily[k][2],abs(daily[k][1]-daily[k-1][3]),abs(daily[k][2]-daily[k-1][3])))
    if k>=14: datr[daily[k][0]]=sum(trs[k-14:k])/14
def atrd1(ts):
    j=bisect_right(dts,ts)-1
    while j>=0 and dts[j] not in datr: j-=1
    return datr.get(dts[j]) if j>=0 else None
def d1_at(ts):
    j=bisect_right(d1t,ts)-1
    return (d1dem[j],d1sup[j]) if j>=0 else ([],[])

def fnum(x,nd=2):
    return round(x,nd) if x is not None else ''

rows=[]
for r in base:
    i=int(r['candidate_id'][1:]); ts=ts_by_idx[i]; p=float(matrix[i]['entry_close']); a=ATR4[i] or 0
    pol=float(matrix[i]['level']); lab=label(r)
    dem4,sup4=boxes4h.get(ts,(None,None)); avail4=dem4 is not None
    dem4=dem4 or []; sup4=sup4 or []
    # ---- DEMAND 4H ----
    below=[(hi,lo) for hi,lo in dem4 if hi<=p]; inside=[(hi,lo) for hi,lo in dem4 if lo<=p<=hi]
    nd=max(below,key=lambda b:b[0]) if below else (inside[0] if inside else None)
    if nd:
        d_top=(p-nd[0])/a if a else None; d_mid=(p-(nd[0]+nd[1])/2)/a if a else None
        d_low=(p-nd[1])/a if a else None; d_w=(nd[0]-nd[1])/a if a else None
    else: d_top=d_mid=d_low=d_w=None
    # touched on retest: any low in [i-WIN,i] dipped to/inside nearest demand top
    touched=False
    if nd:
        for j in range(max(0,i-WIN),i+1):
            if L[j]<=nd[0]: touched=True; break
    dem_below_pol = bool(nd and nd[0] < pol)
    dem_origin = bool(nd and a and abs(pol-nd[0])<=1.5*a and nd[0]<=pol)  # demand top near polarity = leg base (exploratory)
    # ---- SUPPLY 4H ----
    above=[(hi,lo) for hi,lo in sup4 if lo>=p]; ns=min(above,key=lambda b:b[1]) if above else None
    if ns:
        s_low=(ns[1]-p)/a if a else None; s_mid=((ns[0]+ns[1])/2-p)/a if a else None
        s_high=(ns[0]-p)/a if a else None; s_w=(ns[0]-ns[1])/a if a else None
    else: s_low=s_mid=s_high=s_w=None
    broken=[(hi,lo) for hi,lo in sup4 if hi<p]
    supply_broken=bool(broken)
    # rejection in window: high reached into nearest supply then close below its low
    rejected=False
    if ns:
        for j in range(max(0,i-WIN),i+1):
            if H[j]>=ns[1] and C[j]<ns[1]: rejected=True; break
    blk2=bool(ns and a and p<ns[1]<=p+2*a); blk3=bool(ns and a and p<ns[1]<=p+3*a); blk4=bool(ns and a and p<ns[1]<=p+4*a)
    # ---- D1 ----
    dd,ds=d1_at(ts); ad=atrd1(ts)
    dd_below=[(hi,lo) for hi,lo in dd if hi<=p]; nddl=max(dd_below,key=lambda b:b[0]) if dd_below else None
    ds_above=[(hi,lo) for hi,lo in ds if lo>=p]; ndsu=min(ds_above,key=lambda b:b[1]) if ds_above else None
    d1_dem_dist=(p-nddl[0])/ad if (nddl and ad) else None
    d1_sup_dist=(ndsu[1]-p)/ad if (ndsu and ad) else None
    # ---- polarity relation ----
    dem_from_pol=(pol-nd[0])/a if (nd and a) else None
    sup_from_pol=(ns[1]-pol)/a if (ns and a) else None
    reclaim_from_sup=s_low; reclaim_from_dem=d_top
    # ---- categories (HYPOTHESIS_ONLY / TAG_ONLY) ----
    if nd is None or (d_top is not None and d_top>4): dem_cat='DEMAND_ABSENT_OR_IRRELEVANT'
    elif touched and dem_below_pol: dem_cat='DEMAND_SUPPORTING_RETEST'
    elif dem_origin: dem_cat='DEMAND_ORIGIN_OF_LEG'
    elif d_top is not None and d_top>3: dem_cat='DEMAND_TOO_DEEP'
    else: dem_cat='DEMAND_PRESENT_NEUTRAL'
    if ns is None or (s_low is not None and s_low>4): sup_cat='CLEAN_SKY'
    elif s_low is not None and s_low<1 and rejected: sup_cat='SUPPLY_NEAR_AND_REJECTING'
    elif s_low is not None and s_low<1 and supply_broken: sup_cat='SUPPLY_NEAR_BUT_BROKEN'
    elif s_low is not None and s_low<1: sup_cat='SUPPLY_FRESH_DANGEROUS'
    elif blk2: sup_cat='SUPPLY_BLOCKS_TARGET'
    elif s_low is not None and s_low>=2: sup_cat='SUPPLY_FAR_ENOUGH'
    else: sup_cat='SUPPLY_PRESENT_NEUTRAL'
    if sup_from_pol is not None and sup_from_pol<1: pol_cat='POLARITY_UNDER_SUPPLY_PRESSURE'
    elif supply_broken and s_low is not None: pol_cat='RECLAIM_ACCEPTED_ABOVE_SUPPLY'
    elif rejected: pol_cat='RECLAIM_REJECTED_BELOW_SUPPLY'
    elif dem_below_pol and dem_from_pol is not None and dem_from_pol<=2: pol_cat='POLARITY_SUPPORTED_BY_DEMAND'
    else: pol_cat='POLARITY_FLOATING_NO_BASE'
    # exploratory quality score (higher = more BOM-like by reconciliation hints): far supply + supported polarity
    q=0
    if sup_cat in ('CLEAN_SKY','SUPPLY_FAR_ENOUGH','SUPPLY_NEAR_BUT_BROKEN'): q+=1
    if sup_cat in ('SUPPLY_FRESH_DANGEROUS','SUPPLY_NEAR_AND_REJECTING'): q-=1
    if dem_cat in ('DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG'): q+=1
    if pol_cat in ('POLARITY_SUPPORTED_BY_DEMAND','RECLAIM_ACCEPTED_ABOVE_SUPPLY'): q+=1
    if pol_cat=='POLARITY_UNDER_SUPPLY_PRESSURE': q-=1
    rows.append({'candidate_id':r['candidate_id'],'timestamp':r['timestamp'],'source':r['source'],'label':lab,'gt_id':r['gt_id'],
      'entry_price':round(p,2),'polarity':round(pol,2),'atr4h':round(a,2),
      'has_4h_demand_below':int(bool(nd)),'nearest_4h_demand_low':fnum(nd[1]) if nd else '','nearest_4h_demand_high':fnum(nd[0]) if nd else '',
      'dist_4h_demand_top_atr':fnum(d_top),'dist_4h_demand_mid_atr':fnum(d_mid),'dist_4h_demand_low_atr':fnum(d_low),'demand_4h_width_atr':fnum(d_w),
      'demand_4h_age_bars':'UNAVAILABLE(x1x2_ordinal)','demand_4h_touched_on_retest':int(touched),
      'demand_4h_origin_of_leg_cand':int(dem_origin),'demand_4h_below_polarity':int(dem_below_pol),'demand_4h_below_stop':'UNAVAILABLE(no_SL_in_v2.2)',
      'has_4h_supply_overhead':int(bool(ns)),'nearest_4h_supply_low':fnum(ns[1]) if ns else '','nearest_4h_supply_high':fnum(ns[0]) if ns else '',
      'dist_4h_supply_low_atr':fnum(s_low),'dist_4h_supply_mid_atr':fnum(s_mid),'dist_4h_supply_high_atr':fnum(s_high),'supply_4h_width_atr':fnum(s_w),
      'supply_4h_age_bars':'UNAVAILABLE(x1x2_ordinal)','supply_4h_touched_before_entry':int(rejected or supply_broken),
      'supply_4h_broken_before_entry':int(supply_broken),'supply_4h_rejected_before_entry':int(rejected),
      'supply_4h_blocks_target_2ATR':int(blk2),'supply_4h_blocks_target_3ATR':int(blk3),'supply_4h_blocks_target_4ATR':int(blk4),
      'has_d1_demand_below':int(bool(nddl)),'dist_d1_demand_atr':fnum(d1_dem_dist),
      'has_d1_supply_overhead':int(bool(ndsu)),'dist_d1_supply_atr':fnum(d1_sup_dist),
      'demand_dist_from_polarity_atr':fnum(dem_from_pol),'supply_dist_from_polarity_atr':fnum(sup_from_pol),
      'reclaim_close_dist_from_supply_atr':fnum(reclaim_from_sup),'reclaim_close_dist_from_demand_atr':fnum(reclaim_from_dem),
      'demand_category':dem_cat,'supply_category':sup_cat,'polarity_category':pol_cat,'quality_score_exploratory':q,
      'feature_availability':'4H_OB=%s;targets=ATR_proxy(no_SL);age=UNAVAILABLE' % ('yes' if avail4 else 'NO')})

FQ=list(rows[0].keys())
with open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=FQ); w.writeheader(); w.writerows(rows)
print(f"wrote demand_supply_quality.csv: {len(rows)} candidates ; 4H_OB missing-align: {sum(1 for r in rows if 'NO' in r['feature_availability'])}")
# persist for analysis stage
json.dump(rows,open(os.environ.get('L2_DSQ_ROWS','/tmp/dsq_rows.json'),'w'))
print("BOM cand:",sum(1 for r in rows if r['label']=='BOM'),"NAO cand:",sum(1 for r in rows if r['label']=='NAO'),"UNK:",sum(1 for r in rows if r['label']=='UNKNOWN'))
