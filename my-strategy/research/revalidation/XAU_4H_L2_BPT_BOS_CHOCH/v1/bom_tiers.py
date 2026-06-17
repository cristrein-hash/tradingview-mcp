import json,csv,statistics
from collections import defaultdict,Counter
D="results"
q=json.load(open('/tmp/dsq_rows.json'))
GT=json.load(open('/tmp/L2_ground_truth_v1.json'))['BOM_HIGH']
gt={e['GT_ID']:e for e in GT}

# --- tier rule (grounded; R measured only for GT02/03/20) ---
A={'GT02','GT03','GT18','GT21','GT23','GT27'}   # BIG_WINNER class OR measured RR>=4
C={'GT15','GT25','GT13A'}                         # weak/small/atypical candle, no measured big R
def tier(g):
    if g in A: return 'A_TIER_PROTECT'
    if g in C: return 'C_TIER_SACRIFICABLE'
    return 'B_TIER_PROTECT_IF_POSSIBLE'
FRAG={'GT13B','GT17A','GT23','GT24'}

# per-event supply/demand from quality (median across candidates; event flagged if rule true for ALL surviving)
bom_ev=defaultdict(list)
for r in q:
    if r['label']=='BOM' and r['gt_id']: bom_ev[r['gt_id']].append(r)
def fl(x):
    try: return float(x)
    except: return None
def ev_med(g,feat):
    vals=[fl(r[feat]) for r in bom_ev[g] if fl(r[feat]) is not None]
    return round(statistics.median(vals),2) if vals else None

tiers=[]
for g in sorted(gt):
    e=gt[g]
    tiers.append({'gt_id':g,'classe':e.get('classe'),
      'RR_target':e.get('RR_target','NA'),'mfe_R':e.get('mfe_R',e.get('MFE_R','NA')),
      'tipo_candle':(e.get('tipo_candle') or '')[:60],
      'fragile_survivor':'yes' if g in FRAG else 'no',
      'supply_dist_low_atr':ev_med(g,'dist_4h_supply_low_atr'),
      'supply_dist_from_polarity_atr':ev_med(g,'supply_dist_from_polarity_atr'),
      'demand_support_cat':Counter(r['demand_category'] for r in bom_ev[g]).most_common(1)[0][0] if bom_ev[g] else '',
      'supply_cat':Counter(r['supply_category'] for r in bom_ev[g]).most_common(1)[0][0] if bom_ev[g] else '',
      'tier':tier(g),
      'notes':'R measured only GT02/03/20; tier from classe+candle strength (judgment, confirm visual)'})
with open(f"{D}/l2_bpt_bom_tiers.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(tiers[0].keys())); w.writeheader(); w.writerows(tiers)
print("=== BOM TIERS ===")
for t in tiers:
    print(f"  {t['gt_id']:<7}{t['tier']:<28}{t['classe']:<22} sup_dist={t['supply_dist_low_atr']} sup_pol={t['supply_dist_from_polarity_atr']} {t['supply_cat']:<26} frag={t['fragile_survivor']}")
print("A:",sorted(A)," C:",sorted(C))

# --- supply-risk tradeoff (event-level kill by tier) ---
nao_ev=defaultdict(list); unk=[]
for r in q:
    if r['label']=='NAO' and r['gt_id']: nao_ev[r['gt_id']].append(r)
    elif r['label']=='UNKNOWN': unk.append(r)
tier_of={g:tier(g) for g in gt}
def rule_flag(r,name):
    s=fl(r['dist_4h_supply_low_atr']); 
    if name=='supply<=0.5ATR': return s is not None and s<=0.5
    if name=='supply<=1.0ATR': return s is not None and s<=1.0
    if name=='supply<=1.5ATR': return s is not None and s<=1.5
    if name=='supply_blocks_target_2ATR': return r['supply_4h_blocks_target_2ATR']=='1'
    if name=='supply_near1.0+no_demand_support': return (s is not None and s<=1.0) and r['demand_category'] in ('DEMAND_ABSENT_OR_IRRELEVANT','DEMAND_TOO_DEEP')
    if name=='supply_near1.0+no_origin_of_leg': return (s is not None and s<=1.0) and r['demand_4h_origin_of_leg_cand']=='0'
    if name=='supply_near1.0+polarity_under_supply': return (s is not None and s<=1.0) and r['polarity_category']=='POLARITY_UNDER_SUPPLY_PRESSURE'
    return False
RULES=['supply<=0.5ATR','supply<=1.0ATR','supply<=1.5ATR','supply_blocks_target_2ATR',
       'supply_near1.0+no_demand_support','supply_near1.0+no_origin_of_leg','supply_near1.0+polarity_under_supply']
def event_killed(ev,name):  # killed if ALL candidates flagged (no survivor)
    killed=[]
    for g,rs in ev.items():
        if all(rule_flag(r,name) for r in rs): killed.append(g)
    return killed
tr=[]
print("\n=== SUPPLY-RISK TRADEOFF (event-level kills) ===")
for name in RULES:
    bk=event_killed(bom_ev,name); nk=event_killed(nao_ev,name)
    a=sum(1 for g in bk if tier_of[g]=='A_TIER_PROTECT'); b=sum(1 for g in bk if tier_of[g]=='B_TIER_PROTECT_IF_POSSIBLE'); c=sum(1 for g in bk if tier_of[g]=='C_TIER_SACRIFICABLE')
    uk=sum(1 for r in unk if rule_flag(r,name))
    risk='HIGH(kills A)' if a>0 else ('MED(kills B)' if b>0 else ('LOW(only C/none)' ))
    tr.append({'rule':name,'A_killed':a,'B_killed':b,'C_killed':c,'BOM_events_killed':len(bk),'BOM_ids':'|'.join(bk),
      'NAO_events_cut':len(nk),'NAO_ids':'|'.join(nk),'UNKNOWN_cand_cut':uk,
      'reduction_pct_of_base':round(100*uk/2965,1),'risk':risk})
    print(f"  {name:<38} kills A{a} B{b} C{c} (BOM:{bk}) | NAOcut {len(nk)} | UNKcut {uk} | {risk}")
with open(f"{D}/l2_bpt_supply_risk_tradeoff.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(tr[0].keys())); w.writeheader(); w.writerows(tr)
