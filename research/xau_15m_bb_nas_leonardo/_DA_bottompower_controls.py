#!/usr/bin/env python3
"""DEVIL'S ADVOCATE controls for XAU 15M bottom-power separability (Cris 2026-06-27 attack).
Runs 6 controls against bottom_features.jsonl. Numbers only. RAW-causal, in-sample (no OOS by canon)."""
import json,statistics as st,random
from pathlib import Path
from itertools import combinations
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"bottom_features.jsonl").read_text().splitlines()]
META={'block','t','yr','tier','tier_clean','leg_atr','power_score','session'}
NUMF=[k for k in ROWS[0] if k not in META and isinstance(ROWS[0][k],(int,float))]
def strong3(r): return 0 if r["tier"]=="FRACO" else 1
def strong2(r): return 1 if r["tier"] in ("MONSTRO","FORTE") else 0
def is_medio(r): return r["tier"]=="MEDIO"
BASE3=sum(strong3(r) for r in ROWS)/len(ROWS); BASE2=sum(strong2(r) for r in ROWS)/len(ROWS)

def auc(rows,feat,tgt):
    vv=[(r[feat],tgt(r)) for r in rows if r.get(feat) is not None]
    pos=[v for v,y in vv if y==1]; neg=[v for v,y in vv if y==0]
    if not pos or not neg: return None,0,0
    sv=sorted(vv,key=lambda x:x[0]); vals=[v for v,_ in sv]
    ranks=[0]*len(vals); j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        rr=(j+k)/2+1
        for m in range(j,k+1): ranks[m]=rr
        j=k+1
    rsum_pos=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
    n1=len(pos); n0=len(neg); U=rsum_pos-n1*(n1+1)/2
    return round(U/(n1*n0),3),n1,n0

TOPF=["legpos90","h1_pos","rsi_min8","atr_regime","dist_demand_atr","h1_rsi","atr_compression_pre","dealing_range_pos","h1_eff","vpnode_dist_atr"]
out=[]
P=out.append

# ============ POINT 1: REGIME CONFOUND ============
P("="*70); P("POINT 1 — REGIME CONFOUND (partial out macro_bull / h1_trend)")
P("="*70)
bull=[r for r in ROWS if r.get("macro_bull")==1]
nobull=[r for r in ROWS if r.get("macro_bull")==0]
P(f"macro_bull==1: n={len(bull)}  not-FRACO={sum(strong3(r) for r in bull)/len(bull):.3f}  MON+FORTE={sum(strong2(r) for r in bull)/len(bull):.3f}")
P(f"macro_bull==0: n={len(nobull)} not-FRACO={sum(strong3(r) for r in nobull)/len(nobull):.3f}  MON+FORTE={sum(strong2(r) for r in nobull)/len(nobull):.3f}")
# also h1_trend partition
for tname,subset in (("ALL",ROWS),("macro_bull==1",bull),("macro_bull==0",nobull)):
    P(f"\n-- WITHIN {tname} (n={len(subset)}) AUC not-FRACO / MON+FORTE --")
    P(f"   {'feat':<20}{'auc3':>7}{'auc2':>7}{'n1':>5}{'n0':>5}")
    for f in TOPF:
        a3,n1,n0=auc(subset,f,strong3); a2,_,_=auc(subset,f,strong2)
        P(f"   {f:<20}{str(a3):>7}{str(a2):>7}{n1:>5}{n0:>5}")
# how much is macro_bull/h1_trend itself
a3b,_,_=auc(ROWS,"macro_bull",strong3); a3h,_,_=auc(ROWS,"h1_trend",strong3)
a2b,_,_=auc(ROWS,"macro_bull",strong2); a2h,_,_=auc(ROWS,"h1_trend",strong2)
P(f"\n   macro_bull alone: auc3={a3b} auc2={a2b}   h1_trend alone: auc3={a3h} auc2={a2h}")

# ============ POINT 2: YEAR CONCENTRATION ============
P("\n"+"="*70); P("POINT 2 — YEAR CONCENTRATION (top-3 combos per-year n+rate)")
P("="*70)
TOP14=NUMF  # rebuild combo ranking like engine does (top14 by sep)
res=[]
for f in NUMF:
    a3,_,_=auc(ROWS,f,strong3)
    if a3 is None: continue
    res.append((abs(a3-.5),f))
