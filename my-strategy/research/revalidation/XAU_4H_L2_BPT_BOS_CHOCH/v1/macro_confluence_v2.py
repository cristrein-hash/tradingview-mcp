#!/usr/bin/env python3
"""MACRO CONFLUENCE v2 — macro override (condicional) + late-top detector. DIAGNÓSTICO/calibração.
Reusa os 9 especialistas v1 como EVIDÊNCIA (confluence_62.csv); muda SÓ a lógica de combinação.
Sem outcome. Sem engine/produção. Causal. Thresholds declarados, não tunados a IDs."""
import json,csv,bisect
RR="repro_recovery";D="results"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
v1={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_macro_specialist_confluence_62.csv"))}
def load_daily(p):
    rows=[json.loads(l) for l in open(p) if json.loads(l).get('ts')];rows.sort(key=lambda r:r['ts']);return rows
extB=load_daily("../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl")
extW=load_daily("../../../../strategies/candidates/regime_classifier_v3/xau_weekly_with_features.jsonl")
def clk(rows,ed):
    ds=[r['ts'] for r in rows];i=bisect.bisect_left(ds,ed)-1;return rows[i] if i>=0 else None
def fn(v):
    try:return float(v)
    except:return None
def tb(v): return v in(True,'true','True','1',1)

# raw macro/late-top features por episódio (causal: regime_B D-1, weekly prev-week, packet close-i)
def macro_feats(p):
    P=pk[int(v1[p]['episode_id'])] if 'episode_id' in v1[p] else None
    # episode_id não está no confluence csv? usar bar_idx via matrix
    return None
# precisamos do bar_idx -> vem da matriz
mat={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
def ep(p):return int(mat[p]['episode_id'])

# THRESHOLDS DECLARADOS
LEGPOS_HIGH=85; WK_RSI_OB=70; D1SUP_NEAR=1.0; RISE_HI=3.5
BULL_FAM={'MACRO_BULL_RUN_CONTINUATION','BULL_PULLBACK_CONTINUATION','RANGE_MACRO_BULL_RECLAIM','BOTTOM_REVERSAL_VALID','CAPITULATION_RECLAIM_VALID','NO_OVERHEAD_MARKUP'}
RISK_FAM={'BEAR_BOUNCE_RISK','CORRECTIVE_BEAR_LEG','LATE_TOP_EXHAUSTION','SUPPLY_COLADA_REJECTION'}
STRONG_LOCAL_BULL={'NO_OVERHEAD_MARKUP','MACRO_BULL_RUN_CONTINUATION'}

def features(p):
    e=ep(p);P=pk[e];ed=P['datetime'][:10];Bx=clk(extB,ed) or {};Wk=clk(extW,ed) or {}
    return dict(
        macro_broken=tb(Bx.get('macro_broken')),distribution=tb(Bx.get('distribution_flag')),
        cascade=fn(Bx.get('cascade_score')),stall=tb(Bx.get('stall')),sharp_drop=tb(Bx.get('sharp_drop')),
        dist_alarm=tb(Bx.get('dist_alarm')),d_break_bear=tb(Bx.get('d_break_bear')),w_break_bear=tb(Bx.get('w_break_bear')),
        legpos90=fn(P.get('legpos90')),dist_d1_supply=fn(P.get('dist_d1_supply_atr')),
        wk_rsi=fn(Wk.get('rsi_14')),wk_slope=fn(Wk.get('slope_20_pct')),
        rise20=fn(P.get('rise20_atr')),bear_div=fn(P.get('rsi_bear_div_20b')),rsi=fn(P.get('rsi')))

def macro_fatal(F):
    rc=[]
    if F['macro_broken']: rc.append('macro_broken')
    if F['distribution']: rc.append('distribution_flag')
    if F['cascade'] is not None and F['cascade']<=-2 and (F['d_break_bear'] or F['w_break_bear']): rc.append('cascade+break_bear')
    if F['dist_alarm'] and F['sharp_drop']: rc.append('dist_alarm+sharp_drop')
    return (len(rc)>0, rc)

def late_top(F):
    if F['legpos90'] is None or F['legpos90']<LEGPOS_HIGH: return (False,[])
    corr=[]
    if F['distribution']: corr.append('distribution')
    if F['dist_d1_supply'] is not None and F['dist_d1_supply']<D1SUP_NEAR: corr.append('d1_supply_near')
    if F['bear_div'] is not None and F['bear_div']>=1: corr.append('bear_div')
    if F['rise20'] is not None and F['rise20']>=RISE_HI: corr.append('rise20_extended')
    if F['wk_rsi'] is not None and F['wk_rsi']>=WK_RSI_OB: corr.append('weekly_OB')
    return (len(corr)>=1, corr)  # legpos alto + >=1 corroborador de exaustão/distribuição (mesmo c/ momentum forte)

def confluence_v2(p):
    R=v1[p]; v1state=R['macro_state']
    sup=R['supply'];dem=R['demand'];mom=R['momentum'];mtf=R['mtf'];cap=R['capit']
    F=features(p)
    mf,mf_rc=macro_fatal(F); lt,lt_rc=late_top(F)
    rc=[]
    # corroboração de risco (o "JUNTO com")
    risk_corr = sup in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET') or mom=='WEAK_MOMENTUM' or dem in('DEMAND_FRAGILE','DEMAND_ABSENT') or mtf=='BEAR_ALIGN' or lt
    # 1) LATE-TOP detector tem prioridade (resolve late-top-com-momentum)
    if lt:
        return 'LATE_TOP_EXHAUSTION','high','late_top:'+'+'.join(lt_rc)
    # 2) macro fatal CONDICIONAL (só bloqueia com corroboração)
    if mf and risk_corr:
        if v1state in STRONG_LOCAL_BULL:
            return 'UNKNOWN_CONFLICT','medium',f'macro_fatal({"+".join(mf_rc)})_vs_local_bull'
        if cap=='CLIMAX_RECLAIM':
            return v1state,R['confidence'],'climax_overrides_macro'  # fundo real sobrepõe
        return 'CORRECTIVE_BEAR_LEG','high',f'macro_fatal+risk_corr({"+".join(mf_rc)})'
    # 3) macro fatal SOZINHO (sem corroboração) -> NÃO bloqueia, só rebaixa confiança
    if mf and v1state in BULL_FAM:
        return v1state,'low',f'macro_fatal_alone_conf_down({"+".join(mf_rc)})'
    # 4) sem macro fatal -> mantém v1
    return v1state,R['confidence'],'v1_kept'

# RODAR
rows=[];diag=[];cmp_rows=[]
for p in sorted(v1,key=lambda x:(v1[x]['set'],x[0],int(x[1:]))):
    R=v1[p];s2,c2,rc2=confluence_v2(p);F=features(p)
    fam1=R['family'];fam2='BULL' if s2 in BULL_FAM else('RISK' if s2 in RISK_FAM else 'NEUTRO')
    rows.append(dict(plot_id=p,set=R['set'],datetime=R['datetime'],v1_state=R['macro_state'],v1_family=fam1,
        v2_state=s2,v2_family=fam2,v2_confidence=c2,v2_reason=rc2,final_verdict=R['final_verdict'],
        supply=R['supply'],demand=R['demand'],momentum=R['momentum'],mtf=R['mtf'],regime=R['regime'],capit=R['capit']))
    cmp_rows.append(dict(plot_id=p,set=R['set'],v1_state=R['macro_state'],v1_family=fam1,v2_state=s2,v2_family=fam2,changed=('YES' if fam1!=fam2 else '')))
    # diag falsos BULL (B-set ou must-block que eram BULL em v1)
    if R['set']=='B' and fam1=='BULL':
        mf,mf_rc=macro_fatal(F);lt,lt_rc=late_top(F)
        diag.append(dict(plot_id=p,v1_state=R['macro_state'],regime=R['regime'],mtf=R['mtf'],momentum=R['momentum'],supply=R['supply'],
            macro_fatal=mf,macro_fatal_rc='+'.join(mf_rc),late_top=lt,late_top_rc='+'.join(lt_rc),v2_state=s2,v2_family=fam2,
            feature_values=f"macro_broken={F['macro_broken']};distribution={F['distribution']};cascade={F['cascade']};legpos90={F['legpos90']};dist_d1_supply={F['dist_d1_supply']};wk_rsi={F['wk_rsi']};bear_div={F['bear_div']};rise20={F['rise20']}"))
with open(f"{D}/l2_bpt_macro_confluence_v2_states_62.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
with open(f"{D}/l2_bpt_macro_confluence_v2_v1_comparison.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(cmp_rows[0].keys()));w.writeheader();w.writerows(cmp_rows)
with open(f"{D}/l2_bpt_macro_confluence_v2_false_bull_diagnostic.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(diag[0].keys()));w.writeheader();w.writerows(diag)
from collections import Counter
def famset(s,key): return Counter(r[key] for r in rows if r['set']==s)
print("=== TAREFA 1: falsos BULL no B-set (v1) -> macro_fatal/late_top presentes? ===")
for d in diag: print(f"  {d['plot_id']:<4} v1={d['v1_state']:<26} macro_fatal={d['macro_fatal']}({d['macro_fatal_rc']}) late_top={d['late_top']}({d['late_top_rc']}) -> v2={d['v2_state']}")
print(f"\n=== família por SET: v1 -> v2 ===")
for s in('A','B','C'):
    print(f"  {s}: v1={dict(famset(s,'v1_family'))} -> v2={dict(famset(s,'v2_family'))}")
print("\nestados v2:",dict(Counter(r['v2_state'] for r in rows)))

# ANCHOR CHECK v1 vs v2
PRESERVE=['T34','T35','T37','S20','S24','S25','S26','S27','S29','S30','S31','S32','T39','T41','S35','S36','S37','S38']
BLOCK=['T40','S40']
bymap={r['plot_id']:r for r in rows}
ac=[]
p1=p2=b1=b2=0
for p in PRESERVE:
    if p not in bymap:continue
    r=bymap[p];o1=r['v1_family']=='BULL';o2=r['v2_family']=='BULL'
    p1+=o1;p2+=o2;ac.append(dict(plot_id=p,role='preserve',v1_family=r['v1_family'],v2_family=r['v2_family'],v1_ok=o1,v2_ok=o2,v2_state=r['v2_state']))
for p in BLOCK:
    if p not in bymap:continue
    r=bymap[p];o1=r['v1_family']=='RISK';o2=r['v2_family']=='RISK'
    b1+=o1;b2+=o2;ac.append(dict(plot_id=p,role='block',v1_family=r['v1_family'],v2_family=r['v2_family'],v1_ok=o1,v2_ok=o2,v2_state=r['v2_state']))
with open(f"{D}/l2_bpt_macro_confluence_v2_anchor_check.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['plot_id','role','v1_family','v2_family','v1_ok','v2_ok','v2_state']);w.writeheader();w.writerows(ac)
npp=len([p for p in PRESERVE if p in bymap]);nbb=len([p for p in BLOCK if p in bymap])
# B-set block rate
Bblock1=sum(1 for r in rows if r['set']=='B' and r['v1_family']=='RISK');Bblock2=sum(1 for r in rows if r['set']=='B' and r['v2_family']=='RISK')
nB=sum(1 for r in rows if r['set']=='B')
print(f"\n=== ANCHOR CHECK v1 -> v2 ===")
print(f"  preserve(BULL): {p1}/{npp} -> {p2}/{npp}")
print(f"  block(RISK): {b1}/{nbb} -> {b2}/{nbb}")
print(f"  B-set block(RISK): {Bblock1}/{nB} -> {Bblock2}/{nB}")
print(f"  preserve PERDIDOS por v2:",[r['plot_id'] for r in ac if r['role']=='preserve' and r['v1_ok'] and not r['v2_ok']])
