#!/usr/bin/env python3
"""L2/BPT v2.2 — macro-context VISUAL RECONCILIATION for 17 BOM + 6 NAO.
Re-measures WITHOUT tight thresholds: nearest 4H OB DEMAND below entry (leg-support),
nearest 4H SUPPLY above (overhead), nearest D1 DEMAND below (to expose the 0.5-ATR artifact).
Reports raw ATR distances so the previous at_D1_demand=0/17 can be diagnosed (threshold vs real).
RAW gz read-only. NO backtest/PnL/filter/plot/production/SLIM.
"""
import json, csv, gzip
from datetime import datetime, timezone
from bisect import bisect_right

D = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
RAW = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
GZ_4H = [f"{RAW}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",
         f"{RAW}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
GZ_1D = f"{RAW}/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz"
COB = "OB Detector"

# frozen input -> ts/ATR4
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
ts_by_idx={i:frozen[i]['ts_epoch'] for i in range(len(frozen))}
H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR4=[None]*len(frozen); trs=[]
for i in range(1,len(frozen)):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR4[i]=sum(trs[i-14:i])/14

# the 23 GT/NAO events -> representative candidate (from matrix labels)
matrix=[r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))]
for r in matrix: r['ei']=int(r['candidate_id'][1:])
BOM=['GT01','GT02','GT03','GT08','GT09','GT10','GT13A','GT13B','GT15','GT17A','GT18','GT21','GT23','GT24','GT25','GT27','GT20']
NAO=['GT04A','GT06A','GT06B','GT12','GT14_NAO','GT19A']
# pick the earliest candidate-bar per event as representative (entry proxy)
def rep(gid,label):
    cs=[r for r in matrix if r['gt_id']==gid and r['label']==label]
    if not cs: return None
    return min(cs,key=lambda r:r['ei'])
events=[(g,'BOM') for g in BOM]+[(g,'NAO') for g in NAO]

# 4H boxes as-of-bar
boxes4h={}
for gz in GZ_4H:
    with gzip.open(gz,'rt') as f:
        for line in f:
            try: d=json.loads(line)
            except: continue
            ov=d.get('ohlcv') or []
            if not ov: continue
            bt=ov[-1]['time']
            cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
            if not cob: continue
            dem=[];sup=[]
            for b in (cob.get('all_boxes') or []):
                hi,lo,tx=b.get('high'),b.get('low'),(b.get('text') or '').upper()
                x1=b.get('x1'); x2=b.get('x2')
                if hi is None: continue
                (dem if tx=='DEMAND' else sup if tx=='SUPPLY' else []).append((hi,lo,x1,x2))
            boxes4h[bt]=(dem,sup)

# 1D demand timeline + ATR_D1
d1t=[];d1d=[];daily=[]
with gzip.open(GZ_1D,'rt') as f:
    for line in f:
        try: d=json.loads(line)
        except: continue
        rcd=d.get('replay_current_date')
        if rcd is None: continue
        cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
        dem=[(b['high'],b['low']) for b in (cob.get('all_boxes') or []) if cob and (b.get('text') or '').upper()=='DEMAND' and b.get('high') is not None]
        d1t.append(rcd); d1d.append(dem)
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
def d1dem(ts):
    j=bisect_right(d1t,ts)-1
    return d1d[j] if j>=0 else []

