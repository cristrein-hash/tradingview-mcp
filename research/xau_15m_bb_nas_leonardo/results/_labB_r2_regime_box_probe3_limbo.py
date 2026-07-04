#!/usr/bin/env python3
"""LAB B r2 — REGIME BOX probe 3 (LOOK #2 do ledger): dissecção do limbo pós-breakout
L7 := BULL ∧ prev_hi_dist_atr ∈ (−10,−2]. Convergência (a/b/c congeladas), estabilidade, jackknife, painel."""
import json,datetime as dt
from pathlib import Path
from collections import Counter
HERE=Path(__file__).parent
FE=json.loads((HERE/"_labB_r2_regime_box_feats.json").read_text())
ALL=[json.loads(l) for l in (HERE/"lab_g_candidates.jsonl").read_text().splitlines()]
# integridade pós-regeneração (incidente symlink 2026-07-04): valores medidos ANTES do incidente
_b=[r for r in ALL if r.get("g_in_base435")==1 and r.get("g_v5h")!="BEAR"]
assert len(ALL)==4739 and len(_b)==435, (len(ALL),len(_b))
assert abs(sum(r["g_R"]-0.80/r["g_risk"] for r in _b)-233.6)<0.1 and sum(1 for r in _b if r["g_R"]>=3)==53
G={r["cj_t"]:r for r in _b}
for f in FE:
    f["net"]=f["g_R"]-0.80/f["g_risk"]; f.update({k:G[f["cj_t"]].get(k) for k in ("n_supply_overhead","h1n_clean_sky_atr","clean_sky_atr","legpos90","g_box96")})
import statistics as st
med_sup=st.median(sorted(f["n_supply_overhead"] for f in FE))
med_sky=st.median(sorted(f["h1n_clean_sky_atr"] for f in FE if f["h1n_clean_sky_atr"] is not None))
print(f"medianas BASE: n_supply_overhead={med_sup}  h1n_clean_sky_atr={med_sky}")
L7=[f for f in FE if f["v5h"]=="BULL" and f["prev_hi_dist_atr"] is not None and -10<f["prev_hi_dist_atr"]<=-2]
def cell(rows,tag):
    n=len(rows)
    if not n: print(f"  {tag:<40} N   0"); return
    net=[r["net"] for r in rows]; w=sum(1 for x in net if x>0); run=sum(1 for r in rows if r["g_R"]>=3)
    print(f"  {tag:<40} N{n:>4} WRliq{100*w/n:>5.1f}% avgNET{sum(net)/n:>+7.3f} sumNET{sum(net):>+8.1f} run{run:>3}")
cell(L7,"L7 limbo (BULL prev_hi (-10,-2])")
print("\n-- convergência (congelada) --")
A=[f for f in L7 if f["n_supply_overhead"]>=med_sup]
B=[f for f in L7 if 178<f["rbox_age_h"]<=415]
C=[f for f in L7 if (f["h1n_clean_sky_atr"] or 99)<=med_sky]
cell(A,"L7 ∧ a) supply>=med"); cell([f for f in L7 if f["n_supply_overhead"]<med_sup],"L7 ∧ supply<med")
cell(B,"L7 ∧ b) age adolescente (178,415]"); cell([f for f in L7 if not (178<f["rbox_age_h"]<=415)],"L7 ∧ age fora")
cell(C,"L7 ∧ c) h1n_sky<=med"); cell([f for f in L7 if (f["h1n_clean_sky_atr"] or 99)>med_sky],"L7 ∧ h1n_sky>med")
n_conf=lambda f: (f["n_supply_overhead"]>=med_sup)+(178<f["rbox_age_h"]<=415)+((f["h1n_clean_sky_atr"] or 99)<=med_sky)
for k in (0,1,2,3): cell([f for f in L7 if n_conf(f)==k],f"L7 com {k} confirmações")
cell([f for f in L7 if n_conf(f)>=2],"L7 com >=2 confirmações (SKIP cand)")
cell([f for f in L7 if n_conf(f)<2],"L7 com <2 confirmações")
print("\n-- estabilidade --")
for y in (2024,2025,2026): cell([f for f in L7 if f["yr"]==y],f"L7 {y}")
wk=Counter(f["g_week"] for f in L7)
print("  semanas:",dict(sorted(wk.items())))
wsum={w:sum(f["net"] for f in L7 if f["g_week"]==w) for w in wk}
worst=min(wsum,key=wsum.get)
print(f"  jackknife pior semana {worst} ({wsum[worst]:+.1f}): resto:",end="")
rest=[f for f in L7 if f["g_week"]!=worst]
print(f" N{len(rest)} sumNET{sum(f['net'] for f in rest):+.1f} WR{100*sum(1 for f in rest if f['net']>0)/len(rest):.0f}%")
best=max(wsum,key=wsum.get)
rest2=[f for f in L7 if f["g_week"]!=best]
print(f"  jackknife melhor semana {best} ({wsum[best]:+.1f}): resto: N{len(rest2)} sumNET{sum(f['net'] for f in rest2):+.1f}")
print("\n-- lista L7 (episódios) --")
for f in sorted(L7,key=lambda z:z["cj_t"]):
    print(f"  {dt.datetime.utcfromtimestamp(f['cj_t']).strftime('%Y-%m-%d %H:%M')} wk{f['g_week']} prev_hi{f['prev_hi_dist_atr']:>6.1f} age{f['rbox_age_h']:>4}h sup{f['n_supply_overhead']:>2} sky{f['h1n_clean_sky_atr']} conf{n_conf(f)} R{f['g_R']:>+6.2f} net{f['net']:>+6.2f}")
print("\n-- painéis completos --")
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
    print(f"  {tag:<34} N{n:>4} WR{100*w/n:>5.1f}% run{run:>3} sumNET{sm:>+8.1f} avgNET{sm/n:>+7.3f} DD{dd:>7.1f} r/DD{abs(sm/dd) if dd<0 else 99:>6.2f} stk-{mL}/+{mW} | {py[2024]}/{py[2025]}/{py[2026]}")
panel(FE,"BASE 435")
S7={f["cj_t"] for f in L7}
panel([f for f in FE if f["cj_t"] not in S7],"BASE − L7 (SKIP integral)")
S2={f["cj_t"] for f in L7 if n_conf(f)>=2}
panel([f for f in FE if f["cj_t"] not in S2],"BASE − (L7 ∧ conf>=2)")
# size-reduction 0.5 no L7 (rota REVIEW/size)
half=[dict(f) for f in FE]
for f in half:
    if f["cj_t"] in S7: f["net"]=0.5*f["net"]; f["g_R"]=0.5*f["g_R"]
panel(half,"BASE c/ L7 @ half-size")
