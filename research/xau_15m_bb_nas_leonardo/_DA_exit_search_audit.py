#!/usr/bin/env python3
"""DA AUDIT of the CAUSAL exit-rule search (XAU 15M LONG, n=170, in-sample).
Attacks RIDER +71.3 vs LETRUN +66.3. Computes: selection-spread, concentration,
RIDER grid robustness, per-year, fill-realism (intrabar gap), RIDER<LETRUN losses,
runner-capture power. RAW-causal, no OOS. Numbers only."""
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480; RCAP=20.0
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
def fnum(x): return float(x) if x not in (None,"","None") else None
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst

def sim(mode,s,cj,entry,sl,atr,K,loose,track=False):
    """returns (exit_price, breach_low_at_trail_exit or None).
    track=True records the candle LOW on the bar that triggered a trail/SL exit,
    to test fill realism (did we fill at trail level or did candle gap through it)."""
    risk=entry-sl; end=min(cj+HMAX,len(s)-1); r1=False; ridem=False; trail=sl; runhi=entry
    for k in range(cj+1,end+1):
        b=s[k]; lo,hi,cl=b["l"],b["h"],b["c"]
        if lo<=trail and (r1 or trail>sl):
            return (trail, lo) if track else (trail,None)
        if lo<=sl and not r1:
            return (sl, lo) if track else (sl,None)
        runhi=max(runhi,hi)
        if (hi-entry)/risk>=1: r1=True
        if (hi-entry)/risk>=K: ridem=True
        if not r1: continue
        if mode=="LETRUN":
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
        elif mode=="RIDER":
            if not ridem:
                sw=cf_low(s,k)
                if sw: trail=max(trail,sw-0.1*atr)
            else:
                trail=max(trail, runhi-loose*risk)
    return (s[end]["c"], None)

# load trade context once
data=[]; big=set()
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); gt=GT.get(num)
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=fd["cj"]; i=fd["i"]; atr=s[i]["atr"]
    entry=fnum(gt["entry"]); sl=float(tr["sl"]); risk=entry-sl
    ce=fnum(gt["cris_exit"]); rp=fnum(gt["cris_Rpot"]); yr=int(fd["yr"])
    if rp and rp>3: big.add(num)
    data.append(dict(num=num,s=s,cj=cj,entry=entry,sl=sl,atr=atr,risk=risk,ce=ce,rp=rp,yr=yr))

def Rval(ex,entry,risk): return max(-1.0,min(RCAP,(ex-entry)/risk))

def run(mode,K,loose,track=False):
    out=[]
    for d in data:
        ex,brlow=sim(mode,d["s"],d["cj"],d["entry"],d["sl"],d["atr"],K or 3,loose,track=track)
        out.append(dict(num=d["num"],R=Rval(ex,d["entry"],d["risk"]),ex=ex,brlow=brlow,
                        entry=d["entry"],risk=d["risk"],yr=d["yr"],rp=d["rp"]))
    return out
