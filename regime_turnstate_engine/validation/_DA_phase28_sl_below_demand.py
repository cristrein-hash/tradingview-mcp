#!/usr/bin/env python3
"""DEVIL'S ADVOCATE on phase28_intrarange_sl_below_demand.
Adversarial audit, priority order:
 P1 CAUSALITY of RANGE membership + rmin_causal. THE make-or-break.
    box_of(t) uses s['start']<=t<=s['end'] where s['end'] = the ts the RANGE *resolved* (FUTURE at entry).
    Truly-causal test: re-run the FSM (which IS bar-by-bar causal) and ask reg[bi]=='RANGE' AT THE ENTRY BAR.
    Count trades that are 'intra-range' by the completed-segment boundary but were NOT yet RANGE causally at entry.
 P2 per-year base vs causal: sumR/WR/DD/saved/worsened. Concentration.
 P3 convexity: net R lost on winners that 'piorou' vs R gained on 'SALVOU'. Right-tail destruction.
 P4 selection/Bonferroni over the 3x2 grid.
 P5 execution realism: gap-through, risk-in-points dispersion.
ORPHAN-GUARD: saved script under validation/, run once, report."""
import json,csv,io,contextlib,sys,bisect,datetime as dt,statistics as stx
from pathlib import Path
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
# reg[] causal at every bar (the FSM's own output for the reported config)
REG=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
def sim_letrun(bi,entry,sl):
    risk=entry-sl
    if risk<=0: return None,risk
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0,risk
    return (C[end]-entry)/risk,risk
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];box=box_of(t)
    if not box: continue
    i0=bisect.bisect_left(T,box['start']);iE=bisect.bisect_right(T,box['end'])-1
    box_floor=min(L[i0:iE+1])
    rmin_causal=min(L[i0:bi+1])
    a=atr(bi);entry=float(r["entry"]);orig_sl=float(r["sl"])
    tr.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"yr":dt.datetime.utcfromtimestamp(t).year,
               "entry":entry,"orig_sl":orig_sl,"box_floor":box_floor,"rmin_causal":rmin_causal,"atr":a,
               "R_base":round(float(r["letrun_struct"])-COST,2),
               "reg_at_entry":REG[bi],                 # TRULY causal regime at the entry bar
               "box_end":box['end'],"box_start":box['start']})

# ---- P1: CAUSALITY OF RANGE MEMBERSHIP ----
print("="*90)
print("P1  CAUSALITY OF 'INTRA-RANGE' MEMBERSHIP")
print("="*90)
not_yet_range=[x for x in tr if x["reg_at_entry"]!="RANGE"]
entry_after_boxstart=[x for x in tr if x["bi"]>bisect.bisect_left(T,x["box_start"])]
print(f"  intra-range trades (by completed-segment [start,end]) : {len(tr)}")
print(f"  of those, reg[entry_bar] causally == 'RANGE'          : {sum(1 for x in tr if x['reg_at_entry']=='RANGE')}")
print(f"  of those, reg[entry_bar] causally != 'RANGE' (LOOK-AHEAD MEMBERSHIP): {len(not_yet_range)}")
from collections import Counter
print(f"     what were they causally at entry: {dict(Counter(x['reg_at_entry'] for x in not_yet_range))}")
# how far after box start does entry sit (a range only 'exists' as membership once it has resolved)
# also: is box['end'] (resolution) in the FUTURE relative to entry? by construction end>=entry always for members;
# the real test is whether reg[bi] was RANGE at bi. Show a few offenders.
for x in sorted(not_yet_range,key=lambda z:z['bi'])[:15]:
    de=dt.datetime.utcfromtimestamp(x['box_end']).strftime("%Y-%m-%d")
    print(f"     {x['date']} reg@entry={x['reg_at_entry']:5} but box resolves(end)={de}  -> labelled RANGE only after")

# rmin_causal secondary check: is L[bi] settled at entry? entry=close of bar bi -> L[bi] known. OK by construction.
# but rmin uses min(L[i0:bi+1]); i0=bisect(box_start). box_start itself: is the segment START causal?
# In FSM, the RANGE state onset bar is where reg flips to RANGE -> that IS causal. Compare box_start vs first causal RANGE bar.
print("\n  rmin_causal window integrity: box_start vs first bar reg==RANGE in that segment")
def first_range_bar(bstart,bend):
    i=bisect.bisect_left(T,bstart)
    while i<n4 and T[i]<=bend:
        if REG[i]=='RANGE': return i
        i+=1
    return None
mism=0
for s in segs:
    fb=first_range_bar(s['start'],s['end'])
    if fb is None: continue
    if abs(T[fb]-s['start'])>1: mism+=1
print(f"     segments whose json-start != first causal RANGE bar: {mism}/{len(segs)} (0 => start is causal)")

def agg(rs,keyR):
    rs=[x for x in rs if x.get(keyR) is not None];n=len(rs)
    if not n: return "N=0",0,0,0
    rs=sorted(rs,key=lambda x:x["bi"]);s=sum(x[keyR] for x in rs);w=sum(1 for x in rs if x[keyR]>0)
    cum=peak=dd=0
    for x in rs: cum+=x[keyR];peak=max(peak,cum);dd=min(dd,cum-peak)
    return f"N={n:3} WR={100*w/n:3.0f}% sumR={s:+7.1f} avgR={s/n:+5.2f} DD={dd:7.1f}",s,100*w/n,dd