res.sort(reverse=True); TOP=[f for _,f in res[:14]]
med={f:st.median([r[f] for r in ROWS if r.get(f) is not None]) for f in TOP}
allres={f:auc(ROWS,f,strong3)[0] for f in NUMF}
dirn={f:(1 if allres[f]>=.5 else -1) for f in NUMF}
def sel(rows,combo):
    o=[]
    for r in rows:
        ok=True
        for f in combo:
            v=r.get(f)
            if v is None: ok=False;break
            if dirn[f]>0 and v<med[f]: ok=False;break
            if dirn[f]<0 and v>med[f]: ok=False;break
        if ok:o.append(r)
    return o
combos=[]
for sz in (2,3):
    for c in combinations(TOP,sz):
        s=sel(ROWS,c); n=len(s)
        if n<25: continue
        rate=sum(strong3(r) for r in s)/n
        combos.append((rate,c,s))
combos.sort(reverse=True)
top3=combos[:3]
for rate,c,s in top3:
    P(f"\ncombo {'+'.join(c)}  n={len(s)} rate3={rate:.3f} lift={rate/BASE3:.2f} MON+FORTE={sum(strong2(r) for r in s)/len(s):.3f}")
    for y in (2024,2025,2026):
        sy=[r for r in s if r["yr"]==y]
        if sy:
            P(f"   {y}: n={len(sy):>3} not-FRACO={sum(strong3(r) for r in sy)/len(sy):.3f} MON+FORTE={sum(strong2(r) for r in sy)/len(sy):.3f}  (base3 yr={sum(strong3(r) for r in ROWS if r['yr']==y)/max(1,len([r for r in ROWS if r['yr']==y])):.3f})")
        else:
            P(f"   {y}: n=0")

# ============ POINT 3: SELECTION / NULL PERMUTATION ============
P("\n"+"="*70); P("POINT 3 — SELECTION/MULTIPLE-TESTING (permutation null)")
P("="*70)
def best_combo_lift(rows_local):
    """run same combo search, return best lift & count of combos with lift>=1.5 (n>=25)."""
    base=sum(strong3(r) for r in rows_local)/len(rows_local)
    best=0; cnt15=0
    for sz in (2,3):
        for c in combinations(TOP,sz):
            s=sel(rows_local,c); n=len(s)
            if n<25: continue
            rate=sum(strong3(r) for r in s)/n; lift=rate/base
            if lift>best: best=lift
            if lift>=1.5: cnt15+=1
    return best,cnt15
obs_best,obs_cnt=best_combo_lift(ROWS)
P(f"OBSERVED: best lift={obs_best:.3f}  #combos lift>=1.5 = {obs_cnt}")
K=300; random.seed(42)
null_best=[]; null_cnt=[]
tiers=[r["tier"] for r in ROWS]
for it in range(K):
    perm=tiers[:]; random.shuffle(perm)
    shuf=[dict(r) for r in ROWS]
    for r,tt in zip(shuf,perm): r["tier"]=tt
    # need strong3 over shuffled; reuse sel which depends on features only (dirn/med fixed from real)
    base=sum(strong3(r) for r in shuf)/len(shuf)
    best=0;cnt=0
    for sz in (2,3):
        for c in combinations(TOP,sz):
            s=sel(shuf,c); n=len(s)
            if n<25: continue
            rate=sum(strong3(r) for r in s)/n; lift=rate/base
            if lift>best:best=lift
            if lift>=1.5:cnt+=1
    null_best.append(best); null_cnt.append(cnt)
null_best.sort()
def pct(arr,p): return arr[min(len(arr)-1,int(p*len(arr)))]
P(f"NULL best-lift over K={K}: mean={st.mean(null_best):.3f} p50={pct(null_best,.5):.3f} p95={pct(null_best,.95):.3f} p99={pct(null_best,.99):.3f} max={max(null_best):.3f}")
n_ge=sum(1 for b in null_best if b>=obs_best)
P(f"   empirical p(best>=observed {obs_best:.3f}) = {n_ge}/{K} = {n_ge/K:.4f}")
P(f"NULL #combos lift>=1.5: mean={st.mean(null_cnt):.1f} p95={pct(sorted(null_cnt),.95)} max={max(null_cnt)}   OBSERVED={obs_cnt}")
ncombos_total=sum(1 for sz in (2,3) for c in combinations(TOP,sz))
P(f"   total combos searched (n>=25 subset of {ncombos_total}); Bonferroni note: best combo p must beat 0.05/{ncombos_total}={0.05/ncombos_total:.5f}")

