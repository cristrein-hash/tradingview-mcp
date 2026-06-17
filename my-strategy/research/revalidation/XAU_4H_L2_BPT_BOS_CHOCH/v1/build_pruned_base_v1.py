#!/usr/bin/env python3
"""L2/BPT v2.2 — build selective PRUNED BASE V1 (recall-first, 17/17 preserved).
Reads the diagnostic candidate matrix; applies ONLY safe layers; re-verifies recall at
EVENT level for every combination. NO backtest/PnL/plot/MCP/production/SLIM. Diagnostic base.
"""
import csv, json
from collections import defaultdict, Counter
from datetime import datetime, timezone

D = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
rows = list(csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv")))
for r in rows:
    r['entry_idx'] = int(r['candidate_id'][1:])

# event capturing sets (entry_idx within +-2 of each GT, from matrix labels)
bom_ev = defaultdict(set); nao_ev = defaultdict(set)
for r in rows:
    if r['label'] == 'BOM': bom_ev[r['gt_id']].add(r['entry_idx'])
    elif r['label'] == 'NAO': nao_ev[r['gt_id']].add(r['entry_idx'])
N_BOM = len(bom_ev); N_NAO = len(nao_ev)
n_unk = sum(1 for r in rows if r['label'] == 'UNKNOWN')

SAFE_BLK = ['volume_fraco','bear_flag','no_retest','no_polarity_defense','false_tipo_B_dump_direto','no_absorption','overextended_entry']
DANGER_BLK = ['first_retomada','BOS_fraco','bear_macro','cluster_BUY_climax']
REDUNDANT_SRC = {'fractal_2_2','nivel_interno','topo_duplo'}  # sole-recall 0 each
BACKBONE_SRC = 'fractal_3_3'  # sole-recall 10/17 -> never drop

def src_family(s):
    if s in ('fractal_3_3','fractal_2_2'): return 'fractal'
    if s in ('topo_duplo','range_top','swing_high_simples'): return 'structural'
    if s == 'nivel_interno': return 'proximity'
    return 'other'

def pruned_by_blk(r, blks): return any(r['blk_'+b] == '1' for b in blks)
def pruned_by_src(r, srcs): return r['source'] in srcs

def recall_after(kept_idx):
    return sum(1 for s in bom_ev.values() if s & kept_idx)
def nao_kept_after(kept_idx):
    return sum(1 for s in nao_ev.values() if s & kept_idx)

ALL_IDX = set(r['entry_idx'] for r in rows)

def evaluate(name, prune_fn, desc):
    kept = set(r['entry_idx'] for r in rows if not prune_fn(r))
    rec = recall_after(kept)
    nao = nao_kept_after(kept)
    kept_rows = [r for r in rows if r['entry_idx'] in kept]
    yrs = Counter(r['year'] for r in kept_rows)
    spread = len([y for y in yrs]) or 1
    return {'name':name,'desc':desc,'total':len(kept),'pct_cut':round(100*(len(rows)-len(kept))/len(rows),1),
            'BOM_recall':f"{rec}/{N_BOM}",'recall_ok':rec==N_BOM,'NAO_captured':f"{nao}/{N_NAO}",
            'cand_per_year':round(len(kept)/7,0),'sources':dict(Counter(r['source'] for r in kept_rows)),
            '_kept':kept}

# greedy 17/17-preserving union over SAFE_BLK ordered by individual UNKNOWN cut (volume_fraco biggest)
order = ['volume_fraco','overextended_entry','bear_flag','no_retest','no_polarity_defense','false_tipo_B_dump_direto','no_absorption']
greedy = []
kept = set(ALL_IDX)
for b in order:
    trial = set(r['entry_idx'] for r in rows if r['entry_idx'] in kept and r['blk_'+b] != '1')
    # recompute against full removal of this blocker on the ORIGINAL set, union-style:
    cand_kept = set(r['entry_idx'] for r in rows if not pruned_by_blk(r, greedy+[b]))
    if recall_after(cand_kept) == N_BOM:
        greedy.append(b)

P0 = evaluate('P0_original', lambda r: False, 'base original, sem pruning')
P1 = evaluate('P1_greedy_safe', lambda r: pruned_by_blk(r, greedy), f'union gulosa verificada 17/17: {greedy}')
P2 = evaluate('P2_source_prune', lambda r: pruned_by_src(r, REDUNDANT_SRC), f'drop fontes redundantes {sorted(REDUNDANT_SRC)} (mantem fractal_3_3 backbone)')
# P3 conservative = intersection of P1 and P2 removals (remove only what BOTH remove)
def p3_prune(r): return pruned_by_blk(r, greedy) and pruned_by_src(r, REDUNDANT_SRC)
P3 = evaluate('P3_conservative_intersection', p3_prune, 'interseção conservadora: remove só o que P1 E P2 removem')

versions = [P0, P1, P2, P3]

# ---- choose base: max ruído cut, recall 17/17, simple, no dangerous layer, keep fractal_3_3 ----
# user approved ~40% -> P1 (greedy safe union, -41%, 17/17, fractal_3_3 intact)
CHOSEN = P1
chosen_kept = CHOSEN['_kept']

# ---- outputs ----
def gt_match(r): return 'yes' if r['label']=='BOM' else 'no'
def nao_match(r): return 'yes' if r['label']=='NAO' else 'no'
def prune_reason(r):
    if r['entry_idx'] in chosen_kept: return ''
    reasons = [b for b in greedy if r['blk_'+b]=='1']
    return '|'.join(reasons)

out_fields = ['candidate_id','timestamp','source','source_family','reason_flags','kept','prune_reason',
              'GT_match','NAO_match','gt_id','notes']
def to_out(r):
    flags = '|'.join(b for b in (SAFE_BLK+DANGER_BLK) if r.get('blk_'+b)=='1')
    return {'candidate_id':r['candidate_id'],'timestamp':r['ts'],'source':r['source'],
            'source_family':src_family(r['source']),'reason_flags':flags,
            'kept':'kept' if r['entry_idx'] in chosen_kept else 'pruned',
            'prune_reason':prune_reason(r),'GT_match':gt_match(r),'NAO_match':nao_match(r),
            'gt_id':r['gt_id'],'notes':r['variant']+'/'+r['tipo']}

base_rows = [to_out(r) for r in rows]
with open(f"{D}/l2_bpt_v2_2_pruned_base_v1.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=out_fields); w.writeheader()
    w.writerows([o for o in base_rows if o['kept']=='kept'])
with open(f"{D}/l2_bpt_v2_2_pruned_base_v1_removed.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=out_fields); w.writeheader()
    w.writerows([o for o in base_rows if o['kept']=='pruned'])

# gt recall per event in the chosen base
gt_rows=[]
for gid,s in sorted(bom_ev.items()):
    surv = s & chosen_kept
    gt_rows.append({'gt_id':gid,'capturing_candidates_total':len(s),'surviving_in_base':len(surv),
                    'captured_in_base':'yes' if surv else 'no',
                    'surviving_ids':'|'.join('C%d'%i for i in sorted(surv))})
with open(f"{D}/l2_bpt_v2_2_pruned_base_v1_gt_recall.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(gt_rows[0].keys())); w.writeheader(); w.writerows(gt_rows)

summary={'status':['CANDIDATE_BASE','NOT_STRATEGY','NOT_VALIDATION','RECALL_PRESERVED_17_17'],
  'chosen_base':'L2_BPT_V2_2_PRUNED_BASE_V1 = P1 (greedy safe union)',
  'safe_layers_used':greedy,'forbidden_layers':DANGER_BLK,'backbone_source':BACKBONE_SRC,
  'versions':{v['name']:{k:v[k] for k in v if k!='_kept'} for v in versions},
  'recall_revalidated_after_combination':True}
with open(f"{D}/l2_bpt_v2_2_pruned_base_v1_summary.json","w") as f:
    json.dump(summary,f,indent=2)

# console
print(f"events: BOM={N_BOM} NAO={N_NAO} | greedy safe layers: {greedy}")
print(f"{'version':<32}{'total':>7}{'cut%':>7}  {'recall':>7} {'NAO':>6}  sources")
for v in versions:
    print(f"  {v['name']:<30}{v['total']:>7}{v['pct_cut']:>6}% {v['BOM_recall']:>8} {v['NAO_captured']:>6}  {sorted(v['sources'].keys())}")
print(f"\nCHOSEN = {CHOSEN['name']}  ({CHOSEN['total']} cand, -{CHOSEN['pct_cut']}%, recall {CHOSEN['BOM_recall']}, NAO {CHOSEN['NAO_captured']})")
print(f"fractal_3_3 in base: {CHOSEN['sources'].get('fractal_3_3',0)} (backbone preserved)")
print(f"outputs: pruned_base_v1.csv ({CHOSEN['total']}), _removed.csv ({len(rows)-CHOSEN['total']}), _gt_recall.csv (17), _summary.json")
