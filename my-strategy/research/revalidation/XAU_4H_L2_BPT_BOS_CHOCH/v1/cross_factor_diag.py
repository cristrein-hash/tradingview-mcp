#!/usr/bin/env python3
"""L2/BPT v2.2 — cross-factor diagnostic (BOM vs NAO vs UNKNOWN), event-level recall.
Universe = full candidate matrix (7763). Prune semantics = union (remove if any factor true)
for pairs/triples; intersection for source-targeted (fractal_3_3 x tag). NO veto promotion,
NO PnL/backtest/plot/MCP/production/SLIM. Diagnostic only.
"""
import csv, json
from itertools import combinations
from collections import defaultdict, Counter

D = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
rows = list(csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv")))
for r in rows: r['ei'] = int(r['candidate_id'][1:])
def num(x):
    try: return float(x)
    except: return None

bom_ev = defaultdict(set); nao_ev = defaultdict(set)
for r in rows:
    if r['label']=='BOM': bom_ev[r['gt_id']].add(r['ei'])
    elif r['label']=='NAO': nao_ev[r['gt_id']].add(r['ei'])
N_BOM=len(bom_ev); N_NAO=len(nao_ev)
n_unk=sum(1 for r in rows if r['label']=='UNKNOWN')
FRAGILE=['GT13B','GT17A','GT23','GT24']
ALL=set(r['ei'] for r in rows)
REDUNDANT={'fractal_2_2','nivel_interno','topo_duplo'}

# ---- factor predicates (prune-if-true). ALL from real matrix fields; none invented. ----
BLK=['false_tipo_B_dump_direto','CHoCH_not_BOS','first_retomada','bear_flag','BOS_fraco',
     'cluster_BUY_climax','bear_macro','volume_fraco','no_absorption','no_polarity_defense',
     'no_retest','overextended_entry']
factors={}
for b in BLK: factors[b]=(lambda b: (lambda r: r['blk_'+b]=='1'))(b)
factors['src_redundant']=lambda r: r['source'] in REDUNDANT
factors['nas_short_ge5']=lambda r: (num(r['nas_short_10']) or 0)>=5
factors['dist_pol_lt04']=lambda r: (num(r['dist_pol_atr']) if num(r['dist_pol_atr']) is not None else 99)<0.4
factors['rsi_lt50']=lambda r: (num(r['rsi']) if num(r['rsi']) is not None else 99)<50
factors['atr_pct_lt03']=lambda r: (num(r['atr_pct']) if num(r['atr_pct']) is not None else 99)<0.3
DANGER={'first_retomada','BOS_fraco','bear_macro','cluster_BUY_climax'}  # known BOM-killers
UNAVAILABLE=['at_D1_demand','macro_leg_block','supply_overhead','custom_ob_demand','custom_ob_supply']

# precompute prune index set per factor
fidx={fn:set(r['ei'] for r in rows if fp(r)) for fn,fp in factors.items()}

def metrics(prune_set, label):
    kept=ALL-prune_set
    bom_keep=sum(1 for s in bom_ev.values() if s&kept)
    nao_cut=sum(1 for s in nao_ev.values() if not (s&kept))
    unk_cut=sum(1 for r in rows if r['label']=='UNKNOWN' and r['ei'] in prune_set)
    frag_ok=all((bom_ev[g]&kept) for g in FRAGILE)
    after=len(kept); red=len(rows)-after
    if bom_keep==N_BOM: cls='SAFE_CANDIDATE'
    elif bom_keep>=15: cls='BORDERLINE'
    elif bom_keep<15: cls='DANGEROUS'
    return {'factors':label,'count_before':len(rows),'count_after':after,'reduction_count':red,
            'reduction_pct':round(100*red/len(rows),1),'BOM_preserved':bom_keep,'BOM_lost':N_BOM-bom_keep,
            'NAO_events_cut':nao_cut,'UNKNOWN_cut':unk_cut,'cand_per_year':round(after/7,0),
            'fragile_ok':frag_ok,'class':cls}

# ---- Tarefa 3: all 2-factor unions ----
names=list(factors.keys())
two=[]
for a,b in combinations(names,2):
    m=metrics(fidx[a]|fidx[b], f"{a}+{b}")
    m['has_danger']=a in DANGER or b in DANGER
    two.append(m)
two.sort(key=lambda m:(-(m['class']=='SAFE_CANDIDATE'), -m['UNKNOWN_cut']))

# ---- Tarefa 4: 3-factor shortlist = extend top SAFE 2-factor (by UNKNOWN cut) with each factor ----
top_safe2=[m for m in two if m['class']=='SAFE_CANDIDATE'][:6]
three=[]
seen=set()
for m in top_safe2:
    a,b=m['factors'].split('+')
    for c in names:
        if c in (a,b): continue
        key=frozenset([a,b,c])
        if key in seen: continue
        seen.add(key)
        mm=metrics(fidx[a]|fidx[b]|fidx[c], f"{a}+{b}+{c}")
        mm['has_danger']=any(x in DANGER for x in (a,b,c))
        three.append(mm)
three.sort(key=lambda m:(-(m['class']=='SAFE_CANDIDATE'), -m['UNKNOWN_cut']))

# ---- Tarefa 5: mandatory interactions ----
mand=[]
def add_mand(label,prune_set,note,available=True):
    if not available:
        mand.append({'interaction':label,'available':False,'note':note}); return
    m=metrics(prune_set,label); m['interaction']=label; m['available']=True; m['note']=note
    mand.append(m)
add_mand('volume_fraco x overextended_entry', fidx['volume_fraco']|fidx['overextended_entry'],'union')
add_mand('volume_fraco x bear_flag', fidx['volume_fraco']|fidx['bear_flag'],'union')
add_mand('volume_fraco x no_retest', fidx['volume_fraco']|fidx['no_retest'],'union')
add_mand('overextended_entry x bear_context(bear_flag)', fidx['overextended_entry']|fidx['bear_flag'],'supply UNAVAILABLE -> bear_flag proxy')
add_mand('no_polarity_defense x no_absorption', fidx['no_polarity_defense']|fidx['no_absorption'],'union')
add_mand('no_retest x false_tipo_B_dump_direto', fidx['no_retest']|fidx['false_tipo_B_dump_direto'],'union')
add_mand('bear_flag x nas_short_ge5', fidx['bear_flag']|fidx['nas_short_ge5'],'nas_short available')
add_mand('supply_overhead x cluster_BUY_climax', None,'supply_overhead UNAVAILABLE in v2.2 input',available=False)
add_mand('at_D1_demand_false x bear_macro', None,'at_D1_demand UNAVAILABLE in v2.2 input',available=False)
# #10 fractal_3_3 source x each risk tag (intersection: source==fractal_3_3 AND tag)
f33=set(r['ei'] for r in rows if r['source']=='fractal_3_3')
f33x=[]
for b in BLK:
    inter=f33 & fidx[b]
    m=metrics(inter, f"fractal_3_3 & {b}"); m['interaction']=f"fractal_3_3 x {b}"; m['available']=True
    m['note']='intersection (targeted: only fractal_3_3 candidates with risk tag)'
    f33x.append(m)

# ---- Tarefa 6: fragile BOM protection across all SAFE 2/3-factor + mandatory ----
frag_rows=[]
def frag_detail(label,prune_set):
    kept=ALL-prune_set
    d={'combo':label}
    for g in FRAGILE:
        surv=bom_ev[g]&kept
        d[g]=f"{len(surv)}surv" if surv else "LOST"
    d['all_fragile_ok']=all(bom_ev[g]&kept for g in FRAGILE)
    return d
for m in ([x for x in two if x['class']=='SAFE_CANDIDATE'][:15]):
    a,b=m['factors'].split('+'); frag_rows.append(frag_detail(m['factors'],fidx[a]|fidx[b]))
for m in ([x for x in three if x['class']=='SAFE_CANDIDATE'][:10]):
    parts=m['factors'].split('+'); ps=set().union(*[fidx[p] for p in parts]); frag_rows.append(frag_detail(m['factors'],ps))

# ---- outputs ----
def wcsv(path,rs,fields):
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rs)
mf=['factors','count_after','reduction_pct','BOM_preserved','BOM_lost','NAO_events_cut','UNKNOWN_cut','cand_per_year','fragile_ok','has_danger','class']
wcsv(f"{D}/l2_bpt_v2_2_cross_factor_matrix.csv", two, mf)
safe_all=[m for m in two if m['class']=='SAFE_CANDIDATE']+[m for m in three if m['class']=='SAFE_CANDIDATE']
safe_all.sort(key=lambda m:-m['UNKNOWN_cut'])
wcsv(f"{D}/l2_bpt_v2_2_top_safe_combinations.csv", safe_all, mf)
dang=[m for m in two+three if m['class']=='DANGEROUS']
dang.sort(key=lambda m:m['BOM_preserved'])
wcsv(f"{D}/l2_bpt_v2_2_dangerous_combinations.csv", dang, mf)
wcsv(f"{D}/l2_bpt_v2_2_fragile_bom_protection.csv", frag_rows, ['combo']+FRAGILE+['all_fragile_ok'])

