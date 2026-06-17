#!/usr/bin/env python3
"""L2/BPT v2.2 PRUNED_BASE_V2 — enrich with macro-structural layers (RAW-derived, causal).
Layers: Custom OB v11 DEMAND/SUPPLY (4H, as-of-bar), supply_overhead (4H), at_d1_demand v2
(1D, causal d1_record_used guard: max replay_current_date <= entry_time; inside OR near_from_above).
macro_leg = REFERENCE_ONLY (only 5 manual block rows in pack) -> NOT derived (no invention).
NO PnL/backtest/plot/MCP/production/SLIM. RAW gz read-only.
"""
import json, csv, gzip
from datetime import datetime, timezone
from collections import defaultdict
from bisect import bisect_right

BASE_D = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
RAW_DIR = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
GZ_4H = [f"{RAW_DIR}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",
         f"{RAW_DIR}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
GZ_1D = f"{RAW_DIR}/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz"
COB = "OB Detector"
TOL_D1 = 0.5  # *ATR_D1 — diagnostic tolerance (calibration, reported; not a final threshold)
TOL_4H = 0.5  # *ATR_4H

# ---- candidates: entry_idx -> ts_epoch (frozen input) + matrix labels (PRUNED_BASE_V2 kept only) ----
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
ts_by_idx={i:frozen[i]['ts_epoch'] for i in range(len(frozen))}
# ATR4H (Wilder14) from frozen OHLC
H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR4=[None]*len(frozen); p=14
trs=[]
for i in range(1,len(frozen)):
    tr=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])); trs.append(tr)
    if i>=p:
        ATR4[i]=sum(trs[i-p:i])/p
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{BASE_D}/l2_bpt_v2_2_candidate_matrix.csv"))}
base=[r for r in csv.DictReader(open(f"{BASE_D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
cand_idx=[int(r['candidate_id'][1:]) for r in base]
cand_ts={i:ts_by_idx[i] for i in cand_idx}

# ---- 4H Custom OB boxes: bar_time -> (demand[(hi,lo)], supply[(hi,lo)]) , as-of that bar ----
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
            dem=[]; sup=[]
            for b in (cob.get('all_boxes') or []):
                hi,lo,tx=b.get('high'),b.get('low'),(b.get('text') or '').upper()
                if hi is None or lo is None: continue
                if tx=='DEMAND': dem.append((hi,lo))
                elif tx=='SUPPLY': sup.append((hi,lo))
            boxes4h[bt]=(dem,sup)  # last snapshot for that bar wins

# ---- 1D timeline: sorted replay_current_date -> (DEMAND boxes) ; daily OHLC for ATR_D1 ----
d1_times=[]; d1_dem=[]; daily=[]
with gzip.open(GZ_1D,'rt') as f:
    for line in f:
        try: d=json.loads(line)
        except: continue
        rcd=d.get('replay_current_date')
        if rcd is None: continue
        cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
        dem=[]
        if cob:
            for b in (cob.get('all_boxes') or []):
                if (b.get('text') or '').upper()=='DEMAND' and b.get('high') is not None:
                    dem.append((b['high'],b['low']))
        d1_times.append(rcd); d1_dem.append(dem)
        ov=d.get('ohlcv') or []
        if ov:
            lb=ov[-1]
            daily.append((lb['time'],lb['high'],lb['low'],lb['close']))
# daily ATR14 series keyed by close_time (closed dailies only)
daily=sorted(set(daily)); dts=[x[0] for x in daily]
datr={}; trs=[]
for k in range(1,len(daily)):
    tr=max(daily[k][1]-daily[k][2],abs(daily[k][1]-daily[k-1][3]),abs(daily[k][2]-daily[k-1][3])); trs.append(tr)
    if k>=14: datr[daily[k][0]]=sum(trs[k-14:k])/14

def atr_d1_at(ts):  # ATR of last daily CLOSED before ts
    j=bisect_right(dts,ts)-1
    while j>=0 and dts[j] not in datr: j-=1
    return datr.get(dts[j]) if j>=0 else None

def d1_demand_at(ts):  # causal guard: max replay_current_date <= ts
    j=bisect_right(d1_times,ts)-1
    return (d1_dem[j], d1_times[j]) if j>=0 else ([],None)

# ---- enrich ----
def zone_inside(p,boxes): return any(lo<=p<=hi for hi,lo in boxes)
def nearest_above(p,boxes):  # box whose high <= p (support below), min dist
    cand=[(p-hi) for hi,lo in boxes if hi<=p]
    return min(cand) if cand else None
def nearest_below(p,boxes):  # box whose low >= p (zone above)
    cand=[(lo-p) for hi,lo in boxes if lo>=p]
    return min(cand) if cand else None

rows=[]
miss4=0
for r in base:
    i=int(r['candidate_id'][1:]); ts=cand_ts[i]; price=float(matrix[i]['entry_close'])
    a4=ATR4[i] or 0
    dem4,sup4=boxes4h.get(ts,(None,None))
    if dem4 is None: miss4+=1; dem4=[]; sup4=[]; avail4=False
    else: avail4=True
    inside_dem4=zone_inside(price,dem4); inside_sup4=zone_inside(price,sup4)
    # supply_overhead = SUPPLY box above price (low>price)
    da=nearest_below(price,sup4); supply_overhead=da is not None and (a4>0 and da<=3.0*a4)
    dist_sup=round(da,2) if da is not None else ''
    dn=nearest_above(price,dem4); near_dem4=dn is not None and a4>0 and dn<=TOL_4H*a4
    dist_dem=round(dn,2) if dn is not None else ''
    # at_d1_demand v2
    dem1,d1used=d1_demand_at(ts); atrd=atr_d1_at(ts)
    inside_d1=zone_inside(price,dem1)
    above=nearest_above(price,dem1)  # demand high<=p
    dist_above_atr=round(above/atrd,2) if (above is not None and atrd) else ''
    near_from_above=(above is not None and atrd and above<=TOL_D1*atrd)
    at_d1_demand=bool(inside_d1 or near_from_above)
    lab=r['GT_match']=='yes' and 'BOM' or (r['NAO_match']=='yes' and 'NAO' or 'UNKNOWN')
    rows.append({'candidate_id':r['candidate_id'],'timestamp':r['timestamp'],'source':r['source'],
        'label':lab,'GT_match':r['GT_match'],'NAO_match':r['NAO_match'],'gt_id':r['gt_id'],
        'at_D1_demand':int(at_d1_demand),'inside_d1_demand':int(inside_d1),'dist_above_d1_atr':dist_above_atr,
        'd1_record_used_ts':datetime.fromtimestamp(d1used,tz=timezone.utc).isoformat() if d1used else '',
        'supply_overhead':int(bool(supply_overhead)),'dist_to_supply':dist_sup,
        'inside_custom_ob_demand':int(inside_dem4),'near_custom_ob_demand':int(near_dem4),'dist_to_demand':dist_dem,
        'inside_custom_ob_supply':int(inside_sup4),
        'macro_leg_id':'REFERENCE_ONLY','macro_leg_phase':'REFERENCE_ONLY','macro_leg_direction':'REFERENCE_ONLY',
        'feature_availability':'4H_OB=%s;D1=%s' % ('yes' if avail4 else 'NO', 'yes' if d1used else 'NO'),
        'context_notes':''})

F=list(rows[0].keys())
with open(f"{BASE_D}/l2_bpt_v2_2_pruned_base_v2_macro_context.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=F); w.writeheader(); w.writerows(rows)
print(f"enriched {len(rows)} candidates | 4H OB missing-align: {miss4}")
print(json.dumps({'n':len(rows),'miss4':miss4,'boxes4h_bars':len(boxes4h),'d1_records':len(d1_times)}))
