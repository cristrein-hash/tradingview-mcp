#!/usr/bin/env python3
"""REGIME/CONTEXT/FUEL v1 — LAYERS 2-4. DIAGNÓSTICO. Sem outcome como predicado. Sem engine/produção.
Layer2 A/B/C; Layer3 univariado+pairwise+arvore(prof<=3,folha>=5); Layer4 split temporal+reverso+shuffle-null."""
import json,csv,os,bisect,math,statistics as st
from collections import Counter
RR="repro_recovery";D="results"
random_seed=20260621
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
mat={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
cris={r['plot_id']:r['cris_verdict'] for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0_cris_verdicts.csv"))}
def fn(v):
    try:return float(v)
    except:return None
# externas causais D-1
def load_daily(p):
    rows=[json.loads(l) for l in open(p) if json.loads(l).get('ts')];rows.sort(key=lambda r:r['ts']);return rows
extB=load_daily("../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl")
extD=load_daily("../../../../strategies/candidates/regime_classifier_v3/xau_daily_with_features.jsonl")
extL1=load_daily("../../../../core/regime_l1/regime_l1_v4_classifications.jsonl")
def clk(rows,ed):
    dates=[r['ts'] for r in rows];i=bisect.bisect_left(dates,ed)-1;return rows[i] if i>=0 else None
STATE_NUM={'BULL':1,'TRANSITION':0,'BEAR':-1,'NONE':0,'UNKNOWN':0}
def ext_feats(ep):
    ed=pk[ep]['datetime'][:10];rB=clk(extB,ed);rD=clk(extD,ed);rL=clk(extL1,ed)
    f={}
    if rB:
        f['ext_regimeB_state']=STATE_NUM.get(rB.get('v3_state'),0)
        f['ext_regimeB_combined_score']=fn(rB.get('combined_score'))
        f['ext_regimeB_macro_broken']=1 if rB.get('macro_broken') else 0
        f['ext_regimeB_cascade']=fn(rB.get('cascade_score'))
        f['ext_regimeB_dd13w']=fn(rB.get('drawdown_pct_13w'))
    if rL: f['ext_regimeL1']=STATE_NUM.get(rL.get('regime_l1_v4'),0)
    if rD: f['ext_daily_slope20']=fn(rD.get('slope_20_pct'));f['ext_daily_rsi14']=fn(rD.get('rsi_14'))
    return f

# ---- LAYER 2: A/B/C ----
def final(pid):
    c=cris.get(pid)
    if c: return 'PROTECT' if c.startswith('PROTECT') else('BLOCK' if c.startswith('BLOCK') else('REVIEW' if c.startswith('REVIEW') else('TRANSFORM' if c.startswith('TRANSFORM') else mat[pid]['visual_verdict'])))
    return mat[pid]['visual_verdict']
C_NAMED={'T34','T36','S39','S19','T27','S14'}  # ambiguos puros (T40->B must-block; reportado)
A=[p for p in mat if p.startswith('S') and final(p)=='PROTECT' and p not in C_NAMED]
B=[p for p in mat if p.startswith('T') and final(p)=='BLOCK' and p not in C_NAMED]
Cset=[p for p in mat if p in C_NAMED or final(p) in('REVIEW','TRANSFORM')]
def ep(p):return int(mat[p]['episode_id'])
print(f"LAYER2: A(bull-cortado)={len(A)} B(bear-aceito)={len(B)} C(ambiguo,fora-fit)={len(Cset)}")
print(f"  A={sorted(A,key=lambda x:int(x[1:]))}\n  B={sorted(B,key=lambda x:int(x[1:]))}\n  C={sorted(Cset,key=lambda x:(x[0],int(x[1:])))}")

# feature matrix (packet numerics + externas) — NUNCA outcome
def feats(p):
    e=ep(p);pp=pk[e];f={}
    for k,v in pp.items():
        if k.startswith('_') or k in('bar_idx','ts','datetime','episode_id','price'): continue
        fv=fn(v)
        if fv is not None: f[k]=fv
    f.update(ext_feats(e))
    # interações causais (anti-erro: legpos/dist_supply condicionais)
    ls=f.get('legpos90');mom=f.get('trend_30_atr')
    if ls is not None and mom is not None: f['INT_legpos90_x_trend30']=ls*mom/100
    dsup=f.get('dist_4h_supply_low_atr');ovh=1 if pk[e].get('has_4h_supply_overhead')=='yes' else 0
    if dsup is not None: f['INT_distsupply_x_overhead']=dsup*ovh   # supply colada SÓ conta se há overhead
    f['has_overhead']=ovh
    f['supply_broken_before']=1 if pk[e].get('supply_broken_before')=='yes' else 0
    return f
FA=[feats(p) for p in A];FB=[feats(p) for p in B]
ALLK=sorted(set().union(*[set(f) for f in FA+FB]))

# ---- LAYER 3: univariado (effect-size + AUC + best threshold) ----
def vals(F,k):return [f[k] for f in F if k in f]
def auc(a,b):  # prob(rand a> rand b)
    if not a or not b:return 0.5
    w=sum((1 if x>y else 0.5 if x==y else 0) for x in a for y in b);return w/(len(a)*len(b))
def best_thr(a,b):  # threshold que melhor separa A(bull) de B; acc balanceada
    allv=sorted(set(a+b));best=(0.5,None,None)
    for t in allv:
        # A>=t bull
        accA=sum(1 for x in a if x>=t)/len(a);accB=sum(1 for x in b if x<t)/len(b);ba=(accA+accB)/2
        if ba>best[0]:best=(ba,t,'A>=t')
        accA2=sum(1 for x in a if x<t)/len(a);accB2=sum(1 for x in b if x>=t)/len(b);ba2=(accA2+accB2)/2
        if ba2>best[0]:best=(ba2,t,'A<t')
    return best
uni=[]
for k in ALLK:
    a,b=vals(FA,k),vals(FB,k)
    if len(a)<5 or len(b)<5:continue
    ma,mb=st.median(a),st.median(b);pooled=(st.pstdev(a)+st.pstdev(b))/2 or 1;es=abs(ma-mb)/pooled
    ar=auc(a,b);ba,thr,dir=best_thr(a,b)
    uni.append(dict(feature=k,n_A=len(a),n_B=len(b),median_A=round(ma,3),median_B=round(mb,3),effect_size=round(es,2),
                    AUC=round(ar,3),bal_acc=round(ba,3),threshold=round(thr,3) if thr is not None else None,rule_dir=dir))
uni.sort(key=lambda x:-x['bal_acc'])
with open(f"{D}/l2_bpt_regime_v1_feature_separation_full.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['feature','n_A','n_B','median_A','median_B','effect_size','AUC','bal_acc','threshold','rule_dir']);w.writeheader();w.writerows(uni)
print(f"\nLAYER3 univariado: {len(uni)} features -> top 12 por bal_acc:")
for r in uni[:12]:print(f"  {r['feature']:<30} ba={r['bal_acc']} AUC={r['AUC']} es={r['effect_size']} medA={r['median_A']} medB={r['median_B']} [{r['rule_dir']} {r['threshold']}]")

# ---- LAYER 3: pairwise (AND de 2 top features) ----
top=[r['feature'] for r in uni[:8]]
def rule_pred(f,k,thr,dir): 
    if k not in f:return None
    return (f[k]>=thr) if dir=='A>=t' else (f[k]<thr)
thrmap={r['feature']:(r['threshold'],r['rule_dir']) for r in uni}
pw=[]
for i in range(len(top)):
    for j in range(i+1,len(top)):
        k1,k2=top[i],top[j];t1,d1=thrmap[k1];t2,d2=thrmap[k2]
        # AND: bull se ambos apontam bull
        accA=sum(1 for f in FA if rule_pred(f,k1,t1,d1) and rule_pred(f,k2,t2,d2))/len(FA)
        accB=sum(1 for f in FB if not(rule_pred(f,k1,t1,d1) and rule_pred(f,k2,t2,d2)))/len(FB)
        pw.append(dict(rule=f"{k1}[{d1}{t1}] AND {k2}[{d2}{t2}]",recall_A=round(accA,3),block_B=round(accB,3),bal=round((accA+accB)/2,3)))
pw.sort(key=lambda x:-x['bal'])
with open(f"{D}/l2_bpt_regime_v1_pairwise.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['rule','recall_A','block_B','bal']);w.writeheader();w.writerows(pw[:20])
print(f"\nLAYER3 pairwise top 5:")
for r in pw[:5]:print(f"  {r['rule']}  recallA={r['recall_A']} blockB={r['block_B']} bal={r['bal']}")

# ---- LAYER 3: arvore greedy prof<=3 folha>=5 ----
def gini(la,lb):
    n=la+lb;return 0 if n==0 else 1-(la/n)**2-(lb/n)**2
def best_split(items):  # items=[(featdict,label A=1/B=0)]
    base=None;keys=set().union(*[set(f) for f,_ in items])
    bestg=1e9;bestrule=None
    for k in keys:
        vs=sorted(set(f[k] for f,_ in items if k in f))
        for t in vs:
            L=[(f,y) for f,y in items if k in f and f[k]<t];Rr=[(f,y) for f,y in items if k in f and f[k]>=t]
            if len(L)<5 or len(Rr)<5:continue
            g=(len(L)*gini(sum(y for _,y in L),sum(1-y for _,y in L))+len(Rr)*gini(sum(y for _,y in Rr),sum(1-y for _,y in Rr)))/len(items)
            if g<bestg:bestg=g;bestrule=(k,t)
    return bestrule,bestg
items=[(f,1) for f in FA]+[(f,0) for f in FB]
tree_rows=[]
def grow(items,depth,path):
    a=sum(y for _,y in items);b=len(items)-a
    if depth>=3 or a==0 or b==0 or len(items)<10:
        tree_rows.append(dict(path=' & '.join(path) or 'ROOT',n=len(items),A=a,B=b,purity=round(max(a,b)/len(items),2)));return
    rule,g=best_split(items)
    if not rule:tree_rows.append(dict(path=' & '.join(path) or 'ROOT',n=len(items),A=a,B=b,purity=round(max(a,b)/len(items),2)));return
    k,t=rule
    grow([(f,y) for f,y in items if k in f and f[k]<t],depth+1,path+[f"{k}<{round(t,2)}"])
    grow([(f,y) for f,y in items if k in f and f[k]>=t],depth+1,path+[f"{k}>={round(t,2)}"])
grow(items,0,[])
with open(f"{D}/l2_bpt_regime_v1_tree_rules.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['path','n','A','B','purity']);w.writeheader();w.writerows(tree_rows)
print(f"\nLAYER3 árvore (prof<=3,folha>=5): {len(tree_rows)} folhas")
for r in tree_rows:print(f"  [{r['A']}A/{r['B']}B pur={r['purity']}] {r['path']}")

# ---- LAYER 4: shuffle-null (best univariate bal_acc vs labels permutados) ----
import random;random.seed(random_seed)
bestfeat=uni[0]['feature'];real_ba=uni[0]['bal_acc']
pool=vals(FA,bestfeat)+vals(FB,bestfeat);na=len(vals(FA,bestfeat))
null_ba=[]
for _ in range(2000):
    random.shuffle(pool);a=pool[:na];b=pool[na:]
    null_ba.append(best_thr(a,b)[0])
p_null=sum(1 for x in null_ba if x>=real_ba)/len(null_ba)
print(f"\nLAYER4 shuffle-null (feature top '{bestfeat}' ba={real_ba}): null mediana={round(st.median(null_ba),3)} p95={round(sorted(null_ba)[1900],3)} | P(null>=real)={p_null}")

# ---- LAYER 4: split temporal ----
def yr(p):return mat[p]['datetime'][:4]
def split_eval(trainA,trainB,testA,testB):
    if len(trainA)<5 or len(trainB)<5 or not testA or not testB:return None
    FtrA=[feats(p) for p in trainA];FtrB=[feats(p) for p in trainB]
    # refita best single feature no train
    best=(0,None,None,None)
    for k in ALLK:
        a=[f[k] for f in FtrA if k in f];b=[f[k] for f in FtrB if k in f]
        if len(a)<5 or len(b)<5:continue
        ba,t,d=best_thr(a,b)
        if ba>best[0]:best=(ba,k,t,d)
    ba,k,t,d=best
    if k is None:return None
    FteA=[feats(p) for p in testA];FteB=[feats(p) for p in testB]
    accA=sum(1 for f in FteA if rule_pred(f,k,t,d))/len(FteA);accB=sum(1 for f in FteB if not rule_pred(f,k,t,d))/len(FteB)
    return dict(train_feature=k,thr=round(t,3),dir=d,train_ba=round(ba,3),test_recallA=round(accA,3),test_blockB=round(accB,3),test_ba=round((accA+accB)/2,3))
early=lambda p:yr(p)<'2024';late=lambda p:yr(p)>='2024'
sp=[]
r1=split_eval([p for p in A if early(p)],[p for p in B if early(p)],[p for p in A if late(p)],[p for p in B if late(p)])
if r1:r1['split']='train2020-23/test2024-26';sp.append(r1)
r2=split_eval([p for p in A if late(p)],[p for p in B if late(p)],[p for p in A if early(p)],[p for p in B if early(p)])
if r2:r2['split']='train2024-26/test2020-23(reverso)';sp.append(r2)
with open(f"{D}/l2_bpt_regime_v1_heldout.csv","w",newline="") as f:
    if sp:
        w=csv.DictWriter(f,fieldnames=['split','train_feature','thr','dir','train_ba','test_recallA','test_blockB','test_ba']);w.writeheader();w.writerows(sp)
print(f"\nLAYER4 split temporal:")
for r in sp:print(f"  {r['split']}: feat={r['train_feature']} train_ba={r['train_ba']} -> TEST ba={r['test_ba']} (recallA={r['test_recallA']} blockB={r['test_blockB']})")
nA_e=sum(1 for p in A if early(p));nA_l=sum(1 for p in A if late(p));nB_e=sum(1 for p in B if early(p));nB_l=sum(1 for p in B if late(p))
print(f"  n por bloco: A early={nA_e} late={nA_l} | B early={nB_e} late={nB_l}  {'(PEQUENO — held-out frágil)' if min(nA_e,nA_l,nB_e,nB_l)<5 else ''}")

# save sets
for nm,S in [('setA',A),('setB',B),('setC',Cset)]:
    with open(f"{D}/l2_bpt_regime_v1_{nm}.csv","w",newline="") as f:
        w=csv.writer(f);w.writerow(['plot_id','episode_id','datetime','stage_a','final_verdict'])
        for p in sorted(S,key=lambda x:(x[0],int(x[1:]))):w.writerow([p,ep(p),mat[p]['datetime'][:10],mat[p]['stage_a'],final(p)])
print("\nsets A/B/C salvos. LAYERS 2-4 OK.")