summary={'universe':len(rows),'BOM_events':N_BOM,'NAO_events':N_NAO,'UNKNOWN':n_unk,
  'two_factor_tested':len(two),'three_factor_tested':len(three),
  'safe_2f':sum(1 for m in two if m['class']=='SAFE_CANDIDATE'),
  'borderline_2f':sum(1 for m in two if m['class']=='BORDERLINE'),
  'dangerous_2f':sum(1 for m in two if m['class']=='DANGEROUS'),
  'best_safe_2f':two[0]['factors'] if two and two[0]['class']=='SAFE_CANDIDATE' else None,
  'best_safe_2f_cut':two[0]['UNKNOWN_cut'] if two else None,
  'best_safe_3f':(safe_all[0]['factors'] if safe_all else None),
  'best_safe_3f_cut':(safe_all[0]['UNKNOWN_cut'] if safe_all else None),
  'unavailable_factors':UNAVAILABLE,'mandatory':mand,'fractal_3_3_targeted':f33x}
json.dump(summary,open(f"{D}/l2_bpt_v2_2_cross_factor_summary.json",'w'),indent=2)

# console
print(f"universe={len(rows)} BOM_ev={N_BOM} NAO_ev={N_NAO} UNK={n_unk}")
print(f"2-factor tested={len(two)} (SAFE {summary['safe_2f']} / BORDER {summary['borderline_2f']} / DANGER {summary['dangerous_2f']})")
print(f"3-factor shortlist tested={len(three)}")
print("\nTOP SAFE (17/17) by UNKNOWN cut:")
for m in safe_all[:10]:
    print(f"  {m['factors']:<48} -{m['reduction_pct']:>4}% UNKcut={m['UNKNOWN_cut']:>4} NAOcut={m['NAO_events_cut']} frag={m['fragile_ok']} {'DANGERmix' if m['has_danger'] else ''}")
print("\nMANDATORY interactions:")
for m in mand:
    if not m.get('available',True): print(f"  {m['interaction']:<42} UNAVAILABLE — {m['note']}"); continue
    print(f"  {m['interaction']:<42} BOM {m['BOM_preserved']}/{N_BOM} NAOcut {m['NAO_events_cut']} UNKcut {m['UNKNOWN_cut']} frag={m['fragile_ok']} [{m['class']}]")
print("\nfractal_3_3 x risk tag (targeted intersection):")
for m in sorted(f33x,key=lambda m:-m['UNKNOWN_cut'])[:6]:
    print(f"  {m['interaction']:<40} BOM {m['BOM_preserved']}/{N_BOM} UNKcut {m['UNKNOWN_cut']} frag={m['fragile_ok']} [{m['class']}]")
print("\nDANGEROUS (worst):")
for m in dang[:5]:
    print(f"  {m['factors']:<48} BOM {m['BOM_preserved']}/{N_BOM} (lost {m['BOM_lost']})")