# ============ POINT 4: LABEL LEAK (sweep_reclaim_bars forward) ============
P("\n"+"="*70); P("POINT 4 — LABEL LEAK / LOOK-AHEAD")
P("="*70)
P("build_bottom_features.py L107-110: sweep_reclaim_bars scans range(i+1, i+8) => FORWARD bars after bottom bar i = LOOK-AHEAD.")
P("All other top features (legpos*, h1_*, rsi_min8, atr_*, dist_demand, vpnode) use i-N..i only (causal).")
a3sr,_,_=auc(ROWS,"sweep_reclaim_bars",strong3)
P(f"sweep_reclaim_bars AUC3={a3sr} (in engine top-14, dirn={dirn.get('sweep_reclaim_bars')}).")
# rebuild TOP excluding leaked feature, re-rank combos
TOP_clean=[f for f in TOP if f!="sweep_reclaim_bars"]
P(f"TOP14 with leak: {'sweep_reclaim_bars' in TOP}.  Re-running combo search WITHOUT sweep_reclaim_bars (TOP={len(TOP_clean)}).")
combos_clean=[]
for sz in (2,3):
    for c in combinations(TOP_clean,sz):
        s=sel(ROWS,c); n=len(s)
        if n<25: continue
        rate=sum(strong3(r) for r in s)/n
        combos_clean.append((rate,c,len(s),sum(strong2(r) for r in s)/len(s)))
combos_clean.sort(reverse=True)
P("Top-6 combos WITHOUT leaked feature:")
for rate,c,n,mf in combos_clean[:6]:
    P(f"   {'+'.join(c):<46} n={n:>3} rate3={rate:.3f} lift={rate/BASE3:.2f} MON+FORTE={mf:.2f}")

# ============ POINT 5: EFFECT MAGNITUDE across leave-block folds ============
P("\n"+"="*70); P("POINT 5 — EFFECT MAGNITUDE (AUC spread across 8 leave-block folds)")
P("="*70)
blocks=sorted(set(r["block"] for r in ROWS))
P(f"{len(blocks)} blocks.")
P(f"{'feat':<20}{'fullAUC':>8}{'foldMin':>8}{'foldMax':>8}{'spread':>8}  per-fold")
for f in ["rsi_min8","h1_rsi","atr_compression_pre","legpos90","atr_regime"]:
    full,_,_=auc(ROWS,f,strong3)
    fold=[]
    for blk in blocks:
        g=[r for r in ROWS if r["block"]!=blk]
        a,_,_=auc(g,f,strong3)
        if a is not None: fold.append(a)
    P(f"{f:<20}{str(full):>8}{min(fold):>8.3f}{max(fold):>8.3f}{max(fold)-min(fold):>8.3f}  {[round(x,2) for x in fold]}")
# Also leave-ONE-block-IN (does single block carry it?) -> per-block standalone AUC
P("\nPer-block STANDALONE AUC (does 1 block carry the signal?):")
for f in ["rsi_min8","atr_compression_pre","legpos90"]:
    perblk=[]
    for blk in blocks:
        g=[r for r in ROWS if r["block"]==blk]
        a,n1,n0=auc(g,f,strong3)
        perblk.append((blk,a,n1+n0))
    P(f"  {f}: "+"  ".join(f"{b[5:]}:{a}" for b,a,_ in perblk))

# ============ POINT 6: MEDIO placement (FRACO vs MEDIO hard boundary) ============
P("\n"+"="*70); P("POINT 6 — MEDIO PLACEMENT (FRACO-vs-MEDIO hard boundary)")
P("="*70)
from collections import Counter
P(f"tier counts: {dict(Counter(r['tier'] for r in ROWS))}")
fm=[r for r in ROWS if r["tier"] in ("FRACO","MEDIO")]
def is_med(r): return 1 if r["tier"]=="MEDIO" else 0
fmf=[r for r in ROWS if r["tier"] in ("FRACO","MONSTRO","FORTE")]
def is_strong2t(r): return 1 if r["tier"] in ("MONSTRO","FORTE") else 0
P(f"\nAUC FRACO-vs-MEDIO (hard) and FRACO-vs-MON+FORTE (easy):")
P(f"{'feat':<20}{'F-vs-MED':>10}{'F-vs-MF':>10}")
for f in TOPF:
    am,_,_=auc(fm,f,is_med); ae,_,_=auc(fmf,f,is_strong2t)
    P(f"{f:<20}{str(am):>10}{str(ae):>10}")

rep="\n".join(out); print(rep)
(HERE/"_DA_bottompower_controls.txt").write_text(rep)
print("\n-> _DA_bottompower_controls.txt")
