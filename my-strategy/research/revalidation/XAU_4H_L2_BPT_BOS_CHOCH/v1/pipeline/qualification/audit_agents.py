#!/usr/bin/env python3
"""Auditoria da rubrica + 14 agentes do TAKE engine (Partes 2-6). Não retuna, não muda decisões.
Lê decisões individuais (qual_dec_*), packets (84 fatores), outcomes. Produz as CSVs do bloco."""
import json,csv,glob,re,os
from collections import Counter,defaultdict
RR="repro_recovery"; D="results"
dec=[]
for fp in sorted(glob.glob(f"{RR}/qual_dec_*.jsonl")):
    b=fp.split('qual_dec_')[1][:2]
    for l in open(fp):
        if l.strip(): r=json.loads(l); r['_batch']=b; dec.append(r)
decby={r['bar_idx']:r for r in dec}
pk={json.loads(l)['bar_idx']:json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
out={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
FKEYS=list(next(iter(pk.values())).keys())

# ---- PARTE 2: 84-factor map ----
def grp(k):
    if any(s in k for s in ['rsi','RSI']):return 'momentum/RSI'
    if any(s in k for s in ['demand','supply','reclaim']):return 'demand/supply'
    if any(s in k for s in ['bub','poc']):return 'bubbles/auction'
    if 'nas' in k:return 'NAS'
    if any(s in k for s in ['vol','VAL','POC','va_']):return 'volume/SVP'
    if any(s in k for s in ['legpos','drop20','rise20','trend','slope','sma','consec','range','atr','sweet']):return 'momentum/legpos'
    if any(s in k for s in ['smc','bos','choch']):return 'SMC'
    if any(s in k for s in ['sl_','F_STRICT','hour','dead']):return 'risk/anti-top'
    if any(s in k for s in ['macro','regime','rsi_1d']):return 'macro/regime'
    return 'meta'
with open(f"{D}/l2_bpt_agent_input_84_factor_map.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['factor','group','causal','in_prompt','null_rate_pct','caveat'])
    for k in FKEYS:
        nulls=sum(1 for i in pk if pk[i].get(k) in (None,'',[]))
        cav=''
        if k=='macro_leg_direction':cav='REFERENCE_ONLY na maioria (placeholder, pouco útil)'
        elif 'supply' in k and 'blocks' in k:cav='flag binário (distância contínua dist_4h_supply_low_atr é o sinal real)'
        elif k in('rel_volume','below_VAL','dist_POC_atr','va_width_atr'):cav='Session VP nativo; causalidade within-session auditada OK'
        elif 'smc' in k:cav='LuxAlgo pode repintar; usar direção/recência, não preço exato'
        w.writerow([k,grp(k),'YES','YES (packet completo dado ao agente)',round(100*nulls/len(pk),1),cav])

# ---- flags textuais no reasoning ----
def txt(r): return (' '.join(r.get('positive_factors',[])+r.get('negative_factors',[]))+' '+(r.get('decisive_reason') or '')).lower()
def has(r,pats): t=txt(r); return any(p in t for p in pats)
FLAGS={
 'supply_distance':['supply','overhead','atr away','blocks'],   # refinar abaixo p/ distance vs flag
 'capitulation':['capitul','oversold','washout','flush','falling','sweet','drop20','rsi 3','rsi3'],
 'top_exhaustion':['top','exhaust','blow-off','blowoff','overbought','late','parabol','climax'],
 'demand':['demand','colad','defended','reclaim','origin'],
 'sl_quality':['sl ','v_reversal','tight','wide','risk-shap','atr sl','stop'],
 'macro_leg':['trend','macro','leg','uptrend','downtrend','sma50'],
 'drift_beta':['drift','beta','bull market','bull-beta'],
}
def supply_dist_vs_flag(r):
    t=txt(r)
    dist = bool(re.search(r'\d+(\.\d+)?\s*atr.*(supply|overhead)|(supply|overhead).*\d+(\.\d+)?\s*atr',t))
    flag = ('blocks' in t or 'block the' in t or 'capping' in t or 'capped' in t)
    return dist,flag

# ---- PARTE 3: reasoning audit matrix ----
with open(f"{D}/l2_bpt_agent_reasoning_audit_matrix.csv","w",newline="") as f:
    cols=['episode_id','bar_idx','batch','decision','direction','confidence','setup_type','n_pos','n_neg',
          'decisive_reason','closest_known','ment_supply_dist','ment_supply_flag','ment_capit','ment_top','ment_demand','ment_sl','ment_macro','ment_drift']
    w=csv.writer(f);w.writerow(cols)
    for r in dec:
        d,fl=supply_dist_vs_flag(r)
        w.writerow([r.get('episode_id'),r['bar_idx'],r['_batch'],r['decision'],r['direction'],r.get('confidence'),
                    r.get('expected_setup_type'),len(r.get('positive_factors',[])),len(r.get('negative_factors',[])),
                    (r.get('decisive_reason') or '')[:160],'|'.join(r.get('closest_known_examples') or []),
                    int(d),int(fl),int(has(r,FLAGS['capitulation'])),int(has(r,FLAGS['top_exhaustion'])),
                    int(has(r,FLAGS['demand'])),int(has(r,FLAGS['sl_quality'])),int(has(r,FLAGS['macro_leg'])),int(has(r,FLAGS['drift_beta']))])

# ---- PARTE 4/6: meta-validation + reasoning vs outcome ----
def realR(i): return float(out[i]['realR']) if i in out else None
def win(i): return out[i]['exitype'].startswith('WIN') if i in out else False
groups={'TAKE_win':[],'TAKE_lose':[],'SKIP_win':[],'SKIP_lose':[],'REVIEW_win':[],'REVIEW_lose':[]}
for r in dec:
    i=r['bar_idx']
    if i not in out: continue
    g=r['decision']+('_win' if win(i) else '_lose')
    if g in groups: groups[g].append(r)
# frequência de flags por grupo
flagnames=['ment_supply_dist','ment_supply_flag','ment_capit','ment_top','ment_demand','ment_sl','ment_macro','ment_drift']
def flagvec(r):
    d,fl=supply_dist_vs_flag(r)
    return {'ment_supply_dist':int(d),'ment_supply_flag':int(fl),'ment_capit':int(has(r,FLAGS['capitulation'])),
            'ment_top':int(has(r,FLAGS['top_exhaustion'])),'ment_demand':int(has(r,FLAGS['demand'])),
            'ment_sl':int(has(r,FLAGS['sl_quality'])),'ment_macro':int(has(r,FLAGS['macro_leg'])),'ment_drift':int(has(r,FLAGS['drift_beta']))}
with open(f"{D}/l2_bpt_agent_reasoning_vs_outcome.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['group','n','avgR','pct_'+'  pct_'.join(flagnames).split('  ')[0]]+['pct_'+x for x in flagnames])
    for g,rs in groups.items():
        if not rs: w.writerow([g,0]+['']*(2+len(flagnames)));continue
        avg=sum(realR(r['bar_idx']) for r in rs)/len(rs)
        pcts=[round(100*sum(flagvec(r)[fn] for r in rs)/len(rs)) for fn in flagnames]
        w.writerow([g,len(rs),round(avg,3)]+pcts)
# meta-validation: confidence vs outcome + supply_dist vs flag usage + setup_type performance
with open(f"{D}/l2_bpt_agent_meta_validation.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['question','metric','value'])
    # confidence buckets
    for lo,hi in [(0,45),(45,55),(55,70),(70,101)]:
        ids=[r['bar_idx'] for r in dec if lo<=(r.get('confidence') or 0)<hi and r['bar_idx'] in out]
        if ids:
            avg=sum(realR(i) for i in ids)/len(ids); wr=100*sum(1 for i in ids if win(i))/len(ids)
            w.writerow([f'confidence[{lo}-{hi})',f'n={len(ids)} avgR',f'{avg:+.3f} WR={wr:.0f}%'])
    # supply: distance vs flag usage overall
    nd=sum(1 for r in dec if supply_dist_vs_flag(r)[0]); nf=sum(1 for r in dec if supply_dist_vs_flag(r)[1])
    w.writerow(['usa supply_distance contínua?',f'{nd}/{len(dec)} decisões mencionam dist-ATR',f'{100*nd/len(dec):.0f}%'])
    w.writerow(['usa supply flag (blocks/capped)?',f'{nf}/{len(dec)}',f'{100*nf/len(dec):.0f}%'])
    # capitulation recognized in TAKE bottom_reversal?
    br=[r for r in dec if r.get('expected_setup_type')=='bottom_reversal']
    cap=sum(1 for r in br if has(r,FLAGS['capitulation']))
    w.writerow(['reconhece capitulação em bottom_reversal?',f'{cap}/{len(br)}',f'{100*cap/max(1,len(br)):.0f}%'])
    # top penalized in SKIP?
    sk=[r for r in dec if r['decision']=='SKIP']
    topp=sum(1 for r in sk if has(r,FLAGS['top_exhaustion']))
    w.writerow(['penaliza topo/tarde em SKIP?',f'{topp}/{len(sk)}',f'{100*topp/max(1,len(sk)):.0f}%'])
    # setup_type performance
    for st in ['bottom_reversal','demand_reclaim','bull_pullback','late_top','bear_bounce','unclear']:
        ids=[r['bar_idx'] for r in dec if r.get('expected_setup_type')==st and r['bar_idx'] in out]
        if ids: w.writerow([f'setup={st}',f'n={len(ids)} avgR',f'{sum(realR(i) for i in ids)/len(ids):+.3f}'])

# ---- PARTE 5: agreement (fan-out -> sem ensemble) + inter-agent consistency ----
with open(f"{D}/l2_bpt_agent_agreement_disagreement.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['note','value'])
    w.writerow(['ESTRUTURA','FAN-OUT por lote (não ensemble): 0 episódios com >1 decisão; cada trade 1 agente'])
    w.writerow(['agreement per-trade','N/A (sem decisões multi-agente por trade) -> HARD-STOP PARCIAL p/ voto/entropy'])
    w.writerow(['agregador/voto/consenso','INEXISTENTE; decisão final = decisão do único agente do lote'])
    w.writerow(['---inter-agent consistency (por lote)---',''])
    for b in sorted(set(r['_batch'] for r in dec)):
        rs=[r for r in dec if r['_batch']==b]
        c=Counter(r['decision'] for r in rs); ids=[r['bar_idx'] for r in rs if r['bar_idx'] in out]
        avg=sum(realR(i) for i in ids)/len(ids) if ids else 0
        w.writerow([f'batch {b}',f"TAKE{c['TAKE']}/REV{c['REVIEW']}/SKIP{c['SKIP']} avgR={avg:+.2f}"])
print("WROTE: input_84_factor_map, reasoning_audit_matrix, reasoning_vs_outcome, meta_validation, agreement_disagreement")
# resumo p/ doc
print("\n=== RESUMO META ===")
print("supply_distance mencionada:",sum(1 for r in dec if supply_dist_vs_flag(r)[0]),"/",len(dec))
print("supply_flag mencionada:",sum(1 for r in dec if supply_dist_vs_flag(r)[1]),"/",len(dec))
for g,rs in groups.items():
    if rs: print(f"  {g}: n={len(rs)} avgR={sum(realR(r['bar_idx']) for r in rs)/len(rs):+.3f}")
