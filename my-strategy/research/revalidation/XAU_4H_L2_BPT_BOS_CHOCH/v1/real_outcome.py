#!/usr/bin/env python3
"""L2/BPT v2.2 PRUNED_BASE_V2 — REAL trade outcome (structural SL + R-targets, stop-first).
THIS is what was requested (not forward MFE drift). Entry=reclaim close; structural SL = recent
retest swing low - 0.1ATR (R-bounded floor 0.3 / ceil 1.5 ATR), as in the census engine; targets
+2/+3/+4R, stop-first intrabar, time-stop 60 bars. Aggregated PER EPISODE (dedup serial signals).
Lift vs random-entry base rate. SL validated against GT stop_cris (17 BOM). Mechanical, RAW-only,
NO PnL$/promotion/plot/production/SLIM. NOT final validation (gross, in-sample).
"""
import json, csv, statistics
from collections import defaultdict, Counter

D="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen); H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
base=[r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
gt={e['GT_ID']:e for e in json.load(open('/tmp/L2_ground_truth_v1.json'))['BOM_HIGH']}
def lab(r): return 'BOM' if r['GT_match']=='yes' else ('NAO' if r['NAO_match']=='yes' else 'UNKNOWN')
RW=6; R_FLOOR=0.3; R_CEIL=1.5; MAXHOLD=60; TARGETS=[2.0,3.0,4.0]

def structural_sl(i,p,atr):
    lo=min(L[max(0,i-RW+1):i+1])
    sl=lo-0.1*atr; risk=p-sl
    if risk<=0: return None,None,'no_struct_low'
    if risk<R_FLOOR*atr: sl=p-R_FLOOR*atr; risk=R_FLOOR*atr
    flag='R_ceiling' if risk>R_CEIL*atr else 'ok'
    return sl,risk,flag

def sim(i,p,risk,tR):
    tgt=p+tR*risk; sl=p-risk; end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        if L[j]<=sl: return -1.0,'stop'
        if H[j]>=tgt: return tR,'target'
    return (C[end]-p)/risk,'time'

def outcome_set(idxs, tR):
    res=[]
    for i in idxs:
        p=C[i]; atr=ATR[i]
        if not atr: continue
        sl,risk,flag=structural_sl(i,p,atr)
        if sl is None: continue
        r,how=sim(i,p,risk,tR)
        res.append((r,how,flag))
    return res

# ---- episodes (dedup: gap>6 bars = new episode); one trade per episode = first candidate ----
rows_lab={int(r['candidate_id'][1:]):lab(r) for r in base}
rows_gt={int(r['candidate_id'][1:]):r['gt_id'] for r in base}
idxs=sorted(rows_lab)
episodes=[]; cur=[idxs[0]]
for a,b in zip(idxs,idxs[1:]):
    if b-a<=6: cur.append(b)
    else: episodes.append(cur); cur=[b]
episodes.append(cur)
# episode label: BOM if contains BOM, elif NAO, else UNKNOWN ; representative = first idx
ep_reps=[]
for e in episodes:
    labs=[rows_lab[i] for i in e]
    el='BOM' if 'BOM' in labs else ('NAO' if 'NAO' in labs else 'UNKNOWN')
    rep=e[0]
    if el=='BOM': rep=[i for i in e if rows_lab[i]=='BOM'][0]
    elif el=='NAO': rep=[i for i in e if rows_lab[i]=='NAO'][0]
    ep_reps.append((rep,el))

# ---- validate structural SL vs GT stop_cris (17 BOM) ----
val=[]
for r in base:
    if r['GT_match']!='yes': continue
    i=int(r['candidate_id'][1:]); p=C[i]; atr=ATR[i]
    sl,risk,flag=structural_sl(i,p,atr)
    g=gt.get(r['gt_id']); sc=g.get('stop_cris') if g else None
    try: scv=float(str(sc).split()[0].replace('ou','').strip())
    except: scv=None
    if sl is not None:
        val.append({'gt_id':r['gt_id'],'entry':round(p,2),'my_SL':round(sl,2),'risk_atr':round(risk/atr,2),
                    'gt_stop_cris':scv,'my_risk':round(p-sl,2),'gt_risk':round(p-scv,2) if scv else None,
                    'flag':flag})

# ---- outcomes per episode by label, target +2R ----
def agg(label,tR):
    reps=[rep for rep,el in ep_reps if el==label]
    res=outcome_set(reps,tR)
    if not res: return None
    rs=[x[0] for x in res]; wr=sum(1 for x in res if x[0]>0)/len(res)
    return {'n_episodes':len(res),'WR':round(100*wr,1),'sumR':round(sum(rs),1),'avgR':round(sum(rs)/len(rs),2),
            'tgt':sum(1 for x in res if x[1]=='target'),'stop':sum(1 for x in res if x[1]=='stop'),'time':sum(1 for x in res if x[1]=='time')}

# ---- base-rate: random entries (all bars) same SL logic ----
def base_rate(tR,step=3):
    ids=list(range(2*14,N-MAXHOLD-1,step))
    res=outcome_set(ids,tR)
    rs=[x[0] for x in res]
    return {'n':len(res),'WR':round(100*sum(1 for x in res if x[0]>0)/len(res),1),'avgR':round(sum(rs)/len(rs),3)}

print("=== STRUCTURAL SL validation vs GT stop_cris (17 BOM) ===")
ok=0
for v in val:
    close = v['gt_risk'] and abs(v['my_risk']-v['gt_risk'])/v['gt_risk']<=0.6
    ok+= 1 if close else 0
    print(f"  {v['gt_id']:<6} entry {v['entry']:<9} mySL {v['my_SL']:<9}(r {v['risk_atr']}ATR) gtStop {v['gt_stop_cris']} | myRisk {v['my_risk']} gtRisk {v['gt_risk']} {v['flag']}")
print(f"  SL within 60% of Cris risk: {ok}/{len(val)} (my SL is TIGHTER = recent retest low, vs Cris wider structural)")

print("\n=== REAL OUTCOME per episode (structural SL, +2R, stop-first, time60) ===")
for label in ['BOM','NAO','UNKNOWN']:
    a=agg(label,2.0); print(f"  {label:<8} {a}")
print("\n=== BASE RATE (random entries same SL) +2R ===")
br=base_rate(2.0); print(f"  {br}")
bom=agg('BOM',2.0); unk=agg('UNKNOWN',2.0)
print(f"\n=== LIFT (WR vs base rate) ===")
print(f"  BOM WR {bom['WR']}% / base {br['WR']}% = lift x{bom['WR']/br['WR']:.2f}")
print(f"  UNKNOWN WR {unk['WR']}% / base {br['WR']}% = lift x{unk['WR']/br['WR']:.2f}")

# targets sweep
print("\n=== targets sweep (per-episode avgR) ===")
for tR in TARGETS:
    print(f"  +{tR}R: BOM {agg('BOM',tR)} | UNKNOWN {agg('UNKNOWN',tR)} | base avgR {base_rate(tR)['avgR']}")

# write outputs
with open(f"{D}/l2_bpt_real_outcome_sl_validation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(val[0].keys())); w.writeheader(); w.writerows(val)
out=[]
for tR in TARGETS:
    for label in ['BOM','NAO','UNKNOWN']:
        a=agg(label,tR) or {}
        a.update({'label':label,'target':tR}); out.append(a)
    b=base_rate(tR); out.append({'label':'BASE_RATE','target':tR,'n_episodes':b['n'],'WR':b['WR'],'avgR':b['avgR']})
with open(f"{D}/l2_bpt_real_outcome_per_episode.csv","w",newline="") as f:
    flds=['label','target','n_episodes','WR','sumR','avgR','tgt','stop','time']
    w=csv.DictWriter(f,fieldnames=flds,extrasaction='ignore'); w.writeheader(); w.writerows(out)
print(f"\nepisodes total {len(episodes)} (BOM {sum(1 for _,e in ep_reps if e=='BOM')} NAO {sum(1 for _,e in ep_reps if e=='NAO')} UNK {sum(1 for _,e in ep_reps if e=='UNKNOWN')})")