def sumR(rs): return round(sum(x["R"] for x in rs),2)
def metr(rs):
    n=len(rs); sm=sum(x["R"] for x in rs); w=sum(1 for x in rs if x["R"]>0)
    eq=pk=dd=0
    for x in sorted(rs,key=lambda y:y["num"]):
        eq+=x["R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
    cap=sum(1 for x in rs if x["num"] in big and x["R"]>=3)
    return n,round(100*w/n,1),round(sm,1),round(dd,1),cap

LET=run("LETRUN",None,None)
LETmap={x["num"]:x["R"] for x in LET}

# ===== POINT 1: SELECTION BIAS — spread across configs + concentration =====
print("="*70); print("POINT 1 — SELECTION BIAS / CONCENTRATION"); print("="*70)
# all configs from both labs
exit_csv={int(r["num"]):r for r in csv.DictReader(open(HERE/"lab_exit_rules.csv"))}
rulecols=["TGT1_R","TGT2_R","TGT3_R","LETRUN_R","SWING_R","CHAND2_R","CHAND3_R","EMA21_R","NASs_R","SELLb_R","STRUCT_R"]
lab1_sums={}
for c in rulecols:
    lab1_sums[c.replace("_R","")]=round(sum(float(exit_csv[n][c]) for n in exit_csv),2)
# conditional configs
CONF=[("LETRUN",None,None),("RIDER",2,1.5),("RIDER",2,2.0),("RIDER",2,2.5),
      ("RIDER",3,1.5),("RIDER",3,2.0),("RIDER",3,2.5),("RIDE",3,"swing")]
lab2_sums={}
for mode,K,loose in CONF:
    if mode=="RIDE": continue  # swing variant handled in lab1 family; skip dup
    tag=f"{mode}" if mode=="LETRUN" else f"RIDER_K{K}_gb{loose}"
    lab2_sums[tag]=sumR(run(mode,K,loose))
allsums=list(lab1_sums.values())+[v for k,v in lab2_sums.items() if k!="LETRUN"]
print("lab_exit_rules sums:", {k:v for k,v in sorted(lab1_sums.items(),key=lambda z:-z[1])})
print("RIDER family sums:", {k:v for k,v in sorted(lab2_sums.items(),key=lambda z:-z[1])})
print(f"\nALL configs (n={len(allsums)}) sumR: min={min(allsums)} max={max(allsums)} "
      f"mean={round(st.mean(allsums),1)} std={round(st.pstdev(allsums),1)}")
print(f"best RIDER +71.3 vs LETRUN +66.4 delta = +{round(71.3-66.4,1)}R")
print(f"delta / std(all configs) = {round((71.3-66.4)/st.pstdev(allsums),2)} sigma")
# concentration: which trades drive RIDER K3 gb2.0 vs LETRUN
RID=run("RIDER",3,2.0)
diffs=sorted([(x["num"],round(x["R"]-LETmap[x["num"]],2),round(LETmap[x["num"]],2),round(x["R"],2))
              for x in RID if abs(x["R"]-LETmap[x["num"]])>0.01],key=lambda z:-z[1])
print(f"\ntrades where RIDER K3gb2.0 differs from LETRUN: {len(diffs)}")
print("top gainers (num, dR, LETRUN_R, RIDER_R):", diffs[:6])
print("losers (RIDER worse):", [d for d in diffs if d[1]<0])
tot_delta=round(sum(d[1] for d in diffs),2)
print(f"total delta sum = {tot_delta}R")
pos=sorted([d for d in diffs if d[1]>0],key=lambda z:-z[1])
if pos:
    print(f"top1 trade contributes {pos[0][1]}R = {round(100*pos[0][1]/max(tot_delta,.01))}% of delta")
    top3=round(sum(d[1] for d in pos[:3]),2)
    print(f"top3 trades contribute {top3}R = {round(100*top3/max(tot_delta,.01))}% of delta")

# ===== POINT 2: RIDER K/gb GRID robustness =====
print("\n"+"="*70); print("POINT 2 — RIDER GRID (K 1..4, gb 1.0..3.0 step .5)"); print("="*70)
Ks=[1,2,3,4]; gbs=[1.0,1.5,2.0,2.5,3.0]
print("        gb=1.0   1.5    2.0    2.5    3.0")
grid={}
for K in Ks:
    rowvals=[]
    for gb in gbs:
        s_=sumR(run("RIDER",K,gb)); grid[(K,gb)]=s_; rowvals.append(s_)
    print(f"K={K}   "+"  ".join(f"{v:6.1f}" for v in rowvals))
allgrid=list(grid.values())
print(f"\ngrid sumR: min={min(allgrid)} max={max(allgrid)} mean={round(st.mean(allgrid),1)} "
      f"std={round(st.pstdev(allgrid),2)} range={round(max(allgrid)-min(allgrid),1)}")
bestcell=max(grid,key=grid.get)
print(f"best cell K={bestcell[0]} gb={bestcell[1]} = {grid[bestcell]}")
# neighbors of best
nb=[grid.get((bestcell[0]+dk,bestcell[1]+dg)) for dk in(-1,0,1) for dg in(-.5,0,.5)
    if (dk,dg)!=(0,0) and (bestcell[0]+dk,bestcell[1]+dg) in grid]
print(f"neighbor cells of best: {nb}")
print(f"best - worst neighbor = {round(grid[bestcell]-min(x for x in nb if x is not None),2)}R")

# ===== POINT 3: per-year =====
print("\n"+"="*70); print("POINT 3 — PER-YEAR  LETRUN vs RIDER K2gb2.0 vs RIDER K3gb2.0"); print("="*70)
R2=run("RIDER",2,2.0); R3=run("RIDER",3,2.0)
def by_year(rs):
    d={}
    for x in rs: d.setdefault(x["yr"],[]).append(x["R"])
    return {y:round(sum(v),2) for y,v in sorted(d.items())}
def cnt_year(rs):
    d={}
    for x in rs: d[x["yr"]]=d.get(x["yr"],0)+1
    return d
print("year counts:", cnt_year(LET))
print("LETRUN      per-year:", by_year(LET))
print("RIDER K2g2  per-year:", by_year(R2))
print("RIDER K3g2  per-year:", by_year(R3))
ly=by_year(LET); r2y=by_year(R2); r3y=by_year(R3)
print("delta K2g2-LETRUN:", {y:round(r2y[y]-ly[y],2) for y in ly})
print("delta K3g2-LETRUN:", {y:round(r3y[y]-ly[y],2) for y in ly})

# ===== POINT 4: FILL REALISM =====
print("\n"+"="*70); print("POINT 4 — FILL REALISM (trail exits: candle gapped through?)"); print("="*70)
RT=run("RIDER",3,2.0,track=True)
gap_trades=[]
for x in RT:
    if x["brlow"] is None: continue       # exited at end-of-window close, not a trail breach
    trail_level=x["ex"]                    # we fill AT trail
    gap=trail_level-x["brlow"]             # how far candle low is below assumed fill, in price
    gapR=gap/x["risk"]
    if gapR>0.05:
        gap_trades.append((x["num"],round(gap,2),round(gapR,2)))
print(f"RIDER K3g2.0 exits that breached a trail/SL: {sum(1 for x in RT if x['brlow'] is not None)}")
print(f"of those, candle LOW below the assumed fill by >0.05R (optimistic fill): {len(gap_trades)}")
gap_trades.sort(key=lambda z:-z[2])
print("worst optimistic fills (num, $gap, Rgap):", gap_trades[:10])
if gap_trades:
    print(f"median Rgap on gapped fills = {round(st.median([g[2] for g in gap_trades]),2)}R, "
          f"max = {max(g[2] for g in gap_trades)}R")
    tot_opt=round(sum(g[2] for g in gap_trades),2)
    print(f"total optimistic R if all filled at candle-low instead = -{tot_opt}R "
          f"(would erase {round(100*tot_opt/(71.3-66.4))}% of the +4.9R uplift)" if (71.3-66.4)>0 else "")

# ===== POINT 5: RIDER worse than LETRUN =====
print("\n"+"="*70); print("POINT 5 — RIDER WORSE THAN LETRUN (gave back more)"); print("="*70)
worse=[(x["num"],round(x["R"]-LETmap[x["num"]],2)) for x in RID if x["R"]<LETmap[x["num"]]-0.01]
print(f"trades where RIDER K3g2.0 < LETRUN: {len(worse)} -> {worse}")
print(f"total R lost on those: {round(sum(w[1] for w in worse),2)}R")
betr=[(x["num"],round(x["R"]-LETmap[x["num"]],2)) for x in RID if x["R"]>LETmap[x["num"]]+0.01]
print(f"trades where RIDER > LETRUN: {len(betr)}, total gain: {round(sum(b[1] for b in betr),2)}R")

# ===== POINT 6: runner-capture power =====
print("\n"+"="*70); print("POINT 6 — RUNNER CAPTURE POWER (n=25)"); print("="*70)
capL=[x["num"] for x in LET if x["num"] in big and x["R"]>=3]
capR=[x["num"] for x in RID if x["num"] in big and x["R"]>=3]
print(f"LETRUN captures runners(>=3R): {len(capL)}/25 -> {sorted(capL)}")
print(f"RIDER K3g2.0 captures: {len(capR)}/25 -> {sorted(capR)}")
print(f"net new runners captured: {len(set(capR)-set(capL))} -> {sorted(set(capR)-set(capL))}")
# what R do the 25 runners actually get under RIDER
ridrun=sorted([(x["num"],round(x["rp"],1),round(LETmap[x["num"]],2),round(x["R"],2))
               for x in RID if x["num"] in big],key=lambda z:-z[1])
print("\n25 runners (num, cris_Rpot, LETRUN_R, RIDER_R):")
for r in ridrun: print(f"  #{r[0]:>3} Rpot={r[1]:>5} LETRUN={r[2]:>5} RIDER={r[3]:>5}")
missed=[r for r in ridrun if r[3]<3]
print(f"\nrunners RIDER still FAILS to reach +3R: {len(missed)}/25")
print(f"median RIDER_R across all 25 runners: {round(st.median([r[3] for r in ridrun]),2)} "
      f"(vs cris median Rpot {round(st.median([r[1] for r in ridrun]),2)})")
# binomial-ish power note
print(f"\nbase runner rate among 170: {len(big)}/170 = {round(100*len(big)/170,1)}%")
print(f"capture improvement: {len(capL)}->{len(capR)} of 25 = +{len(capR)-len(capL)} trades")
