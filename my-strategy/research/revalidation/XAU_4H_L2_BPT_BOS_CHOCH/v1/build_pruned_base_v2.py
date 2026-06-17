#!/usr/bin/env python3
"""L2/BPT v2.2 — formalize PRUNED BASE V2 = overextended_entry + src_redundant + bear_flag.
Reproduces the user-approved cross-factor combination. Event-level recall must stay 17/17.
NO new combinations, NO PnL/backtest/plot/MCP/production/SLIM. CANDIDATE_BASE only.
If any BOM event is lost -> STOP, do not formalize.
"""
import csv, json, sys
from collections import defaultdict, Counter

D = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
rows = list(csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv")))
for r in rows: r['ei'] = int(r['candidate_id'][1:])
REDUNDANT = {'fractal_2_2','nivel_interno','topo_duplo'}
BACKBONE = 'fractal_3_3'
FRAGILE = ['GT13B','GT17A','GT23','GT24']

def src_family(s):
    if s in ('fractal_3_3','fractal_2_2'): return 'fractal'
    if s in ('topo_duplo','range_top','swing_high_simples'): return 'structural'
    if s == 'nivel_interno': return 'proximity'
    return 'other'

# event capturing sets
bom_ev = defaultdict(set); nao_ev = defaultdict(set)
for r in rows:
    if r['label']=='BOM': bom_ev[r['gt_id']].add(r['ei'])
    elif r['label']=='NAO': nao_ev[r['gt_id']].add(r['ei'])
N_BOM=len(bom_ev); N_NAO=len(nao_ev)
n_unk=sum(1 for r in rows if r['label']=='UNKNOWN')
ALL=set(r['ei'] for r in rows)

# ---- V2 rule predicates (all from real matrix fields) ----
def f_overext(r): return r['blk_overextended_entry']=='1'
def f_srcred(r):  return r['source'] in REDUNDANT
def f_bearflag(r):return r['blk_bear_flag']=='1'
def v2_prune(r):  return f_overext(r) or f_srcred(r) or f_bearflag(r)

prune_set=set(r['ei'] for r in rows if v2_prune(r))
kept=ALL-prune_set

# ---- Tarefa 3: recall event-level, HARD STOP if any BOM lost ----
def recall(ks): return {g for g,s in bom_ev.items() if s&ks}
kept_bom=recall(kept)
lost_bom=set(bom_ev)-kept_bom
if lost_bom:
    print(f"FAIL: BOM lost {sorted(lost_bom)} -> NOT formalizing V2"); sys.exit(1)
frag_status={g:('preserved' if (bom_ev[g]&kept) else 'LOST') for g in FRAGILE}
if any(v=='LOST' for v in frag_status.values()):
    print(f"FAIL: fragile lost {frag_status} -> NOT formalizing V2"); sys.exit(1)

# ---- Tarefa 1/2: reproduce + P0/P1/P2/P3 ----
def stat(name, prune_fn, rule):
    ks=ALL-set(r['ei'] for r in rows if prune_fn(r))
    rb=len(recall(ks)); nao=sum(1 for s in nao_ev.values() if not (s&ks))
    unk=sum(1 for r in rows if r['label']=='UNKNOWN' and r['ei'] not in ks)
    return {'name':name,'rule':rule,'candidates':len(ks),'reduction':len(rows)-len(ks),
            'reduction_pct':round(100*(len(rows)-len(ks))/len(rows),1),'cand_per_year':round(len(ks)/7,0),
            'BOM_recall':f"{rb}/{N_BOM}",'NAO_captured':f"{N_NAO-nao}/{N_NAO}",'NAO_cut':nao,
            'UNKNOWN_cut':unk}
P1_BLK=['volume_fraco','bear_flag','no_retest','no_polarity_defense','false_tipo_B_dump_direto','no_absorption']
versions=[
 stat('P0_original', lambda r: False, 'sem pruning'),
 stat('P1_pruned_base_v1', lambda r: any(r['blk_'+b]=='1' for b in P1_BLK), 'greedy safe union (6 blockers)'),
 stat('P2_pruned_base_v2', v2_prune, 'overextended_entry + src_redundant + bear_flag'),
 stat('P3ref_volfraco_x_bearflag', lambda r: r['blk_volume_fraco']=='1' or r['blk_bear_flag']=='1', 'reference only'),
 stat('P3ref_fractal33_x_overext', lambda r: (r['source']=='fractal_3_3' and r['blk_overextended_entry']=='1'), 'reference only (intersection)'),
]

# ---- Tarefa 4: NAO/UNKNOWN detail ----
nao_cut_ids=[g for g,s in nao_ev.items() if not (s&kept)]
nao_keep_ids=[g for g,s in nao_ev.items() if (s&kept)]
unk_cut=sum(1 for r in rows if r['label']=='UNKNOWN' and r['ei'] in prune_set)
unk_keep=n_unk-unk_cut
# density by source in base
dens_base=Counter(r['source'] for r in rows if r['ei'] in kept)
dens_orig=Counter(r['source'] for r in rows)

# ---- outputs ----
def reason(r):
    if r['ei'] in kept: return ''
    rs=[]
    if f_overext(r): rs.append('overextended_entry')
    if f_srcred(r): rs.append('src_redundant')
    if f_bearflag(r): rs.append('bear_flag')
    return '|'.join(rs)
def out_row(r):
    return {'candidate_id':r['candidate_id'],'timestamp':r['ts'],'source':r['source'],
            'source_family':src_family(r['source']),
            'kept':'kept' if r['ei'] in kept else 'pruned','prune_reason':reason(r),
            'overextended_entry':r['blk_overextended_entry'],
            'src_redundant':int(f_srcred(r)),'bear_flag':r['blk_bear_flag'],
            'GT_match':'yes' if r['label']=='BOM' else 'no',
            'NAO_match':'yes' if r['label']=='NAO' else 'no',
            'gt_id':r['gt_id'],
            'fragile_BOM':'yes' if r['gt_id'] in FRAGILE else 'no',
            'notes':r['variant']+'/'+r['tipo']}
F=['candidate_id','timestamp','source','source_family','kept','prune_reason','overextended_entry',
   'src_redundant','bear_flag','GT_match','NAO_match','gt_id','fragile_BOM','notes']
allout=[out_row(r) for r in rows]
def w(path,rs,fields):
    with open(path,'w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(rs)
w(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv",[o for o in allout if o['kept']=='kept'],F)
w(f"{D}/l2_bpt_v2_2_pruned_base_v2_removed.csv",[o for o in allout if o['kept']=='pruned'],F)

# gt recall comparison P0/P1/P2
def cap(ks,ev): return {g:(g in {gg for gg,s in ev.items() if s&ks}) for g in ev}
ks_p1=ALL-set(r['ei'] for r in rows if any(r['blk_'+b]=='1' for b in P1_BLK))
gt_rows=[]
for g,s in sorted(bom_ev.items()):
    surv=s&kept
    surv_src=sorted({r['source'] for r in rows if r['ei'] in surv})
    gt_rows.append({'gt_id':g,'captured_in_original':'yes',
        'captured_in_pruned_v1':'yes' if (s&ks_p1) else 'no',
        'captured_in_pruned_v2':'yes' if surv else 'no',
        'number_of_surviving_candidates':len(surv),'surviving_sources':'|'.join(surv_src),
        'fragile':'yes' if g in FRAGILE else 'no','notes':''})
w(f"{D}/l2_bpt_v2_2_pruned_base_v2_gt_recall.csv",gt_rows,
  ['gt_id','captured_in_original','captured_in_pruned_v1','captured_in_pruned_v2',
   'number_of_surviving_candidates','surviving_sources','fragile','notes'])

# nao/unknown
nao_rows=[]
for g,s in sorted(nao_ev.items()):
    surv=s&kept
    nao_rows.append({'nao_id':g,'capturing_candidates':len(s),'surviving_in_v2':len(surv),
        'status':'cut' if not surv else 'remains','surviving_sources':'|'.join(sorted({r['source'] for r in rows if r['ei'] in surv}))})
nao_rows.append({'nao_id':'_UNKNOWN_SUMMARY','capturing_candidates':n_unk,'surviving_in_v2':unk_keep,
    'status':f'cut={unk_cut} remain={unk_keep}','surviving_sources':''})
w(f"{D}/l2_bpt_v2_2_pruned_base_v2_nao_unknown.csv",nao_rows,
  ['nao_id','capturing_candidates','surviving_in_v2','status','surviving_sources'])

# source density
sd=[]
for src in sorted(dens_orig):
    sd.append({'source':src,'source_family':src_family(src),'count_original':dens_orig[src],
        'count_v2':dens_base.get(src,0),'pct_of_v2':round(100*dens_base.get(src,0)/max(len(kept),1),1),
        'is_backbone':'yes' if src==BACKBONE else 'no','redundant':'yes' if src in REDUNDANT else 'no'})
w(f"{D}/l2_bpt_v2_2_pruned_base_v2_source_density.csv",sd,
  ['source','source_family','count_original','count_v2','pct_of_v2','is_backbone','redundant'])

summary={'base':'L2_BPT_V2_2_PRUNED_BASE_V2',
  'status':['CANDIDATE_BASE','NOT_STRATEGY','NOT_VALIDATION','RECALL_PRESERVED_17_17',
            'DENSITY_REDUCED_61_8_PERCENT','WORKING_BASE_FOR_DEEPER_CONTEXT_ANALYSIS'],
  'rule':'prune if (overextended_entry OR src_redundant OR bear_flag)','redundant_sources':sorted(REDUNDANT),
  'backbone':BACKBONE,'forbidden_as_veto':['first_retomada','nas_short_ge5','BOS_fraco','bear_macro','cluster_BUY_climax'],
  'borderline_not_base':{'rule':'volume_fraco x overextended_entry','BOM':'15/17','kills':['GT13B','GT24']},
  'candidates_original':len(rows),'candidates_v2':len(kept),'reduction_pct':versions[2]['reduction_pct'],
  'cand_per_year':versions[2]['cand_per_year'],'BOM_recall':f"{len(kept_bom)}/{N_BOM}",
  'fragile_status':frag_status,'NAO_cut':nao_cut_ids,'NAO_remain':nao_keep_ids,
  'UNKNOWN_cut':unk_cut,'UNKNOWN_remain':unk_keep,'versions':versions,
  'recall_revalidated_after_combination':True,
  'unavailable_discriminators':['at_D1_demand','supply_overhead','custom_ob_demand_supply','macro_leg']}
json.dump(summary,open(f"{D}/l2_bpt_v2_2_pruned_base_v2_summary.json",'w'),indent=2)

# console
print(f"V2 rule: prune if (overextended_entry OR src_redundant OR bear_flag)")
print(f"candidates 7763 -> {len(kept)}  (-{versions[2]['reduction_pct']}%)  ~{versions[2]['cand_per_year']}/yr")
print(f"BOM recall {len(kept_bom)}/{N_BOM} | fragile: {frag_status}")
print(f"NAO cut {len(nao_cut_ids)}/{N_NAO} -> {nao_cut_ids}; remain {nao_keep_ids}")
print(f"UNKNOWN cut {unk_cut}, remain {unk_keep}")
print(f"fractal_3_3 in V2: {dens_base.get(BACKBONE,0)} (backbone preserved)")
print("\nP0/P1/P2/P3:")
for v in versions:
    print(f"  {v['name']:<32} {v['candidates']:>5} (-{v['reduction_pct']:>4}%) recall {v['BOM_recall']} NAO {v['NAO_captured']} UNKcut {v['UNKNOWN_cut']}")
print("\nGT recall (v2): min survivors =", min(g['number_of_surviving_candidates'] for g in gt_rows))