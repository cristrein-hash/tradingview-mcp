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
geom={ 'C%d'%o['bar_idx']:o for o in json.load(open('/tmp/plot_geometry.json'))}
geom_by_ep={o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
def fl(x):
    try:return float(x)
    except:return None

def features(o):
    i=o['bar_idx']; pol=float(matrix[i]['level']); p=C[i]; atr=ATR[i]; cid=o['candidate_id']; q=qual.get(cid,{})
    # acceptance_after_reclaim (user spec): next 2-4 closes don't close below polarity; OR HH/HL
    held=all(C[j]>=pol for j in range(i+1,min(i+5,N)))
    hh = max(H[i+1:min(i+5,N)],default=p) > H[i] and min(L[i+1:min(i+5,N)],default=p) >= pol
    acceptance = held or hh
    # bear-leg context: close<SMA20 AND down-slope last 20 OR first_retomada/bear_flag
    bear_struct = (SMA20[i] is not None and p<SMA20[i] and (C[i]-C[max(0,i-20)])<0)
    bear_leg = bear_struct or matrix[i]['blk_first_retomada']=='1' or matrix[i]['blk_bear_flag']=='1'
    # supply context
    sup_broken = q.get('supply_4h_broken_before_entry')=='1'
    sup_rejected = q.get('supply_4h_rejected_before_entry')=='1'
    sd = fl(q.get('dist_4h_supply_low_atr')); sup_near = sd is not None and sd<=1
    demc=q.get('demand_category',''); supc=q.get('supply_category','')
    # top cluster: NAS short recent high
    nas_short=fl(matrix[i]['nas_short_10']) or 0; top_cluster = nas_short>=6
    # late/extended: up-streak before entry (many consecutive higher closes) or far above polarity
    upstreak=0
    for j in range(i,max(0,i-10),-1):
        if C[j]>C[j-1]: upstreak+=1
        else: break
    dist_pol=(p-pol)/atr if atr else 0
    late = upstreak>=5 or dist_pol>2.5
    return dict(acceptance=acceptance,held=held,hh=hh,bear_leg=bear_leg,sup_broken=sup_broken,sup_rejected=sup_rejected,
                sup_near=sup_near,demc=demc,supc=supc,top_cluster=top_cluster,late=late,dist_pol=round(dist_pol,2),nas_short=nas_short)

def categorize(f):
    # transparent decision tree (mechanical first-pass; visual_confirm PENDING)
    if f['bear_leg'] and not f['acceptance']: return 'BEAR_LEG_RECLAIM_TRAP','perna bear + reclaim não aceitou'
    if f['sup_near'] and f['sup_rejected'] and not f['acceptance']: return 'SUPPLY_REJECTION','supply colado + rejeição, sem aceitação'
    if f['top_cluster'] and not f['acceptance']: return 'TOP_SWEEP_REJECTION','cluster TOP/NAS + sem aceitação'
    if f['sup_broken'] and f['acceptance']: return 'ACCEPTED_SUPPLY_BREAK','rompeu supply e aceitou acima'
    if f['demc']=='DEMAND_SUPPORTING_RETEST' and f['acceptance']: return 'DEMAND_SUPPORTED_RECLAIM','demanda apoia + aceitação'
    if f['acceptance'] and not f['late']: return 'POLARITY_DEFENDED','segurou acima da polaridade'
    if f['late']: return 'LATE_EXTENDED_ENTRY','entrada esticada/perna madura'
    if f['acceptance'] and f['late']: return 'GENERIC_BULL_DRIFT','aceitou mas só por drift/tarde'
    return 'NEEDS_SECOND_REVIEW','ambíguo (sem sinal claro)'

rows=[]
for ep in sorted(geom_by_ep):
    o=geom_by_ep[ep]; f=features(o); cat,reason=categorize(f)
    # confirm / invalidate criteria (per category)
    confirm={'ACCEPTED_SUPPLY_BREAK':'fecha e segura acima da supply rompida; HH/HL',
      'POLARITY_DEFENDED':'2-4 closes acima da polaridade; não perde o nível',
      'DEMAND_SUPPORTED_RECLAIM':'retest toca demanda e defende; reclaim verde aceito',
      'BEAR_LEG_RECLAIM_TRAP':'(invalida a entrada) — sem confirmação válida em perna bear',
      'TOP_SWEEP_REJECTION':'(invalida) varreu topo e rejeitou',
      'SUPPLY_REJECTION':'(invalida) bateu supply e falhou',
      'LATE_EXTENDED_ENTRY':'precisaria pullback/retest, não entrada esticada',
      'GENERIC_BULL_DRIFT':'só vale se houver estrutura real; senão é drift',
      'NEEDS_SECOND_REVIEW':'olho humano'}[cat]
    invalidate={'ACCEPTED_SUPPLY_BREAK':'volta a fechar abaixo da supply/polaridade',
      'POLARITY_DEFENDED':'close abaixo da polaridade nos próximos candles',
      'DEMAND_SUPPORTED_RECLAIM':'perde a demanda / fecha abaixo',
      'BEAR_LEG_RECLAIM_TRAP':'continua a perna de baixa / LL',
      'TOP_SWEEP_REJECTION':'reverte para baixo após o sweep',
      'SUPPLY_REJECTION':'rejeição confirma topo',
      'LATE_EXTENDED_ENTRY':'reverte sem retest',
      'GENERIC_BULL_DRIFT':'perde estrutura quando o drift para',
      'NEEDS_SECOND_REVIEW':'—'}[cat]
    seems = 'NAO_real' if cat in ('BEAR_LEG_RECLAIM_TRAP','TOP_SWEEP_REJECTION','SUPPLY_REJECTION') else ('ambíguo' if cat in ('LATE_EXTENDED_ENTRY','GENERIC_BULL_DRIFT','NEEDS_SECOND_REVIEW') else 'BOM_real_candidato')
    rows.append({'episode_id':'E%d'%ep,'chart_label':o['label'],'timestamp':o['time_iso'],
      'visual_category':cat,'reason':reason,
      'q_aceitou_acima_supply':'aceitou' if f['acceptance'] else 'rejeitou/n_aceitou',
      'q_polaridade_defendida':'sim' if f['held'] else 'não',
      'q_reclaim_segurou':'segurou' if f['acceptance'] else 'falhou',
      'q_bull_ou_bear_leg':'bear_leg' if f['bear_leg'] else 'bull/neutro',
      'q_valor_ou_tardia':'tardia' if f['late'] else 'valor',
      'q_top_cluster_exaustao':'sim' if f['top_cluster'] else 'não',
      'q_supply_bloqueia_ou_absorvida':'absorvida/rompida' if f['sup_broken'] else ('bloqueia(perto)' if f['sup_near'] else 'longe/n/a'),
      'q_demanda_apoia':'apoia' if f['demc']=='DEMAND_SUPPORTING_RETEST' else ('longe/ausente' if f['demc'] in('DEMAND_ABSENT_OR_IRRELEVANT','DEMAND_TOO_DEEP') else 'neutra'),
      'confirma_entrada':confirm,'invalida_entrada':invalidate,'seems':seems,
      'visual_confirm':'PENDING','dist_pol_atr':f['dist_pol'],'nas_short_10':f['nas_short']})

with open(f"{D}/l2_bpt_visual_episode_labels.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print("category distribution (MECHANICAL first-pass, visual_confirm PENDING):")
for k,v in Counter(r['visual_category'] for r in rows).most_common(): print(f"  {k:<26} {v}")
print("\nseems:",dict(Counter(r['seems'] for r in rows)))
print("\nper-episode:")
for r in rows: print(f"  {r['episode_id']:<4} {r['chart_label']:<16} {r['visual_category']:<24} aceit={r['q_aceitou_acima_supply']:<16} leg={r['q_bull_ou_bear_leg']}")
