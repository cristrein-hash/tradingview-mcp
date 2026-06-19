#!/usr/bin/env python3
"""FASE 2A — runner de evidência por especialista (SEM aggregator, SEM decisão TAKE/SKIP).
--prep   : seleciona amostra balanceada de 25 (5 TAKE-win/5 TAKE-lose/5 SKIP-win/5 SKIP-lose/5 REVIEW),
           STRIPA outcome/old-decision/old-setup_type do INPUT (outcome só p/ balancear a amostra),
           anexa o context_label da Fase 1, e grava o sample. NÃO toca decisions_merged.
--collect: lê os outputs dos 10 especialistas, VALIDA cada evidência (Fase 0) e grava evidência +
           relatório de validação + matriz ablation-ready. Não cria decisão."""
import os,sys,csv,json,glob,argparse,random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_agent_evidence import validate_evidence
random.seed(20260619)
D="results"; RR="repro_recovery"
SAMPLE=f"{D}/specialist_sample.jsonl"; OUTDIR=f"{D}/specialist_out"
LEAK={"episode_id","decision","direction","confidence","expected_setup_type","setup_type","realR","exitype","is_winner_gt","is_loser_gt","closest_to_DIAG"}
SPECIALISTS=["demand_supply","capitulation","exhaustion_top","volume_vp","nas","bubbles","rsi_momentum","risk_sl","bull_beta","devils_advocate"]

def prep(nbatch=2):
    pk={json.loads(l)['bar_idx']:json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
    sa={int(json.loads(l)['_bar_idx']):json.loads(l).get('context_label') for l in open(f"{D}/l2_bpt_stage_a_context_labels.jsonl")}
    # MÁXIMA PRECISÃO: amostra = TODOS os 276 episódios (população inteira do engine)
    ids=sorted(pk)
    clean=[]
    for i in ids:
        c={k:val for k,val in pk[i].items() if k not in LEAK}     # strip outcome/decision/setup_type
        c["context_label_stageA"]=sa.get(i)                        # contexto Fase 1 (não é decisão/outcome)
        clean.append(c)
    leaked=set()
    for c in clean: leaked|=(set(c)&LEAK)
    assert not leaked, f"VAZAMENTO: {leaked}"
    os.makedirs(OUTDIR,exist_ok=True)
    with open(SAMPLE,"w") as f:
        for c in clean: f.write(json.dumps(c)+"\n")
    # batches compartilhados (cada especialista processa cada batch)
    sz=(len(clean)+nbatch-1)//nbatch
    for b in range(nbatch):
        sl=clean[b*sz:(b+1)*sz]
        if sl: open(f"{D}/specialist_batch_{b:02d}.jsonl","w").write("\n".join(json.dumps(c) for c in sl)+"\n")
    print(f"prep: amostra COMPLETA {len(clean)} episódios (máxima precisão) -> {SAMPLE} + {nbatch} batches")
    print(f"input/episódio: 83 fatores + context_label_stageA; SEM {sorted(LEAK)} (0 vazamento)")

def collect():
    pk={json.loads(l)['bar_idx']:json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
    evs=[]; vrows=[]; mat={}
    for fp in sorted(glob.glob(f"{OUTDIR}/*.jsonl")):
        fam=os.path.basename(fp)[:-6]
        for l in open(fp):
            if not l.strip(): continue
            try: r=json.loads(l)
            except: continue
            bi=int(r.get('episode_id')) if str(r.get('episode_id','')).lstrip('-').isdigit() else r.get('bar_idx')
            p=pk.get(bi,{})
            ev_list=r.get('evidence',[]); valid=0; reasons=[]; facs=[]; forb=False; vmis=False; narr=False
            for ev in ev_list:
                ev.setdefault('specialist_id',fam); ev.setdefault('episode_id',str(bi)); ev.setdefault('causal',True)
                res=validate_evidence(ev,p)
                facs.append(ev.get('factor_used'))
                if res['valid']: valid+=1
                else:
                    reasons+=res['reasons']
                    if any('nao_permitido' in x for x in res['reasons']): forb=True
                    if any('value_difere' in x for x in res['reasons']): vmis=True
                    if any('value_ausente' in x or 'campo_obrigatorio_ausente:value' in x for x in res['reasons']): narr=True
                evs.append({**ev,'_valid':res['valid'],'_bar_idx':bi,'_family':fam})
            vrows.append(dict(episode_id=bi,specialist_id=fam,evidence_count=len(ev_list),valid_count=valid,
                              invalid_count=len(ev_list)-valid,invalid_reasons=';'.join(sorted(set(reasons)))[:120],
                              factors_used='|'.join([x for x in facs if x][:8]),forbidden_factor_used='yes' if forb else 'no',
                              value_mismatch='yes' if vmis else 'no',narrative_without_value='yes' if narr else 'no'))
            # matriz ablation-ready
            dec_factors=[ev.get('factor_used') for ev in ev_list if ev.get('decisive_or_supporting')=='decisive' and ev.get('_valid',True)]
            mat[(bi,fam)]=dict(episode_id=bi,context_label=r.get('context_label_stageA') or '',specialist_id=fam,
                positive_evidence_count=sum(1 for ev in ev_list if ev.get('impact')=='positive'),
                negative_evidence_count=sum(1 for ev in ev_list if ev.get('impact')=='negative'),
                veto_count=sum(1 for ev in ev_list if ev.get('impact')=='veto'),
                review_flag_count=sum(1 for ev in ev_list if ev.get('impact')=='review_flag'),
                decisive_factors='|'.join([x for x in dec_factors if x]),
                unresolved_conflicts=' / '.join(r.get('unresolved_conflicts',[]))[:100])
    with open(f"{D}/l2_bpt_specialist_evidence_phase2a.jsonl","w") as f:
        for e in evs: f.write(json.dumps(e)+"\n")
    with open(f"{D}/l2_bpt_specialist_evidence_validation_phase2a.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(vrows[0].keys()));w.writeheader();w.writerows(vrows)
    with open(f"{D}/l2_bpt_specialist_ablation_ready_matrix.csv","w",newline="") as f:
        cols=['episode_id','context_label','specialist_id','positive_evidence_count','negative_evidence_count','veto_count','review_flag_count','decisive_factors','unresolved_conflicts']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(mat.values())
    tot=len(evs); val=sum(1 for e in evs if e['_valid'])
    print(f"collect: {tot} evidências, {val} válidas ({100*val/max(1,tot):.0f}%)")
    print(f"especialistas com output: {sorted(set(e['_family'] for e in evs))}")
    print(f"forbidden_factor_used: {sum(1 for r in vrows if r['forbidden_factor_used']=='yes')} rows | value_mismatch: {sum(1 for r in vrows if r['value_mismatch']=='yes')} | narrative_no_value: {sum(1 for r in vrows if r['narrative_without_value']=='yes')}")

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--prep",action="store_true");ap.add_argument("--collect",action="store_true")
    a=ap.parse_args()
    if a.prep: prep()
    elif a.collect: collect()
    else: print("--prep ou --collect")
