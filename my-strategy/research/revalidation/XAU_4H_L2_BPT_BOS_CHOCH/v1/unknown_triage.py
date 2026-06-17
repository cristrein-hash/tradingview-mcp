#!/usr/bin/env python3
"""L2/BPT — UNKNOWN triage (PER EPISODE). Buckets + controlled visual sample (50-70) + label
taxonomy. Reuses structural-SL outcome (the corrected measure) + demand/supply quality. NO new
backtest/edge claim, NO filter, NO plot, NO production/SLIM. Diagnostic/planning only.
"""
import json, csv, statistics
from collections import defaultdict, Counter

D="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen); H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen]
ts=[r['ts_epoch'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
from datetime import datetime,timezone
def fmt(t): return datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
base=[r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
reclass={r['candidate_id']:r['reclass'] for r in csv.DictReader(open(f"{D}/l2_bpt_unknown_strong_reclassification.csv"))}
def lab(r): return 'BOM' if r['GT_match']=='yes' else ('NAO' if r['NAO_match']=='yes' else 'UNKNOWN')
labof={int(r['candidate_id'][1:]):lab(r) for r in base}
RW=6;R_FLOOR=0.3;R_CEIL=1.5;MAXHOLD=60
def sl_risk(i,p,atr):
    lo=min(L[max(0,i-RW+1):i+1]); sl=lo-0.1*atr; risk=p-sl
    if risk<=0: return None,None
    if risk<R_FLOOR*atr: risk=R_FLOOR*atr
    return p-risk,risk
def sim2R(i):
    p=C[i];atr=ATR[i]
    if not atr: return None,None
    sl,risk=sl_risk(i,p,atr)
    if sl is None: return None,None
    tgt=p+2*risk;end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        if L[j]<=sl: return -1.0,'stop'
        if H[j]>=tgt: return 2.0,'target'
    return (C[end]-p)/risk,'time'

# ---- episodes (gap>6) ----
idxs=sorted(labof); episodes=[]; cur=[idxs[0]]
for a,b in zip(idxs,idxs[1:]):
    if b-a<=6: cur.append(b)
    else: episodes.append(cur); cur=[b]
episodes.append(cur)
bom_idx=[i for i in idxs if labof[i]=='BOM']
def near_bom(i,w=12): return any(abs(i-b)<=w for b in bom_idx)

# UNKNOWN episodes (no BOM and no NAO in cluster)
unk_eps=[]
absorbed_unk_in_bom=0
for e in episodes:
    labs=[labof[i] for i in e]
    if 'BOM' in labs: absorbed_unk_in_bom+=sum(1 for i in e if labof[i]=='UNKNOWN'); continue
    if 'NAO' in labs: continue
    unk_eps.append(e)

rows=[]
for e in unk_eps:
    rep=e[0]; cid='C%d'%rep; q=qual.get(cid,{})
    r,how=sim2R(rep)
    sd=q.get('dist_4h_supply_low_atr');
    def fl(x):
        try:return float(x)
        except:return None
    sd=fl(sd); demc=q.get('demand_category',''); supc=q.get('supply_category',''); polc=q.get('polarity_category','')
    rows.append({'episode_first_idx':rep,'candidate_id':cid,'timestamp':fmt(ts[rep]),'n_candidates_in_episode':len(e),
      'outcome_R_2R':round(r,2) if r is not None else '','outcome_how':how or '',
      'dist_supply_low_atr':sd if sd is not None else '','demand_category':demc,'supply_category':supc,'polarity_category':polc,
      'reclass':reclass.get(cid,'NA'),'near_BOM_12b':int(near_bom(rep)),
      'dense_leg':int(len(e)>=8)})
# buckets (non-exclusive membership)
def bucket_flags(x):
    sd=x['dist_supply_low_atr']; r=x['outcome_R_2R']
    f={}
    f['UNKNOWN_HIGH_OUTCOME_BOMlike']= isinstance(r,float) and r>=2 and x['demand_category'] in ('DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG')
    f['UNKNOWN_LOW_OUTCOME_NAOlike']= isinstance(r,float) and r<=-1 and (x['polarity_category']=='POLARITY_UNDER_SUPPLY_PRESSURE' or (isinstance(sd,float) and sd<=1))
    f['UNKNOWN_SUPPLY_PRESSURE']= isinstance(sd,float) and sd<=1
    f['UNKNOWN_CLEAN_SKY']= x['supply_category']=='CLEAN_SKY'
    f['UNKNOWN_DEMAND_SUPPORTED']= x['demand_category']=='DEMAND_SUPPORTING_RETEST'
    f['UNKNOWN_NO_DEMAND_SUPPORT']= x['demand_category'] in ('DEMAND_ABSENT_OR_IRRELEVANT','DEMAND_TOO_DEEP')
    f['UNKNOWN_DUPLICATE_DENSE_LEG']= x['dense_leg']==1
    f['UNKNOWN_SINGLE_CLEAN_SIGNAL']= x['n_candidates_in_episode']<=2
    f['UNKNOWN_TOP_SWEEP_RISK']= x['reclass']=='GENERIC_BULL_FOLLOW_THROUGH' and isinstance(r,float) and r<0
    f['UNKNOWN_NEEDS_VISUAL']= (r=='' ) or (x['demand_category']=='' )
    return f
for x in rows: x['buckets']='|'.join(k for k,v in bucket_flags(x).items() if v) or 'UNCLASSIFIED'

# bucket summary
buckets=['UNKNOWN_HIGH_OUTCOME_BOMlike','UNKNOWN_LOW_OUTCOME_NAOlike','UNKNOWN_SUPPLY_PRESSURE','UNKNOWN_CLEAN_SKY',
 'UNKNOWN_DEMAND_SUPPORTED','UNKNOWN_NO_DEMAND_SUPPORT','UNKNOWN_DUPLICATE_DENSE_LEG','UNKNOWN_SINGLE_CLEAN_SIGNAL',
 'UNKNOWN_TOP_SWEEP_RISK','UNKNOWN_NEEDS_VISUAL']
CIRCULAR={'UNKNOWN_HIGH_OUTCOME_BOMlike','UNKNOWN_LOW_OUTCOME_NAOlike','UNKNOWN_TOP_SWEEP_RISK'}  # defined ON outcome
bsum=[]
for bk in buckets:
    mem=[x for x in rows if bucket_flags(x)[bk]]
    rs=[x['outcome_R_2R'] for x in mem if isinstance(x['outcome_R_2R'],float)]
    bsum.append({'bucket':bk,
      'type':'SELECTION_GROUP_outcome_defined_NOT_a_finding' if bk in CIRCULAR else 'structural_bucket',
      'n_episodes':len(mem),'avgR':round(sum(rs)/len(rs),2) if rs else '',
      'WR_pct':('tautological' if bk in CIRCULAR else round(100*sum(1 for v in rs if v>0)/len(rs),1)) if rs else '',
      'why_review':{'UNKNOWN_HIGH_OUTCOME_BOMlike':'parecem winners L2 — confirmar setup real',
        'UNKNOWN_LOW_OUTCOME_NAOlike':'parecem losers — confirmar top/trap',
        'UNKNOWN_SUPPLY_PRESSURE':'supply colado — risco de teto','UNKNOWN_CLEAN_SKY':'sem teto — continuação limpa?',
        'UNKNOWN_DEMAND_SUPPORTED':'demanda apoia — setup L2?','UNKNOWN_NO_DEMAND_SUPPORT':'sem base — flutuante?',
        'UNKNOWN_DUPLICATE_DENSE_LEG':'sinais seriais na mesma perna','UNKNOWN_SINGLE_CLEAN_SIGNAL':'sinal isolado limpo',
        'UNKNOWN_TOP_SWEEP_RISK':'bull genérico que falhou','UNKNOWN_NEEDS_VISUAL':'dados insuficientes'}[bk],
      'priority':'high' if bk in('UNKNOWN_HIGH_OUTCOME_BOMlike','UNKNOWN_LOW_OUTCOME_NAOlike','UNKNOWN_SUPPLY_PRESSURE') else 'med'})
with open(f"{D}/l2_bpt_unknown_triage_buckets.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(bsum[0].keys())); w.writeheader(); w.writerows(bsum)

# visual sample plan — OUTCOME-BLIND, stratified by PRE-TRADE structural features only.
# (DA FATAL: selecting/showing outcome biases the human labeler -> outcome is NOT used here and
#  NOT written to the sample file. Stratify on supply/demand/leg-density only, deterministic pick.)
ok=[x for x in rows if isinstance(x['outcome_R_2R'],float)]
sel=[]
def add(items,reason,q):
    for x in items:
        sel.append({'episode_first_idx':x['episode_first_idx'],'candidate_id':x['candidate_id'],'timestamp':x['timestamp'],
          'selection_stratum':reason,'visual_question':q,
          'supply_category':x['supply_category'],'demand_category':x['demand_category'],
          'dist_supply_low_atr':x['dist_supply_low_atr'],'n_candidates_in_episode':x['n_candidates_in_episode']})
# strata = pre-trade structure only; deterministic by timestamp for reproducibility
def strat(pred): return sorted([x for x in rows if pred(x)],key=lambda x:x['timestamp'])
add(strat(lambda x:isinstance(x['dist_supply_low_atr'],float) and x['dist_supply_low_atr']<=1)[:12],'supply_pressure_<=1ATR','Comprou contra o teto ou supply era fraco/rompido?')
add(strat(lambda x:x['supply_category']=='CLEAN_SKY')[:12],'clean_sky','Céu limpo = setup L2 ou já esticado/tardio?')
add(strat(lambda x:x['demand_category']=='DEMAND_SUPPORTING_RETEST')[:10],'demand_supported','Demanda apoia um reclaim real?')
add(strat(lambda x:x['demand_category'] in('DEMAND_ABSENT_OR_IRRELEVANT','DEMAND_TOO_DEEP'))[:10],'no_demand_support','Polaridade flutuante sem base?')
add(strat(lambda x:x['dense_leg']==1)[:10],'dense_leg','Sinal serial — há polaridade/retest reais ou só drift da perna?')
add(strat(lambda x:x['n_candidates_in_episode']<=2)[:10],'single_clean_signal','Sinal isolado — setup limpo ou ruído?')
add([x for x in rows if x['near_BOM_12b']==1],'near_known_BOM','Por que é UNKNOWN e não BOM — mesmo setup ou diferente?')
# dedup by candidate_id, cap ~70 (outcome NOT in output -> blind labeling)
seen=set(); sample=[]
for s in sel:
    if s['candidate_id'] in seen: continue
    seen.add(s['candidate_id']); sample.append(s)
sample=sample[:70]
with open(f"{D}/l2_bpt_unknown_visual_sample_plan.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(sample[0].keys())); w.writeheader(); w.writerows(sample)

# label taxonomy
TAX=[('TRUE_BPT_LONG','reclaim válido sobre polaridade real, demanda/estrutura apoiando, R-viável','polaridade clara + retest + reclaim verde aceito','candidato a TRUE_L2_SETUP'),
 ('ACCEPTABLE_BPT_LONG','setup L2 ok mas não perfeito (supply moderado, reclaim ok)','aceitação razoável, algum supply acima','operável com cautela'),
 ('WEAK_BPT_LONG','reclaim fraco / polaridade duvidosa','corpo fraco, perfuração rasa','baixa prioridade'),
 ('BAD_TOP_ENTRY','entrada em topo/contra supply colado','supply imediato acima, RSI esticado','excluir / NAO-like'),
 ('BEAR_LEG_TRAP','reclaim dentro de perna bear forte','LH/LL contínuos, bear flag','excluir'),
 ('GENERIC_BULL_MOVE','só subiu por drift, sem âncora L2','sem polaridade/retest claros','não é L2 — ruído'),
 ('DUPLICATE_OF_BETTER_ENTRY','sinal serial na mesma perna de entrada melhor','vários candidatos próximos','manter só o melhor'),
 ('NO_CLEAR_POLARITY','não há polaridade estrutural identificável','nível ambíguo','descartar/visual'),
 ('NO_RECLAIM_ACCEPTANCE','rompeu mas sem aceitação/retest','sweep sem hold','excluir'),
 ('NEEDS_SECOND_REVIEW','ambíguo','requer 2a leitura','fila')]
with open(f"{D}/l2_bpt_unknown_label_taxonomy.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(['label','definition','what_to_observe','future_consequence'])
    for t in TAX: w.writerow(t)

# console
print(f"UNKNOWN episodes: {len(unk_eps)} | UNKNOWN candidates absorbed into BOM episodes (dedup): {absorbed_unk_in_bom}")
rs_all=[x['outcome_R_2R'] for x in rows if isinstance(x['outcome_R_2R'],float)]
print(f"UNKNOWN episode outcome(+2R): n={len(rs_all)} WR {round(100*sum(1 for v in rs_all if v>0)/len(rs_all),1)}% avgR {round(sum(rs_all)/len(rs_all),2)}")
print("reclass dist:",dict(Counter(x['reclass'] for x in rows)))
print("\nbuckets:")
for b in bsum: print(f"  {b['bucket']:<34} n={b['n_episodes']:<4} WR={b['WR_pct']} avgR={b['avgR']} [{b['priority']}]")
print(f"\nvisual sample (dedup): {len(sample)} episodes")
print("near_BOM UNKNOWN episodes:",sum(1 for x in rows if x['near_BOM_12b']==1))
# write the full per-episode triage too
with open(f"{D}/l2_bpt_unknown_triage_episodes.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
