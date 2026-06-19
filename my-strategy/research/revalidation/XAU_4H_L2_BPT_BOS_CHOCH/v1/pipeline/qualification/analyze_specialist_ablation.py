#!/usr/bin/env python3
"""FASE 2B — ablation/contribuição marginal dos 10 especialistas. DIAGNÓSTICO APENAS (outcome pós-hoc).
NÃO cria aggregator, NÃO cria decisão, NÃO retuna, NÃO promove regra. Lê: ablation matrix + net_reads
(specialist_out) + outcomes + old decisions + Stage A labels. Produz as 5 CSVs do bloco."""
import json,csv,glob,math,os
from collections import Counter,defaultdict
D="results"
mat={(int(r['episode_id']),r['specialist_id']):r for r in csv.DictReader(open(f"{D}/l2_bpt_specialist_ablation_ready_matrix.csv"))}
netread={}
for fp in glob.glob(f"{D}/specialist_out/*.jsonl"):
    fam=os.path.basename(fp)[:-6]
    for l in open(fp):
        if l.strip():
            r=json.loads(l); bi=int(r['episode_id']) if str(r['episode_id']).lstrip('-').isdigit() else r.get('bar_idx')
            netread[(bi,fam)]=r.get('net_read')
out={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_decisions_merged.csv"))}
sa={int(json.loads(l)['_bar_idx']):json.loads(l).get('context_label') for l in open(f"{D}/l2_bpt_stage_a_context_labels.jsonl")}
SPEC=sorted(set(k[1] for k in mat))
EP=sorted(set(k[0] for k in mat if k[0] in out))
def R(i): return float(out[i]['realR'])
def win(i): return out[i]['exitype'].startswith('WIN')
def stance(i,s):  # supportive/hostile/neutral
    return netread.get((i,s),'neutral')
def veto(i,s): return int(mat.get((i,s),{}).get('veto_count','0') or 0)>0
def review(i,s): return int(mat.get((i,s),{}).get('review_flag_count','0') or 0)>0
def mean(xs): return sum(xs)/len(xs) if xs else 0.0
def sd(xs):
    if len(xs)<2: return 0.0
    m=mean(xs); return math.sqrt(sum((x-m)**2 for x in xs)/(len(xs)-1))
def cohend(a,b):
    if len(a)<2 or len(b)<2: return 0.0
    na,nb=len(a),len(b); sp=math.sqrt(((na-1)*sd(a)**2+(nb-1)*sd(b)**2)/(na+nb-2)) if na+nb>2 else 0
    return (mean(a)-mean(b))/sp if sp else 0.0

# ---- TAREFA 1: contribuição marginal ----
with open(f"{D}/l2_bpt_specialist_marginal_contribution.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['specialist','n_cov','avgR_sup','n_sup','avgR_hos','n_hos','avgR_neu','n_neu',
        'avgR_veto','n_veto','avgR_review','n_review','WR_sup','WR_hos','diff_sup_minus_hos','cohend_sup_hos',
        'diff_veto_minus_nonveto','CI95_sup','min_bucket_n'])
    for s in SPEC:
        sup=[R(i) for i in EP if stance(i,s)=='supportive']; hos=[R(i) for i in EP if stance(i,s)=='hostile']
        neu=[R(i) for i in EP if stance(i,s)=='neutral']
        vet=[R(i) for i in EP if veto(i,s)]; nonvet=[R(i) for i in EP if not veto(i,s)]
        rev=[R(i) for i in EP if review(i,s)]
        wrs=100*mean([1 if win(i) else 0 for i in EP if stance(i,s)=='supportive']) if sup else 0
        wrh=100*mean([1 if win(i) else 0 for i in EP if stance(i,s)=='hostile']) if hos else 0
        ci= 1.96*sd(sup)/math.sqrt(len(sup)) if len(sup)>1 else 0
        w.writerow([s,len(EP),round(mean(sup),3),len(sup),round(mean(hos),3),len(hos),round(mean(neu),3),len(neu),
            round(mean(vet),3),len(vet),round(mean(rev),3),len(rev),round(wrs),round(wrh),
            round(mean(sup)-mean(hos),3),round(cohend(sup,hos),2),round(mean(vet)-mean(nonvet),3),
            f"[{mean(sup)-ci:.2f},{mean(sup)+ci:.2f}]",min(len(sup),len(hos),len(neu))])

