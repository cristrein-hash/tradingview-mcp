#!/usr/bin/env python3
"""BACKBONE DETERMINÍSTICO — leg-state D1/weekly (macro leg, NÃO 4H). Causal: daily com date < D (shift D-1).
Monta pacotes de evidência por trade (leg-state D1 + camadas condicionais) p/ confluência por agentes. Sem outcome."""
import json,csv,bisect
RR="repro_recovery";D="results"
daily=[json.loads(l) for l in open("../../../../strategies/candidates/regime_classifier_v3/xau_daily_with_features.jsonl") if json.loads(l).get('ts')]
daily.sort(key=lambda r:r['ts'])
weekly=[json.loads(l) for l in open("../../../../strategies/candidates/regime_classifier_v3/xau_weekly_with_features.jsonl") if json.loads(l).get('ts')]
weekly.sort(key=lambda r:r['ts'])
extB=[json.loads(l) for l in open("../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl") if json.loads(l).get('ts')]
extB.sort(key=lambda r:r['ts'])
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
mat={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
cris={r['plot_id']:r['cris_verdict'] for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0_cris_verdicts.csv"))}
v1={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_macro_specialist_confluence_62.csv"))}
def fn(v):
    try:return float(v)
    except:return None
def ep(p):return int(mat[p]['episode_id'])
def final(pid):
    c=cris.get(pid)
    if c:return 'PROTECT' if c.startswith('PROTECT') else('BLOCK' if c.startswith('BLOCK') else('REVIEW' if c.startswith('REVIEW') else('TRANSFORM' if c.startswith('TRANSFORM') else mat[pid]['visual_verdict'])))
    return mat[pid]['visual_verdict']
C_NAMED={'T34','T36','S39','S19','T27','S14'}
A=[p for p in mat if p.startswith('S') and final(p)=='PROTECT' and p not in C_NAMED]
B=[p for p in mat if p.startswith('T') and final(p)=='BLOCK' and p not in C_NAMED]
Cset=[p for p in mat if p in C_NAMED or final(p) in('REVIEW','TRANSFORM')]
SET={**{p:'A' for p in A},**{p:'B' for p in B},**{p:'C' for p in Cset}}

def daily_before(ed):  # daily bars com date ESTRITAMENTE < ed (shift D-1, causal)
    ds=[r['ts'] for r in daily];i=bisect.bisect_left(ds,ed);return daily[:i]
def dfractals(bars,k=3,lookback=120):
    Hd=[b['high'] for b in bars];Ld=[b['low'] for b in bars];n=len(bars)
    SH=[];SL=[]
    for p in range(max(k,n-lookback),n-k):
        if all(Hd[p]>Hd[j] for j in range(p-k,p)) and all(Hd[p]>=Hd[j] for j in range(p+1,p+k+1)): SH.append(Hd[p])
        if all(Ld[p]<Ld[j] for j in range(p-k,p)) and all(Ld[p]<=Ld[j] for j in range(p+1,p+k+1)): SL.append(Ld[p])
    return SH,SL
def macro_leg(ed,price):
    bars=daily_before(ed)
    if len(bars)<30: return 'UNKNOWN',{'n_daily':len(bars)}
    SH,SL=dfractals(bars)
    Bx=extB[bisect.bisect_left([r['ts'] for r in extB],ed)-1] if extB else {}
    wk=weekly[bisect.bisect_left([r['ts'] for r in weekly],ed)-1] if weekly else {}
    f={'n_SH':len(SH),'n_SL':len(SL),'regimeB_state':Bx.get('v3_state'),'regimeB_combined':Bx.get('combined_score'),
       'macro_broken':Bx.get('macro_broken'),'weekly_slope':wk.get('slope_20_pct'),'weekly_rsi':wk.get('rsi_14'),
       'last_daily_close':bars[-1]['close']}
    if len(SH)<2 or len(SL)<2: 
        # fallback no regime
        st=Bx.get('v3_state')
        return ('MACRO_BULL_LEG' if st=='BULL' else 'MACRO_BEAR_LEG' if st=='BEAR' else 'MACRO_TRANSITION'),f
    HH=SH[-1]>SH[-2];HL=SL[-1]>SL[-2]
    f.update({'daily_HH':HH,'daily_HL':HL,'last_daily_SH':round(SH[-1],1),'last_daily_SL':round(SL[-1],1)})
    cs=fn(Bx.get('combined_score'));wsl=fn(wk.get('slope_20_pct'))
    if HH and HL: return 'MACRO_BULL_LEG',f
    if (not HH) and (not HL):
        if cs is not None and cs>0: return 'MACRO_CORRECTIVE_PULLBACK',f  # daily LH/LL mas regime ainda bull = correção
        return 'MACRO_BEAR_LEG',f
    if HL and not HH: return 'MACRO_RANGE',f
    return 'MACRO_TRANSITION',f

# montar pacotes de evidência (cego ao outcome)
packs=[]
for p in sorted(SET,key=lambda x:(SET[x],x[0],int(x[1:]))):
    i=ep(p);P=pk[i];Q=dsq.get(i,{});R=v1[p];ed=P['datetime'][:10]
    leg,lf=macro_leg(ed,P['price'])
    pack=dict(plot_id=p,set=SET[p],datetime=ed,
        d1_macro_leg=leg, d1_evidence=lf,
        # camadas condicionais (ALIVE/SECOND_LAYER/RETEST)
        macro_v1_specialists={k:R[k] for k in('supply','demand','volume','mtf','regime','momentum','capit','fuel','risk')},
        sup_cat=Q.get('supply_category'),pol_cat=Q.get('polarity_category'),demand_cat=Q.get('demand_category'),
        svp={'below_VAL':P.get('below_VAL'),'dist_POC_atr':P.get('dist_POC_atr'),'dist_VAL_atr':P.get('dist_VAL_atr'),'va_width_atr':P.get('va_width_atr'),'rel_volume':P.get('rel_volume')},
        has_overhead=P.get('has_4h_supply_overhead'),dist_4h_supply=P.get('dist_4h_supply_low_atr'),supply_broken=P.get('supply_broken_before'),
        momentum={'trend_30_atr':P.get('trend_30_atr'),'rsi':P.get('rsi'),'rsi_1d':P.get('rsi_1d'),'legpos90':P.get('legpos90'),'rise20_atr':P.get('rise20_atr'),'bear_div':P.get('rsi_bear_div_20b')},
        capit={'drop20_atr':P.get('drop20_atr'),'rsi_min8':P.get('rsi_min8'),'sweet_spot':P.get('sweet_spot_falling_knife')},
        entry_quality={'dist_4h_demand':P.get('dist_4h_demand_low_atr'),'demand_touched':Q.get('demand_4h_touched_on_retest'),'reclaim_body':P.get('reclaim_body_atr')},
        risk_sl={'sl_atr':P.get('sl_atr'),'sl_type':P.get('sl_type')})
    packs.append(pack)
with open(f"{D}/l2_bpt_leg_state_d1_evidence_packs.jsonl","w") as f:
    for pk_ in packs: f.write(json.dumps(pk_,ensure_ascii=False)+"\n")
from collections import Counter
print(f"backbone D1 + packs: {len(packs)} trades")
print("d1_macro_leg:",dict(Counter(x['d1_macro_leg'] for x in packs)))
print("\nd1_macro_leg POR SET (A deve BULL/CORRECTIVE-pullback; B mix; bear-traps deve BEAR):")
for s in('A','B','C'):
    print(f"  {s}: {dict(Counter(x['d1_macro_leg'] for x in packs if x['set']==s))}")
# batches p/ agentes (4 batches ~15-16)
import math
nb=4;sz=math.ceil(len(packs)/nb)
for b in range(nb):
    sl=packs[b*sz:(b+1)*sz]
    if sl:
        with open(f"{D}/_leg_conf_batch{b}.jsonl","w") as f:
            for x in sl: f.write(json.dumps(x,ensure_ascii=False)+"\n")
        print(f"batch{b}: {len(sl)} trades")
