#!/usr/bin/env python3
"""MACRO STRUCTURAL READING ENGINE — 9 especialistas sobre os 62 (ENSINO/CALIBRAÇÃO). DIAGNÓSTICO.
Sem outcome como predicado. Sem engine/decisions/produção. Especialistas = leitores DETERMINÍSTICOS
auditáveis (feature values + reason codes + interpretação). Thresholds DECLARADOS, não tunados a IDs.
Causalidade: packet=close bar i; dsq categórico=range i-12..i; regime_B_v3=shift D-1; weekly=prev-week;
SVP=as-of-bar (validado 7f3c852, sem shift)."""
import json,csv,bisect,datetime as dt
RR="repro_recovery";D="results"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
mat={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
cris={r['plot_id']:r['cris_verdict'] for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0_cris_verdicts.csv"))}
def load_daily(p):
    rows=[json.loads(l) for l in open(p) if json.loads(l).get('ts')];rows.sort(key=lambda r:r['ts']);return rows
extB=load_daily("../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl")
extW=load_daily("../../../../strategies/candidates/regime_classifier_v3/xau_weekly_with_features.jsonl")
def clk(rows,ed):
    ds=[r['ts'] for r in rows];i=bisect.bisect_left(ds,ed)-1;return rows[i] if i>=0 else None
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

# THRESHOLDS DECLARADOS
MOM_TREND=1.5; MOM_RSI1D=53; LEGPOS_HIGH=85; RSI_OB=65; DROP_CAP=2.5; RSI_OS=35
def ev(name,state,conf,supports,conflicts,reasons,feats,interp,prov=True):
    return dict(specialist=name,state=state,confidence=conf,supports='|'.join(supports),conflicts='|'.join(conflicts),
                reason_codes='|'.join(reasons),feature_values=';'.join(f"{k}={v}" for k,v in feats.items()),
                market_interpretation=interp,provenance_ok=prov)

def spec_supply(P,Q,Bx):
    sc=Q.get('supply_category');pc=Q.get('polarity_category');dist=fn(P.get('dist_4h_supply_low_atr'));ovh=P.get('has_4h_supply_overhead')
    f={'supply_category':sc,'polarity_category':pc,'dist_4h_supply':dist,'has_overhead':ovh}
    if sc=='CLEAN_SKY': return ev('supply','CLEAN_SKY_BULLISH','high',['no_overhead'],[],['CLEAN_SKY'],f,"sem teto = markup/ATH bullish")
    if sc=='SUPPLY_NEAR_BUT_BROKEN': return ev('supply','MARKUP_BREAKING','high',['markup'],[],['SUPPLY_BROKEN'],f,"rompendo supply próxima = markup")
    if sc in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS'): return ev('supply','SUPPLY_REJECTING_RISK','high',[],['supply_rejecting'],[sc],f,"supply viva colada acima = risco")
    if sc=='SUPPLY_BLOCKS_TARGET': return ev('supply','SUPPLY_BLOCKS_TARGET','medium',[],['target_obstructed'],['BLOCKS_TARGET'],f,"supply bloqueia alvo = R ruim")
    if sc=='SUPPLY_FAR_ENOUGH': return ev('supply','SUPPLY_FAR_NEUTRAL','medium',['room'],[],['FAR_ENOUGH'],f,"supply longe = espaço ok")
    return ev('supply','SUPPLY_NEUTRAL','low',[],[],['neutral'],f,"sem leitura forte")

def spec_demand(P,Q):
    dc=Q.get('demand_category');dist=fn(P.get('dist_4h_demand_low_atr'));age=Q.get('demand_4h_age_bars');touched=Q.get('demand_4h_touched_on_retest')
    f={'demand_category':dc,'dist_4h_demand':dist,'touched_retest':touched}
    if dc in('DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG'): return ev('demand','DEMAND_DEFENDED','high',['demand_defended'],[],[dc],f,"demanda defendida real")
    if dc=='DEMAND_PRESENT_NEUTRAL': return ev('demand','DEMAND_NEUTRAL','medium',['demand_present'],[],['PRESENT_NEUTRAL'],f,"demanda presente neutra")
    if dc=='DEMAND_TOO_DEEP': return ev('demand','DEMAND_FRAGILE','medium',[],['demand_deep'],['TOO_DEEP'],f,"demanda muito funda = entrada esticada")
    return ev('demand','DEMAND_ABSENT','high',[],['no_demand_base'],['ABSENT'],f,"sem base de demanda = floating")

def spec_volume(P):
    bv=P.get('below_VAL');dpoc=fn(P.get('dist_POC_atr'));dval=fn(P.get('dist_VAL_atr'));vaw=fn(P.get('va_width_atr'));rv=fn(P.get('rel_volume'))
    f={'below_VAL':bv,'dist_POC':dpoc,'dist_VAL':dval,'va_width':vaw,'rel_volume':rv}
    mat_note='maturity:VP-as-of-bar'
    if bv is True or (dval is not None and dval<0): return ev('volume','REJECTION_BELOW_VALUE','medium',[],['below_value'],['BELOW_VAL',mat_note],f,"preço abaixo do VAL = rejeição/distribuição")
    if dpoc is not None and dpoc>0.3: return ev('volume','ACCEPTANCE_ABOVE_VALUE','medium',['acceptance_above'],[],['ABOVE_POC',mat_note],f,"aceitação acima do valor = bullish")
    if vaw is not None and rv is not None and rv>1.3 and vaw>1.5: return ev('volume','EXPANSION_CLIMAX','medium',['vol_expansion'],[],['EXPANSION',mat_note],f,"expansão de VA + volume alto = clímax/expansão")
    return ev('volume','IN_VALUE_BALANCE','low',[],[],['BALANCE',mat_note],f,"dentro do valor = balanço")

def spec_mtf(P,Bx,Wk):
    t30=fn(P.get('trend_30_atr'));rsi1d=fn(P.get('rsi_1d'));d_bull=Bx and Bx.get('d_break_bull');d_bear=Bx and Bx.get('d_break_bear')
    w_slope=fn(Wk.get('slope_20_pct')) if Wk else None;w_bull=Bx and Bx.get('w_break_bull');w_bear=Bx and Bx.get('w_break_bear')
    f={'trend_30_4h':t30,'rsi_1d':rsi1d,'d_break':('bull' if d_bull else 'bear' if d_bear else 'none'),'w_break':('bull' if w_bull else 'bear' if w_bear else 'none'),'weekly_slope':w_slope}
    bull=sum([t30 is not None and t30>0, rsi1d is not None and rsi1d>=MOM_RSI1D, bool(d_bull), (w_slope is not None and w_slope>0) or bool(w_bull)])
    bear=sum([bool(d_bear),bool(w_bear),t30 is not None and t30<-1.5])
    if bull>=3 and bear==0: return ev('mtf','FULL_BULL_ALIGN','high',['mtf_bull'],[],['4H+1D+W bull'],f,"alinhamento bull multi-TF = bull-run maior")
    if bear>=2: return ev('mtf','BEAR_ALIGN','high',[],['mtf_bear'],['d/w break bear'],f,"alinhamento bear = bounce local provável")
    if bull>=2: return ev('mtf','PARTIAL_BULL','medium',['partial_bull'],[],['parcial'],f,"alinhamento parcial bull")
    return ev('mtf','MTF_CONFLICT','low',[],['mtf_conflict'],['conflito'],f,"timeframes em conflito")

def spec_regime(Bx):
    if not Bx: return ev('regime','REGIME_UNKNOWN','low',[],['no_data'],['no_regime'],{},"sem regime D-1",False)
    cs=fn(Bx.get('combined_score'));casc=fn(Bx.get('cascade_score'));mb=Bx.get('macro_broken');dist=Bx.get('distribution_flag')
    stall=Bx.get('stall');sd=Bx.get('sharp_drop');da=Bx.get('dist_alarm');st=Bx.get('v3_state');dd=fn(Bx.get('drawdown_pct_13w'))
    f={'v3_state':st,'combined_score':cs,'cascade':casc,'macro_broken':mb,'distribution':dist,'stall':stall,'sharp_drop':sd,'dist_alarm':da,'dd13w':dd}
    if mb or dist: return ev('regime','MACRO_BROKEN_DISTRIBUTION','high',[],['macro_broken'],['MACRO_BROKEN' if mb else 'DISTRIBUTION'],f,"macro quebrado/distribuição = topo macro")
    if casc is not None and casc<=-2 and (Bx.get('d_break_bear') or Bx.get('w_break_bear')): return ev('regime','CASCADE_DECLINE','high',[],['cascade'],['CASCADE'],f,"cascade de quebras = markdown")
    if cs is not None and cs>0 and not mb: return ev('regime','MACRO_BULL','high',['macro_bull'],[],['combined>0'],f,"regime macro bull")
    if stall or da or sd: return ev('regime','MACRO_TRANSITION_RISK','medium',[],['transition'],['STALL/ALARM'],f,"transição/alerta macro")
    return ev('regime','MACRO_NEUTRAL','low',[],[],['neutral'],f,"regime neutro/transição")

def spec_momentum(P):
    t30=fn(P.get('trend_30_atr'));rsi=fn(P.get('rsi'));rsi1d=fn(P.get('rsi_1d'));lp=fn(P.get('legpos90'));rise=fn(P.get('rise20_atr'));bdiv=fn(P.get('rsi_bear_div_20b'))
    mom_strong=(t30 is not None and t30>=MOM_TREND) or (rsi1d is not None and rsi1d>=MOM_RSI1D)
    f={'trend_30':t30,'rsi':rsi,'rsi_1d':rsi1d,'legpos90':lp,'rise20':rise,'bear_div':bdiv}
    if lp is not None and lp>=LEGPOS_HIGH and not mom_strong and (rsi is not None and rsi>=RSI_OB): return ev('momentum','LATE_TOP_EXHAUSTION','high',[],['exhaustion'],['legpos_high+weak+OB'],f,"legpos alto + momentum fraco + OB = exaustão de topo")
    if mom_strong and lp is not None and lp>=LEGPOS_HIGH: return ev('momentum','HEALTHY_HIGH_LEGPOS','high',['strong_bull'],[],['legpos_high+momentum'],f,"legpos alto COM momentum = continuação sadia")
    if mom_strong: return ev('momentum','STRONG_BULL_MOMENTUM','high',['strong_bull'],[],['momentum_strong'],f,"momentum bull forte")
    return ev('momentum','WEAK_MOMENTUM','medium',[],['weak'],['momentum_weak'],f,"momentum fraco = bounce/indeciso")

def spec_capit(P):
    drop=fn(P.get('drop20_atr'));rmin=fn(P.get('rsi_min8'));sweet=P.get('sweet_spot_falling_knife');bsell=fn(P.get('bub_sell_total'));recl=fn(P.get('reclaim_body_atr'))
    f={'drop20':drop,'rsi_min8':rmin,'sweet_spot':sweet,'bub_sell':bsell,'reclaim_body':recl}
    if drop is not None and drop>=DROP_CAP and rmin is not None and rmin<=RSI_OS and recl is not None and recl>0: return ev('capit','CLIMAX_RECLAIM','high',['climax_reclaim'],[],['drop+oversold+reclaim'],f,"drop forte + oversold + reclaim = clímax/fundo")
    if drop is not None and drop>=DROP_CAP and (recl is None or recl<=0): return ev('capit','FALLING_KNIFE','high',[],['knife'],['drop_no_reclaim'],f,"drop forte sem reclaim = faca caindo")
    return ev('capit','NO_CAPITULATION','low',[],[],['no_cap'],f,"sem capitulação relevante")

def spec_fuel(P,Q):
    sc=Q.get('supply_category');dsup=fn(P.get('dist_4h_supply_low_atr'));dd1=P.get('dist_d1_supply_atr');blocks=Q.get('supply_4h_blocks_target_2ATR')
    f={'supply_category':sc,'dist_4h_supply':dsup,'dist_d1_supply':dd1,'blocks_target':blocks}
    if sc=='CLEAN_SKY' or P.get('has_4h_supply_overhead')=='0' or not dd1: return ev('fuel','high_fuel','high',['clean_sky'],[],['no_overhead'],f,"sem teto = combustível alto")
    if sc=='SUPPLY_BLOCKS_TARGET' or (dsup is not None and dsup<1.5): return ev('fuel','low_fuel','high',[],['obstructed'],['blocks/colada'],f,"supply colada/bloqueia = combustível baixo")
    if dsup is not None and dsup>=3: return ev('fuel','high_fuel','medium',['room'],[],['far_supply'],f,"supply longe = combustível alto")
    return ev('fuel','medium_fuel','medium',[],[],['moderate'],f,"combustível médio")

def spec_risk(P):
    sla=fn(P.get('sl_atr'));slt=P.get('sl_type')
    f={'sl_atr':sla,'sl_type':slt}
    if sla is None: return ev('risk','SL_UNKNOWN','low',[],['no_sl'],['no_sl'],f,"sem SL",False)
    if sla<1.2: return ev('risk','SL_TOO_SHORT','high',[],['sl_short'],['sl<1.2ATR'],f,"SL curto demais = stop no ruído (ex T34)")
    if sla>5: return ev('risk','SL_TOO_WIDE','medium',[],['sl_wide'],['sl>5ATR'],f,"SL largo = R ruim")
    if slt in('NORMAL_DEMAND_BASE','DEMAND_BASE'): return ev('risk','SL_STRUCTURAL_OK','high',['sl_ok'],[],['demand_base'],f,"SL estrutural na demanda = ok")
    return ev('risk','SL_NEUTRAL','medium',[],[],['neutral'],f,"SL aceitável")

SPECS=[spec_supply,spec_demand,spec_volume,spec_mtf,spec_regime,spec_momentum,spec_capit,spec_fuel,spec_risk]

# ---- CONFLUÊNCIA (interpretável, não voto cego) ----
def confluence(reads):
    R={r['specialist']:r for r in reads}
    sup=R['supply']['state'];dem=R['demand']['state'];vol=R['volume']['state'];mtf=R['mtf']['state']
    reg=R['regime']['state'];mom=R['momentum']['state'];cap=R['capit']['state'];fuel=R['fuel']['state'];risk=R['risk']['state']
    bull_macro = reg in('MACRO_BULL',) or mtf in('FULL_BULL_ALIGN','PARTIAL_BULL')
    bear_macro = reg in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or mtf=='BEAR_ALIGN'
    rc=[]
    # FATAIS de topo/bear primeiro
    if mom=='LATE_TOP_EXHAUSTION' and sup in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'):
        return 'LATE_TOP_EXHAUSTION','high',['late_top']
    if bear_macro and sup in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET') and mom=='WEAK_MOMENTUM':
        return 'BEAR_BOUNCE_RISK','high',['bear+supply+weak']
    if bear_macro and mom=='WEAK_MOMENTUM':
        return 'CORRECTIVE_BEAR_LEG','medium',['bear_corrective']
    if sup=='SUPPLY_REJECTING_RISK' and mom=='WEAK_MOMENTUM' and not bull_macro:
        return 'SUPPLY_COLADA_REJECTION','high',['supply_colada']
    # CAPITULAÇÃO/fundo
    if cap=='CLIMAX_RECLAIM' and dem in('DEMAND_DEFENDED','DEMAND_NEUTRAL'):
        return 'CAPITULATION_RECLAIM_VALID','high',['climax_reclaim']
    if cap=='CLIMAX_RECLAIM':
        return 'BOTTOM_REVERSAL_VALID','medium',['bottom']
    if cap=='FALLING_KNIFE':
        return 'CORRECTIVE_BEAR_LEG','medium',['falling_knife']
    # BULL families
    if sup=='CLEAN_SKY_BULLISH' and mom in('STRONG_BULL_MOMENTUM','HEALTHY_HIGH_LEGPOS'):
        return 'NO_OVERHEAD_MARKUP','high',['clean_sky+momentum']
    if bull_macro and mtf=='FULL_BULL_ALIGN' and mom in('STRONG_BULL_MOMENTUM','HEALTHY_HIGH_LEGPOS') and sup not in('SUPPLY_REJECTING_RISK',):
        return 'MACRO_BULL_RUN_CONTINUATION','high',['full_bull']
    if bull_macro and dem=='DEMAND_DEFENDED' and sup not in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'):
        return 'BULL_PULLBACK_CONTINUATION','high',['bull+demand']
    if bull_macro and vol=='ACCEPTANCE_ABOVE_VALUE':
        return 'RANGE_MACRO_BULL_RECLAIM','medium',['bull+acceptance']
    if bull_macro:
        return 'BULL_PULLBACK_CONTINUATION','medium',['bull_macro_default']
    # resto
    if reg in('MACRO_NEUTRAL','MACRO_TRANSITION_RISK') and mom=='WEAK_MOMENTUM':
        return 'MID_RANGE_NOISE','low',['mid_range']
    return 'UNKNOWN_CONFLICT','low',['conflict']

# ---- RODAR ----
ev_rows=[];conf_rows=[]
BULL_FAM={'MACRO_BULL_RUN_CONTINUATION','BULL_PULLBACK_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','BOTTOM_REVERSAL_VALID','CAPITULATION_RECLAIM_VALID','NO_OVERHEAD_MARKUP'}
RISK_FAM={'BEAR_BOUNCE_RISK','CORRECTIVE_BEAR_LEG','LATE_TOP_EXHAUSTION','SUPPLY_COLADA_REJECTION'}
for p in sorted(SET,key=lambda x:(SET[x],x[0],int(x[1:]))):
    e=ep(p);P=pk[e];Q=dsq.get(e,{});ed=P['datetime'][:10]
    Bx=clk(extB,ed);Wk=clk(extW,ed)
    reads=[]
    for fnsp in SPECS:
        try:
            r=fnsp(P,Q,Bx) if fnsp==spec_supply else (fnsp(P,Bx,Wk) if fnsp==spec_mtf else (fnsp(Bx) if fnsp==spec_regime else (fnsp(P,Q) if fnsp in(spec_demand,spec_fuel) else fnsp(P))))
        except TypeError:
            r=fnsp(P)
        reads.append(r);r2=dict(r);r2['plot_id']=p;r2['set']=SET[p];ev_rows.append(r2)
    state,conf,rc=confluence(reads)
    fam='BULL' if state in BULL_FAM else ('RISK' if state in RISK_FAM else 'NEUTRO')
    conf_rows.append(dict(plot_id=p,set=SET[p],datetime=ed,macro_state=state,family=fam,confidence=conf,reason=' '.join(rc),
        supply=reads[0]['state'],demand=reads[1]['state'],volume=reads[2]['state'],mtf=reads[3]['state'],regime=reads[4]['state'],
        momentum=reads[5]['state'],capit=reads[6]['state'],fuel=reads[7]['state'],risk=reads[8]['state'],final_verdict=final(p)))
# outputs
ec=['plot_id','set','specialist','state','confidence','supports','conflicts','reason_codes','feature_values','market_interpretation','provenance_ok']
with open(f"{D}/l2_bpt_macro_specialist_evidence_62.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=ec,extrasaction='ignore');w.writeheader();w.writerows(ev_rows)
cc=['plot_id','set','datetime','macro_state','family','confidence','reason','supply','demand','volume','mtf','regime','momentum','capit','fuel','risk','final_verdict']
with open(f"{D}/l2_bpt_macro_specialist_confluence_62.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cc);w.writeheader();w.writerows(conf_rows)
from collections import Counter
print(f"processados: {len(conf_rows)} trades (A{len(A)} B{len(B)} C{len(Cset)})")
print(f"evidências: {len(ev_rows)} (9 x {len(conf_rows)})")
print("\nestados finais:",dict(Counter(r['macro_state'] for r in conf_rows)))
print("família:",dict(Counter(r['family'] for r in conf_rows)))
print("\nfamília POR SET (A=bull-cortado deve dar BULL; B=bear-aceito deve dar RISK):")
for s in('A','B','C'):
    fams=Counter(r['family'] for r in conf_rows if r['set']==s);print(f"  {s}: {dict(fams)}")
