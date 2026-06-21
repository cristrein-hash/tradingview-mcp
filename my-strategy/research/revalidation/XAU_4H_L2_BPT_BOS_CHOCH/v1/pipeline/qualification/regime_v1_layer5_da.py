#!/usr/bin/env python3
"""REGIME/CONTEXT/FUEL v1 — LAYER 5 (interpretação + checagem âncoras) + DA + salvar sets. DIAGNÓSTICO."""
import json,csv,bisect
RR="repro_recovery";D="results"
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
# salvar sets (col correta)
for nm,S in [('setA',A),('setB',B),('setC',Cset)]:
    with open(f"{D}/l2_bpt_regime_v1_{nm}.csv","w",newline="") as f:
        w=csv.writer(f);w.writerow(['plot_id','episode_id','datetime','stage_a_context','final_verdict'])
        for p in sorted(S,key=lambda x:(x[0],int(x[1:]))):w.writerow([p,ep(p),mat[p]['datetime'][:10],mat[p].get('stage_a_context',''),final(p)])

# REGRA CANDIDATA (da árvore/univariado): dist_4h_supply_low_atr < 2.33 = bull-run (keep) ; >= = bear (block)
THR=2.33
def dsup(p):return fn(pk[ep(p)].get('dist_4h_supply_low_atr'))
def pred_bull(p):
    v=dsup(p);return None if v is None else (v<THR)
# checagem ÂNCORAS must-preserve / must-block
PRESERVE=['T34','T35','T37','S20','S24','S25','S26','S27','S29','S30','S31','S32','T39','T41','S35','S36','S37','S38']
BLOCK=['T40','S40']
print("=== LAYER5: regra candidata dist_4h_supply_low_atr < 2.33 = bull-run ===")
print("\nMUST-PRESERVE (regra deve dar bull=True):")
ok_p=0;miss_p=[]
for p in PRESERVE:
    if p not in mat: print(f"  {p}: (fora do conjunto plotado)");continue
    v=dsup(p);b=pred_bull(p)
    flag='OK' if b else 'FALHA-corta-winner'
    if b:ok_p+=1
    else:miss_p.append(p)
    print(f"  {p:<5} dist_supply={v} -> bull={b} [{flag}]")
print(f"\nMUST-BLOCK (regra deve dar bull=False):")
ok_b=0;miss_b=[]
for p in BLOCK:
    if p not in mat:print(f"  {p}: (fora)");continue
    v=dsup(p);b=pred_bull(p)
    flag='OK-bloqueia' if b is False else 'FALHA-aceita-trap'
    if b is False:ok_b+=1
    else:miss_b.append(p)
    print(f"  {p:<5} dist_supply={v} -> bull={b} [{flag}]")
# A/B recall
recA=sum(1 for p in A if pred_bull(p))/len(A);blkB=sum(1 for p in B if pred_bull(p) is False)/len(B)
print(f"\nA recall(bull)={recA:.2f} | B block={blkB:.2f}")

# DA anti-overfit/anti-hindsight
da=[
 ("usa_outcome_como_predicado","NAO","regra usa só dist_4h_supply (feature de entrada); outcome nunca entrou"),
 ("feature_causal_entrada","SIM","dist_4h_supply_low_atr conhecível no close do bar i"),
 ("externas_shift_causal","SIM","regime_B_v3/l1_v4/daily só com shift D-1 (Layer1 0 join_issues, shift>=1)"),
 ("macro_leg_testado_nao_nome","SIM","confirmado MORTO empiricamente (REFERENCE_ONLY 276/276)"),
 ("stage_a_nao_confiado","SIM","Stage A não separa A/B (distrib idêntica); usado só como feature"),
 ("shuffle_null","PASS","P(null>=real)=0.0 (feature top); separação não-aleatória"),
 ("held_out_temporal","PARCIAL","train2020-23->test2024-26 ba=0.808 OK; reverso INVIÁVEL (B late n=3); held-out FRÁGIL"),
 ("n_pequeno","FLAG","A=26 B=18 (44); held-out B-side n=3. Calibração, NÃO validação."),
 ("hour_utc_na_arvore","ARTEFATO","árvore pegou hour_utc no 2º split = session-time, NÃO causal-regime; IGNORAR (candidato a forbidden)"),
 ("overfit_por_ID","NAO","regra = 1 threshold interpretável (eixo supply-distance), não casada a IDs"),
 ("colinearidade","NOTA","dist_4h_supply e reclaim_dist_from_supply IDÊNTICAS (mesma medição)"),
 ("anchors_preserve",f"{ok_p}/{len([p for p in PRESERVE if p in mat])}",f"falhas: {miss_p}"),
 ("anchors_block",f"{ok_b}/{len([p for p in BLOCK if p in mat])}",f"falhas: {miss_b}"),
]
with open(f"{D}/l2_bpt_regime_v1_da.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(["check","result","detail"]);[w.writerow(r) for r in da]
print("\n=== DA ===")
for c,r,d in da:print(f"  [{r}] {c}: {d}")
print(f"\nsets A/B/C + DA salvos.")
