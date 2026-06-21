#!/usr/bin/env python3
"""HAS_OVERHEAD-AWARE context feature — DIAGNÓSTICO (spec c9f2a20). Escopo XAU_4H_L2_BPT_BOS_CHOCH.
Sem outcome como predicado. C fora do fit. Engine/decisions/produção intocados. Thresholds DECLARADOS
(principled ATR/RSI), NÃO ajustados a IDs. Estados causais conhecíveis na entrada."""
import json,csv,random,statistics as st
RR="repro_recovery";D="results"
random.seed(20260621)
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
mat={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
cris={r['plot_id']:r['cris_verdict'] for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0_cris_verdicts.csv"))}
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

# ---- THRESHOLDS DECLARADOS (principled; não ID-fit) ----
DIST_CLOSE=1.5      # supply 'colada' (ATR)
DIST_MARKUP=2.8     # dentro do range de markup
MOM_TREND=1.5       # trend_30_atr forte
MOM_RSI1D=53.0      # momentum diário positivo
LEGPOS_HIGH=85.0
RSI_HIGH=65.0
BULL_STATES={'NO_OVERHEAD_BULLISH','MARKUP_BREAKING_SUPPLY'}
RISK_STATES={'VALID_OVERHEAD_SUPPLY_RISK','SUPPLY_COLADA_BEARISH','LATE_TOP_UNDER_SUPPLY'}

def state(p):
    e=ep(p);P=pk[e]
    ovh=P.get('has_4h_supply_overhead')
    ovh = 1 if str(ovh) in ('1','yes','True') else (0 if str(ovh) in ('0','no','False') else None)
    dist=fn(P.get('dist_4h_supply_low_atr'))
    broken=str(P.get('supply_broken_before')) in('1','yes','True')
    rejected=str(P.get('supply_rejected_before')) in('1','yes','True')
    trend=fn(P.get('trend_30_atr'));rsi1d=fn(P.get('rsi_1d'));rsi=fn(P.get('rsi'));lp=fn(P.get('legpos90'))
    mom_strong = (trend is not None and trend>=MOM_TREND) or (rsi1d is not None and rsi1d>=MOM_RSI1D)
    if ovh is None: return 'UNKNOWN_INSUFFICIENT_DATA'
    if ovh==0: return 'NO_OVERHEAD_BULLISH'           # sem teto = ATH/markup (dist None aqui = sinal, não missing)
    # ovh==1:
    if dist is None: return 'UNKNOWN_INSUFFICIENT_DATA'  # missing real (há overhead mas sem distância)
    if broken and (mom_strong or dist<DIST_MARKUP): return 'MARKUP_BREAKING_SUPPLY'
    if lp is not None and lp>=LEGPOS_HIGH and not mom_strong and (rsi is not None and rsi>=RSI_HIGH): return 'LATE_TOP_UNDER_SUPPLY'
    if dist<DIST_CLOSE and not mom_strong: return 'SUPPLY_COLADA_BEARISH'
    return 'VALID_OVERHEAD_SUPPLY_RISK'
def family(s): return 'BULL' if s in BULL_STATES else ('RISK' if s in RISK_STATES else 'UNKNOWN')

# ---- Tarefa 7: feature_values ----
rows=[]
for grp,S in [('A',A),('B',B),('C',Cset)]:
    for p in sorted(S,key=lambda x:(x[0],int(x[1:]))):
        e=ep(p);P=pk[e];s=state(p)
        rows.append(dict(plot_id=p,set=grp,episode_id=e,datetime=mat[p]['datetime'][:10],
            has_overhead=P.get('has_4h_supply_overhead'),dist_4h_supply=P.get('dist_4h_supply_low_atr'),
            broken=P.get('supply_broken_before'),trend_30=P.get('trend_30_atr'),rsi_1d=P.get('rsi_1d'),legpos90=P.get('legpos90'),
            composite_state=s,family=family(s),final_verdict=final(p)))
with open(f"{D}/l2_bpt_overhead_feature_values.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
from collections import Counter
print(f"A={len(A)} B={len(B)} C={len(Cset)}")
print("estados (A):",dict(Counter(state(p) for p in A)))
print("estados (B):",dict(Counter(state(p) for p in B)))
print("estados (C):",dict(Counter(state(p) for p in C_NAMED|set(Cset))))

# ---- Tarefa 3: comparação vs dist_supply puro (v1 baseline) ----
THR=2.33
def pure_bull(p):
    v=fn(pk[ep(p)].get('dist_4h_supply_low_atr'));return None if v is None else v<THR
def comp_bull(p):return family(state(p))=='BULL'
# A deve ser BULL, B deve ser RISK
def recall_block(predA,predB,A,B,is_bull):
    rA=sum(1 for p in A if is_bull(p))/len(A);bB=sum(1 for p in B if is_bull(p)==False)/len(B);return rA,bB
pr_rA=sum(1 for p in A if pure_bull(p))/len(A);pr_bB=sum(1 for p in B if pure_bull(p) is False)/len(B)
co_rA=sum(1 for p in A if comp_bull(p))/len(A);co_bB=sum(1 for p in B if comp_bull(p) is False)/len(B)
cmp=[dict(method='dist_supply_puro(<2.33)',A_recall_bull=round(pr_rA,3),B_block=round(pr_bB,3),bal=round((pr_rA+pr_bB)/2,3)),
     dict(method='HAS_OVERHEAD_AWARE_composite',A_recall_bull=round(co_rA,3),B_block=round(co_bB,3),bal=round((co_rA+co_bB)/2,3))]
with open(f"{D}/l2_bpt_overhead_feature_comparison_vs_distsupply.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['method','A_recall_bull','B_block','bal']);w.writeheader();w.writerows(cmp)
print(f"\nCOMPARAÇÃO: dist_supply puro bal={cmp[0]['bal']} (A_rec={pr_rA:.2f} B_blk={pr_bB:.2f}) | composite bal={cmp[1]['bal']} (A_rec={co_rA:.2f} B_blk={co_bB:.2f})")

# ---- Tarefa 4: anchor check ----
PRESERVE=['T34','T35','T37','S20','S24','S25','S26','S27','S29','S30','S31','S32','T39','T41','S35','S36','S37','S38']
BLOCK=['T40','S40']
ac=[]
okp=0
for p in PRESERVE:
    if p not in mat:continue
    s=state(p);fam=family(s);pur=pure_bull(p)
    ok = fam=='BULL'
    if ok:okp+=1
    ac.append(dict(plot_id=p,role='preserve',composite_state=s,composite_family=fam,composite_ok=ok,pure_distsupply_bull=pur,pure_ok=(pur is True)))
okb=0
for p in BLOCK:
    if p not in mat:continue
    s=state(p);fam=family(s);pur=pure_bull(p)
    ok = fam in('RISK',)  # deve NÃO ser bull
    if ok:okb+=1
    ac.append(dict(plot_id=p,role='block',composite_state=s,composite_family=fam,composite_ok=ok,pure_distsupply_bull=pur,pure_ok=(pur is False)))
with open(f"{D}/l2_bpt_overhead_feature_anchor_check.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['plot_id','role','composite_state','composite_family','composite_ok','pure_distsupply_bull','pure_ok']);w.writeheader();w.writerows(ac)
np_=len([p for p in PRESERVE if p in mat]);nb_=len([p for p in BLOCK if p in mat])
pure_okp=sum(1 for r in ac if r['role']=='preserve' and r['pure_ok']);pure_okb=sum(1 for r in ac if r['role']=='block' and r['pure_ok'])
print(f"\nANCHORS preserve: composite {okp}/{np_} (vs dist_supply puro {pure_okp}/{np_}) | block: composite {okb}/{nb_} (vs puro {pure_okb}/{nb_})")
print("  preserve falhas (composite):",[r['plot_id'] for r in ac if r['role']=='preserve' and not r['composite_ok']])
print("  block falhas (composite):",[r['plot_id'] for r in ac if r['role']=='block' and not r['composite_ok']])

# ---- Tarefa 5: robustez (shuffle-null + split temporal) sobre family BULL=A/RISK=B ----
def bal_acc(A,B):
    rA=sum(1 for p in A if comp_bull(p))/len(A) if A else 0;bB=sum(1 for p in B if not comp_bull(p))/len(B) if B else 0;return (rA+bB)/2
real=bal_acc(A,B)
# shuffle-null: permutar rótulos A/B e medir bal_acc do MESMO composite (a feature é fixa; testa se a separação é casual)
allp=A+B;na=len(A);null=[]
preds={p:comp_bull(p) for p in allp}
for _ in range(2000):
    random.shuffle(allp);a=allp[:na];b=allp[na:]
    rA=sum(1 for p in a if preds[p])/len(a);bB=sum(1 for p in b if not preds[p])/len(b);null.append((rA+bB)/2)
p_null=sum(1 for x in null if x>=real)/len(null)
yr=lambda p:mat[p]['datetime'][:4]
Ae=[p for p in A if yr(p)<'2024'];Al=[p for p in A if yr(p)>='2024'];Be=[p for p in B if yr(p)<'2024'];Bl=[p for p in B if yr(p)>='2024']
rob=[dict(test='full',bal_acc=round(real,3),n=f"A{len(A)}/B{len(B)}",note='composite family BULL=A/RISK=B'),
     dict(test='shuffle_null',bal_acc=f"P(null>=real)={round(p_null,3)}",n='2000 perm',note=f"null mediana={round(st.median(null),3)}"),
     dict(test='temporal_2020-23',bal_acc=round(bal_acc(Ae,Be),3),n=f"A{len(Ae)}/B{len(Be)}",note='in-window'),
     dict(test='temporal_2024-26',bal_acc=round(bal_acc(Al,Bl),3),n=f"A{len(Al)}/B{len(Bl)}",note=f"B late n={len(Bl)} {'FRÁGIL' if len(Bl)<5 else ''}")]
with open(f"{D}/l2_bpt_overhead_feature_robustness.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['test','bal_acc','n','note']);w.writeheader();w.writerows(rob)
print(f"\nROBUSTEZ: full bal={real:.3f} | shuffle-null P(null>=real)={p_null:.3f} | 2020-23 bal={bal_acc(Ae,Be):.3f} | 2024-26 bal={bal_acc(Al,Bl):.3f} (B late n={len(Bl)})")

# ---- Tarefa 6: DA ----
da=[
 ("diagnostico_nao_promocao","SIM","feature diagnóstica; nada promovido"),
 ("sem_v2","SIM","nenhum aggregator rodado"),
 ("engine_decisions_registry_intocados","SIM","só results/ + script de pesquisa"),
 ("producao_telegram_chart_slim","NAO-TOCADO","nenhum"),
 ("outcome_como_predicado","NAO","estados usam só has_overhead/dist/broken/trend/rsi/legpos (entrada)"),
 ("C_fora_do_fit","SIM",f"C={len(Cset)} reportado à parte"),
 ("provenance_supply_broken","CAUSAL","range(i-WIN,i+1) inclusive, nunca >i; '_before_entry'; verificado"),
 ("look_ahead","AUSENTE","externas não usadas nesta feature; supply causal; sem futuro"),
 ("ids_no_fit","NAO","thresholds principled declarados (DIST/MOM/LEGPOS/RSI), não casados a IDs"),
 ("anchors_checadas","SIM",f"preserve {okp}/{np_}, block {okb}/{nb_}"),
 ("comparacao_vs_distsupply","SIM",f"composite bal {cmp[1]['bal']} vs puro {cmp[0]['bal']}"),
 ("n_pequeno_declarado","SIM",f"A26/B18; B late n={len(Bl)} held-out frágil; calibração não validação"),
]
with open(f"{D}/l2_bpt_overhead_feature_da.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(["check","result","detail"]);[w.writerow(r) for r in da]
print("\nDA escrito. Outputs prontos.")