# compute causal-0.1 outcome + risk-in-points
for x in tr:
    rn,risk=sim_letrun(x["bi"],x["entry"],x["rmin_causal"]-0.1*x["atr"])
    x["R_causal01"]=round((rn or 0)-COST,2) if rn is not None else None
    x["risk_pts"]=x["entry"]-(x["rmin_causal"]-0.1*x["atr"])
    x["risk_orig_pts"]=x["entry"]-x["orig_sl"]
# reconciliation
for x in tr:
    rs,_=sim_letrun(x["bi"],x["entry"],x["orig_sl"]);x["R_simorig"]=round((rs or 0)-COST,2)
print("\n  RECONCILIATION base vs sim(orig_sl):",agg(tr,'R_base')[0]," | ",agg(tr,'R_simorig')[0])

# ---- P2: PER-YEAR ----
print("\n"+"="*90);print("P2  PER-YEAR base vs causal-0.1 (concentration)");print("="*90)
yrs=sorted(set(x['yr'] for x in tr))
print(f"  {'yr':4}{'N':>4} | {'base sumR':>10}{'base WR':>8} | {'caus sumR':>10}{'caus WR':>8}{'saved':>7}{'worse':>7}{'dSum':>7}")
for y in yrs:
    sub=[x for x in tr if x['yr']==y]
    _,bs,bw,_=agg(sub,'R_base');_,cs,cw,_=agg(sub,'R_causal01')
    saved=sum(1 for x in sub if x['R_causal01']>0 and x['R_base']<=0)
    worse=sum(1 for x in sub if x['R_causal01']<x['R_base']-0.3)
    print(f"  {y:4}{len(sub):>4} | {bs:>10.1f}{bw:>7.0f}% | {cs:>10.1f}{cw:>7.0f}%{saved:>7}{worse:>7}{cs-bs:>+7.1f}")
_,BS,_,BDD=agg(tr,'R_base');_,CS,_,CDD=agg(tr,'R_causal01')
print(f"  TOTAL base sumR {BS:+.1f} DD {BDD:.1f}  ->  causal sumR {CS:+.1f} DD {CDD:.1f}   (dSum {CS-BS:+.1f})")

# ---- P3: CONVEXITY / RIGHT-TAIL ----
print("\n"+"="*90);print("P3  CONVEXITY: R gained on savers vs R lost on winners");print("="*90)
gained=sum(x['R_causal01']-x['R_base'] for x in tr if x['R_causal01']>x['R_base'])
lost=sum(x['R_base']-x['R_causal01'] for x in tr if x['R_causal01']<x['R_base'])
print(f"  total R gained (trades that improved) : {gained:+.1f}")
print(f"  total R lost   (trades that worsened) : {-lost:+.1f}")
print(f"  NET                                   : {gained-lost:+.1f}")
# biggest winners under base and what happened to them
print("  Top base-winners and their fate under causal SL:")
for x in sorted(tr,key=lambda z:-z['R_base'])[:6]:
    print(f"    {x['date']} base R {x['R_base']:+6.2f} -> causal R {x['R_causal01']:+6.2f}  (risk_pts {x['risk_orig_pts']:.0f}->{x['risk_pts']:.0f})   dR {x['R_causal01']-x['R_base']:+.2f}")
# right tail: sum of R>+3 under each
rt_b=sum(x['R_base'] for x in tr if x['R_base']>3);rt_c=sum(x['R_causal01'] for x in tr if x['R_causal01']>3)
print(f"  right-tail mass (sum R of trades >+3R): base {rt_b:+.1f}  causal {rt_c:+.1f}")
print(f"  max single R:  base {max(x['R_base'] for x in tr):+.2f}  causal {max(x['R_causal01'] for x in tr):+.2f}")

# ---- P4: SELECTION / GRID ----
print("\n"+"="*90);print("P4  GRID (3 buffers x 2 floor defs) — is 0.1-causal cherry-picked?");print("="*90)
for buf in (0.1,0.5,1.0):
    for src,lab in [("box_floor","hindsight-box-floor"),("rmin_causal","causal-runmin")]:
        for x in tr:
            rr,_=sim_letrun(x["bi"],x["entry"],x[src]-buf*x["atr"]);x["_tmp"]=round((rr or 0)-COST,2) if rr is not None else None
        a,s,w,dd=agg(tr,'_tmp')
        print(f"  buf {buf} {lab:22} {a}")

# ---- P5: EXECUTION REALISM ----
print("\n"+"="*90);print("P5  EXECUTION REALISM: risk-in-points dispersion + gap-through");print("="*90)
rp=[x['risk_pts'] for x in tr]
print(f"  risk-in-points causal SL: min {min(rp):.0f} max {max(rp):.0f} median {stx.median(rp):.0f} ratio {max(rp)/max(1,min(rp)):.0f}x")
print(f"  risk-in-points orig   SL: min {min(x['risk_orig_pts'] for x in tr):.0f} max {max(x['risk_orig_pts'] for x in tr):.0f}")
# gap-through: on stopped trades under causal, was there a bar that OPENED below the SL (gap) => fill worse than -1R
gapstops=0;stops=0
for x in tr:
    sl=x['rmin_causal']-0.1*x['atr'];end=min(x['bi']+HZ,n4-1);hit=None
    for j in range(x['bi']+1,end+1):
        if L[j]<=sl: hit=j;break
    if hit is not None:
        stops+=1
        # approximate gap: open of the bar that hit. we only have OHLC via P; use C[hit-1] proxy for prior close vs L
        if C[hit-1]>sl and (sl-L[hit])>0.2*x['atr']:  # closed above SL prior, then pierced deep => slippage risk
            gapstops+=1
print(f"  causal-SL stops: {stops}, of which pierced >0.2ATR beyond SL in one bar (slippage-exposed): {gapstops}")
print("\nDONE.")
