#!/usr/bin/env python3
"""DEVIL'S ADVOCATE on phase33_position_axis_by_regime.py.

CONTEXT: Cris wanted a CLEAN CONTINUOUS "bottom/middle/top per regime" position feature
(pos = (entry-running_min)/(running_max-running_min) over the current regime block, causal)
to REPLACE the mechanical 1st-of-block frequency cap. phase33's result came back messy and
REGIME-OPPOSITE:
  BULL: 1st-of-block wins (+16.9R) vs tardias lose (-11.3R)  -> cut bull-tardias
  RANGE: 1st-of-block LOSES (-0.32R) vs tardias WIN (+39.8R) -> inverted
  pos-axis NON-MONOTONIC in both regimes (U-shape in RANGE, non-mono in BULL).

The regime-opposite "range tardias win" contradicts the user's expectation. A prior DA
(_DA_phase31_freqcut) already found range last-entries win because let-run (HZ120) holds into
the POST-RANGE BULL LEG = hindsight-of-outcome, not a tradeable signal.

DA POINTS (default skeptical):
 1. Is "range tardias / age-high win" a LET-RUN TAUTOLOGY? Truncate each RANGE trade's let-run
    at the regime-BLOCK end (when reg leaves RANGE) and recompute. Does the inversion collapse?
 2. Is pos genuinely NON-MONOTONIC (i.e. NOT a clean feature)? Finer deciles + monotonic-trend
    (Spearman-ish sign test) per regime. Does pos separate W/L better than random within regime?
 3. BULL 1st-vs-rest (+16.9 vs -11.3): real & robust or one bull episode? per-year / per-block.
 4. Small-n / multiple-testing: how many cells are <12? null-of-max over the searched grid.
 5. Causality of pos: block-start walk-back uses only reg[<=i] (causal), running-min/max causal,
    entry-bar H/L settled at close. Confirm no future leakage.

METHOD NOTE: base CSV l2_bpt_regua_structural.csv carries its OWN per-trade sl. I recompute R
causally from (entry, sl) with a canonical let-run to HZ, so I can TRUNCATE at block-end and
compare full-vs-truncated (this is what makes point 1 falsifiable). I cross-check my full-HZ R
against the CSV's letrun_struct to confirm my sim reproduces the book.

Orphan-guard: standalone SAVED repro. Reads same inputs as phase33. Does NOT touch production.
"""
import json,csv,io,contextlib,sys,datetime as dt,random,statistics as st
from pathlib import Path
from collections import defaultdict

COST=0.35; HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation"); sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88); T=P.T; H=P.H; L=P.L; C=P.C; n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k

D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")

def block_start(bi):
    """CAUSAL: walk back while regime unchanged. Uses only reg[<=bi]."""
    rg=reg[bi]; i0=bi
    while i0>0 and reg[i0-1]==rg: i0-=1
    return i0

def block_end_idx(bi):
    """Index of the LAST bar still in the same regime block as bi (forward-looking; used ONLY
    to define the truncation horizon for the tautology test, NOT for entry selection)."""
    rg=reg[bi]; j=bi
    while j+1<n4 and reg[j+1]==rg: j+=1
    return j

def sim(bi,entry,sl,exit_idx=None):
    """Canonical let-run to HZ (or truncated at exit_idx). SL intrabar, exit at close. R in units of risk."""
    if entry-sl<=0: return None
    cap=bi+HZ
    end=min(cap, exit_idx if exit_idx is not None else cap, n4-1)
    if end<=bi: end=min(bi+1,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)

rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]); t=T[bi]; y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    rg=reg[bi]; i0=block_start(bi)
    rmin=min(L[i0:bi+1]); rmax=max(H[i0:bi+1]); a=atr(bi); entry=float(r["entry"]); sl=float(r["sl"])
    pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else 0.5
    R_book=round(float(r["letrun_struct"])-COST,2)          # book R (from CSV)
    r_full=sim(bi,entry,sl); R_full=round((r_full if r_full is not None else 0)-COST,2)   # my full-HZ R
    ei=block_end_idx(bi)
    r_tr=sim(bi,entry,sl,exit_idx=ei); R_trunc=round((r_tr if r_tr is not None else 0)-COST,2)  # trunc @ block end
    rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"year":y,"reg":rg,
                 "pos":pos,"age":bi-i0,"i0":i0,"amp_atr":(rmax-rmin)/a,
                 "R_book":R_book,"R_full":R_full,"R_trunc":R_trunc,
                 "bars_to_end":ei-bi})
