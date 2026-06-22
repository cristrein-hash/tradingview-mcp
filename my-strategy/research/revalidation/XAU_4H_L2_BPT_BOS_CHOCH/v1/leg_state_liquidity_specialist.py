#!/usr/bin/env python3
"""LEG-STATE & LIQUIDITY-STRUCTURE specialist — DIAGNÓSTICO sobre 62 (ensino). Backbone estrutural.
Pivots CAUSAIS (confirmação p+k<=i, nunca futuro). SMC secundário. Camadas anteriores = evidência condicional.
Sem outcome. Sem ID-fit. Sem busca cega. Engine/decisions/produção intocados."""
import json,csv
from collections import Counter
RR="repro_recovery";D="results"
RAW=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(RAW);H=[r['high'] for r in RAW];L=[r['low'] for r in RAW];C=[r['close'] for r in RAW]
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
mat={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
cris={r['plot_id']:r['cris_verdict'] for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0_cris_verdicts.csv"))}
v1mac={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_macro_specialist_confluence_62.csv"))}
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

# ---- PIVOTS CAUSAIS (fractal 3/3; confirmação capada em i) ----
def swing_highs(i,lookback=80,k=3):
    out=[]
    for p in range(max(k, i-lookback), i-k+1):  # exige p+k <= i (confirmado)
        if all(H[p]>H[j] for j in range(p-k,p)) and all(H[p]>=H[j] for j in range(p+1,min(p+k+1,i+1))):
            if p+k<=i: out.append((p,H[p]))
    return out
def swing_lows(i,lookback=80,k=3):
    out=[]
    for p in range(max(k, i-lookback), i-k+1):
        if all(L[p]<L[j] for j in range(p-k,p)) and all(L[p]<=L[j] for j in range(p+1,min(p+k+1,i+1))):
            if p+k<=i: out.append((p,L[p]))
    return out
def atr(i,p=14):
    trs=[max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(max(1,i-p),i)]
    return sum(trs)/len(trs) if trs else 1.0

# ---- LEG-STATE ----
def leg_state(i):
    SH=swing_highs(i);SL=swing_lows(i);a=atr(i)
    f={'n_SH':len(SH),'n_SL':len(SL)}
    if len(SH)<2 or len(SL)<2: return 'UNKNOWN_INSUFFICIENT_STRUCTURE',f,['<2_pivots']
    sh=[v for _,v in SH[-3:]];sl=[v for _,v in SL[-3:]]
    HH = sh[-1]>sh[-2]; HL = sl[-1]>sl[-2]
    last_sl_idx,last_sl=SL[-1];last_sh_idx,last_sh=SH[-1]
    price=C[i]
    f.update({'last_SH':round(last_sh,1),'last_SL':round(last_sl,1),'price':round(price,1),'HH':HH,'HL':HL})
    sl_violated = price < last_sl
    if HH and HL:
        if price < last_sh*0.999 and price>last_sl: return 'BULL_PULLBACK_WITH_HL_INTACT',f,['HH+HL','HL_intacto','pullback']
        return 'BULL_LEG_HH_HL',f,['HH+HL']
    if (not HH) and (not HL):
        if price > last_sl and price < last_sh: return 'BEAR_PULLBACK_TO_SUPPLY',f,['LH+LL','bounce']
        return 'BEAR_LEG_LH_LL',f,['LH+LL']
    # mixed
    if HL and not HH: return 'RANGE_TRANSITION',f,['HL_sem_HH']
    if HH and not HL: return 'CORRECTIVE_BEAR_LEG',f,['HH_mas_LL=correcao']
    return 'RANGE_TRANSITION',f,['mixed']

# ---- LIQUIDITY STRUCTURE ----
def liquidity(i,window=10):
    SH=swing_highs(i);SL=swing_lows(i);a=atr(i)
    f={}
    rc=[]
    # buy-side sweep: algum bar recente fez wick acima de SH prévio e fechou abaixo
    prior_sh=[v for p,v in SH if p<i-1]
    prior_sl=[v for p,v in SL if p<i-1]
    buy_sweep=False;sell_sweep=False;reclaim=False
    for j in range(max(1,i-window),i+1):
        for shv in prior_sh:
            if H[j]>shv and C[j]<shv: buy_sweep=True
        for slv in prior_sl:
            if L[j]<slv and C[j]>slv: sell_sweep=True; 
            if L[j]<slv and C[i]>slv: reclaim=True
    f={'buy_sweep':buy_sweep,'sell_sweep':sell_sweep,'reclaim':reclaim}
    if sell_sweep and reclaim: return 'SWEEP_AND_RECLAIM',f,['sell_sweep+reclaim']
    if buy_sweep: return 'LIQUIDITY_GRAB_REVERSAL_RISK',f,['buy_side_sweep_rejection']
    if sell_sweep: return 'SELL_SIDE_SWEEP',f,['sell_sweep']
    return 'NO_CLEAR_SWEEP',f,['no_sweep']

BULL_LEGS={'BULL_LEG_HH_HL','BULL_PULLBACK_WITH_HL_INTACT'}
BEAR_LEGS={'BEAR_LEG_LH_LL','BEAR_PULLBACK_TO_SUPPLY','CORRECTIVE_BEAR_LEG'}

# ---- CRUZAMENTO interpretável com camadas anteriores ----
def crosscheck(p,leg,liq):
    R=v1mac[p];Q=dsq.get(ep(p),{});P=pk[ep(p)]
    sup=R['supply'];dem=R['demand'];mom=R['momentum'];supcat=Q.get('supply_category')
    used=[];conf=[]
    # leg-conditional readings
    if leg in BULL_LEGS:
        if dem=='DEMAND_DEFENDED': used.append('bull-leg+demand_defended=suporte')
        if supcat=='CLEAN_SKY' and mom in('STRONG_BULL_MOMENTUM','HEALTHY_HIGH_LEGPOS'): used.append('bull-leg+CLEAN_SKY+momentum=bom')
        if supcat=='SUPPLY_NEAR_BUT_BROKEN': used.append('bull-leg+supply_broken=markup')
        if liq=='LIQUIDITY_GRAB_REVERSAL_RISK': conf.append('bull-leg MAS buy-sweep=late-top-risco')
    if leg in BEAR_LEGS:
        if dem=='DEMAND_DEFENDED': conf.append('bear-leg+near-demand=TRAP(nao-suporte)')
        if supcat in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS'): used.append('bear-leg+supply_rejecting=bearish')
        if supcat=='CLEAN_SKY': conf.append('bear-leg+CLEAN_SKY=relief(nao-basta)')
    if liq=='SWEEP_AND_RECLAIM' and dem=='DEMAND_DEFENDED': used.append('sweep+reclaim+demand=reversal-possivel')
    # família de contexto
    if leg in BEAR_LEGS or liq=='LIQUIDITY_GRAB_REVERSAL_RISK': fam='RISK'
    elif leg in BULL_LEGS: fam='BULL'
    else: fam='NEUTRO'
    return fam,used,conf

# ---- RODAR ----
rows=[]
for p in sorted(SET,key=lambda x:(SET[x],x[0],int(x[1:]))):
    i=ep(p);leg,lf,lrc=leg_state(i);liq,qf,qrc=liquidity(i)
    fam,used,conf=crosscheck(p,leg,liq)
    conf_t='high' if leg not in('UNKNOWN_INSUFFICIENT_STRUCTURE','RANGE_TRANSITION') else 'low'
    interp=f"leg={leg}; liq={liq}; contexto={fam}"
    rows.append(dict(plot_id=p,set=SET[p],datetime=pk[i]['datetime'][:10],leg_state=leg,liquidity_state=liq,
        context_family=fam,confidence=conf_t,supports='|'.join(lrc+qrc),conflicts='|'.join(conf),
        reason_codes='|'.join(lrc+qrc),feature_values=';'.join(f"{k}={v}" for k,v in {**lf,**qf}.items()),
        market_interpretation=interp,prior_layers_used='|'.join(used),prior_layers_conflicts='|'.join(conf),
        provenance_ok='pivots_causal+smc_causal',final_verdict=final(p),macro_v1_family=v1mac[p]['family']))
cols=['plot_id','set','datetime','leg_state','liquidity_state','context_family','confidence','supports','conflicts',
      'reason_codes','feature_values','market_interpretation','prior_layers_used','prior_layers_conflicts','provenance_ok','final_verdict','macro_v1_family']
with open(f"{D}/l2_bpt_leg_state_liquidity_evidence_62.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
bym={r['plot_id']:r for r in rows}
print(f"processados: {len(rows)} (A{len(A)} B{len(B)} C{len(Cset)})")
print("leg_state:",dict(Counter(r['leg_state'] for r in rows)))
print("liquidity_state:",dict(Counter(r['liquidity_state'] for r in rows)))
print("context_family:",dict(Counter(r['context_family'] for r in rows)))
print("\nleg_state POR SET:")
for s in('A','B','C'):
    print(f"  {s}: leg={dict(Counter(r['leg_state'] for r in rows if r['set']==s))}")
print("\ncontext_family POR SET (A deve BULL, B deve RISK):")
for s in('A','B','C'):
    print(f"  {s}: {dict(Counter(r['context_family'] for r in rows if r['set']==s))}")
