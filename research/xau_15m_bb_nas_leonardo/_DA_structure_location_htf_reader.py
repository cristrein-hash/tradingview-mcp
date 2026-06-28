#!/usr/bin/env python3
"""STRUCTURE / LOCATION / HTF-DEMAND QUALITY contextual reader (Cris 2026-06-28).
Paradigm: broad convergent contextual reading for XAU 15M LONG bottom QUALIFICATION (NOT single-feature AUC mining).
Goal: find convergent rules that RISK-SHAPE the profitable fractal-low universe (raise avgR, cut DD, avoid knives).

This script ONLY inspects DISTRIBUTIONS to calibrate thresholds. The deterministic harness (engine3_routcome.py)
is the official R measurer. Here R is recomputed with the SAME ruler purely to read which structural/location/
HTF-demand-quality contexts concentrate avgR / good outcomes — it is calibration, not the final verdict.

R ruler (identical to engine3_routcome.py): entry=close cj; SL=min low s[p..cj]-0.1ATR; let-run trailing fractal-low,
R1-armed; HMAX=480; RCAP=20; floor -1.0. Plus NEW derived HTF-demand QUALITY features from raw htf_primitives zones:
  - freshness (cj_t - born_t in HTF bars) of the nearest demand below
  - virgin proxy (zone not re-touched deeply before cj)
  - demand-TOP coincidence (15M low lands within X ATR of a demand TOP, the responsive edge)
  - multi-TF demand stack (both 4H & 1D demand close below in ATR)
"""
import json, bisect, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
ROWS = [json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
        for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK = {k[:10]:v for k,v in PRIM.items()}
H4 = json.load(open(HERE/"htf_primitives"/"htf_4H.primitives.json"))
H1 = json.load(open(HERE/"htf_primitives"/"htf_1D.primitives.json"))

def mk(htf, tf_s):
    s = sorted(htf["series"], key=lambda b:b["t"]); ts=[b["t"] for b in s]
    z = htf["zones"]
    zd = [x for x in z if "DEMAND" in str(x.get("text","")).upper() and x.get("high") is not None]
    return {"s":s,"ts":ts,"tf":tf_s,"zd":zd}
M4 = mk(H4,14400); M1 = mk(H1,86400)

def asof_bar(M,t):
    i = bisect.bisect_right(M["ts"], t-M["tf"])-1
    return M["s"][i] if i>=0 else None

# ---- NEW derived HTF-demand QUALITY features (from raw zones) ----
def htf_quality(M, lo, c, t):
    """Returns dict: dist_top_atr (15M-low to nearest demand TOP below/around), fresh_bars (age of that zone in HTF bars),
    virgin (zone low never broken before cj as proxy untested), top_coincide (15M low within band of demand TOP)."""
    b = asof_bar(M,t); out = {"dist_top_atr":99.0,"fresh_bars":999,"virgin":0,"top_coincide":0,"stack_dist":99.0}
    if not b or not b.get("atr"): return out
    atr = b["atr"]
    # demand zones born before cj whose TOP sits at/below the 15M low region (responsive demand under price)
    cand = [z for z in M["zd"] if z.get("born_t") is not None and z["born_t"] <= t and z["high"] <= c + 0.5*atr]
    if not cand: return out
    # nearest by demand TOP to the 15M low (we want the low to LAND on the demand TOP = responsive edge)
    def dtop(z): return abs(lo - z["high"]) / atr
    z = min(cand, key=dtop)
    out["dist_top_atr"] = round((c - z["high"]) / atr, 2)          # how far price closed above demand top
    out["stack_dist"]   = round((c - z["high"]) / atr, 2)
    out["top_coincide"] = 1 if dtop(z) <= 0.5 else 0               # 15M low pierces/touches demand TOP
    # freshness in HTF bars: (t - born_t)/tf
    out["fresh_bars"]   = int((t - z["born_t"]) / M["tf"])
    # virgin proxy: zone's last_t close to born_t (never extended/retested far in time) => untested before this touch
    lt = z.get("last_t", z["born_t"]); out["virgin"] = 1 if (lt - z["born_t"]) <= 4*M["tf"] else 0
    return out

# ---- R harness (identical ruler) ----
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def R_of(r):
    pr=PRIMK.get(r["block"])
    if not pr: return None
    s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s): return None
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: return None
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr
    return letrun(s,cj,entry,sl,atr)

