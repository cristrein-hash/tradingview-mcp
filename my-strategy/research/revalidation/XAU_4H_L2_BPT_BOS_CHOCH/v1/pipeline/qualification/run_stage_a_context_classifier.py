#!/usr/bin/env python3
"""FASE 1 — runner do Stage A Context Classifier (CEGO à decisão e ao outcome).
--prep   : fatia os packets 2020-2026 em batches, REMOVENDO qualquer vazamento (episode_id de GT,
           e garantindo que NÃO há outcome/decision/setup_type antigo no input). NÃO toca decisions_merged.
--collect: lê os outputs dos agentes Stage A, VALIDA cada evidência (validate_agent_evidence da Fase 0),
           e grava results/l2_bpt_stage_a_context_labels.jsonl. Não gera decisão TAKE/REVIEW/SKIP.
Os labels do Stage A NÃO são decisão; são contexto."""
import os,sys,csv,json,glob,argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_agent_evidence import validate_evidence
RR="repro_recovery"; D="results"
BATCHDIR=os.path.join(D,"stage_a_batches"); OUTDIR=os.path.join(D,"stage_a_out")
LABELS=["bottom_reversal_capitulation","demand_reclaim","bull_pullback_continuation","liquidity_sweep_reversal",
        "late_top_exhaustion","bear_bounce","mid_range_noise","unclear_conflict"]
# campos que NUNCA podem entrar no input do Stage A (anti-vazamento)
LEAK_FIELDS={"episode_id","decision","direction","confidence","expected_setup_type","setup_type",
             "realR","exitype","is_winner_gt","is_loser_gt","closest_to_DIAG"}

def prep(nbatch=7):
    pk=[json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")]
    os.makedirs(BATCHDIR,exist_ok=True)
    clean=[]
    for p in pk:
        c={k:v for k,v in p.items() if k not in LEAK_FIELDS}  # strip qualquer vazamento (episode_id etc.)
        clean.append(c)
    # sanity: nenhum campo de vazamento sobrou
    leaked=set()
    for c in clean: leaked|= (set(c) & LEAK_FIELDS)
    assert not leaked, f"VAZAMENTO no input: {leaked}"
    sz=(len(clean)+nbatch-1)//nbatch
    for b in range(nbatch):
        sl=clean[b*sz:(b+1)*sz]
        if not sl: continue
        with open(f"{BATCHDIR}/batch_{b:02d}.jsonl","w") as f:
            for c in sl: f.write(json.dumps(c)+"\n")
    print(f"prep: {len(clean)} packets limpos (0 vazamento) -> {nbatch} batches em {BATCHDIR}")
    print(f"campos no input (sample): {sorted(clean[0].keys())[:8]}... ({len(clean[0])} fatores)")
    print(f"confirmado SEM: {sorted(LEAK_FIELDS)}")

def collect():
    pk={json.loads(l)['bar_idx']:json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
    rows=[]; nev=0; nev_valid=0; bad=[]
    for fp in sorted(glob.glob(f"{OUTDIR}/stage_a_*.jsonl")):
        for l in open(fp):
            if not l.strip(): continue
            try: r=json.loads(l)
            except: continue
            bi=int(r.get('episode_id')) if str(r.get('episode_id','')).lstrip('-').isdigit() else r.get('bar_idx')
            p=pk.get(bi,{})
            # validar evidências
            ev_results=[]
            for ev in (r.get('positive_context_evidence',[])+r.get('negative_context_evidence',[])):
                ev.setdefault('specialist_id','context_classifier'); ev.setdefault('episode_id',str(bi)); ev.setdefault('causal',True)
                res=validate_evidence(ev,p); nev+=1
                if res['valid']: nev_valid+=1
                else: bad.append((bi,ev.get('factor_used'),';'.join(res['reasons'])[:60]))
                ev_results.append(res['valid'])
            r['_bar_idx']=bi; r['_n_evidence']=len(ev_results); r['_n_valid_evidence']=sum(ev_results)
            r['_label_ok']= r.get('context_label') in LABELS
            rows.append(r)
    with open(f"{D}/l2_bpt_stage_a_context_labels.jsonl","w") as f:
        for r in rows: f.write(json.dumps(r)+"\n")
    from collections import Counter
    print(f"collect: {len(rows)} labels | evidências {nev_valid}/{nev} válidas ({100*nev_valid/max(1,nev):.0f}%)")
    print("distribuição context_label:",dict(Counter(r.get('context_label') for r in rows)))
    print("labels inválidos (fora das 8):",sum(1 for r in rows if not r['_label_ok']))
    if bad: print("ex evidências rejeitadas:",bad[:5])

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--prep",action="store_true");ap.add_argument("--collect",action="store_true");ap.add_argument("--nbatch",type=int,default=7)
    a=ap.parse_args()
    if a.prep: prep(a.nbatch)
    elif a.collect: collect()
    else: print("use --prep ou --collect")
