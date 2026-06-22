#!/usr/bin/env python3
"""ENTRY-QUALITY specialist — DIAGNÓSTICO (testa hipótese: localização-da-entrada separa A bom de B ruim).
Ortogonal ao macro. Sem outcome. Causal. Thresholds declarados, não ID-fit. 62=ensino."""
import json,csv
from collections import Counter
RR="repro_recovery";D="results"
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
# THRESHOLDS DECLARADOS
DEM_NEAR=3.0; DEM_FAR=4.0; VAL_HIGH=1.5; VAL_LOW=0.5
GOOD={'ENTRY_PULLBACK_TO_DEMAND','ENTRY_AT_VALUE_LOW','ENTRY_RECLAIM_DEMAND'}
RISK={'ENTRY_EXTENDED_FROM_DEMAND','ENTRY_HIGH_IN_VALUE','ENTRY_NO_DEMAND_BASE'}
def state(p):
    e=ep(p);P=pk[e];Q=dsq.get(e,{})
    dd=fn(P.get('dist_4h_demand_low_atr'));dval=fn(P.get('dist_VAL_atr'));bv=P.get('below_VAL');dc=Q.get('demand_category')
    f={'dist_demand':dd,'dist_VAL':dval,'below_VAL':bv,'demand_cat':dc}
    rc=[]
    if dc in('DEMAND_ABSENT_OR_IRRELEVANT',): return 'ENTRY_NO_DEMAND_BASE',f,['no_demand']
    if dd is not None and dd>DEM_FAR: return 'ENTRY_EXTENDED_FROM_DEMAND',f,['extended']
    if dval is not None and dval>VAL_HIGH: return 'ENTRY_HIGH_IN_VALUE',f,['high_in_value']
    if bv is True or (dval is not None and dval<VAL_LOW): return 'ENTRY_AT_VALUE_LOW',f,['at_value_low']
    if dd is not None and dd<DEM_NEAR and dc in('DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG'): return 'ENTRY_PULLBACK_TO_DEMAND',f,['pullback_demand']
    return 'ENTRY_NEUTRAL',f,['neutral']
def fam(s): return 'GOOD' if s in GOOD else('RISK' if s in RISK else 'NEUTRAL')
rows=[]
for p in sorted(SET,key=lambda x:(SET[x],x[0],int(x[1:]))):
    s,f,rc=state(p)
    rows.append(dict(plot_id=p,set=SET[p],entry_state=s,entry_family=fam(s),reason='|'.join(rc),
        feature_values=';'.join(f"{k}={v}" for k,v in f.items()),final_verdict=final(p),
        macro_v1_family=v1mac[p]['family'],macro_v1_state=v1mac[p]['macro_state']))
with open(f"{D}/l2_bpt_entry_quality_states_62.csv","w",newline="") as fo:
    w=csv.DictWriter(fo,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def fams(s):return Counter(r['entry_family'] for r in rows if r['set']==s)
print("=== ENTRY-QUALITY family por SET (hipótese: A=GOOD, B=RISK) ===")
for s in('A','B','C'): print(f"  {s}: {dict(fams(s))}")
print("\nestados:",dict(Counter(r['entry_state'] for r in rows)))
# separação A-vs-B: A deve GOOD, B deve RISK
Agood=sum(1 for r in rows if r['set']=='A' and r['entry_family'] in('GOOD','NEUTRAL'))
Brisk=sum(1 for r in rows if r['set']=='B' and r['entry_family']=='RISK')
print(f"\nA 'GOOD/NEUTRAL' (deve ser bom): {Agood}/{len(A)} | B 'RISK' (deve bloquear): {Brisk}/{len(B)}")
# COMBINAÇÃO macro_v1_BULL AND entry_GOOD -> bloqueia B mantendo A?
print("\n=== COMBINAÇÃO: macro_v1=BULL AND entry NÃO-RISK (testa se entry-quality filtra B dentro do bull) ===")
def keep(r): return r['macro_v1_family']=='BULL' and r['entry_family']!='RISK'
Akeep=sum(1 for r in rows if r['set']=='A' and keep(r));Bkeep=sum(1 for r in rows if r['set']=='B' and keep(r))
print(f"  A mantidos (BULL+entry-ok): {Akeep}/{len(A)} | B mantidos (deveria cair): {Bkeep}/{len(B)}")
# ANCHOR CHECK
PRESERVE=['T34','T35','T37','S20','S24','S25','S26','S27','S29','S30','S31','S32','T39','T41','S35','S36','S37','S38']
BLOCK=['T40','S40']
bym={r['plot_id']:r for r in rows}
ac=[];okp=okb=0
for p in PRESERVE:
    if p not in bym:continue
    ok=bym[p]['entry_family'] in('GOOD','NEUTRAL');okp+=ok
    ac.append(dict(plot_id=p,role='preserve',entry_state=bym[p]['entry_state'],entry_family=bym[p]['entry_family'],ok=ok))
for p in BLOCK:
    if p not in bym:continue
    ok=bym[p]['entry_family']=='RISK';okb+=ok
    ac.append(dict(plot_id=p,role='block',entry_state=bym[p]['entry_state'],entry_family=bym[p]['entry_family'],ok=ok))
with open(f"{D}/l2_bpt_entry_quality_anchor_check.csv","w",newline="") as fo:
    w=csv.DictWriter(fo,fieldnames=['plot_id','role','entry_state','entry_family','ok']);w.writeheader();w.writerows(ac)
print(f"\nANCHORS preserve(GOOD/NEUTRAL): {okp}/{len([p for p in PRESERVE if p in bym])} | block(RISK): {okb}/{len([p for p in BLOCK if p in bym])}")
# DA
da=[("diagnostico_apenas","SIM",""),("62_ensino","SIM",""),("outcome_predicado","NAO","features de entrada"),
 ("engine_decisions_registry_producao","INTOCADO",""),("causal","SIM","dist_demand/VAL/demand_cat no close bar i"),
 ("id_fit","NAO","thresholds declarados"),("C_fora_fit","SIM",""),("anchors_checadas","SIM",f"preserve {okp} block {okb}"),
 ("limitacoes","SIM","ver report — hipótese entry-quality")]
with open(f"{D}/l2_bpt_entry_quality_da.csv","w",newline="") as fo:
    w=csv.writer(fo);w.writerow(["check","result","detail"]);[w.writerow(r) for r in da]
print("\noutputs escritos.")
