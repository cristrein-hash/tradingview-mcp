#!/usr/bin/env python3
"""FULL 276 — Macro Reader + Bear-Leg Block v3 aplicado à POPULAÇÃO completa, cronológico, DIAGNÓSTICO.
Reproduz fielmente: macro_leg() (leg_state_d1_backbone), spec_capit/spec_demand (macro_structural_specialists),
gate v3 (bear_leg_block_gate_v3). Causal: daily/weekly/regimeB shift D-1; features as-of-bar.
outcome/realR APENAS para avaliação (nunca predicado). Sem produção, sem 276/OOS extra, sem SLIM."""
import json, csv, bisect
from collections import Counter

RC = "../../../../strategies/candidates/regime_classifier_v3"
RR = "repro_recovery"; D = "results"
def load(p): rows=[json.loads(l) for l in open(p) if json.loads(l).get('ts')]; rows.sort(key=lambda r:r['ts']); return rows
daily=load(f"{RC}/xau_daily_with_features.jsonl")
weekly=load(f"{RC}/xau_weekly_with_features.jsonl")
extB=load(f"{RC}/regime_B_v3_classifications.jsonl")
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
outc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
tqm={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_matrix.csv"))}

def fn(v):
    try: return float(v)
    except: return None
DROP_CAP=2.5; RSI_OS=35; CP_DROP_MIN=1.0

# ---- macro_leg (backbone, shift D-1) ----
dts=[r['ts'] for r in daily]; wts=[r['ts'] for r in weekly]; bts=[r['ts'] for r in extB]
def daily_before(ed): i=bisect.bisect_left(dts,ed); return daily[:i]
def dfractals(bars,k=3,lookback=120):
    Hd=[b['high'] for b in bars];Ld=[b['low'] for b in bars];n=len(bars);SH=[];SL=[]
    for p in range(max(k,n-lookback),n-k):
        if all(Hd[p]>Hd[j] for j in range(p-k,p)) and all(Hd[p]>=Hd[j] for j in range(p+1,p+k+1)): SH.append(Hd[p])
        if all(Ld[p]<Ld[j] for j in range(p-k,p)) and all(Ld[p]<=Ld[j] for j in range(p+1,p+k+1)): SL.append(Ld[p])
    return SH,SL
def macro_leg(ed):
    bars=daily_before(ed)
    if len(bars)<30: return 'UNKNOWN',{'n_daily':len(bars)}
    SH,SL=dfractals(bars)
    Bx=extB[bisect.bisect_left(bts,ed)-1] if extB else {}
    wk=weekly[bisect.bisect_left(wts,ed)-1] if weekly else {}
    f={'n_SH':len(SH),'n_SL':len(SL),'regimeB_state':Bx.get('v3_state'),'regimeB_combined':Bx.get('combined_score'),
       'macro_broken':Bx.get('macro_broken'),'weekly_slope':wk.get('slope_20_pct'),'weekly_rsi':wk.get('rsi_14')}
    if len(SH)<2 or len(SL)<2:
        st=Bx.get('v3_state'); return ('MACRO_BULL_LEG' if st=='BULL' else 'MACRO_BEAR_LEG' if st=='BEAR' else 'MACRO_TRANSITION'),f
    HH=SH[-1]>SH[-2];HL=SL[-1]>SL[-2]; f.update({'daily_HH':HH,'daily_HL':HL})
    cs=fn(Bx.get('combined_score'))
    if HH and HL: return 'MACRO_BULL_LEG',f
    if (not HH) and (not HL):
        if cs is not None and cs>0: return 'MACRO_CORRECTIVE_PULLBACK',f
        return 'MACRO_BEAR_LEG',f
    if HL and not HH: return 'MACRO_RANGE',f
    return 'MACRO_TRANSITION',f

# ---- specialists determinísticos ----
def spec_capit(P):
    drop=fn(P.get('drop20_atr'));rmin=fn(P.get('rsi_min8'));recl=fn(P.get('reclaim_body_atr'))
    if drop is not None and drop>=DROP_CAP and rmin is not None and rmin<=RSI_OS and recl is not None and recl>0: return 'CLIMAX_RECLAIM'
    if drop is not None and drop>=DROP_CAP and (recl is None or recl<=0): return 'FALLING_KNIFE'
    return 'NO_CAPITULATION'
def spec_demand(Q):
    dc=Q.get('demand_category')
    if dc in('DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG'): return 'DEMAND_DEFENDED'
    if dc=='DEMAND_PRESENT_NEUTRAL': return 'DEMAND_NEUTRAL'
    if dc=='DEMAND_TOO_DEEP': return 'DEMAND_FRAGILE'
    return 'DEMAND_ABSENT'

# ---- gate v3 (idêntico a bear_leg_block_gate_v3) ----
def gate(leg,d1,P,Q):
    mb=d1.get('macro_broken') in (True,'true','True','1',1); cs=fn(d1.get('regimeB_combined')); wsl=fn(d1.get('weekly_slope'))
    climax=(spec_capit(P)=='CLIMAX_RECLAIM'); rmin=fn(P.get('rsi_min8')); recl=fn(P.get('reclaim_body_atr')); dem=spec_demand(Q)
    drop=fn(P.get('drop20_atr')); rc=[]
    bt = climax or (rmin is not None and rmin<=32 and recl is not None and recl>=0.4 and dem=='DEMAND_DEFENDED')
    if bt and leg!='MACRO_BULL_LEG':
        rc.append('bottom_turn_climax' if climax else 'bottom_turn_oversold_reclaim_demand')
        return 'PRESERVE_BOTTOM_TURN',rc,bt
    if leg=='MACRO_BEAR_LEG' or (mb and cs is not None and cs<0):
        rc.append(f'bear_markdown(leg={leg},mb={mb},cs={cs})'); return 'BLOCK_BEAR_MARKDOWN',rc,bt
    if leg in('MACRO_RANGE','MACRO_TRANSITION') and not (cs is not None and cs>0) and not (wsl is not None and wsl>0):
        rc.append(f'range_chop(leg={leg},cs={cs},wsl={wsl})'); return 'BLOCK_RANGE_CHOP',rc,bt
    if leg=='MACRO_CORRECTIVE_PULLBACK' and not bt and drop is not None and drop<CP_DROP_MIN:
        rc.append(f'corrective_shallow(drop={drop}<{CP_DROP_MIN})'); return 'BLOCK_CORRECTIVE_PULLBACK',rc,bt
    rc.append(f'allow(leg={leg})'); return 'ALLOW',rc,bt

# ---- aplicar a 276, cronológico ----
order=sorted(pk.keys(), key=lambda b: pk[b]['ts'])
rows=[]
for b in order:
    P=pk[b]; Q=dsq.get(b,{}); ed=P['datetime'][:10]
    leg,d1=macro_leg(ed)
    dec,rc,bt=gate(leg,d1,P,Q)
    o=outc.get(b,{})
    sc=Q.get('supply_category')
    clean_sky = (P.get('supply_blocks_2ATR') in('0','0.0',0) ) or (sc in('CLEAN_SKY','SUPPLY_FAR_ENOUGH'))
    micro_resid = (dec=='ALLOW' and leg in('MACRO_BULL_LEG','MACRO_RANGE') and clean_sky)
    rows.append(dict(bar_idx=b, datetime=P['datetime'], decision=dec, blocked=('YES' if dec.startswith('BLOCK') else 'NO'),
        block_reason=(dec if dec.startswith('BLOCK') else ''), macro_reader_leg=leg,
        d1_regimeB=d1.get('regimeB_state'), d1_combined=d1.get('regimeB_combined'), macro_broken=d1.get('macro_broken'),
        weekly_slope=d1.get('weekly_slope'), bottom_turn=bt, clean_sky_flag=clean_sky, micro_residual_flag=micro_resid,
        sup_cat=sc, capit=spec_capit(P), demand=spec_demand(Q), drop20_atr=fn(P.get('drop20_atr')),
        reason_codes='|'.join(rc),
        # EVAL only (não predicado)
        realR=fn(o.get('realR')), exitype=o.get('exitype'), is_winner_gt=o.get('is_winner_gt')))
with open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)

