#!/usr/bin/env python3
"""L1 EXIT — hardening do candidato CHAND_5 (Chandelier hh-k*ATR).
Grelha-k FINA (3.0..7.0 passo 0.5) p/ ver se k=5 é knife-edge ou plateau. Jackknife-1 (concentração).
null por-k. Por-ano (não é 1 ano só). Causal. Read-only RAW. Output: l1_exit_chand_harden_result.json."""
import sys, json, statistics, random
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
random.seed(20260709); S=scanner.build_series()
def u(ts):
    if len(ts)==16: ts=ts+":00"
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def mk(tsu):
    i=S.idx.get(tsu)
    if i is None: return None
    e=S.C[i]; st0=scanner.structural_sl(S,i)
    if not (e-st0>0): return None
    return dict(i=i,entry=e,stop0=st0,risk=e-st0,tsu=tsu,year=datetime.utcfromtimestamp(S.T[i]).year)
def atr(j): return S.ATR14[j] if (0<=j<S.N and S.ATR14[j]) else (S.ATR14[max(0,j-1)] or 0.0)
def sim_chand(tr,kk,H):
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]; last=min(i+H,S.N-1); eff=st0; hh=S.H[i]
    for j in range(i+1,last+1):
        cand=hh-kk*atr(j-1); eff=max(eff,cand,st0)
        if S.L[j]<=eff: return round((eff-e)/risk,2)
        hh=max(hh,S.H[j])
    return round((S.C[last]-e)/risk,2)
def null_random(tr,H,ntrial):
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]; last=min(i+H,S.N-1); span=last-i
    if span<1: return [0.0]*ntrial
    out=[]
    for _ in range(ntrial):
        kx=random.randint(1,span); Rk=None
        for j in range(i+1,i+kx+1):
            if S.L[j]<=st0: Rk=-1.0; break
        if Rk is None: Rk=(S.C[i+kx]-e)/risk
        out.append(Rk)
    return out
def dd_streak(Rs):
    eq=0.0;pk=0.0;dd=0.0;stk=0;mst=0
    for r in Rs:
        eq+=r;pk=max(pk,eq);dd=min(dd,eq-pk);stk=stk+1 if r<=0 else 0;mst=max(mst,stk)
    return round(dd,1),mst
f24=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]) if t]
tr31=[t for t in (mk(S.T[i]) for i in range(S.N) if scanner.evaluate(S,i).get("state")=="operational_candidate") if t]
s34=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_approved34.json"))) if t]
SETS=[("FINAL-24",f24),("SCANNER-31-V1",tr31),("ESTUDO-34",s34)]
H=300; TR=2000
res={"H":H,"sets":{}}
KS=[3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0]
for name,trs in SETS:
    o={"N":len(trs),"kcurve":{},"per_year_CHAND_5":{},"jackknife_CHAND_5":{}}
    # curva-k + null por-k
    per=[null_random(t,H,TR) for t in trs]; nsum=[sum(per[k][t] for k in range(len(trs))) for t in range(TR)]
    nmean=statistics.mean(nsum)
    for kk in KS:
        Rs=[sim_chand(t,kk,H) for t in trs]; s=sum(Rs); dd,st=dd_streak(Rs)
        p=sum(1 for x in nsum if x>=s)/TR
        o["kcurve"][str(kk)]=dict(sumR=round(s,1),WR=round(100*sum(1 for r in Rs if r>0)/len(Rs)),
            maxDD_R=dd,streak=st,ret_DD=round(s/(abs(dd) or .1),1),p_null=round(p,3))
    o["null_mean"]=round(nmean,1)
    # jackknife CHAND_5
    Rs5=[sim_chand(t,5.0,H) for t in trs]; s5=sum(Rs5); drops=[round(s5-r,1) for r in Rs5]
    o["jackknife_CHAND_5"]=dict(full=round(s5,1),jack_min=min(drops),jack_max=max(drops),
        top_R=round(max(Rs5),1),top2_share=round(sum(sorted(Rs5,reverse=True)[:2])/s5,2) if s5>0 else None)
    # por-ano CHAND_5 vs +3R
    yrs=sorted(set(t["year"] for t in trs))
    for y in yrs:
        idx=[k for k,t in enumerate(trs) if t["year"]==y]
        o["per_year_CHAND_5"][str(y)]=dict(n=len(idx),sumR=round(sum(Rs5[k] for k in idx),1),
            wins=sum(1 for k in idx if Rs5[k]>0))
    res["sets"][name]=o
(HERE/"l1_exit_chand_harden_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
for name,_ in SETS:
    o=res["sets"][name]
    print(f"\n=== {name} N={o['N']} | null_mean={o['null_mean']} ===")
    print(f"{'k':>5} {'sumR':>7} {'WR':>3} {'DD':>5} {'strk':>4} {'ret/DD':>6} {'p_null':>6}")
    for kk in KS:
        p=o["kcurve"][str(kk)]; print(f"{kk:>5} {p['sumR']:>7} {p['WR']:>3} {p['maxDD_R']:>5} {p['streak']:>4} {p['ret_DD']:>6} {p['p_null']:>6}")
    j=o["jackknife_CHAND_5"]; print(f"  jackknife CHAND_5: full={j['full']} drop-one->[{j['jack_min']}..{j['jack_max']}] top={j['top_R']} top2_share={j['top2_share']}")
    print(f"  per-year CHAND_5: "+" ".join(f"{y}:{v['sumR']}({v['wins']}/{v['n']})" for y,v in o['per_year_CHAND_5'].items()))
print("\nsaved l1_exit_chand_harden_result.json")
