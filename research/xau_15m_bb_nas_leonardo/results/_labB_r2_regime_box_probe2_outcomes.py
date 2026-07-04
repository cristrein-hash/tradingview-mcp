#!/usr/bin/env python3
"""LAB B r2 — REGIME BOX probe 2 (LOOK #1 do ledger): outcome nas células/hipóteses CONGELADAS.
Lê _labB_r2_regime_box_feats.json (probe1). NET-SB = g_R − 0.80/g_risk."""
import json
from pathlib import Path
HERE=Path(__file__).parent
F=json.loads((HERE/"_labB_r2_regime_box_feats.json").read_text())
for f in F: f["net"]=f["g_R"]-0.80/f["g_risk"]
def cell(rows,tag):
    n=len(rows)
    if not n: print(f"  {tag:<34} N   0"); return
    net=[r["net"] for r in rows]; w=sum(1 for x in net if x>0); run=sum(1 for r in rows if r["g_R"]>=3)
    print(f"  {tag:<34} N{n:>4} WRliq{100*w/n:>5.1f}% avgNET{sum(net)/n:>+7.3f} sumNET{sum(net):>+8.1f} run{run:>3}")
def quart(vals):
    v=sorted(vals); n=len(v)
    return [v[int(0.25*n)],v[int(0.5*n)],v[int(0.75*n)]]
print("=== células quartil×regime (quartis calibrados NA BASE por regime — declarado) ===")
for reg in ("BULL","RANGE"):
    R=[f for f in F if f["v5h"]==reg]
    for key in ("rbox_pos","rbox_age_h"):
        q=quart([f[key] for f in R])
        print(f"\n{reg} × {key}  (quartis {q})")
        cell([f for f in R if f[key]<=q[0]],"Q1")
        cell([f for f in R if q[0]<f[key]<=q[1]],"Q2")
        cell([f for f in R if q[1]<f[key]<=q[2]],"Q3")
        cell([f for f in R if f[key]>q[2]],"Q4")
print("\n=== bandas estruturais fixas ===")
for reg in ("BULL","RANGE"):
    R=[f for f in F if f["v5h"]==reg]
    print(f"\n{reg} × prev_hi_dist_atr (teto herdado)")
    cell([f for f in R if f["prev_hi_dist_atr"] is not None and f["prev_hi_dist_atr"]<=-10],"<=-10 (muito acima do teto)")
    cell([f for f in R if f["prev_hi_dist_atr"] is not None and -10<f["prev_hi_dist_atr"]<=-2],"(-10,-2]")
    cell([f for f in R if f["prev_hi_dist_atr"] is not None and -2<f["prev_hi_dist_atr"]<=0],"(-2,0] (logo acima do teto)")
    cell([f for f in R if f["prev_hi_dist_atr"] is not None and f["prev_hi_dist_atr"]>0],">0 (teto AINDA acima)")
    cell([f for f in R if f["prev_hi_dist_atr"] is None],"sem prev (censored)")
    print(f"{reg} × rbox_hi_dist_atr (headroom ao topo do regime)")
    cell([f for f in R if f["rbox_hi_dist_atr"]<=1],"<=1 (na máxima do regime)")
    cell([f for f in R if 1<f["rbox_hi_dist_atr"]<=3],"(1,3]")
    cell([f for f in R if 3<f["rbox_hi_dist_atr"]<=8],"(3,8]")
    cell([f for f in R if f["rbox_hi_dist_atr"]>8],">8")
print("\n=== hipóteses congeladas ===")
H={}
H["H1 BULL prev_hi>=-2"]=[f for f in F if f["v5h"]=="BULL" and f["prev_hi_dist_atr"] is not None and f["prev_hi_dist_atr"]>=-2.0]
H["H2 BULL age<=178h"]=[f for f in F if f["v5h"]=="BULL" and f["rbox_age_h"]<=178]
H["H1∧H2 convergente"]=[f for f in H["H1 BULL prev_hi>=-2"] if f["rbox_age_h"]<=178]
H["H3 rboxhi<=1 (all)"]=[f for f in F if f["rbox_hi_dist_atr"]<=1.0]
H["H4 RANGEtop sob teto BULL"]=[f for f in F if f["v5h"]=="RANGE" and f["rbox_pos"]>=0.9 and f["prev_state"]=="BULL" and (f["prev_hi_dist_atr"] or 0)>0]
H["H5 BULL age>=1085"]=[f for f in F if f["v5h"]=="BULL" and f["rbox_age_h"]>=1085]
H["H5 RANGE age>=1032"]=[f for f in F if f["v5h"]=="RANGE" and f["rbox_age_h"]>=1032]
H["H6 RANGE prev_hi<=0"]=[f for f in F if f["v5h"]=="RANGE" and f["prev_hi_dist_atr"] is not None and f["prev_hi_dist_atr"]<=0]
for k,v in H.items(): cell(v,k)
print("\n=== painel completo base vs base-menos-flag (só p/ hipóteses de corte) ===")
def panel(rows,tag):
    rows=sorted(rows,key=lambda z:z["cj_t"]); net=[r["net"] for r in rows]; n=len(net)
    sm=sum(net); w=sum(1 for x in net if x>0); eq=pk=dd=0.0
    for x in net: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in net:
        if x>0: cw+=1; cl=0
        else: cl+=1; cw=0
        mW=max(mW,cw); mL=max(mL,cl)
    py={y:round(sum(r["net"] for r in rows if r["yr"]==y),1) for y in (2024,2025,2026)}
    run=sum(1 for r in rows if r["g_R"]>=3)
    print(f"  {tag:<28} N{n:>4} WR{100*w/n:>5.1f}% run{run:>3} sumNET{sm:>+8.1f} avgNET{sm/n:>+7.3f} DD{dd:>7.1f} r/DD{abs(sm/dd) if dd<0 else 99:>6.2f} stk-{mL}/+{mW} | {py[2024]}/{py[2025]}/{py[2026]}")
panel(F,"BASE 435")
for k in ("H1 BULL prev_hi>=-2","H1∧H2 convergente","H4 RANGEtop sob teto BULL"):
    S={id(x) for x in H[k]}
    panel([f for f in F if id(f) not in S],f"BASE − ({k})")
print("\n=== overlap dos flagged com clusters de loss (g_week) ===")
from collections import Counter
lossw=Counter(f["g_week"] for f in F if f["net"]<=0)
for k in ("H1 BULL prev_hi>=-2","H4 RANGEtop sob teto BULL"):
    rows=H[k]; wk=Counter(r["g_week"] for r in rows)
    multi=[w for w,c in wk.items() if c>=2]
    print(f"  {k}: {len(rows)} flags em {len(wk)} semanas; semanas c/ 2+ flags: {len(multi)}; flags loser {sum(1 for r in rows if r['net']<=0)}")
