#!/usr/bin/env python3
"""FULL 276 — MACRO STRUCTURAL READING ENGINE (9 especialistas REAIS) — rerun completo (canon efaf48a).
Porta o engine `macro_structural_specialists.py` (verbatim) da amostra 62 para a POPULAÇÃO 276.
DIAGNÓSTICO. Sem produção, sem promoção, sem OOS, sem chart/SLIM. outcome só na avaliação (realR CAPADO +3.9R
= hit-rate, NÃO expectancy; classificar por TIPO DE SAÍDA).

Policy derivada da CONFLUÊNCIA multifatorial (9 especialistas), NÃO de feature isolada. macro_phase entra
SÓ como evidência condicional fraca (coluna anotada + termo testável em ablation), NUNCA gate/autoridade.
Camadas cruzadas com status [[feedback_prior_layers_conditional_evidence]].
Validações: ablation (drop-1-specialist), null/permutation (1000x), jackknife (leave-1-year-out), sub-janelas, drought-17.
Reprodutível: este script é salvo e commitado."""
import json, csv, bisect, random
D = "results"
RR = "repro_recovery"

# ---------- INPUTS (276) ----------
pk  = {int(json.loads(l)['bar_idx']): json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
dsq = {int(r['candidate_id'][1:]): r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
outc= {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
mph = {int(r['episode_id']): r['macro_phase_causal'] for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_phase_causal_candidate.csv"))}
bear= {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
# visual-anchored reading (keyed by episode_id == bar_idx number)
va  = {int(r['episode_id']): r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_visual_anchored_reading.csv"))}

def load_daily(p):
    rows=[json.loads(l) for l in open(p) if json.loads(l).get('ts')]; rows.sort(key=lambda r:r['ts']); return rows
extB=load_daily("../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl")
extW=load_daily("../../../../strategies/candidates/regime_classifier_v3/xau_weekly_with_features.jsonl")
def clk(rows,ed):
    ds=[r['ts'] for r in rows]; i=bisect.bisect_left(ds,ed)-1; return rows[i] if i>=0 else None
def fn(v):
    try: return float(v)
    except: return None

# ---------- THRESHOLDS DECLARADOS (verbatim do engine 62) ----------
MOM_TREND=1.5; MOM_RSI1D=53; LEGPOS_HIGH=85; RSI_OB=65; DROP_CAP=2.5; RSI_OS=35
def ev(name,state,conf,supports,conflicts,reasons,feats,interp,prov=True):
    return dict(specialist=name,state=state,confidence=conf,supports='|'.join(supports),conflicts='|'.join(conflicts),
                reason_codes='|'.join(reasons),feature_values=';'.join(f"{k}={v}" for k,v in feats.items()),
                market_interpretation=interp,provenance_ok=prov)

# ---------- 9 ESPECIALISTAS (verbatim) ----------
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
    if bv is True or bv=='True' or (dval is not None and dval<0): return ev('volume','REJECTION_BELOW_VALUE','medium',[],['below_value'],['BELOW_VAL',mat_note],f,"preço abaixo do VAL = rejeição/distribuição")
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

# ---------- CONFLUÊNCIA (verbatim) ----------
def confluence(reads):
    R={r['specialist']:r for r in reads}
    sup=R['supply']['state'];dem=R['demand']['state'];vol=R['volume']['state'];mtf=R['mtf']['state']
    reg=R['regime']['state'];mom=R['momentum']['state'];cap=R['capit']['state'];fuel=R['fuel']['state'];risk=R['risk']['state']
    bull_macro = reg in('MACRO_BULL',) or mtf in('FULL_BULL_ALIGN','PARTIAL_BULL')
    bear_macro = reg in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or mtf=='BEAR_ALIGN'
    if mom=='LATE_TOP_EXHAUSTION' and sup in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'):
        return 'LATE_TOP_EXHAUSTION','high',['late_top']
    if bear_macro and sup in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET') and mom=='WEAK_MOMENTUM':
        return 'BEAR_BOUNCE_RISK','high',['bear+supply+weak']
    if bear_macro and mom=='WEAK_MOMENTUM':
        return 'CORRECTIVE_BEAR_LEG','medium',['bear_corrective']
    if sup=='SUPPLY_REJECTING_RISK' and mom=='WEAK_MOMENTUM' and not bull_macro:
        return 'SUPPLY_COLADA_REJECTION','high',['supply_colada']
    if cap=='CLIMAX_RECLAIM' and dem in('DEMAND_DEFENDED','DEMAND_NEUTRAL'):
        return 'CAPITULATION_RECLAIM_VALID','high',['climax_reclaim']
    if cap=='CLIMAX_RECLAIM':
        return 'BOTTOM_REVERSAL_VALID','medium',['bottom']
    if cap=='FALLING_KNIFE':
        return 'CORRECTIVE_BEAR_LEG','medium',['falling_knife']
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
    if reg in('MACRO_NEUTRAL','MACRO_TRANSITION_RISK') and mom=='WEAK_MOMENTUM':
        return 'MID_RANGE_NOISE','low',['mid_range']
    return 'UNKNOWN_CONFLICT','low',['conflict']

BULL_FAM={'MACRO_BULL_RUN_CONTINUATION','BULL_PULLBACK_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','BOTTOM_REVERSAL_VALID','CAPITULATION_RECLAIM_VALID','NO_OVERHEAD_MARKUP'}
RISK_FAM={'BEAR_BOUNCE_RISK','CORRECTIVE_BEAR_LEG','LATE_TOP_EXHAUSTION','SUPPLY_COLADA_REJECTION'}

def run_specs(b, drop=None):
    """retorna lista de 9 reads; drop=nome do especialista a neutralizar (ablation)."""
    P=pk[b]; Q=dsq.get(b,{}); ed=P['datetime'][:10]; Bx=clk(extB,ed); Wk=clk(extW,ed)
    raw=[spec_supply(P,Q,Bx),spec_demand(P,Q),spec_volume(P),spec_mtf(P,Bx,Wk),spec_regime(Bx),
         spec_momentum(P),spec_capit(P),spec_fuel(P,Q),spec_risk(P)]
    if drop:
        NEUTRAL={'supply':'SUPPLY_NEUTRAL','demand':'DEMAND_NEUTRAL','volume':'IN_VALUE_BALANCE','mtf':'MTF_CONFLICT',
                 'regime':'MACRO_NEUTRAL','momentum':'STRONG_BULL_MOMENTUM','capit':'NO_CAPITULATION','fuel':'medium_fuel','risk':'SL_NEUTRAL'}
        for r in raw:
            if r['specialist']==drop: r['state']=NEUTRAL[drop]
    return raw

def decide(b, drop=None):
    reads=run_specs(b,drop)
    state,conf,rc=confluence(reads)
    fam='BULL' if state in BULL_FAM else ('RISK' if state in RISK_FAM else 'NEUTRO')
    risk=[r for r in reads if r['specialist']=='risk'][0]['state']
    if fam=='RISK': pol='SKIP'
    elif fam=='BULL': pol='REVIEW_RISK' if risk in('SL_TOO_SHORT','SL_TOO_WIDE') else 'TAKE'
    else: pol='REVIEW'
    return state,fam,conf,pol,reads

# ---------- EVAL (por tipo de saída; realR CAPADO) ----------
WIN={'WIN_HELD','WIN_RUNNER'}
def metrics(bidxs):
    rows=sorted(bidxs,key=lambda b:pk[b]['datetime'])
    n=len(rows)
    if n==0: return dict(n=0,WR=0,PF=0,sumR=0,maxDD=0,Lstreak=0,runners=0,big=0,wins=0,be=0,stop=0,scratch=0)
    wins=sum(1 for b in rows if outc[b]['exitype'] in WIN)
    runners=sum(1 for b in rows if outc[b]['exitype']=='WIN_RUNNER')
    be=sum(1 for b in rows if outc[b]['exitype']=='WIN_BE'); stop=sum(1 for b in rows if outc[b]['exitype']=='STOP_LOSS')
    scratch=sum(1 for b in rows if outc[b]['exitype']=='SCRATCH')
    rs=[fn(outc[b]['realR']) or 0 for b in rows]
    pos=sum(r for r in rs if r>0); neg=sum(r for r in rs if r<0)
    PF=round(pos/abs(neg),2) if neg<0 else 999
    cum=0;peak=0;mdd=0
    for r in rs:
        cum+=r;peak=max(peak,cum);mdd=max(mdd,peak-cum)
    ls=0;best=0
    for b in rows:
        if outc[b]['exitype'] in WIN: ls=0
        else: ls+=1; best=max(best,ls)
    return dict(n=n,WR=round(100*wins/n,1),PF=PF,sumR=round(sum(rs),1),maxDD=round(mdd,1),Lstreak=best,
                runners=runners,big=wins,be=be,stop=stop,scratch=scratch)

ALL=sorted(pk.keys(),key=lambda b:pk[b]['datetime'])
TOTAL_RUNNERS=sum(1 for b in ALL if outc[b]['exitype']=='WIN_RUNNER')
TOTAL_BIG=sum(1 for b in ALL if outc[b]['exitype'] in WIN)

# ---------- RODAR ENGINE NOS 276 ----------
dec={}; ev_rows=[]; conf_rows=[]
for b in ALL:
    state,fam,conf,pol,reads=decide(b)
    dec[b]=(state,fam,conf,pol)
    for r in reads:
        r2=dict(r); r2['bar_idx']=b; ev_rows.append(r2)
    o=outc[b]
    conf_rows.append(dict(bar_idx=b,datetime=pk[b]['datetime'][:10],macro_state=state,family=fam,confidence=conf,policy=pol,
        supply=reads[0]['state'],demand=reads[1]['state'],volume=reads[2]['state'],mtf=reads[3]['state'],regime=reads[4]['state'],
        momentum=reads[5]['state'],capit=reads[6]['state'],fuel=reads[7]['state'],risk=reads[8]['state'],
        macro_phase_weak_evidence=mph.get(b,'?'), va_policy=va.get(b,{}).get('final_policy','?'),
        bear_v3=('BLOCK' if bear.get(b,{}).get('blocked')=='True' else 'ALLOW'),
        EVAL_exitype=o['exitype'], EVAL_realR=o['realR']))
ec=['bar_idx','specialist','state','confidence','supports','conflicts','reason_codes','feature_values','market_interpretation','provenance_ok']
with open(f"{D}/l2_bpt_full276_macro_engine_specialist_evidence.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=ec,extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(ev_rows)
cc=list(conf_rows[0].keys())
with open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cc,lineterminator="\n");w.writeheader();w.writerows(conf_rows)

from collections import Counter
TAKE=[b for b in ALL if dec[b][3]=='TAKE']
SKIP=[b for b in ALL if dec[b][3]=='SKIP']
REVIEW=[b for b in ALL if dec[b][3]=='REVIEW']
RREV=[b for b in ALL if dec[b][3]=='REVIEW_RISK']
print("="*70)
print("FULL 276 MACRO ENGINE — 9 especialistas REAIS")
print("policy dist:",dict(Counter(dec[b][3] for b in ALL)))
print("macro_state dist:",dict(Counter(dec[b][0] for b in ALL)))
print("family dist:",dict(Counter(dec[b][1] for b in ALL)))
print(f"\npopulação: {len(ALL)} | total runners={TOTAL_RUNNERS} | total big winners={TOTAL_BIG}")

# ---------- POLICY EVAL + COMPARAÇÃO ----------
bear_allow=[b for b in ALL if bear.get(b,{}).get('blocked')!='True']
va_take=[b for b in ALL if va.get(b,{}).get('final_policy')=='TAKE_CANDIDATE']
buckets={'ENGINE_TAKE':TAKE,'ENGINE_SKIP':SKIP,'ENGINE_REVIEW':REVIEW,'ENGINE_REVIEW_RISK':RREV,
         'BASELINE_no_gate':ALL,'BEAR_V3_allow':bear_allow,'VISUAL_ANCHORED_take':va_take}
comp_rows=[]
print("\n--- BUCKET METRICS (realR CAPADO = hit-rate) ---")
print(f"{'bucket':24} {'n':>4} {'WR':>6} {'PF':>6} {'sumR':>7} {'DD':>6} {'Lstk':>5} {'run':>4} {'big':>4}")
for name,bs in buckets.items():
    m=metrics(bs); m['bucket']=name; m['runners_pct']=f"{m['runners']}/{TOTAL_RUNNERS}"; m['big_pct']=f"{m['big']}/{TOTAL_BIG}"
    comp_rows.append(m)
    print(f"{name:24} {m['n']:>4} {m['WR']:>6} {m['PF']:>6} {m['sumR']:>7} {m['maxDD']:>6} {m['Lstreak']:>5} {m['runners']:>4} {m['big']:>4}")
with open(f"{D}/l2_bpt_full276_macro_engine_policy_eval.csv","w",newline="") as f:
    cols=['bucket','n','WR','PF','sumR','maxDD','Lstreak','runners','runners_pct','big','big_pct','be','stop','scratch']
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(comp_rows)

# ---------- ABLATION (drop-1-specialist) ----------
print("\n--- ABLATION: TAKE bucket ao neutralizar cada especialista ---")
abl_rows=[]
base_m=metrics(TAKE)
abl_rows.append(dict(dropped='NONE(base)',**{k:base_m[k] for k in('n','WR','PF','sumR','runners','big','Lstreak')}))
print(f"{'dropped':14} {'n':>4} {'WR':>6} {'PF':>6} {'run':>4} {'big':>4} {'Lstk':>5}  Δn/ΔWR vs base")
print(f"{'NONE(base)':14} {base_m['n']:>4} {base_m['WR']:>6} {base_m['PF']:>6} {base_m['runners']:>4} {base_m['big']:>4} {base_m['Lstreak']:>5}")
for sp in ['supply','demand','volume','mtf','regime','momentum','capit','fuel','risk']:
    tk=[b for b in ALL if decide(b,drop=sp)[3]=='TAKE']
    m=metrics(tk)
    abl_rows.append(dict(dropped=sp,**{k:m[k] for k in('n','WR','PF','sumR','runners','big','Lstreak')}))
    print(f"{sp:14} {m['n']:>4} {m['WR']:>6} {m['PF']:>6} {m['runners']:>4} {m['big']:>4} {m['Lstreak']:>5}  Δn={m['n']-base_m['n']:+d} ΔWR={m['WR']-base_m['WR']:+.1f}")
with open(f"{D}/l2_bpt_full276_macro_engine_ablation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['dropped','n','WR','PF','sumR','runners','big','Lstreak'],lineterminator="\n");w.writeheader();w.writerows(abl_rows)

# ---------- NULL / PERMUTATION (TAKE WR vs outcome shuffle) ----------
rng=random.Random(42)
obs=metrics(TAKE); obs_wr=obs['WR']; obs_pf=obs['PF']
exitypes=[outc[b]['exitype'] for b in ALL]; realRs=[fn(outc[b]['realR']) or 0 for b in ALL]
take_n=len(TAKE)
ge_wr=0; ge_pf=0; N=2000
for _ in range(N):
    idx=list(range(len(ALL))); rng.shuffle(idx)
    sample=idx[:take_n]
    wins=sum(1 for i in sample if exitypes[i] in WIN)
    rs=[realRs[i] for i in sample]; pos=sum(r for r in rs if r>0); neg=sum(r for r in rs if r<0)
    wr=100*wins/take_n; pf=pos/abs(neg) if neg<0 else 999
    if wr>=obs_wr: ge_wr+=1
    if pf>=obs_pf: ge_pf+=1
p_wr=ge_wr/N; p_pf=ge_pf/N
print(f"\n--- NULL/PERMUTATION (N={N}, random subsets size {take_n}) ---")
print(f"observed TAKE WR={obs_wr}% PF={obs_pf} | p(WR>=obs)={p_wr:.3f} p(PF>=obs)={p_pf:.3f}")
with open(f"{D}/l2_bpt_full276_macro_engine_null.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['metric','observed','p_value','N','interpretacao'])
    w.writerow(['TAKE_WR',obs_wr,round(p_wr,3),N,'p<0.05 = separacao real vs subset aleatorio do mesmo tamanho'])
    w.writerow(['TAKE_PF',obs_pf,round(p_pf,3),N,'idem PF'])

# ---------- JACKKNIFE (leave-1-year-out) ----------
def year(b): return pk[b]['datetime'][:4]
years=sorted(set(year(b) for b in ALL))
print("\n--- JACKKNIFE leave-1-year-out (TAKE) ---")
jk_rows=[]
for y in years:
    tk=[b for b in TAKE if year(b)!=y]; m=metrics(tk)
    jk_rows.append(dict(left_out=y,**{k:m[k] for k in('n','WR','PF','sumR','runners','Lstreak')}))
    print(f"  drop {y}: n={m['n']} WR={m['WR']} PF={m['PF']} runners={m['runners']} Lstk={m['Lstreak']}")
with open(f"{D}/l2_bpt_full276_macro_engine_jackknife.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['left_out','n','WR','PF','sumR','runners','Lstreak'],lineterminator="\n");w.writeheader();w.writerows(jk_rows)

# ---------- SUB-JANELAS temporais (TAKE) ----------
print("\n--- SUB-JANELAS (TAKE) ---")
sub_rows=[]
def window(b):
    d=pk[b]['datetime'][:10]
    return 'P1_2020-22' if d<'2023-01-01' else 'P2_2023-26'
for w_ in ['P1_2020-22','P2_2023-26']:
    tk=[b for b in TAKE if window(b)==w_]; m=metrics(tk)
    sub_rows.append(dict(window=w_,**{k:m[k] for k in('n','WR','PF','sumR','runners','big','Lstreak')}))
    print(f"  {w_}: n={m['n']} WR={m['WR']} PF={m['PF']} sumR={m['sumR']} runners={m['runners']} Lstk={m['Lstreak']}")
for y in years:
    tk=[b for b in TAKE if year(b)==y]; m=metrics(tk)
    sub_rows.append(dict(window=y,**{k:m[k] for k in('n','WR','PF','sumR','runners','big','Lstreak')}))
    print(f"  {y}: n={m['n']} WR={m['WR']} PF={m['PF']} sumR={m['sumR']} runners={m['runners']} Lstk={m['Lstreak']}")
with open(f"{D}/l2_bpt_full276_macro_engine_subwindows.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['window','n','WR','PF','sumR','runners','big','Lstreak'],lineterminator="\n");w.writeheader();w.writerows(sub_rows)

# ---------- DROUGHT-17 (o que macro_phase BULL_RUN tomou; o que o engine decide agora) ----------
DROUGHT_DATES=['2020-07-28','2020-07-30','2020-08-04','2020-08-07','2021-05-31','2021-06-02','2021-06-07',
 '2021-06-10','2021-11-15','2021-11-17','2021-11-22','2021-12-28','2021-12-30','2022-01-14','2022-01-18','2022-01-21','2022-01-25']
drought_b=[b for b in ALL if pk[b]['datetime'][:10] in DROUGHT_DATES]
print(f"\n--- DROUGHT-17 (macro_phase BULL_RUN tomou; engine agora) — {len(drought_b)} encontrados ---")
dr_rows=[]; engine_fixed=0
for b in sorted(drought_b,key=lambda x:pk[x]['datetime']):
    state,fam,conf,pol=dec[b]; ex=outc[b]['exitype']
    fixed = pol in('SKIP','REVIEW','REVIEW_RISK')
    if fixed and ex not in WIN: engine_fixed+=1
    dr_rows.append(dict(datetime=pk[b]['datetime'][:10],engine_policy=pol,macro_state=state,family=fam,
        supply=conf_rows[ALL.index(b)]['supply'],fuel=conf_rows[ALL.index(b)]['fuel'],momentum=conf_rows[ALL.index(b)]['momentum'],
        capit=conf_rows[ALL.index(b)]['capit'],exitype=ex,engine_avoids_loss=fixed and ex not in WIN))
    print(f"  {pk[b]['datetime'][:10]}: engine={pol:11} state={state:26} ex={ex}")
print(f"  => engine evita {engine_fixed}/{len([b for b in drought_b if outc[b]['exitype'] not in WIN])} losses do drought (não-TAKE)")
with open(f"{D}/l2_bpt_full276_macro_engine_drought.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['datetime','engine_policy','macro_state','family','supply','fuel','momentum','capit','exitype','engine_avoids_loss'],lineterminator="\n");w.writeheader();w.writerows(dr_rows)
print("\nDONE. outputs: confluence, specialist_evidence, policy_eval, ablation, null, jackknife, subwindows, drought.")
