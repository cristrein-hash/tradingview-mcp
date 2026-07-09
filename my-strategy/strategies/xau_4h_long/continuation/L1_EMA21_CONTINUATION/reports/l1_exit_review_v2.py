#!/usr/bin/env python3
"""L1_EXIT_REVIEW v2 — corrige os 2 FLAWs do DA:
 (1) HORIZONTE: H=60 truncava a tese de runners (TPs do Cris duram 1-3 MESES). Roda H in
     {60,150,300,600,FULL} para testar de facto a captura de continuação.
 (2) CAUSALIDADE E: regime agora STRICT prior-day (floor à meia-noite -> só classificações de dias
     ANTERIORES; elimina o same-day daily-close look-ahead que o DA apontou).
 + jackknife-1 (concentração) + exit-null (holding aleatório) na melhor regra por conjunto/horizonte.
Baseline V1 (SL=zone_OB_low-0.1ATR). Read-only RAW; sem produção/chart/commit.
Output: l1_exit_review_v2_result.json."""
import sys, json, statistics, random
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
SWING_N=scanner.SWING_N
S=scanner.build_series()
DAY=86400
random.seed(20260709)

def u(ts):
    if len(ts)==16: ts=ts+":00"
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def mk(tsu):
    i=S.idx.get(tsu)
    if i is None: return None
    e=S.C[i]; st0=scanner.structural_sl(S,i)
    if not (e-st0>0): return None
    return dict(i=i,entry=e,stop0=st0,risk=e-st0,target3R=e+3.0*(e-st0),tsu=tsu)

_REG=[None]*S.N   # regime strict prior-day por-bar (pré-computado 1x; lookup O(1))
for _j in range(S.N):
    _mid=(S.T[_j]//DAY)*DAY
    _st,_=scanner.latest_state_before(S.CLS,_mid); _REG[_j]=_st
def regime_strict(j):
    """STRICT prior-day: floor T[j] à meia-noite UTC -> só classificações de dias ANTERIORES (O(1))."""
    return _REG[j]
def swing_low_before(j):
    lo=S.L[max(0,j-SWING_N):j]; return min(lo) if lo else S.L[j]

def sim(tr,rule,H):
    i,e,st0,risk,t3=tr["i"],tr["entry"],tr["stop0"],tr["risk"],tr["target3R"]
    r1=e+risk; activated=False; floor=st0
    last=min(i+H,S.N-1)
    for j in range(i+1,last+1):
        k=j-i; lo,hi,c=S.L[j],S.H[j],S.C[j]
        if not activated and hi>=r1: activated=True
        if lo<=floor: return round((floor-e)/risk,2),k,"STOP"
        if rule=="A" and hi>=t3: return 3.0,k,"TARGET"
        ec=False
        if rule in ("C","C+E") and activated and c<S.EMA21[j]: ec=True
        if rule in ("D","D2","D+E") and activated and c<swing_low_before(j): ec=True
        if rule in ("E","C+E","D+E") and regime_strict(j)!="BULL": ec=True
        if ec: return round((c-e)/risk,2),k,"close_exit"
        if rule in ("B2","D2") and activated and floor<e: floor=e
    return round((S.C[last]-e)/risk,2),(last-i),"TIME"

def null_random(tr,H,ntrial=2000):
    """null: mesmo SL0 floor, mas sai num bar ALEATÓRIO in [1,exposure]. Testa se a regra estrutural
    bate holding aleatório com mesma exposição."""
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]
    last=min(i+H,S.N-1); span=last-i
    if span<1: return [0.0]*ntrial
    out=[]
    for _ in range(ntrial):
        kx=random.randint(1,span); Rk=None
        for j in range(i+1,i+kx+1):
            if S.L[j]<=st0: Rk=(st0-e)/risk; break
        if Rk is None: Rk=(S.C[i+kx]-e)/risk
        out.append(Rk)
    return out

RULES=["A","B","B2","C","D","D2","E","C+E","D+E"]
def panel(Rs,bars,base3R,mfes):
    n=len(Rs); w=sum(1 for r in Rs if r>0); s=sum(Rs)
    g=sum(r for r in Rs if r>0); l=-sum(r for r in Rs if r<0)
    eq=0.0;peak=0.0;dd=0.0;stk=0;mst=0
    for r in Rs:
        eq+=r;peak=max(peak,eq);dd=min(dd,eq-peak)
        stk=stk+1 if r<=0 else 0; mst=max(mst,stk)
    return dict(n=n,sumR=round(s,1),WR=round(100*w/n) if n else 0,PF=round(g/l,2) if l>0 else None,
        avgR=round(s/n,2) if n else 0,medianR=round(statistics.median(Rs),2) if Rs else 0,
        maxDD_R=round(dd,1),streak=mst,exits_gt3R=sum(1 for r in Rs if r>3.0),
        base_winners_reverted=sum(1 for r,b in zip(Rs,base3R) if b and r<=0),
        avg_bars=round(sum(bars)/n,1) if n else 0,
        monumental_sumR=round(sum(Rs[k] for k in range(n) if mfes[k]>=6.0),1))
def jack1(Rs):
    s=sum(Rs); drops=[round(s-r,1) for r in Rs]
    return dict(full=round(s,1),jack_min=min(drops),jack_max=max(drops),
                most_influential_R=round(max(Rs),1))

