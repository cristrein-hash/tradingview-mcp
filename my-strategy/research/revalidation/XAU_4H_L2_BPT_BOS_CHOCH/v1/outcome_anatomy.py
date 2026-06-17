#!/usr/bin/env python3
"""L2/BPT v2.2 PRUNED_BASE_V2 — forward OUTCOME/ANATOMY labeling (mechanical proxy, NOT backtest).
Forward MFE/MAE in ATR over windows 6/12/24/36 (post-hoc analysis; entry uses NO future).
Calibrate anatomy classes against BOM/NAO, then label UNKNOWN. No SL/target promotion, no PnL
as validation, no plot/MCP/production/SLIM. Uses frozen input OHLC only (causal series).
"""
import json, csv, statistics
from collections import Counter, defaultdict

D="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen)
H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR4=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR4[i]=sum(trs[i-14:i])/14
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
base=[r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
def lab(r): return 'BOM' if r['GT_match']=='yes' else ('NAO' if r['NAO_match']=='yes' else 'UNKNOWN')
WINS=[6,12,24,36]; FRAG={'GT13B','GT17A','GT23','GT24'}

def window_stats(i,p,atr,pol,W):
    end=min(i+W,N-1)
    if end<=i or not atr: return None
    hh=max(H[i+1:end+1]); ll=min(L[i+1:end+1]); cr=C[end]
    mfe=(hh-p)/atr; mae=(p-ll)/atr; cret=(cr-p)/atr
    # invalidation: any close below polarity (reclaim lost)
    inval=any(C[j]<pol for j in range(i+1,end+1))
    # MAE before MFE peak (timing)
    mfe_bar=max(range(i+1,end+1),key=lambda j:H[j])
    mae_before=(p-min(L[i+1:mfe_bar+1]))/atr if mfe_bar>i else 0.0
    t_mfe=mfe_bar-i
    return {'mfe':round(mfe,2),'mae':round(mae,2),'cret':round(cret,2),'inval':int(inval),
            'mae_before':round(mae_before,2),'t_mfe':t_mfe,
            'r1':int(mfe>=1),'r2':int(mfe>=2),'r3':int(mfe>=3),'r4':int(mfe>=4),
            'd1':int(mae>=1),'d2':int(mae>=2)}

def classify(s36, s12):
    if s36 is None: return 'NEEDS_VISUAL_REVIEW'
    mfe,mae,mb,inval=s36['mfe'],s36['mae'],s36['mae_before'],s36['inval']
    # structural invalidation early (within 12 bars) before any +1 runup
    if s12 and s12['inval'] and s12['mfe']<1.0 and s12['mae']>=1.5: return 'STRUCTURE_INVALIDATED'
    if mfe>=3 and mb<1.0: return 'STRONG_CONTINUATION'
    if mfe>=2 and mb<1.5: return 'GOOD_CONTINUATION'
    if mfe<1 and mae>=2: return 'TOP_SWEEP_REVERSAL'
    if mfe<1 and mae<1: return 'CHOP_NO_FOLLOW_THROUGH'
    if 1<=mfe<2: return 'WEAK_CONTINUATION'
    if mfe<1 and mae>=1: return 'FAILED_RECLAIM'
    return 'NEEDS_VISUAL_REVIEW'

rows=[]
for r in base:
    i=int(r['candidate_id'][1:]); p=float(matrix[i]['entry_close']); atr=ATR4[i]; pol=float(matrix[i]['level'])
    label=lab(r); cid=r['candidate_id']; ql=qual.get(cid,{})
    st={W:window_stats(i,p,atr,pol,W) for W in WINS}
    cls=classify(st[36],st[12])
    if i+36>=N-1 and st[36] is None: cls='NEEDS_VISUAL_REVIEW'
    row={'candidate_id':cid,'timestamp':r['timestamp'],'source':r['source'],'label':label,'gt_id':r['gt_id'],
         'anatomy_class':cls,'fragile':'yes' if r['gt_id'] in FRAG else 'no',
         'supply_category':ql.get('supply_category',''),'demand_category':ql.get('demand_category',''),
         'dist_4h_supply_low_atr':ql.get('dist_4h_supply_low_atr',''),
         'overextended':matrix[i]['blk_overextended_entry'],'volume_fraco':matrix[i]['blk_volume_fraco'],
         'bear_flag':matrix[i]['blk_bear_flag'],'nas_short_10':matrix[i]['nas_short_10'],
         'sell_bub_10':matrix[i]['sell_bub_10'],'rsi':matrix[i]['rsi']}
    for W in WINS:
        s=st[W]
        if s:
            row[f'mfe_atr_{W}']=s['mfe']; row[f'mae_atr_{W}']=s['mae']; row[f'cret_atr_{W}']=s['cret']; row[f'inval_{W}']=s['inval']
        else:
            row[f'mfe_atr_{W}']=row[f'mae_atr_{W}']=row[f'cret_atr_{W}']=row[f'inval_{W}']=''
    rows.append(row)

FQ=list(rows[0].keys())
with open(f"{D}/l2_bpt_pruned_base_v2_outcome_anatomy.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=FQ); w.writeheader(); w.writerows(rows)

# event-level anatomy for BOM/NAO (dominant class across candidates)
def ev_class(label):
    ev=defaultdict(list)
    for r in rows:
        if r['label']==label and r['gt_id']: ev[r['gt_id']].append(r['anatomy_class'])
    return {g:Counter(cs).most_common(1)[0][0] for g,cs in ev.items()}
bom_cls=ev_class('BOM'); nao_cls=ev_class('NAO')
CONT={'STRONG_CONTINUATION','GOOD_CONTINUATION','WEAK_CONTINUATION'}
FAIL={'FAILED_RECLAIM','TOP_SWEEP_REVERSAL','CHOP_NO_FOLLOW_THROUGH','STRUCTURE_INVALIDATED'}
bom_cont=sum(1 for c in bom_cls.values() if c in CONT); nao_fail=sum(1 for c in nao_cls.values() if c in FAIL)
calib_ok = bom_cont>=12 and nao_fail>=3

unk=[r for r in rows if r['label']=='UNKNOWN']
unk_dist=Counter(r['anatomy_class'] for r in unk)
unk_strong=sum(unk_dist[c] for c in ('STRONG_CONTINUATION','GOOD_CONTINUATION'))
unk_noise=sum(unk_dist[c] for c in ('CHOP_NO_FOLLOW_THROUGH','TOP_SWEEP_REVERSAL','STRUCTURE_INVALIDATED'))
unk_visual=unk_dist['NEEDS_VISUAL_REVIEW']

with open(f"{D}/l2_bpt_pruned_base_v2_unknown_classification.csv","w",newline="") as f:
    flds=['candidate_id','timestamp','source','anatomy_class','supply_category','demand_category','mfe_atr_36','mae_atr_36','cret_atr_36','rsi']
    w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore'); w.writeheader(); w.writerows(unk)
# visual review queue: BOM frag + UNKNOWN strong + NAO + any anomalies
vq=[r for r in rows if (r['fragile']=='yes') or (r['label']=='UNKNOWN' and r['anatomy_class'] in ('STRONG_CONTINUATION','GOOD_CONTINUATION')) or (r['label']=='NAO') or (r['label']=='BOM' and r['anatomy_class'] in FAIL)]
with open(f"{D}/l2_bpt_pruned_base_v2_visual_review_queue.csv","w",newline="") as f:
    flds=['candidate_id','timestamp','label','gt_id','fragile','anatomy_class','supply_category','demand_category','mfe_atr_36','mae_atr_36']
    w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore'); w.writeheader(); w.writerows(vq)

# cross anatomy x tags
def cross(cls_set):
    sub=[r for r in rows if r['anatomy_class'] in cls_set]
    n=len(sub) or 1
    def frac(pred): return round(100*sum(1 for r in sub if pred(r))/n,1)
    return {'n':len(sub),'supply_near<=1ATR%':frac(lambda r:r['dist_4h_supply_low_atr'] not in ('',None) and float(r['dist_4h_supply_low_atr'])<=1),
            'demand_supporting%':frac(lambda r:r['demand_category']=='DEMAND_SUPPORTING_RETEST'),
            'overext%':frac(lambda r:r['overextended']=='1'),'bearflag%':frac(lambda r:r['bear_flag']=='1'),
            'nas_short>=5%':frac(lambda r:r['nas_short_10'] not in ('',None) and float(r['nas_short_10'])>=5)}

summary={'analyzed':len(rows),'calibration':{'BOM_classes':bom_cls,'NAO_classes':nao_cls,
   'BOM_continuation':f"{bom_cont}/{len(bom_cls)}",'NAO_failure':f"{nao_fail}/{len(nao_cls)}",'calib_ok':calib_ok},
   'unknown_distribution':dict(unk_dist),'unknown_strong':unk_strong,'unknown_noise':unk_noise,'unknown_visual':unk_visual,
   'cross':{'STRONG/GOOD':cross({'STRONG_CONTINUATION','GOOD_CONTINUATION'}),
            'TOP_SWEEP_REVERSAL':cross({'TOP_SWEEP_REVERSAL'}),
            'FAILED_RECLAIM':cross({'FAILED_RECLAIM'}),
            'CHOP':cross({'CHOP_NO_FOLLOW_THROUGH'})},
   'status':'MECHANICAL_PROXY_NOT_BACKTEST_NOT_VALIDATION'}
json.dump(summary,open(f"{D}/l2_bpt_pruned_base_v2_outcome_anatomy_summary.json",'w'),indent=2)

print(f"analyzed {len(rows)}")
print(f"CALIBRATION: BOM continuation {bom_cont}/{len(bom_cls)} | NAO failure {nao_fail}/{len(nao_cls)} | calib_ok={calib_ok}")
print("BOM classes:",Counter(bom_cls.values()))
print("NAO classes:",Counter(nao_cls.values()))
print(f"UNKNOWN dist: {dict(unk_dist)}")
print(f"  strong/good={unk_strong}  noise={unk_noise}  visual={unk_visual}")
print("CROSS:")
for k,v in summary['cross'].items(): print(f"  {k}: {v}")
print("fragile BOM anatomy:",{r['gt_id']:r['anatomy_class'] for r in rows if r['fragile']=='yes' and r['label']=='BOM'})