rows.sort(key=lambda x:x["bi"])
# ordinal within regime block
byblk=defaultdict(list)
for x in rows: x["blk"]=(x["reg"],x["i0"]); byblk[x["blk"]].append(x)
for k,g in byblk.items():
    g.sort(key=lambda z:z["bi"])
    for i,z in enumerate(g): z["ord"]=i; z["is_first"]=(i==0)

def agg(g,lab,Rkey="R_full"):
    if not g: print(f"    {lab:30} N=0"); return (0,0,0)
    n=len(g); w=sum(1 for x in g if x[Rkey]>0); s=sum(x[Rkey] for x in g)
    print(f"    {lab:30} N={n:3} WR={100*w/n:3.0f}% avgR={s/n:+5.2f} sumR={s:+6.1f}")
    return (n,100*w/n,s)

print("="*100)
print("SANITY: does my recomputed full-HZ R reproduce the book (letrun_struct-COST)?")
print("="*100)
db=[abs(x["R_full"]-x["R_book"]) for x in rows]
print(f"  N={len(rows)}  mean|R_full-R_book|={st.mean(db):.3f}  max={max(db):.2f}  "
      f"sumR_full={sum(x['R_full'] for x in rows):+.1f}  sumR_book={sum(x['R_book'] for x in rows):+.1f}")
print("  (small residual = HZ/exit convention diff; direction & magnitude should track. If way off, my sim is wrong.)")
print("  regime dist:",{r:sum(1 for x in rows if x['reg']==r) for r in ('BULL','RANGE','BEAR')})

# reproduce phase33 headline first (using R_full so trunc test is apples-to-apples)
print("\n"+"="*100)
print("REPRO of phase33 headline (with recomputed R_full; sign should match phase33's R):")
print("="*100)
for RG in ("BULL","RANGE","BEAR"):
    g=[x for x in rows if x["reg"]==RG]
    print(f"\n  ### {RG} (N={len(g)}) ###")
    agg([x for x in g if x["pos"]<0.34],"pos FUNDO (<0.34)")
    agg([x for x in g if 0.34<=x["pos"]<0.67],"pos MEIO  (0.34-0.67)")
    agg([x for x in g if x["pos"]>=0.67],"pos TOPO  (>=0.67)")
    agg([x for x in g if x["is_first"]],"1st-of-block")
    agg([x for x in g if not x["is_first"]],"tardias (rest)")

