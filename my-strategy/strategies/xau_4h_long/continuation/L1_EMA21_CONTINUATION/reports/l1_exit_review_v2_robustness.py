#!/usr/bin/env python3
"""L1 EXIT REVIEW v2 — robustez das regras ESTRUTURAIS E e D (não só a B blind).
Para cada conjunto e rule in {E,D,B} @ H=300: sumR observado, jackknife-1 (concentração) e
exit-null (holding aleatório com mesmo SL0 floor + mesma exposição) -> p(null>=obs).
Separa edge causal de BETA (exposição longa a bull). Read-only RAW; sem produção/chart/commit.
Output: l1_exit_review_v2_robustness_result.json."""
import sys, json, statistics, random
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
SWING_N=scanner.SWING_N; DAY=86400; random.seed(20260709)
S=scanner.build_series()
_REG=[None]*S.N
for _j in range(S.N):
    _st,_=scanner.latest_state_before(S.CLS,(S.T[_j]//DAY)*DAY); _REG[_j]=_st
def u(ts):
    if len(ts)==16: ts=ts+":00"
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def mk(tsu):
    i=S.idx.get(tsu)
    if i is None: return None
    e=S.C[i]; st0=scanner.structural_sl(S,i)
    if not (e-st0>0): return None
    return dict(i=i,entry=e,stop0=st0,risk=e-st0,target3R=e+3.0*(e-st0),tsu=tsu)
def swing_low_before(j):
    lo=S.L[max(0,j-SWING_N):j]; return min(lo) if lo else S.L[j]
def sim(tr,rule,H):
    i,e,st0,risk,t3=tr["i"],tr["entry"],tr["stop0"],tr["risk"],tr["target3R"]
    r1=e+risk; activated=False; floor=st0; last=min(i+H,S.N-1)
    for j in range(i+1,last+1):
        lo,hi,c=S.L[j],S.H[j],S.C[j]
        if not activated and hi>=r1: activated=True
        if lo<=floor: return round((floor-e)/risk,2)
        if rule=="A" and hi>=t3: return 3.0
        ec=False
        if rule=="C" and activated and c<S.EMA21[j]: ec=True
        if rule=="D" and activated and c<swing_low_before(j): ec=True
        if rule=="E" and _REG[j]!="BULL": ec=True
        if ec: return round((c-e)/risk,2)
        if rule=="D2" and activated and floor<e: floor=e
    return round((S.C[last]-e)/risk,2)
def null_random(tr,H,ntrial):
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]; last=min(i+H,S.N-1); span=last-i
    if span<1: return [0.0]*ntrial
    out=[]
    for _ in range(ntrial):
        kx=random.randint(1,span); Rk=None
        for j in range(i+1,i+kx+1):
            if S.L[j]<=st0: Rk=(st0-e)/risk; break
        if Rk is None: Rk=(S.C[i+kx]-e)/risk
        out.append(Rk)
    return out
def jack1(Rs):
    s=sum(Rs); drops=[s-r for r in Rs]
    return dict(full=round(s,1),jack_min=round(min(drops),1),jack_max=round(max(drops),1),top_R=round(max(Rs),1))

s34=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_approved34.json"))) if t]
f24=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]) if t]
tr31=[t for t in (mk(S.T[i]) for i in range(S.N) if scanner.evaluate(S,i).get("state")=="operational_candidate") if t]
SETS=[("FINAL-24",f24),("SCANNER-31-V1",tr31),("ESTUDO-34",s34)]
H=300; TR=2000
res={"H":H,"trials":TR,"sets":{}}
print(f"robustez @ H={H}, null trials={TR}\n{'set':>14} {'rule':>4} {'obsR':>7} {'jackR-range':>16} {'topR':>6} {'nullMean':>8} {'nullP95':>8} {'p(null>=obs)':>12}")
for name,trs in SETS:
    res["sets"][name]={}
    for rule in ["E","D","B"]:
        Rs=[sim(tr,rule,H) for tr in trs]; obs=sum(Rs); jk=jack1(Rs)
        per=[null_random(tr,H,TR) for tr in trs]
        nsum=[sum(per[k][t] for k in range(len(trs))) for t in range(TR)]
        p=sum(1 for x in nsum if x>=obs)/TR
        rec=dict(obs_sumR=round(obs,1),jackknife=jk,null_mean=round(statistics.mean(nsum),1),
                 null_p95=round(sorted(nsum)[int(0.95*TR)],1),p_null_ge_obs=round(p,3))
        res["sets"][name][rule]=rec
        print(f"{name:>14} {rule:>4} {obs:>7.1f} {str(jk['jack_min'])+'..'+str(jk['jack_max']):>16} {jk['top_R']:>6} {rec['null_mean']:>8} {rec['null_p95']:>8} {p:>12.3f}")
(HERE/"l1_exit_review_v2_robustness_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print("\nsaved l1_exit_review_v2_robustness_result.json")