# ---- TAREFA 2: redundância ----
def enc(i,s): return {'supportive':1,'neutral':0,'hostile':-1}.get(stance(i,s),0)
def corr(a,b):
    n=len(a); ma,mb=mean(a),mean(b); va=sd(a);vb=sd(b)
    if va==0 or vb==0: return 0.0
    return sum((a[k]-ma)*(b[k]-mb) for k in range(n))/((n-1)*va*vb)
vecs={s:[enc(i,s) for i in EP] for s in SPEC}
vetoset={s:set(i for i in EP if veto(i,s)) for s in SPEC}
decfac={s:Counter() for s in SPEC}
for (i,s),r in mat.items():
    for fx in (r.get('decisive_factors') or '').split('|'):
        if fx: decfac[s][fx]+=1
def MI(xs,ys):
    n=len(xs);jc=Counter(zip(xs,ys));xc=Counter(xs);yc=Counter(ys);mi=0
    for (x,y),c in jc.items():
        pxy=c/n;px=xc[x]/n;py=yc[y]/n; mi+=pxy*math.log2(pxy/(px*py))
    hx=-sum((c/n)*math.log2(c/n) for c in xc.values())
    return mi/hx if hx else 0
salab=[sa.get(i) for i in EP]
with open(f"{D}/l2_bpt_specialist_redundancy_matrix.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['specialist_A','specialist_B','stance_corr','veto_jaccard','decisive_factor_overlap'])
    for a in SPEC:
        for b in SPEC:
            if a>=b: continue
            jac=len(vetoset[a]&vetoset[b])/max(1,len(vetoset[a]|vetoset[b]))
            fa,fb=set(decfac[a]),set(decfac[b]); fov=len(fa&fb)/max(1,len(fa|fb))
            w.writerow([a,b,round(corr(vecs[a],vecs[b]),2),round(jac,2),round(fov,2)])
    w.writerow([])
    w.writerow(['specialist','NMI_stance_vs_StageA_label','interpretacao'])
    for s in SPEC:
        st=[stance(i,s) for i in EP]; nmi=MI(st,salab)
        w.writerow([s,round(nmi,2),'eco do Stage A se alto' if nmi>0.25 else 'independente do Stage A'])

# ---- TAREFA 3: leave-one-out ----
def score(i,specs): return sum({'supportive':1,'neutral':0,'hostile':-1}[stance(i,s)] - (2 if veto(i,s) else 0) - (0.5 if review(i,s) else 0) for s in specs)
def pointbis(specs):  # corr(score, win) — separação winners/losers
    sc=[score(i,specs) for i in EP]; wn=[1 if win(i) else 0 for i in EP]; return corr(sc,wn)
def avgR_topq(specs):  # avgR do quartil-top do score vs bottom (separação por R)
    sc=sorted(((score(i,specs),R(i)) for i in EP),reverse=True); q=len(sc)//4
    return mean([r for _,r in sc[:q]])-mean([r for _,r in sc[-q:]])
base_pb=pointbis(SPEC); base_sep=avgR_topq(SPEC)
with open(f"{D}/l2_bpt_specialist_leave_one_out.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['removed_specialist','pointbis_corr_score_win','delta_vs_all','avgR_topq_minus_botq','delta_sep','verdict'])
    w.writerow(['<none/all>',round(base_pb,3),0,round(base_sep,3),0,'baseline'])
    for s in SPEC:
        rest=[x for x in SPEC if x!=s]; pb=pointbis(rest); sep=avgR_topq(rest)
        dpb=pb-base_pb; dsep=sep-base_sep
        verdict='ESSENTIAL(remover piora)' if dsep<-0.05 else ('NOISY(remover melhora)' if dsep>0.05 else 'neutro')
        w.writerow([s,round(pb,3),round(dpb,3),round(sep,3),round(dsep,3),verdict])
print("WROTE marginal_contribution, redundancy_matrix, leave_one_out")
print(f"baseline pointbis(score,win)={base_pb:.3f} | avgR topq-botq={base_sep:.3f}")