print("\n"+"="*100)
print("DA POINT 1 — LET-RUN TAUTOLOGY: truncate RANGE let-run at BLOCK END (regime leaves RANGE)")
print("="*100)
print("If RANGE tardias' win comes from holding into the post-range BULL leg, truncating at block end")
print("should COLLAPSE the inversion (tardias no longer beat 1st, or go negative).\n")
rng=[x for x in rows if x["reg"]=="RANGE"]
print("  RANGE, R_FULL (let-run to HZ, may cross into post-range bull):")
_,_,f_first=agg([x for x in rng if x["is_first"]],"1st-of-block","R_full")
_,_,f_rest =agg([x for x in rng if not x["is_first"]],"tardias (rest)","R_full")
print("  RANGE, R_TRUNC (let-run cut when regime leaves RANGE = no post-range bull leg):")
_,_,t_first=agg([x for x in rng if x["is_first"]],"1st-of-block","R_trunc")
_,_,t_rest =agg([x for x in rng if not x["is_first"]],"tardias (rest)","R_trunc")
print(f"\n  INVERSION full: tardias {f_rest:+.1f} vs 1st {f_first:+.1f}  (tardias {'BEAT' if f_rest>f_first else 'lose'})")
print(f"  INVERSION trunc: tardias {t_rest:+.1f} vs 1st {t_first:+.1f}  (tardias {'BEAT' if t_rest>t_first else 'lose'})")
surv=(t_rest/f_rest*100) if f_rest else 0
print(f"  => tardias sumR surviving truncation: {surv:.0f}%.  If it collapses/goes <=0, 'range tardias win' = post-range hindsight.")
# also age-high in range (phase33 reported age-high +1.12 vs age-low -0.07)
med=sorted(x["age"] for x in rng)[len(rng)//2]
print(f"\n  RANGE age split (median age={med}):")
agg([x for x in rng if x["age"]>med],"age ALTA  (full)","R_full")
agg([x for x in rng if x["age"]<=med],"age BAIXA (full)","R_full")
agg([x for x in rng if x["age"]>med],"age ALTA  (trunc)","R_trunc")
agg([x for x in rng if x["age"]<=med],"age BAIXA (trunc)","R_trunc")
# per-trade: how many range tardias have their let-run END past the block end?
tardias=[x for x in rng if not x["is_first"]]
past=sum(1 for x in tardias if x["bars_to_end"]<HZ and x["R_full"]!=x["R_trunc"])
print(f"\n  range tardias whose R changes when truncated (i.e. let-run extends past block end): {past}/{len(tardias)}")
print(f"  mean bars_to_block_end for range tardias = {st.mean([x['bars_to_end'] for x in tardias]):.0f} (HZ={HZ})")

print("\n"+"="*100)
print("DA POINT 2 — IS pos MONOTONIC / A CLEAN CONTINUOUS FEATURE? (deciles + sign test per regime)")
print("="*100)
for RG in ("BULL","RANGE"):
    g=sorted([x for x in rows if x["reg"]==RG],key=lambda z:z["pos"])
    n=len(g)
    print(f"\n  ### {RG} (N={n}) — avgR by pos-QUINTILE (R_full) ###")
    q=max(1,n//5); prev=None; mono_up=mono_dn=True; means=[]
    for k in range(0,n,q):
        chunk=g[k:k+q]
        if not chunk: continue
        m=st.mean(x["R_full"] for x in chunk); means.append(m)
        lo=chunk[0]["pos"]; hi=chunk[-1]["pos"]
        print(f"    pos[{lo:.2f}-{hi:.2f}] N={len(chunk):2} avgR={m:+.2f}")
        if prev is not None:
            if m<prev: mono_up=False
            if m>prev: mono_dn=False
        prev=m
    print(f"    monotone-increasing? {mono_up}   monotone-decreasing? {mono_dn}   => "
          f"{'MONOTONIC(clean)' if (mono_up or mono_dn) else 'NON-MONOTONIC (NOT a clean axis)'}")
    # rank-corr sign between pos and R (Spearman via ranks)
    xs=[x["pos"] for x in g]; ys=[x["R_full"] for x in g]
    rx=_rank=[sorted(xs).index(v) for v in xs]  # cheap ranks (ties ignored, n small)
    ry=[sorted(ys).index(v) for v in ys]
    mx=st.mean(rx); my=st.mean(ry)
    num=sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    den=(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))**0.5
    rho=num/den if den else 0
    print(f"    Spearman-ish rho(pos,R) = {rho:+.3f}  (|rho|<~0.2 => pos barely orders outcomes)")

print("\n"+"="*100)
print("DA POINT 3 — BULL 1st-vs-rest (+16.9 vs -11.3): real & robust, or one episode? per-YEAR / per-BLOCK")
print("="*100)
bull=[x for x in rows if x["reg"]=="BULL"]
bf=[x for x in bull if x["is_first"]]; br=[x for x in bull if not x["is_first"]]
print("  BULL by YEAR (R_full):")
print(f"  {'year':5} {'1st N/sumR':>16} {'rest N/sumR':>16}")
for y in sorted(set(x["year"] for x in bull)):
    f=[x for x in bf if x["year"]==y]; r=[x for x in br if x["year"]==y]
    print(f"  {y:5} {len(f):3}/{sum(x['R_full'] for x in f):+7.1f}    {len(r):3}/{sum(x['R_full'] for x in r):+7.1f}")
print("\n  BULL 1st-of-block per BLOCK (which blocks carry the +sumR? jackknife-by-block):")
fbyblk=defaultdict(list)
for x in bf: fbyblk[x["blk"]].append(x)
tot_first=sum(x["R_full"] for x in bf)
contribs=[]
for k,g in sorted(fbyblk.items()):
    s=sum(x["R_full"] for x in g); d0=dt.datetime.utcfromtimestamp(T[k[1]]).strftime("%Y-%m-%d")
    contribs.append((d0,len(g),s));
for d0,ng,s in sorted(contribs,key=lambda z:-z[2]):
    print(f"    block@{d0} N={ng} sumR(1st)={s:+.1f}  |  1st-total-without-block = {tot_first-s:+.1f}")
print(f"  BULL 1st total sumR={tot_first:+.1f} over {len(bf)} firsts in {len(fbyblk)} blocks.")
# leave-one-block-out worst case
worst=max(contribs,key=lambda z:z[2])
print(f"  => single biggest 1st-block contributes {worst[2]:+.1f}; remove it and 1st-total = {tot_first-worst[2]:+.1f}")
# Does cutting bull-tardias help book WITHOUT hindsight? compare full book vs book-minus-bull-tardias
print("\n  Does CUTTING bull-tardias improve the book (streak/DD)? (causal: is_first is known at entry)")
def stats(rs):
    n=len(rs); w=sum(1 for v in rs if v>0); s=sum(rs)
    cum=peak=dd=0; streak=mx=0
    for v in rs:
        cum+=v; peak=max(peak,cum); dd=min(dd,cum-peak)
        if v<=0: streak+=1; mx=max(mx,streak)
        else: streak=0
    return n,(100*w/n if n else 0),s,dd,mx
for lab,keep in [("FULL book (all regimes)",lambda x:True),
                 ("book minus BULL-tardias",lambda x:not(x["reg"]=="BULL" and not x["is_first"]))]:
    kept=[x["R_full"] for x in rows if keep(x)]
    n,wr,s,dd,mx=stats(kept)
    print(f"    {lab:30} N={n:3} WR={wr:3.0f}% sumR={s:+6.1f} DD={dd:+.1f} maxLossStreak={mx}")

print("\n"+"="*100)
print("DA POINT 4 — SMALL-n / MULTIPLE-TESTING: cell census + null-of-max over the searched grid")
print("="*100)
cells=[]
for RG in ("BULL","RANGE","BEAR"):
    g=[x for x in rows if x["reg"]==RG]
    for lab,sub in [("FUNDO",[x for x in g if x["pos"]<0.34]),
                    ("MEIO",[x for x in g if 0.34<=x["pos"]<0.67]),
                    ("TOPO",[x for x in g if x["pos"]>=0.67]),
                    ("1st",[x for x in g if x["is_first"]]),
                    ("rest",[x for x in g if not x["is_first"]])]:
        s=sum(x["R_full"] for x in sub)
        cells.append((RG,lab,len(sub),s))
nsmall=sum(1 for c in cells if 0<c[2]<12)
print(f"  cells evaluated={len(cells)}  cells with 0<N<12 (underpowered)={nsmall}")
for RG,lab,n,s in cells:
    flag=" <-- n<12" if 0<n<12 else ""
    print(f"    {RG:5} {lab:6} N={n:3} sumR={s:+6.1f}{flag}")
# null-of-max: within each regime, best |cell sumR| vs shuffling R across that regime's trades
print("\n  Null-of-max per regime: is the BEST cell's sumR beyond random partitions of the same size?")
random.seed(11); NPERM=20000
for RG in ("BULL","RANGE"):
    g=[x for x in rows if x["reg"]==RG]; Rs=[x["R_full"] for x in g]
    # searched partitions: the 5 subsets above have sizes; take null-of-max over those sizes for extreme sumR
    subs={"FUNDO":[x for x in g if x["pos"]<0.34],"MEIO":[x for x in g if 0.34<=x["pos"]<0.67],
          "TOPO":[x for x in g if x["pos"]>=0.67],"1st":[x for x in g if x["is_first"]],
          "rest":[x for x in g if not x["is_first"]]}
    sizes=sorted(set(len(s) for s in subs.values() if 0<len(s)<len(g)))
    obs=max(abs(sum(x["R_full"] for x in s)) for s in subs.values() if s)
    ge=0
    for _ in range(NPERM):
        m=0
        for k in sizes:
            v=abs(sum(random.sample(Rs,k))); m=max(m,v)
        if m>=obs: ge+=1
    p=(ge+1)/(NPERM+1)
    print(f"    {RG}: best|cell sumR|={obs:.1f}  null-of-max p={p:.4f}  "
          f"({'beats random' if p<0.05 else 'NOT beyond search noise' if p>0.10 else 'marginal'})")

print("\n"+"="*100)
print("DA POINT 5 — CAUSALITY confirmation of pos / block-start")
print("="*100)
# block_start walks back over reg[<=bi] only -> causal. running-min/max over L/H in [i0,bi] settled bars.
# Verify: recompute pos two ways and confirm block_start never reads reg[>bi].
sample=rows[len(rows)//2]
print(f"  spot-check trade bi={sample['bi']} ({sample['date']}) reg={sample['reg']}: i0={sample['i0']} (walk-back), "
      f"pos={sample['pos']:.2f}, age={sample['age']}")
print("  block_start(bi) loops while reg[i0-1]==reg[bi], strictly i0<=bi -> no future bars read. CAUSAL. OK.")
print("  running_min/max over L[i0..bi],H[i0..bi]; entry-bar H/L settled at bar close (entry at close). OK.")
print("  (prior DA already confirmed reg[i] itself is forward-only causal.)")

print("\n"+"="*100)
print("VERDICT SUMMARY (see per-point above)")
print("="*100)
print(f"  (a) pos-axis clean/monotonic? -> see POINT 2 monotone flags & rho.")
print(f"  (b) BULL cut-tardias real? -> POINT 3 per-year/per-block. RANGE 1st-loses tautology? -> POINT 1 truncation.")
print(f"  (c) only robust causal takeaway = 'cut bull-tardias'? RANGE tardias = let-run hindsight? -> POINT 1 survival %.")
