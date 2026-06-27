#!/usr/bin/env python3
"""DA Engine2 — R-FRONTIER. The discovery engine optimized LABEL precision. Here we ask the only question that
matters for a prop firm: is there ANY 2-3 feature combo (same TOP-16 AUC features, same thresholds) whose TAKEN
set is actually PROFITABLE in let-run R and beats random? Rank ALL combos by avgR and by sumR, with a per-combo
null p-value. Also reports the best by sumR with n>=80 (tradeable frequency). RAW-causal, IN-SAMPLE.
Honest 'best rule' answer. -> _DA_entry2_rfrontier.json"""
import json,random,statistics as st
from pathlib import Path
from itertools import combinations
HERE=Path(__file__).parent
random.seed(11)
HMAX=480; RCAP=20.0
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}; SER={k:v["series"] for k,v in PRIMK.items()}
TIDX={k:{b["t"]:i for i,b in enumerate(s)} for k,s in SER.items()}
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun_long(s,ei,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
for r in ROWS:
    blk=r["block"]; s=SER.get(blk); ti=TIDX.get(blk,{})
    p=ti.get(r["t"]); cj=ti.get(r["cj_t"]); r["_R"]=None
    if s is None or p is None or cj is None or cj>=len(s)-1: continue
    atr=s[p]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr
    r["_R"]=letrun_long(s,cj,entry,sl,atr)
POOL=[r for r in ROWS if r["_R"] is not None]
GLOB_AVG=st.mean(r["_R"] for r in POOL)
print(f"universe avgR={GLOB_AVG:.3f} n={len(POOL)} sumR={sum(r['_R'] for r in POOL):.1f}")
META={'block','t','cj_t','yr','label','is_monforte','is_medfraco','is_bottom'}
NUMF=[k for k in ROWS[0] if k not in META and k!="_R" and isinstance(ROWS[0][k],(int,float))]
def auc(feat):
    vv=[(r[feat],r["is_monforte"]) for r in ROWS if r.get(feat) is not None]
    pos=[v for v,y in vv if y]; neg=[v for v,y in vv if not y]
    if not pos or not neg: return .5
    sv=sorted(vv,key=lambda x:x[0]); vals=[v for v,_ in sv]; ranks=[0]*len(vals); j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        rr=(j+k)/2+1
        for m in range(j,k+1): ranks[m]=rr
        j=k+1
    rsp=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
    return (rsp-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
aucs=sorted(((f,auc(f)) for f in NUMF),key=lambda x:-abs(x[1]-.5))
TOP=[f for f,a in aucs[:16]]; dirn={f:(1 if a>=.5 else -1) for f,a in aucs}
def thr(f,q):
    vals=sorted(r[f] for r in ROWS if r.get(f) is not None); return vals[int(q*len(vals))]
TH={f:(thr(f,0.60) if dirn[f]>0 else thr(f,0.40)) for f in TOP}
def passes(r,f):
    v=r.get(f)
    if v is None: return False
    return v>=TH[f] if dirn[f]>0 else v<=TH[f]
res=[]
for sz in (2,3):
    for cc in combinations(TOP,sz):
        sel=[r for r in POOL if all(passes(r,f) for f in cc)]
        if len(sel)<40: continue
        Rs=[r["_R"] for r in sel]; n=len(Rs); sumR=sum(Rs); avg=sumR/n
        wr=100*sum(1 for x in Rs if x>0)/n
        res.append({"combo":"+".join(cc),"n":n,"WR":round(wr,1),"sumR":round(sumR,1),"avgR":round(avg,3),
                    "mf":sum(r["is_monforte"] for r in sel)})
# null p per combo (avgR vs random same-n)
def null_p(n,obs_avg,K=1500):
    cnt=0
    for _ in range(K):
        rs=random.sample(POOL,n); a=sum(r["_R"] for r in rs)/n
        if a>=obs_avg: cnt+=1
    return cnt/K
res.sort(key=lambda x:-x["avgR"])
print("\n=== TOP 10 combos by avgR (let-run R) ===")
print(f"{'combo':<46}{'n':>5}{'WR':>6}{'sumR':>7}{'avgR':>7}{'mf':>4}{'p':>6}")
for c in res[:10]:
    c["p_avgR"]=null_p(c["n"],c["avgR"])
    print(f"{c['combo']:<46}{c['n']:>5}{c['WR']:>6}{c['sumR']:>7}{c['avgR']:>7}{c['mf']:>4}{c['p_avgR']:>6}")
res2=sorted(res,key=lambda x:-x["sumR"])
print("\n=== TOP 10 combos by sumR ===")
for c in res2[:10]:
    if "p_avgR" not in c: c["p_avgR"]=null_p(c["n"],c["avgR"])
    print(f"{c['combo']:<46}{c['n']:>5}{c['WR']:>6}{c['sumR']:>7}{c['avgR']:>7}{c['mf']:>4}{c['p_avgR']:>6}")
# how many of ALL combos beat universe avgR at p<0.05 (raw, before Bonferroni)
n_beat=sum(1 for c in res if null_p(c["n"],c["avgR"],K=600)<0.05 and c["avgR"]>GLOB_AVG)
print(f"\ncombos tested={len(res)} | combos with avgR>universe AND raw p<0.05 = {n_beat} "
      f"(Bonferroni alpha=0.05/{len(res)}={0.05/len(res):.2e})")
json.dump({"universe_avgR":round(GLOB_AVG,3),"n_combos":len(res),
           "top_by_avgR":res[:10],"top_by_sumR":res2[:10],"n_beat_raw_p05":n_beat},
          open(HERE/"_DA_entry2_rfrontier.json","w"),indent=1)
print("-> _DA_entry2_rfrontier.json")