# ---- enrich rows with derived quality feats + R ----
for r in ROWS:
    pr=PRIMK.get(r["block"])
    if not pr: r["_R"]=None; continue
    s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None: r["_R"]=None; continue
    lo=s[p]["l"]; c=s[cj]["c"]; t=r["cj_t"]
    q4=htf_quality(M4,lo,c,t); q1=htf_quality(M1,lo,c,t)
    r["q4_dist_top"]=q4["dist_top_atr"]; r["q4_fresh"]=q4["fresh_bars"]; r["q4_virgin"]=q4["virgin"]; r["q4_coincide"]=q4["top_coincide"]
    r["q1_dist_top"]=q1["dist_top_atr"]; r["q1_fresh"]=q1["fresh_bars"]; r["q1_virgin"]=q1["virgin"]; r["q1_coincide"]=q1["top_coincide"]
    r["_R"]=R_of(r)

VALID=[r for r in ROWS if r["_R"] is not None]
print(f"valid entries with R: {len(VALID)} / {len(ROWS)}")

def isnum(v): return isinstance(v,(int,float)) and not isinstance(v,bool)
def m(sel):
    rs=[r["_R"] for r in sel]; n=len(rs)
    if not n: return None
    sm=sum(rs); w=sum(1 for x in rs if x>0); mf=sum(r["is_monforte"] for r in sel)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return dict(n=n,WR=round(100*w/n,1),sumR=round(sm,1),avgR=round(sm/n,3),maxDD=round(dd,1),mf=mf)
BASE=m(VALID)
print("TAKE-ALL baseline:", BASE)
MFtot=sum(r["is_monforte"] for r in VALID)
print(f"MF total={MFtot}\n")

def show(name,cond):
    sel=[r for r in VALID if cond(r)]; mm=m(sel)
    if not mm: print(f"  {name:<46} EMPTY"); return
    keep=round(100*mm['n']/BASE['n']); print(f"  {name:<46} n={mm['n']:>4} ({keep:>3}%) WR={mm['WR']:>5} avgR={mm['avgR']:>6} sumR={mm['sumR']:>7} DD={mm['maxDD']:>6} mf={mm['mf']}")

def dist(name,key,qs=(0.1,0.25,0.5,0.75,0.9)):
    vals=sorted(r[key] for r in VALID if isnum(r.get(key)))
    if not vals: print(f"{name}: no numeric"); return
    qv={q:round(vals[min(int(q*len(vals)),len(vals)-1)],3) for q in qs}
    print(f"{name:<22} n={len(vals)} min={vals[0]} {qv} max={vals[-1]}")

print("="*70); print("DISTRIBUTIONS (location / structure / HTF-demand-quality)"); print("="*70)
for k in ("dealing_range_pos","legpos60","legpos90","h1_pos","pullback_depth","downleg_eff",
          "h4n_dist_demand_atr","h1n_dist_demand_atr","h4n_clean_sky_atr","h1n_clean_sky_atr",
          "dist_demand_atr","clean_sky_atr","n_supply_overhead","rsi_low","rsi_min8",
          "q4_dist_top","q1_dist_top","q4_fresh","q1_fresh"):
    dist(k,k)

