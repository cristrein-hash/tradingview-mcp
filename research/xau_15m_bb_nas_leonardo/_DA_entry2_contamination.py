#!/usr/bin/env python3
"""DA Engine2 test #4 — CONTAMINATION reality. Best combo takes 37 MED/FRACO vs 27 MON/FORTE.
Q: does the rule 'exclude MED/FRACO'? Among TAKEN bottoms only, MON+FORTE share vs base bottom-share.
Is there ANY enrichment of MON+FORTE *within bottoms*, or only vs NONE?
Fisher/chi on 2x2: (taken vs not) x (MF vs MEDFRACO) restricted to is_bottom==1.
-> _DA_entry2_contamination.json"""
import json
from pathlib import Path
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
META={'block','t','cj_t','yr','label','is_monforte','is_medfraco','is_bottom'}
NUMF=[k for k in ROWS[0] if k not in META and isinstance(ROWS[0][k],(int,float))]
def auc(feat,lab="is_monforte"):
    vv=[(r[feat],r[lab]) for r in ROWS if r.get(feat) is not None]
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

def fisher_one_sided(a,b,c,d):
    """one-sided p (enrichment of a in row1) via hypergeometric tail. small counts -> exact."""
    from math import lgamma,exp
    def lcomb(n,k): return lgamma(n+1)-lgamma(k+1)-lgamma(n-k+1)
    r1=a+b; r2=c+d; c1=a+c; c2=b+d; n=a+b+c+d
    def p(k):  # P(X=k) for table with same margins, X = top-left
        return exp(lcomb(c1,k)+lcomb(c2,r1-k)-lcomb(n,r1))
    lo=max(0,r1-c2); hi=min(r1,c1)
    return sum(p(k) for k in range(a,hi+1))

COMBOS=[("reclaim_atr","h1_pos","killzone"),
        ("legpos60","reclaim_atr","killzone"),
        ("pullback_depth","reclaim_atr","killzone")]
OUT={}
TOTMF=sum(r["is_monforte"] for r in ROWS); TOTMFR=sum(r["is_medfraco"] for r in ROWS)
TOTBOT=sum(r["is_bottom"] for r in ROWS)
base_bottom_mf_share=TOTMF/TOTBOT
print(f"Among ALL 197 bottoms: MON+FORTE={TOTMF} MED/FRACO={TOTMFR} -> base MF-share within bottoms={base_bottom_mf_share:.3f}")
for cc in COMBOS:
    name="+".join(cc)
    sel=[r for r in ROWS if all(passes(r,f) for f in cc)]
    botsel=[r for r in sel if r["is_bottom"]]
    mf_in=sum(r["is_monforte"] for r in botsel); mfr_in=sum(r["is_medfraco"] for r in botsel)
    # bottoms NOT taken
    notsel=[r for r in ROWS if r["is_bottom"] and not all(passes(r,f) for f in cc)]
    mf_out=sum(r["is_monforte"] for r in notsel); mfr_out=sum(r["is_medfraco"] for r in notsel)
    share_in=mf_in/(mf_in+mfr_in) if (mf_in+mfr_in) else 0
    share_out=mf_out/(mf_out+mfr_out) if (mf_out+mfr_out) else 0
    # 2x2: rows=[taken,not], cols=[MF,MEDFRACO]; test enrichment of MF among taken bottoms
    p=fisher_one_sided(mf_in,mfr_in,mf_out,mfr_out)
    print(f"\nCOMBO {name}")
    print(f"  taken bottoms: MF={mf_in} MEDFRACO={mfr_in} -> MF-share-within-taken-bottoms={share_in:.3f}")
    print(f"  NOT-taken bottoms: MF={mf_out} MEDFRACO={mfr_out} -> MF-share={share_out:.3f}")
    print(f"  base MF-share within all bottoms={base_bottom_mf_share:.3f}")
    print(f"  enrichment (taken share - base)={share_in-base_bottom_mf_share:+.3f}  Fisher 1-sided p(MF enriched among taken)={p:.3f}")
    print(f"  => does it EXCLUDE MED/FRACO within bottoms? {'YES (MF share up & p<0.05)' if (share_in>base_bottom_mf_share and p<0.05) else 'NO — takes MED/FRACO at ~base rate, no enrichment within bottoms'}")
    OUT[name]={"mf_in":mf_in,"mfr_in":mfr_in,"mf_out":mf_out,"mfr_out":mfr_out,
               "share_in":round(share_in,3),"share_out":round(share_out,3),
               "base_share":round(base_bottom_mf_share,3),"enrichment":round(share_in-base_bottom_mf_share,3),
               "fisher_p":round(p,3)}
json.dump(OUT,open(HERE/"_DA_entry2_contamination.json","w"),indent=1)
print("\n-> _DA_entry2_contamination.json")
