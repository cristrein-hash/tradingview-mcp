#!/usr/bin/env python3
"""L2/BPT — o que os LOSERS QUE VAZAM (refined PRESERVE) têm de diferente dos LOSERS CORTADOS (refined BLOCK)
e dos RUNNERS (Cris). DIAGNÓSTICO/hipótese — n minúsculo, qualquer achado é TESTADO no full 276 (lição DA overfit).
Causal. realR uncapped. Multi-fatorial."""
import csv, json
D="results"; RR="repro_recovery"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
frozen=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]; C=[r['close'] for r in frozen]
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
surg={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_bearleg_surgical.csv"))}
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
def decel(i,w=6):
    if i-2*w<0: return False
    return (C[i]-C[i-w])/w>(C[i-w]-C[i-2*w])/w

# grupos (do surgical CSV)
LEAK=[b for b in surg if surg[b]['klass']=='loser' and surg[b]['refined']=='PRESERVE']  # vazam
BLK =[b for b in surg if surg[b]['klass']=='loser' and surg[b]['refined']=='BLOCK']      # cortados certo
RUN =[b for b in surg if surg[b]['klass']=='runner']                                      # preservar
print("="*80);print("LOSERS QUE VAZAM vs CORTADOS vs RUNNERS (dentro do bear_leg)")
print(f"LEAK(vazam)={len(LEAK)}  BLOCKED(cortados)={len(BLK)}  RUNNERS={len(RUN)}")

# features ricas p/ perfilar
def feat(b):
    e=eng[b];d=dec.get(b,{});x=xv2.get(b,{});P=pk[b]
    return {
     'demand_DEFENDED':d.get('demand')=='DEMAND_DEFENDED','demand_ABSENT':d.get('demand')=='DEMAND_ABSENT',
     'capit_CLIMAX':d.get('capit')=='CLIMAX_RECLAIM','capit_KNIFE':d.get('capit')=='FALLING_KNIFE',
     'mom_WEAK':e.get('momentum')=='WEAK_MOMENTUM','mom_STRONG':e.get('momentum')=='STRONG_BULL_MOMENTUM',
     'sup_CLEAN':d.get('sup_cat')=='CLEAN_SKY','sup_REJECT':d.get('sup_cat') in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET'),
     'decel':decel(b),'reclaim>0.5':(fn(P.get('reclaim_body_atr')) or 0)>0.5,
     'bub_SELL_CLIMAX':x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL','bub_SELL_DIST':x.get('bubbles')=='BUBBLE_SELL_DISTRIBUTION',
     'weekly_slope<0':(fn(d.get('weekly_slope')) or 0)<0,'macro_broken':d.get('macro_broken')=='True',
     'rsi_min8<=30':(fn(P.get('rsi_min8')) or 99)<=30,'drop20>=3':(fn(P.get('drop20_atr')) or 0)>=3,
     'va_below':P.get('below_VAL') in(True,'True'),'fuel_low':e.get('fuel')=='low_fuel',
    }
keys=list(feat(RUN[0]).keys())
def rate(grp,k): return sum(1 for b in grp if feat(b)[k])/len(grp) if grp else 0
print(f"\n{'feature':18}{'RUN%':>6}{'LEAK%':>7}{'BLK%':>6}  diferencial")
for k in keys:
    rr=rate(RUN,k);lk=rate(LEAK,k);bk=rate(BLK,k)
    # o que separa RUNNER de LEAK (o discriminador que faltou): runner tem, leak não
    mark=''
    if rr>=0.5 and rr>lk*1.6: mark=' <<RUNNER vs LEAK (candidato)'
    if lk>=0.5 and lk>rr*1.6: mark=' <<LEAK-marca (loser disfarçado)'
    if bk>=0.5 and bk>lk*1.6: mark+=' [BLK-marca]'
    print(f"{k:18}{100*rr:>6.0f}{100*lk:>7.0f}{100*bk:>6.0f}{mark}")

# candidatos: feature que RUNNER tem e LEAK não -> testar no FULL 276 (não repetir overfit)
print(f"\n--- TESTE DE GENERALIZAÇÃO no FULL 276 (lição DA: bear-leg-only não vale) ---")
nR=sum(1 for b in EP if MFE[b]>=5); base=nR/len(EP)
cands=[k for k in keys if rate(RUN,k)>=0.5 and rate(RUN,k)>rate(LEAK,k)*1.6]
print(f"candidatos (RUN tem, LEAK não): {cands}")
for k in cands:
    grp=[b for b in EP if feat(b)[k]]; rr=sum(1 for b in grp if MFE[b]>=5)/len(grp) if grp else 0
    print(f"  {k:18} full276: n={len(grp):>3} runner_rate={100*rr:.0f}% (base {100*base:.0f}%) lift={rr/base:.2f}")
print("\nVEREDITO: se nenhum candidato bate lift>1 robusto no full 276, o diferencial LEAK-vs-RUN é específico/ruído (n=5).")
print("DONE leaked vs blocked.")
