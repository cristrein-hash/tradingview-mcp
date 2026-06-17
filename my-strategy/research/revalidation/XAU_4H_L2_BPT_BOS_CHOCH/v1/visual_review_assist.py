import json,csv
from datetime import datetime,timezone
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen];O=[r['open'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
SMA20=[None]*N
for i in range(19,N): SMA20[i]=sum(C[i-19:i+1])/20
geom_by_ep={o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
firstpass={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_episode_labels.csv"))}
def fl(x):
    try:return float(x)
    except:return None

def nearest_smc(i):
    # smc_recent at bar i: list of {text(CHoCH/BOS/EQH/EQL), x(bars ago), price}
    smc=frozen[i].get('smc_recent') or []
    if not smc: return 'none'
    smc=sorted(smc,key=lambda e:e.get('x',999))[:3]
    return ' / '.join(f"{e.get('text')}@{e.get('x')}b({round(e.get('price',0),0):.0f})" for e in smc)
def nearest_nas(i):
    nas=frozen[i].get('nas_recent') or []
    if not nas: return 'none'
    n=min(nas,key=lambda e:e.get('x',999)); return f"{n.get('text')}@{n.get('x')}b"

rows=[]
for ep in sorted(geom_by_ep):
    o=geom_by_ep[ep]; i=o['bar_idx']; cid=o['candidate_id']; q=qual.get(cid,{}); fp=firstpass['E%d'%ep]
    pol=float(matrix[i]['level']); p=C[i]; atr=ATR[i]
    held=all(C[j]>=pol for j in range(i+1,min(i+5,N)))
    hh=max(H[i+1:min(i+5,N)],default=p)>H[i] and min(L[i+1:min(i+5,N)],default=p)>=pol
    acc=held or hh
    bear=(SMA20[i] is not None and p<SMA20[i] and (C[i]-C[max(0,i-20)])<0) or matrix[i]['blk_first_retomada']=='1' or matrix[i]['blk_bear_flag']=='1'
    sd=fl(q.get('dist_4h_supply_low_atr')); dd=fl(q.get('dist_4h_demand_top_atr'))
    body=abs(C[i]-O[i])/(H[i]-L[i]) if H[i]>L[i] else 0
    green=C[i]>O[i]
    # mechanical corroboration of first-pass category
    fp_cat=fp['visual_category']
    # structural read: which category the objective data most supports
    if bear and not acc: data_cat='BEAR_LEG_RECLAIM_TRAP'
    elif (sd is not None and sd<=1) and q.get('supply_4h_rejected_before_entry')=='1' and not acc: data_cat='SUPPLY_REJECTION'
    elif (fl(matrix[i]['nas_short_10']) or 0)>=6 and not acc: data_cat='TOP_SWEEP_REJECTION'
    elif q.get('supply_4h_broken_before_entry')=='1' and acc: data_cat='ACCEPTED_SUPPLY_BREAK'
    elif q.get('demand_category')=='DEMAND_SUPPORTING_RETEST' and acc: data_cat='DEMAND_SUPPORTED_RECLAIM'
    elif acc: data_cat='POLARITY_DEFENDED'
    else: data_cat='NEEDS_SECOND_REVIEW'
    corrob = 'SUPPORTS' if data_cat==fp_cat else ('AMBIGUOUS' if data_cat=='NEEDS_SECOND_REVIEW' else f'SUGGESTS_{data_cat}')
    rows.append({'episode_id':'E%d'%ep,'chart_label':o['label'],'timestamp':o['time_iso'],'navigate_to':o['time_iso'],
      'firstpass_category':fp_cat,
      # --- objective pre-outcome structural dossier (NO outcome/R) ---
      'polarity_level':round(pol,2),'entry_close':round(p,2),'atr':round(atr,2) if atr else '',
      'recent_smc_struct':nearest_smc(i),'recent_nas':nearest_nas(i),
      'reclaim_candle':('verde' if green else 'vermelho')+f' body{int(body*100)}%',
      'demand_below_cat':q.get('demand_category',''),'dist_demand_atr':dd if dd is not None else '',
      'supply_overhead_cat':q.get('supply_category',''),'dist_supply_atr':sd if sd is not None else '',
      'supply_broken':q.get('supply_4h_broken_before_entry',''),'supply_rejected':q.get('supply_4h_rejected_before_entry',''),
      'acceptance_after_reclaim':'ACEITOU' if acc else 'NÃO_aceitou',
      'bear_leg_context':'SIM' if bear else 'não','nas_short_10':matrix[i]['nas_short_10'],'rsi':matrix[i]['rsi'],
      'claude_structural_read':data_cat,'mechanical_corroboration':corrob,
      # --- columns for CRIS to fill visually (left blank/awaiting) ---
      'visual_label_final':'','visual_confirm':'AWAITING_USER','why_visual':'',
      'acceptance_or_rejection':'','polarity_defended':'','supply_accepted_or_rejected':'',
      'demand_support':'','bear_leg_context_user':'','top_sweep_risk':'','reviewer_note':''})

with open(f"{D}/l2_bpt_visual_episode_labels.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print("mechanical corroboration of first-pass (objective data vs first-pass):")
for k,v in Counter(r['mechanical_corroboration'] for r in rows).most_common(): print(f"  {k:<32} {v}")
print("\ndossier ready — visual_confirm=AWAITING_USER for all 41 (Cris fills on chart)")
print("\nepisodes where data DISAGREES with first-pass (priority review):")
for r in rows:
    if r['mechanical_corroboration'].startswith('SUGGESTS'):
        print(f"  {r['episode_id']:<4} {r['timestamp']:<17} firstpass={r['firstpass_category']:<24} data={r['claude_structural_read']:<24} acc={r['acceptance_after_reclaim']} bear={r['bear_leg_context']}")
