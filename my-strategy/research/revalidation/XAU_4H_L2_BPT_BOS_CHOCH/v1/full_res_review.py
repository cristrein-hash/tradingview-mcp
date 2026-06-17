import csv
D="results"
prior={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_episode_labels.csv"))}
# Annotations transcribed from the 11 full-res prints (Cris's marks). print file in image_file.
# Only episodes with a readable annotation are asserted; others = NO_VISIBLE_ANNOTATION.
A={
 'E1':('p03','MUITO BOM. SL estrutural correto gera BIG WINNER','TRUE_L2_STRUCTURAL_SETUP','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E13':('p01','Entrada e SL corretos; vira BIG WINNER dos bons','TRUE_L2_STRUCTURAL_SETUP','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E17':('p03/p05','BIG WINNER','TRUE_L2_STRUCTURAL_SETUP','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E27':('p01','ENTRADA REAL CORRETA do cluster; BIG WINNER','TRUE_L2_STRUCTURAL_SETUP','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E30':('p01','BIG WINNER','TRUE_L2_STRUCTURAL_SETUP','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E40':('p09/p10','BIG WINNER, entrada perfeita, SL curto e eficiente','TRUE_L2_STRUCTURAL_SETUP','yes','setup_ok','SL_RETEST_LOW'),
 'E21':('p06','WINNER OK','POLARITY_DEFENDED','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E22':('p06','WINNER OK (SL a corrigir)','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E23':('p06','WINNER OK','POLARITY_DEFENDED','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E5':('p06','WINNER OK','POLARITY_DEFENDED','yes','setup_ok','SL_STRUCTURE_LOW'),
 'E19':('p06','WINNER, SL a corrigir; SL estrutural aqui','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E20':('p06','SKY D+ (cluster winners, SL a corrigir)','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E3':('p04/p05','SUP D+; SL estrutural é aqui','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E4':('p06','SUP UNK; SL estrutural aqui','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E28':('p04/p05','cluster: viram winners com SL estrutural','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E29':('p04/p05','cluster: viram winners com SL estrutural','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E2':('p05','cluster: viram winners com SL estrutural','VALID_SETUP_BAD_SL','unclear','SL_issue','SL_STRUCTURE_LOW'),
 'E38':('p08/p09/p10','LOSER por SL curto demais; vira winner com SL estrutural','VALID_SETUP_BAD_SL','yes','SL_issue','SL_STRUCTURE_LOW'),
 'E41':('p11','Ponto de entrada correto é mais abaixo; loser que precisa virar BIG WINNER','VALID_SETUP_LATE_ENTRY','yes','SL_and_entry','SL_STRUCTURE_LOW'),
 'E25':('p01','Entrada precipitada; eliminar (a real é E27)','LATE_EXTENDED_ENTRY','no','entry_premature','n/a'),
 'E26':('p01','Entrada precipitada; eliminar (a real é E27)','LATE_EXTENDED_ENTRY','no','entry_premature','n/a'),
 'E35':('p01','Entrada precipitada; eliminar (a real é E27)','LATE_EXTENDED_ENTRY','no','entry_premature','n/a'),
 'E15':('p02','NÃO pode existir: topo duplo, entra após barra bear forte','BEAR_LEG_RECLAIM_TRAP','no','macro_bear','n/a'),
 'E34':('p02','NÃO: exaustão; entrar em queda clara de venda não pode','EXHAUSTION_LONG_TRAP','no','macro_bear','n/a'),
 'E24':('p06','Entrada de topo, exaustão clara, MACRO BEAR claro','MACRO_BEAR_NO_LONG','no','macro_bear','n/a'),
 'E39':('p10','Compra sem sentido após perna bear clara; cego para virada bear','MACRO_BEAR_NO_LONG','no','macro_bear','n/a'),
 'E36':('p07','Regime bear (cluster out/2020-mar/2021): não funciona','MACRO_BEAR_NO_LONG','no','macro_bear','n/a'),
 'E6':('p07','Regime bear: não funciona','MACRO_BEAR_NO_LONG','no','macro_bear','n/a'),
 'E7':('p07','Regime bear: não funciona','MACRO_BEAR_NO_LONG','no','macro_bear','n/a'),
 'E8':('p07','Regime bear: não funciona','MACRO_BEAR_NO_LONG','unclear','macro_bear','n/a'),
 'E9':('p07','Regime bear: não funciona','MACRO_BEAR_NO_LONG','no','macro_bear','n/a'),
 'E10':('p07','Regime bear: não funciona','MACRO_BEAR_NO_LONG','unclear','macro_bear','n/a'),
 'E37':('p07/p08','Regime bear: não funciona','MACRO_BEAR_NO_LONG','no','macro_bear','n/a'),
 'E11':('p08','Loser COMPREENSÍVEL pela lógica da estratégia','BEAR_LEG_RECLAIM_TRAP','no','understood_loser','n/a'),
 'E12':('p08','Mesma config de E11 — por que detector NÃO entrou? quantificar','NEEDS_SECOND_REVIEW','unclear','detector_recall_gap','n/a'),
 'E14':('p02','SKY D- (contexto bear region)','NEEDS_SECOND_REVIEW','unclear','macro_review','n/a'),
 'E16':('p03/p05','SKY D- (cluster)','NEEDS_SECOND_REVIEW','unclear','macro_review','n/a'),
 'E31':('p04/p05','D- cluster: SL estrutural aqui (vira winner)','VALID_SETUP_BAD_SL','unclear','SL_issue','SL_STRUCTURE_LOW'),
 'E32':('p04/p05','D- cluster: SL estrutural aqui','VALID_SETUP_BAD_SL','unclear','SL_issue','SL_STRUCTURE_LOW'),
 'E18':('p04/p05','cluster','NEEDS_SECOND_REVIEW','unclear','macro_review','n/a'),
 'E33':('p05/p06','D- D- (cluster perto de E24 topo)','NEEDS_SECOND_REVIEW','unclear','macro_review','n/a'),
}
rows=[]
for ep in sorted(prior, key=lambda e:int(e[1:])):
    p=prior[ep]
    a=A.get(ep,('','NO_VISIBLE_ANNOTATION',p['firstpass_category'],'unclear','unread','n/a'))
    rows.append({'image_file':a[0] or 'not_clearly_visible','episode_id':ep,
      'user_annotation':a[1],'previous_label':p['firstpass_category'],
      'corrected_visual_label':a[2],'valid_long_yes_no_unclear':a[3],'issue_type':a[4],
      'suggested_SL_model':a[5],
      'acceptance_quality':p.get('acceptance_after_reclaim',''),'supply_status':p.get('supply_overhead_cat',''),
      'demand_status':p.get('demand_below_cat',''),'macro_leg_context':p.get('bear_leg_context',''),
      'SL_issue_or_setup_issue':('SL' if a[4]=='SL_issue' else ('SETUP/MACRO' if a[4]=='macro_bear' else a[4])),
      'notes':f"reclaim {p.get('reclaim_candle','')}; supply_dist {p.get('dist_supply_atr','')}ATR; NASsh {p.get('nas_short_10','')}"})
with open(f"{D}/l2_bpt_full_res_visual_episode_review.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print("corrected labels:",dict(Counter(r['corrected_visual_label'] for r in rows)))
print("valid_long:",dict(Counter(r['valid_long_yes_no_unclear'] for r in rows)))
print("issue_type:",dict(Counter(r['issue_type'] for r in rows)))
print("annotated episodes:",sum(1 for r in rows if r['user_annotation'] not in('NO_VISIBLE_ANNOTATION','')))