rows=[]
for gid,lab in events:
    r=rep(gid,lab)
    if not r: rows.append({'gt_id':gid,'label':lab,'note':'no representative candidate'}); continue
    i=r['ei']; ts=ts_by_idx[i]; p=float(r['entry_close']); a4=ATR4[i] or 0
    dem4,sup4=boxes4h.get(ts,(None,None)); avail4 = dem4 is not None
    dem4=dem4 or []; sup4=sup4 or []
    # nearest 4H DEMAND below entry (box high <= p): leg-support demand
    below=[(hi,lo) for hi,lo,_,_ in dem4 if hi<=p]
    nd=max(below,key=lambda b:b[0]) if below else None     # highest demand below = immediate support
    inside_dem=[(hi,lo) for hi,lo,_,_ in dem4 if lo<=p<=hi]
    # nearest 4H SUPPLY above (low>=p)
    above=[(hi,lo) for hi,lo,_,_ in sup4 if lo>=p]
    ns=min(above,key=lambda b:b[1]) if above else None
    # broken supply: any supply box now fully below p (high<p) -> price broke above it
    broken=[(hi,lo) for hi,lo,_,_ in sup4 if hi<p]
    # D1 demand below
    dem1=d1dem(ts); ad1=atrd1(ts)
    d1below=[(hi,lo) for hi,lo in dem1 if hi<=p]
    nd1=max(d1below,key=lambda b:b[0]) if d1below else None
    rows.append({'gt_id':gid,'label':lab,'timestamp':r['ts'],'entry_price':round(p,2),'atr4h':round(a4,2),
      'has_4h_demand_below':int(bool(nd) or bool(inside_dem)),
      'nearest_4h_demand_low':round(nd[1],2) if nd else (round(inside_dem[0][1],2) if inside_dem else ''),
      'nearest_4h_demand_high':round(nd[0],2) if nd else (round(inside_dem[0][0],2) if inside_dem else ''),
      'distance_to_4h_demand_atr':round((p-nd[0])/a4,2) if (nd and a4) else (0.0 if inside_dem else ''),
      'inside_4h_demand':int(bool(inside_dem)),
      'n_4h_demand_below':len(below),
      'has_4h_supply_overhead':int(bool(ns)),
      'nearest_4h_supply_low':round(ns[1],2) if ns else '','nearest_4h_supply_high':round(ns[0],2) if ns else '',
      'distance_to_4h_supply_atr':round((ns[1]-p)/a4,2) if (ns and a4) else '',
      'n_4h_supply_broken_below':len(broken),
      'supply_4h_broken_or_rejected':'broken_recent' if broken else ('overhead' if ns else 'none'),
      'has_d1_demand_below':int(bool(nd1)),
      'distance_to_d1_demand_atr':round((p-nd1[0])/ad1,2) if (nd1 and ad1) else '',
      'prev_at_D1_demand_flag':'0 (artifact: tol 0.5 ATR_D1 too tight)',
      'feature_availability':'4H_OB=%s' % ('yes' if avail4 else 'NO'),
      'visual_reconciliation_status':'NEEDS_USER_VISUAL_CONFIRM',
      'mismatch_reason':'4H demand-below not measured before; D1 tol too tight'})

flds=list(rows[0].keys())
with open(f"{D}/l2_bpt_macro_context_gt_visual_reconciliation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

# summary
def cnt(lab,key,pred): return sum(1 for x in rows if x.get('label')==lab and pred(x.get(key)))
import statistics
def meddist(lab,key):
    vals=[x[key] for x in rows if x.get('label')==lab and isinstance(x.get(key),(int,float))]
    return round(statistics.median(vals),2) if vals else None
print("=== RECONCILIATION (17 BOM + 6 NAO) ===")
print(f"4H demand below present: BOM {cnt('BOM','has_4h_demand_below',lambda v:v==1)}/17  NAO {cnt('NAO','has_4h_demand_below',lambda v:v==1)}/6")
print(f"  median dist_to_4h_demand_atr: BOM {meddist('BOM','distance_to_4h_demand_atr')}  NAO {meddist('NAO','distance_to_4h_demand_atr')}")
print(f"D1 demand below present:  BOM {cnt('BOM','has_d1_demand_below',lambda v:v==1)}/17  NAO {cnt('NAO','has_d1_demand_below',lambda v:v==1)}/6")
print(f"  median dist_to_d1_demand_atr: BOM {meddist('BOM','distance_to_d1_demand_atr')}  NAO {meddist('NAO','distance_to_d1_demand_atr')}")
print(f"4H supply overhead:       BOM {cnt('BOM','has_4h_supply_overhead',lambda v:v==1)}/17  NAO {cnt('NAO','has_4h_supply_overhead',lambda v:v==1)}/6")
print(f"  median dist_to_4h_supply_atr: BOM {meddist('BOM','distance_to_4h_supply_atr')}  NAO {meddist('NAO','distance_to_4h_supply_atr')}")
print(f"supply broken recently:   BOM {cnt('BOM','n_4h_supply_broken_below',lambda v:isinstance(v,int) and v>0)}/17  NAO {cnt('NAO','n_4h_supply_broken_below',lambda v:isinstance(v,int) and v>0)}/6")
print(f"\nwrote {len(rows)} rows -> gt_visual_reconciliation.csv")