#!/usr/bin/env python3
"""L1 EXIT — TRAILING LARGO + ANATOMIA DE PULLBACK (testa a tese do Cris:
'continuation ⇒ maioria run SEM pullback, logo trail largo devia cavalgar o run').
1) Chandelier k in {4,5,6,8,10} + swing-estrutural largo -> vê se afrouxar o stop captura o run.
2) DIAGNÓSTICO por-trade: profundidade do MAIOR pullback (em ATR e em R) a partir do pico corrente,
   ANTES do trade atingir o pico final. Responde empiricamente 'os runs são limpos?'.
Métrica-chave = return/DD (não só sumR). null p/ separar edge de beta. Causal (info<=j-1).
Read-only RAW; sem produção/chart/commit. Output: l1_exit_trailing_wide_result.json."""
import sys, json, statistics, random
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
SWING_N=scanner.SWING_N; random.seed(20260709); S=scanner.build_series()
def u(ts):
    if len(ts)==16: ts=ts+":00"
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def mk(tsu):
    i=S.idx.get(tsu)
    if i is None: return None
    e=S.C[i]; st0=scanner.structural_sl(S,i)
    if not (e-st0>0): return None
    return dict(i=i,entry=e,stop0=st0,risk=e-st0,target3R=e+3.0*(e-st0),tsu=tsu)
def atr(j): return S.ATR14[j] if (0<=j<S.N and S.ATR14[j]) else (S.ATR14[max(0,j-1)] or 0.0)
def sim_A(tr,H):
    i,e,st0,risk,t3=tr["i"],tr["entry"],tr["stop0"],tr["risk"],tr["target3R"]
    last=min(i+H,S.N-1)
    for j in range(i+1,last+1):
        if S.L[j]<=st0: return -1.0
        if S.H[j]>=t3: return 3.0
    return round((S.C[last]-e)/risk,2)
def sim_chand(tr,kk,H):
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]; last=min(i+H,S.N-1); eff=st0; hh=S.H[i]
    for j in range(i+1,last+1):
        cand=hh-kk*atr(j-1); eff=max(eff,cand,st0)
        if S.L[j]<=eff: return round((eff-e)/risk,2),j-i
        hh=max(hh,S.H[j])
    return round((S.C[last]-e)/risk,2),(last-i)
def sim_swing_wide(tr,bb,H):
    """swing estrutural LARGO: stop = menor low das últimas 2*SWING_N barras confirmadas - bb*ATR."""
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]; last=min(i+H,S.N-1); eff=st0
    W=2*SWING_N
    for j in range(i+1,last+1):
        sw=min(S.L[max(0,j-W):j]); cand=sw-bb*atr(j-1); eff=max(eff,cand,st0)
        if S.L[j]<=eff: return round((eff-e)/risk,2),j-i
    return round((S.C[last]-e)/risk,2),(last-i)

def pullback_anatomy(tr,H):
    """Do entry ao pico final (dentro de H): maior retrace do pico CORRENTE, em ATR e em R.
    'run limpo' = pullback pequeno. Também: R do pico final (MFE)."""
    i,e,risk=tr["i"],tr["entry"],tr["risk"]; last=min(i+H,S.N-1)
    peak=e; a0=atr(i) or 1e-9; maxdd_atr=0.0; maxdd_R=0.0; mfe=0.0; peak_bar=0
    for j in range(i+1,last+1):
        if S.H[j]>peak: peak=S.H[j]; peak_bar=j-i
        dd=(peak-S.L[j])
        maxdd_atr=max(maxdd_atr,dd/a0); maxdd_R=max(maxdd_R,dd/risk)
        mfe=max(mfe,(S.H[j]-e)/risk)
    return dict(mfe_R=round(mfe,1),peak_bar=peak_bar,maxpullback_ATR=round(maxdd_atr,2),maxpullback_R=round(maxdd_R,2))
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
def panel(Rs,bars):
    n=len(Rs); w=sum(1 for r in Rs if r>0); s=sum(Rs); g=sum(r for r in Rs if r>0); l=-sum(r for r in Rs if r<0)
    eq=0.0;peak=0.0;dd=0.0;stk=0;mst=0
    for r in Rs:
        eq+=r;peak=max(peak,eq);dd=min(dd,eq-peak);stk=stk+1 if r<=0 else 0;mst=max(mst,stk)
    ddv=abs(round(dd,1)) or 0.1
    return dict(sumR=round(s,1),WR=round(100*w/n),maxDD_R=round(dd,1),streak=mst,
        ret_DD=round(s/ddv,1),avgR=round(s/n,2),exits_gt3R=sum(1 for r in Rs if r>3),avg_bars=round(sum(bars)/n,1))