def run_set(name,trades,horizons,cris=None):
    base3R={}; mfes=[]
    # MFE full-horizon (para flag monumental) + baseline exato 3R (H=60 first-touch)
    for tr in trades:
        R,_,_=sim(tr,"A",60); base3R[tr["tsu"]]=abs(R-3.0)<1e-6
    Hfull=S.N
    for tr in trades:
        m=0.0
        for j in range(tr["i"]+1,min(tr["i"]+Hfull,S.N-1)+1):
            m=max(m,(S.H[j]-tr["entry"])/tr["risk"])
        mfes.append(round(m,2))
    b3=[base3R[tr["tsu"]] for tr in trades]
    out={"set":name,"N":len(trades),"monumentals_mfe>=6R":sum(1 for m in mfes if m>=6.0),"by_horizon":{}}
    for H in horizons:
        HH=S.N if H=="FULL" else H
        rr={}
        for rule in RULES:
            sims=[sim(tr,rule,HH) for tr in trades]
            Rs=[x[0] for x in sims]; bars=[x[1] for x in sims]
            p=panel(Rs,bars,b3,mfes)
            if cris is not None:
                ext=[x for x in cris if x.get("extended")]; byu={u(x["ts"]):x for x in ext}
                cap=sum(R for tr,(R,_,_) in zip(trades,sims) if byu.get(tr["tsu"]))
                idl=sum(float(byu[tr["tsu"]]["R_ideal"]) for tr in trades if byu.get(tr["tsu"]))
                p["runner_capture_ratio"]=round(cap/idl,3) if idl>0 else None
            rr[rule]=p
        out["by_horizon"][str(H)]=rr
    return out,b3,mfes

res={"note":"v2: strict prior-day regime + horizontes estendidos + jackknife + null (corrige FLAWs DA)",
     "horizons":[60,150,300,600,"FULL"],"sets":{}}
s34=[mk(u(t["ts"])) for t in json.load(open(DATA/"l1_approved34.json"))]; s34=[t for t in s34 if t]
f24=[mk(u(t["ts"])) for t in json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]]; f24=[t for t in f24 if t]
cris=json.load(open(HERE/"l1_cris_tp_extensions.json"))
opers=[S.T[i] for i in range(S.N) if (lambda ev: ev.get("state")=="operational_candidate")(scanner.evaluate(S,i))]
tr31=[mk(t) for t in opers]; tr31=[t for t in tr31 if t]
HZ=[60,150,300,600,"FULL"]
o24,b3_24,mfe24=run_set("FINAL-24",f24,HZ,cris=cris); res["sets"]["FINAL-24"]=o24
o31,b3_31,mfe31=run_set("SCANNER-31-V1",tr31,HZ); res["sets"]["SCANNER-31-V1"]=o31
o34,_,_=run_set("ESTUDO-34",s34,HZ); res["sets"]["ESTUDO-34"]=o34

# jackknife + null na melhor regra (por sumR) de cada conjunto no horizonte FULL
res["robustness_FULL"]={}
for name,trs in [("FINAL-24",f24),("SCANNER-31-V1",tr31),("ESTUDO-34",s34)]:
    rr=res["sets"][name]["by_horizon"]["FULL"]
    best=max((r for r in RULES if r!="A"),key=lambda r:rr[r]["sumR"])
    Rs=[sim(tr,best,S.N)[0] for tr in trs]
    nulls=[]
    for tr in trs: nulls.append(sum(null_random(tr,S.N)) if False else None)  # placeholder per-trade
    # exit-null agregado: soma de R sob exit aleatório, distribuição
    trials=2000; null_sums=[0.0]*trials
    per=[null_random(tr,S.N,trials) for tr in trs]
    for t in range(trials): null_sums[t]=sum(per[k][t] for k in range(len(trs)))
    obs=sum(Rs); pval=sum(1 for x in null_sums if x>=obs)/trials
    res["robustness_FULL"][name]=dict(best_rule=best,obs_sumR=round(obs,1),
        jackknife=jack1(Rs),
        null_mean=round(statistics.mean(null_sums),1),null_p95=round(sorted(null_sums)[int(0.95*trials)],1),
        null_p_ge_obs=round(pval,3),baseline_A_H60=round(sum(sim(tr,"A",60)[0] for tr in trs),1))

(HERE/"l1_exit_review_v2_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
# print
for sn in ["FINAL-24","SCANNER-31-V1","ESTUDO-34"]:
    o=res["sets"][sn]; print(f"\n=== {sn} N={o['N']} monum(MFE>=6R)={o['monumentals_mfe>=6R']} ===")
    print(f"{'H':>5} "+" ".join(f"{r:>6}" for r in RULES)+"   (sumR; A=baseline)")
    for H in HZ:
        rr=o["by_horizon"][str(H)]
        print(f"{str(H):>5} "+" ".join(f"{rr[r]['sumR']:>6}" for r in RULES))
    # detalhe FULL da melhor
    rb=res["robustness_FULL"][sn]; bh=o["by_horizon"]["FULL"][rb["best_rule"]]
    print(f"  FULL best={rb['best_rule']}: sumR={bh['sumR']} WR={bh['WR']} maxDD={bh['maxDD_R']} strk={bh['streak']} revW={bh['base_winners_reverted']} monR={bh['monumental_sumR']} rcr={bh.get('runner_capture_ratio')} bars={bh['avg_bars']}")
    print(f"       jackknife={rb['jackknife']}  null_mean={rb['null_mean']} null_p95={rb['null_p95']} p(null>=obs)={rb['null_p_ge_obs']}  baseA(H60)={rb['baseline_A_H60']}")
print("\nsaved l1_exit_review_v2_result.json")
