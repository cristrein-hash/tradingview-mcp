#!/usr/bin/env python3
"""DA Engine2 test #2 — NULL on precision lift. Permute is_monforte labels K times, re-run the SAME combo
search (same TOP-16 AUC features, same quantile thresholds, same combo enumeration, same selection criteria),
record the best combo's MON+FORTE precision/lift each permutation. Is observed prec 7.3% / lift 5.7x beyond null?
-> _DA_entry2_null_precision.json"""
import json,random,statistics as st
from pathlib import Path
from itertools import combinations
HERE=Path(__file__).parent
random.seed(7)
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
META={'block','t','cj_t','yr','label','is_monforte','is_medfraco','is_bottom'}
NUMF=[k for k in ROWS[0] if k not in META and isinstance(ROWS[0][k],(int,float))]
N=len(ROWS)

def auc_for(labels):
    """AUC of each feature vs given binary label vector; rank-based."""
    out={}
    for feat in NUMF:
        vv=[(ROWS[i][feat],labels[i]) for i in range(N) if ROWS[i].get(feat) is not None]
        pos=[v for v,y in vv if y]; neg=[v for v,y in vv if not y]
        if not pos or not neg: out[feat]=.5; continue
        sv=sorted(vv,key=lambda x:x[0]); vals=[v for v,_ in sv]; ranks=[0]*len(vals); j=0
        while j<len(vals):
            k=j
            while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
            rr=(j+k)/2+1
            for m in range(j,k+1): ranks[m]=rr
            j=k+1
        rsp=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
        out[feat]=(rsp-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
    return out

def thr(f,q):
    vals=sorted(r[f] for r in ROWS if r.get(f) is not None); return vals[int(q*len(vals))]

def best_combo_prec(labels,base):
    aucs=sorted(NUMF,key=lambda f:-abs(auc_cache[f]-.5)) if False else None
    A=auc_for(labels)
    order=sorted(((f,A[f]) for f in NUMF),key=lambda x:-abs(x[1]-.5))
    TOP=[f for f,_ in order[:16]]; dirn={f:(1 if A[f]>=.5 else -1) for f in TOP}
    TH={f:(thr(f,0.60) if dirn[f]>0 else thr(f,0.40)) for f in TOP}
    def passes(r,f):
        v=r.get(f)
        if v is None: return False
        return v>=TH[f] if dirn[f]>0 else v<=TH[f]
    MF=sum(labels); best_prec=0; best_lift=0
    for sz in (2,3):
        for cc in combinations(TOP,sz):
            sel=[i for i in range(N) if all(passes(ROWS[i],f) for f in cc)]
            if not sel: continue
            mf=sum(labels[i] for i in sel); rec=mf/MF if MF else 0
            if mf>=12 and rec>=0.20:
                prec=mf/len(sel)
                if prec>best_prec: best_prec=prec; best_lift=prec/base
    return best_prec,best_lift

# observed
true_lab=[r["is_monforte"] for r in ROWS]
base=sum(true_lab)/N
obs_prec,obs_lift=best_combo_prec(true_lab,base)
print(f"OBSERVED best combo: prec={obs_prec:.4f} lift={obs_lift:.2f} (base={base:.4f})")

K=200
null_prec=[]; null_lift=[]
idx=list(range(N))
for k in range(K):
    perm=true_lab[:]; random.shuffle(perm)
    bp,bl=best_combo_prec(perm,base)
    null_prec.append(bp); null_lift.append(bl)
    if (k+1)%50==0: print(f"  perm {k+1}/{K} ... null best-prec so far mean={st.mean(null_prec):.4f} max={max(null_prec):.4f}")

p_prec=sum(1 for x in null_prec if x>=obs_prec)/K
p_lift=sum(1 for x in null_lift if x>=obs_lift)/K
print(f"\nNULL best-combo precision (K={K}): mean={st.mean(null_prec):.4f} sd={st.pstdev(null_prec):.4f} "
      f"max={max(null_prec):.4f}")
print(f"NULL best-combo lift: mean={st.mean(null_lift):.2f} max={max(null_lift):.2f}")
print(f"observed prec {obs_prec:.4f} -> p={p_prec:.3f} | observed lift {obs_lift:.2f} -> p={p_lift:.3f}")
print("INTERP: this null accounts for the multiple-comparisons search (best-of-many combos per permutation).")
json.dump({"obs_prec":obs_prec,"obs_lift":obs_lift,"base":base,"K":K,
           "null_prec_mean":st.mean(null_prec),"null_prec_sd":st.pstdev(null_prec),"null_prec_max":max(null_prec),
           "null_lift_mean":st.mean(null_lift),"null_lift_max":max(null_lift),
           "p_prec":p_prec,"p_lift":p_lift},open(HERE/"_DA_entry2_null_precision.json","w"),indent=1)
print("-> _DA_entry2_null_precision.json")
