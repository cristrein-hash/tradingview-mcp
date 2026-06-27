#!/usr/bin/env python3
"""DA Engine2 test #1 + #3 — R-OUTCOME (the decisive practical test).
For the TAKEN set of top combos, compute actual let-run trade R (entry=close cj, SL=min low s[p..cj]-0.1ATR,
let-run trail via cf_low, HMAX=480 RCAP=20 — identical engine to build_8atr_dataset.py).
Compare vs (a) ALL 4502, (b) random selections of same n (null), (c) only the matched MON+FORTE.
Per-year too. RAW-causal, IN-SAMPLE. -> _DA_entry2_routcome.json + stdout."""
import json,bisect,random,statistics as st
from pathlib import Path
from itertools import combinations
HERE=Path(__file__).parent
random.seed(42)
HMAX=480; RCAP=20.0

# ---- primitives ----
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
SER={k:v["series"] for k,v in PRIMK.items()}
TIDX={k:{b["t"]:i for i,b in enumerate(s)} for k,s in SER.items()}  # t -> bar idx

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

# ---- candidates ----
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]

def trade_R(r):
    """Compute let-run R for a candidate. p = bar idx of fractal low (s[p]['t']==r['t']), cj = entry bar."""
    blk=r["block"]; s=SER.get(blk)
    if s is None: return None
    ti=TIDX[blk]
    p=ti.get(r["t"]); cj=ti.get(r["cj_t"])
    if p is None or cj is None or cj>=len(s)-1: return None
    atr=s[p]["atr"]
    if not atr: return None
    entry=s[cj]["c"]
    sl=min(x["l"] for x in s[p:cj+1])-0.1*atr
    return letrun_long(s,cj,entry,sl,atr)

# precompute R for ALL candidates (cache)
print("computing R for all 4502 candidates ...")
for r in ROWS:
    r["_R"]=trade_R(r)
VALID=[r for r in ROWS if r["_R"] is not None]
print(f"  valid R computed: {len(VALID)}/{len(ROWS)}")

def stats(sel):
    Rs=[r["_R"] for r in sel if r["_R"] is not None]
    if not Rs: return None
    n=len(Rs); wins=sum(1 for x in Rs if x>0)
    sumR=sum(Rs)
    # maxDD on the equity curve (chronological order by cj_t)
    srt=sorted([r for r in sel if r["_R"] is not None],key=lambda x:x["cj_t"])
    eq=0; peak=0; dd=0
    for r in srt:
        eq+=r["_R"]; peak=max(peak,eq); dd=min(dd,eq-peak)
    return {"n":n,"WR":round(100*wins/n,1),"sumR":round(sumR,1),"avgR":round(sumR/n,3),
            "maxDD":round(dd,1),"mf":sum(r["is_monforte"] for r in sel),
            "medfraco":sum(r["is_medfraco"] for r in sel),
            "none":sum(1 for r in sel if r["label"]=="NONE")}

def byyear(sel):
    out={}
    for y in (2024,2025,2026):
        sub=[r for r in sel if r["yr"]==y]
        s=stats(sub)
        out[y]=s
    return out

# ---- rebuild combo selectors (replicate engine_entry_discovery thresholds) ----
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
def sel_combo(cc): return [r for r in ROWS if all(passes(r,f) for f in cc)]

TOPCOMBOS=[("reclaim_atr","h1_pos","killzone"),
           ("legpos60","reclaim_atr","killzone"),
           ("pullback_depth","reclaim_atr","killzone")]

print("\n"+"="*70)
print("BASELINE: take ALL candidates")
allst=stats(ROWS); print(" ",allst)
print("  by-year:",{y:byyear(ROWS)[y] for y in (2024,2025,2026)})

print("\nMATCHED MON+FORTE only (the 58 true strong bottoms)")
mfsel=[r for r in ROWS if r["is_monforte"]]; print(" ",stats(mfsel))
print("\nMATCHED MED/FRACO only")
print(" ",stats([r for r in ROWS if r["is_medfraco"]]))
print("\nALL bottoms (197)"); print(" ",stats([r for r in ROWS if r["is_bottom"]]))
print("\nNONE only (4305 noise micro-lows)"); print(" ",stats([r for r in ROWS if r["label"]=="NONE"]))

RESULTS={"all":allst,"all_byyear":{str(y):byyear(ROWS)[y] for y in (2024,2025,2026)},
         "matched_mf":stats(mfsel),"matched_medfraco":stats([r for r in ROWS if r["is_medfraco"]]),
         "all_bottoms":stats([r for r in ROWS if r["is_bottom"]]),
         "none":stats([r for r in ROWS if r["label"]=="NONE"]),"combos":{}}

for cc in TOPCOMBOS:
    sel=sel_combo(cc); name="+".join(cc)
    s=stats(sel); n=len(sel)
    print("\n"+"="*70); print(f"COMBO {name}  (n={n})"); print(" ",s)
    by=byyear(sel); print("  by-year:")
    for y in (2024,2025,2026): print(f"    {y}: {by[y]}")
    # NULL: random selections of same n from full universe, compare sumR & avgR
    K=2000; nullsum=[]; nullavg=[]
    pool=[r for r in ROWS if r["_R"] is not None]
    for _ in range(K):
        rs=random.sample(pool,min(n,len(pool)))
        ss=sum(r["_R"] for r in rs); nullsum.append(ss); nullavg.append(ss/len(rs))
    obs=s["sumR"]; obsavg=s["avgR"]
    p_sum=sum(1 for x in nullsum if x>=obs)/K
    p_avg=sum(1 for x in nullavg if x>=obsavg)/K
    print(f"  NULL random same-n (K={K}): mean sumR={st.mean(nullsum):.1f} sd={st.pstdev(nullsum):.1f}"
          f" | obs sumR={obs} p={p_sum:.3f} | obs avgR={obsavg} p_avg={p_avg:.3f}"
          f" | null avgR mean={st.mean(nullavg):.3f}")
    RESULTS["combos"][name]={"overall":s,"byyear":{str(y):by[y] for y in (2024,2025,2026)},
        "null_sumR_mean":round(st.mean(nullsum),1),"null_sumR_sd":round(st.pstdev(nullsum),1),
        "p_sumR":p_sum,"p_avgR":p_avg,"null_avgR_mean":round(st.mean(nullavg),3)}

json.dump(RESULTS,open(HERE/"_DA_entry2_routcome.json","w"),indent=1,default=str)
print("\n-> _DA_entry2_routcome.json")