# ---- population audit ----
dts2=[r['datetime'] for r in rows]
aud=[("n",len(rows)),("date_min",min(dts2)),("date_max",max(dts2)),
     ("ts_sorted","YES" if all(pk[order[i]]['ts']<=pk[order[i+1]]['ts'] for i in range(len(order)-1)) else "NO"),
     ("dup_bar_idx",len(order)-len(set(order))),
     ("realR_coverage",f"{sum(1 for r in rows if r['realR'] is not None)}/{len(rows)}"),
     ("leg_UNKNOWN",sum(1 for r in rows if r['macro_reader_leg']=='UNKNOWN'))]
with open(f"{D}/l2_bpt_full276_population_audit.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(["check","value"]);[w.writerow(r) for r in aud]

print("=== POPULATION AUDIT ===");[print(f"  {k}: {v}") for k,v in aud]
print("\n=== leg distribution (276) ===",dict(Counter(r['macro_reader_leg'] for r in rows)))
print("=== gate decisions (276) ===",dict(Counter(r['decision'] for r in rows)))
nb=sum(1 for r in rows if r['blocked']=='YES'); na=len(rows)-nb
print(f"\nALLOW={na}  BLOCK={nb}")
print("blocks por reason:",dict(Counter(r['block_reason'] for r in rows if r['blocked']=='YES')))