s34=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_approved34.json"))) if t]
f24=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]) if t]
tr31=[t for t in (mk(S.T[i]) for i in range(S.N) if scanner.evaluate(S,i).get("state")=="operational_candidate") if t]
cris={u(x["ts"]):x for x in json.load(open(HERE/"l1_cris_tp_extensions.json"))}
SETS=[("FINAL-24",f24),("SCANNER-31-V1",tr31),("ESTUDO-34",s34)]
H=300; TR=2000
res={"H":H,"sets":{}}
RULES=[("CHAND_4",lambda t:sim_chand(t,4,H)),("CHAND_5",lambda t:sim_chand(t,5,H)),
       ("CHAND_6",lambda t:sim_chand(t,6,H)),("CHAND_8",lambda t:sim_chand(t,8,H)),
       ("CHAND_10",lambda t:sim_chand(t,10,H)),("SWINGW_1",lambda t:sim_swing_wide(t,1.0,H))]
for name,trs in SETS:
    baseA=round(sum(sim_A(t,H) for t in trs),1); baseDD=0.0
    Rs=[sim_A(t,H) for t in trs]; eq=0;pk=0;dd=0
    for r in Rs: eq+=r;pk=max(pk,eq);dd=min(dd,eq-pk)
    o={"N":len(trs),"baseline_A":dict(sumR=baseA,maxDD_R=round(dd,1),ret_DD=round(baseA/(abs(dd) or .1),1)),"rules":{},"anatomy":{}}
    for rn,fn in RULES:
        sims=[fn(t) for t in trs]; o["rules"][rn]=panel([x[0] for x in sims],[x[1] for x in sims])
        # runner capture nos extendidos
        cap=sum(R for t,(R,_) in zip(trs,sims) if t["tsu"] in cris and cris[t["tsu"]].get("extended"))
        idl=sum(float(cris[t["tsu"]]["R_ideal"]) for t in trs if t["tsu"] in cris and cris[t["tsu"]].get("extended"))
        o["rules"][rn]["rcr"]=round(cap/idl,3) if idl>0 else None
    # anatomia de pullback (agregada)
    ana=[pullback_anatomy(t,H) for t in trs]
    winners=[a for a,t in zip(ana,trs) if sim_A(t,H)>0]
    o["anatomy"]=dict(
        n_winners=len(winners),
        median_maxpullback_ATR=round(statistics.median(a["maxpullback_ATR"] for a in ana),2),
        median_maxpullback_R=round(statistics.median(a["maxpullback_R"] for a in ana),2),
        winners_median_pullback_ATR=round(statistics.median(a["maxpullback_ATR"] for a in winners),2) if winners else None,
        winners_median_pullback_R=round(statistics.median(a["maxpullback_R"] for a in winners),2) if winners else None,
        pct_trades_pullback_le_2ATR=round(100*sum(1 for a in ana if a["maxpullback_ATR"]<=2)/len(ana)),
        pct_trades_pullback_le_4ATR=round(100*sum(1 for a in ana if a["maxpullback_ATR"]<=4)/len(ana)),
        median_MFE_R=round(statistics.median(a["mfe_R"] for a in ana),1))
    # null na melhor por ret_DD
    best=max(o["rules"],key=lambda r:o["rules"][r]["ret_DD"])
    fn=dict(RULES)[best]; Rb=[fn(t)[0] for t in trs]; obs=sum(Rb)
    per=[null_random(t,H,TR) for t in trs]; nsum=[sum(per[k][t] for k in range(len(trs))) for t in range(TR)]
    o["null_best_retDD"]=dict(rule=best,obs_sumR=round(obs,1),null_mean=round(statistics.mean(nsum),1),p_null_ge_obs=round(sum(1 for x in nsum if x>=obs)/TR,3))
    res["sets"][name]=o
(HERE/"l1_exit_trailing_wide_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
for name,_ in SETS:
    o=res["sets"][name]; b=o["baseline_A"]; a=o["anatomy"]
    print(f"\n=== {name} N={o['N']} | +3R: sumR={b['sumR']} DD={b['maxDD_R']} ret/DD={b['ret_DD']} ===")
    print(f"{'rule':>9} {'sumR':>6} {'WR':>3} {'DD':>5} {'strk':>4} {'ret/DD':>6} {'>3R':>3} {'rcr':>5} {'bars':>5}")
    for rn in [r[0] for r in RULES]:
        p=o["rules"][rn]; print(f"{rn:>9} {p['sumR']:>6} {p['WR']:>3} {p['maxDD_R']:>5} {p['streak']:>4} {p['ret_DD']:>6} {p['exits_gt3R']:>3} {str(p['rcr']):>5} {p['avg_bars']:>5}")
    print(f"  ANATOMIA pullback: mediana={a['median_maxpullback_ATR']}ATR / {a['median_maxpullback_R']}R | winners={a['winners_median_pullback_ATR']}ATR/{a['winners_median_pullback_R']}R | <=2ATR:{a['pct_trades_pullback_le_2ATR']}% <=4ATR:{a['pct_trades_pullback_le_4ATR']}% | MFE_med={a['median_MFE_R']}R")
    nb=o["null_best_retDD"]; print(f"  best ret/DD={nb['rule']}: obs={nb['obs_sumR']} null_mean={nb['null_mean']} p(null>=obs)={nb['p_null_ge_obs']}")
print("\nsaved l1_exit_trailing_wide_result.json")