print("\n"+"="*70); print("SINGLE-LENS slices (calibration only)"); print("="*70)
show("legpos60 <= 0.5 (shallow pullback)", lambda r: isnum(r.get('legpos60')) and r['legpos60']<=0.5)
show("legpos60 <= 0.35 (very shallow)", lambda r: isnum(r.get('legpos60')) and r['legpos60']<=0.35)
show("dealing_range_pos <= 0.4 (discount)", lambda r: isnum(r.get('dealing_range_pos')) and r['dealing_range_pos']<=0.4)
show("dealing_range_pos <= 0.25 (deep disc)", lambda r: isnum(r.get('dealing_range_pos')) and r['dealing_range_pos']<=0.25)
show("h4n_clean_sky >= 1.5 (runner room)", lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
show("h4n_clean_sky >= 3.0 (big room)", lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=3.0)
show("clean_sky_atr >= 2.0 (15M room)", lambda r: isnum(r.get('clean_sky_atr')) and r['clean_sky_atr']>=2.0)
show("n_supply_overhead <= 3 (clear above)", lambda r: isnum(r.get('n_supply_overhead')) and r['n_supply_overhead']<=3)
show("n_supply_overhead == 0", lambda r: isnum(r.get('n_supply_overhead')) and r['n_supply_overhead']==0)
show("h4n_dist_demand <= 0.5 (on 4H dem)", lambda r: isnum(r.get('h4n_dist_demand_atr')) and r['h4n_dist_demand_atr']<=0.5)
show("h4n_dist_demand <= 1.0", lambda r: isnum(r.get('h4n_dist_demand_atr')) and r['h4n_dist_demand_atr']<=1.0)
show("q4_coincide (low lands 4H dem top)", lambda r: r.get('q4_coincide')==1)
show("q1_coincide (low lands 1D dem top)", lambda r: r.get('q1_coincide')==1)
show("q4_virgin demand", lambda r: r.get('q4_virgin')==1)
show("q4_fresh <= 30 bars (fresh 4H dem)", lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30)
show("h4n_trend == 1 (4H uptrend)", lambda r: r.get('h4n_trend')==1)
show("h1n_trend == 1 (1D uptrend)", lambda r: r.get('h1n_trend')==1)
show("h4n_trend==1 & h1n_trend==1 (both up)", lambda r: r.get('h4n_trend')==1 and r.get('h1n_trend')==1)

print("\n"+"="*70); print("CONVERGENT RULE PROPOSALS (2-3 lens)"); print("="*70)
# R1: Discount + fresh/close 4H demand TOP + clean sky
show("R1 disc<=0.4 & h4dist<=1.0 & h4sky>=1.5",
     lambda r: isnum(r.get('dealing_range_pos')) and r['dealing_range_pos']<=0.4
     and isnum(r.get('h4n_dist_demand_atr')) and r['h4n_dist_demand_atr']<=1.0
     and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
# R2: Shallow pullback + clean sky + low overhead supply (controlled, not deep)
show("R2 legpos60<=0.5 & sky>=2 & nsup<=4",
     lambda r: isnum(r.get('legpos60')) and r['legpos60']<=0.5
     and isnum(r.get('clean_sky_atr')) and r['clean_sky_atr']>=2.0
     and isnum(r.get('n_supply_overhead')) and r['n_supply_overhead']<=4)
# R3: 15M low lands on 4H demand top (coincide) + 1D uptrend
show("R3 q4_coincide & h1n_trend==1",
     lambda r: r.get('q4_coincide')==1 and r.get('h1n_trend')==1)
# R4: multi-TF demand stack (both 4H & 1D demand close below) + room
show("R4 h4dist<=1.5 & h1dist<=2.5 & h4sky>=1.5",
     lambda r: isnum(r.get('h4n_dist_demand_atr')) and r['h4n_dist_demand_atr']<=1.5
     and isnum(r.get('h1n_dist_demand_atr')) and r['h1n_dist_demand_atr']<=2.5
     and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
# R5: NOT-knife discount with controlled downleg (avoid falling knife) + room
show("R5 disc<=0.4 & downleg_eff<=0.5 & sky>=1.5 & knife==0",
     lambda r: r.get('falling_knife',0)==0 and isnum(r.get('dealing_range_pos')) and r['dealing_range_pos']<=0.4
     and isnum(r.get('downleg_eff')) and r['downleg_eff']<=0.5
     and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
# R6: clean sky big + shallow pullback (pure runner-room x controlled)
show("R6 legpos60<=0.5 & h4sky>=3.0",
     lambda r: isnum(r.get('legpos60')) and r['legpos60']<=0.5
     and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=3.0)

print("\n"+"="*70); print("REFINEMENT: the two standouts + convergences + per-year + null"); print("="*70)
import random
show("S_fresh q4_fresh<=30", lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30)
show("S_sky h4n_clean_sky>=1.5", lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
show("CONV fresh<=30 & sky>=1.5",
     lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
show("CONV fresh<=30 & sky>=1.5 & h4trend==1",
     lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5 and r.get('h4n_trend')==1)
show("CONV fresh<=30 & nsup<=10",
     lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and isnum(r.get('n_supply_overhead')) and r['n_supply_overhead']<=10)
show("CONV sky>=1.5 & nsup<=10",
     lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5 and isnum(r.get('n_supply_overhead')) and r['n_supply_overhead']<=10)
show("CONV sky>=1.5 & h4trend==1 & h1trend==1",
     lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5 and r.get('h4n_trend')==1 and r.get('h1n_trend')==1)

# is q4_fresh<=30 just a clean_sky proxy? check correlation of memberships
A=set(id(r) for r in VALID if isnum(r.get('q4_fresh')) and r['q4_fresh']<=30)
B=set(id(r) for r in VALID if isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
print(f"\nfresh<=30 set={len(A)} sky>=1.5 set={len(B)} overlap={len(A&B)} jaccard={len(A&B)/len(A|B):.2f}")

print("\nPER-YEAR for the two standouts + best conv:")
def peryear(name,cond):
    print(f" [{name}]")
    for y in sorted(set(r['yr'] for r in VALID)):
        sel=[r for r in VALID if r['yr']==y and cond(r)]; mm=m(sel)
        if mm: print(f"    {y}: n={mm['n']:>4} WR={mm['WR']:>5} avgR={mm['avgR']:>6} sumR={mm['sumR']:>7} DD={mm['maxDD']:>6}")
peryear("fresh<=30", lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30)
peryear("sky>=1.5", lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
peryear("conv fresh<=30 & sky>=1.5", lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)

# null: random same-n avgR for the standouts
random.seed(11)
def nullcheck(name,cond):
    sel=[r for r in VALID if cond(r)]; n=len(sel)
    avgs=[]
    for _ in range(500):
        rs=[r['_R'] for r in random.sample(VALID,n)]; avgs.append(sum(rs)/n)
    obs=sum(r['_R'] for r in sel)/n
    avgs.sort(); pct=sum(1 for a in avgs if a>=obs)/len(avgs)
    print(f"  NULL {name}: obs avgR={obs:.3f} rand_mean={st.mean(avgs):.3f} rand_p95={avgs[int(.95*len(avgs))]:.3f} P(rand>=obs)={pct:.3f}")
nullcheck("fresh<=30", lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30)
nullcheck("sky>=1.5", lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)
nullcheck("conv fresh<=30 & sky>=1.5", lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)

print("\n"+"="*70); print("SELF-DA CHECKS (E:99-sentinel / D:MF retention+lift / B:regime)"); print("="*70)
show("sky in [1.5,5) bounded room", lambda r: isnum(r.get('h4n_clean_sky_atr')) and 1.5<=r['h4n_clean_sky_atr']<5)
show("sky in [5,99) wide room", lambda r: isnum(r.get('h4n_clean_sky_atr')) and 5<=r['h4n_clean_sky_atr']<99)
show("sky ==99 (NO overhead supply)", lambda r: r.get('h4n_clean_sky_atr')==99)
show("sky <1.5 (capped by supply)", lambda r: isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']<1.5)
show("CONV fresh<=30 & sky in[1.5,99) NO sentinel",
     lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and isnum(r.get('h4n_clean_sky_atr')) and 1.5<=r['h4n_clean_sky_atr']<99)
show("CONV fresh<=30 & sky==99 sentinel only",
     lambda r: isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and r.get('h4n_clean_sky_atr')==99)

mf_all=[r for r in VALID if r['is_monforte']==1]
print(f"\nMON+FORTE total={len(mf_all)} sumR={round(sum(r['_R'] for r in mf_all),1)} avgR={round(sum(r['_R'] for r in mf_all)/len(mf_all),3)}")
conv=lambda r:isnum(r.get('q4_fresh')) and r['q4_fresh']<=30 and isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5
for nm,cond in [("fresh<=30",lambda r:isnum(r.get('q4_fresh')) and r['q4_fresh']<=30),
                ("sky>=1.5",lambda r:isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5),("conv",conv)]:
    kept=[r for r in mf_all if cond(r)]; cut=[r for r in mf_all if not cond(r)]
    print(f"  {nm}: MF kept={len(kept)}/{len(mf_all)} sumR_kept={round(sum(r['_R'] for r in kept),1)} | MF cut={len(cut)} sumR_cut={round(sum(r['_R'] for r in cut),1)}")
top=sorted(VALID,key=lambda r:r['_R'],reverse=True)[:30]
print(f"top30 runners sumR={round(sum(r['_R'] for r in top),1)} kept: fresh={sum(1 for r in top if isnum(r.get('q4_fresh')) and r['q4_fresh']<=30)}/30 sky={sum(1 for r in top if isnum(r.get('h4n_clean_sky_atr')) and r['h4n_clean_sky_atr']>=1.5)}/30 conv={sum(1 for r in top if conv(r))}/30")
kept=[r for r in VALID if conv(r)]; cut=[r for r in VALID if not conv(r)]
print(f"CONV lift decomp: KEPT n={len(kept)} avgR={round(sum(r['_R'] for r in kept)/len(kept),3)} loserfrac={round(sum(1 for r in kept if r['_R']<0)/len(kept),3)} | CUT n={len(cut)} avgR={round(sum(r['_R'] for r in cut)/len(cut),3)} loserfrac={round(sum(1 for r in cut if r['_R']<0)/len(cut),3)}")
