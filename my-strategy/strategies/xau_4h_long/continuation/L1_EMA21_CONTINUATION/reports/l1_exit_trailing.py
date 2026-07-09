#!/usr/bin/env python3
"""L1 EXIT REVIEW — TRAILING STOPS DE VERDADE (resposta à objeção do Cris).
As regras C/D anteriores eram strawman (saída no 1º close<EMA/swing = shakeout; stop NUNCA ratchetava).
Aqui: trailing RATCHET real, com buffer ATR, saída intrabar SÓ quando o preço bate o stop ELEVADO.
Todos causais: stop ativo no bar j usa highs/ATR/swings CONFIRMADOS até j-1 (nada do bar j).
Famílias:
  CHAND_k  = Chandelier: eff_stop = max(prev, max(H[i..j-1]) - k*ATR[j-1]), k in {2,3,4}
  ATRT_k   = ATR-trail:  eff_stop = max(prev, C[j-1] - k*ATR[j-1]), k in {2,3}
  RLAD     = R-ladder:   trail 1R atrás do pico-R confirmado (em degraus inteiros); stop_R=floor(maxR)-1
  SWBUF_b  = swing-ratchet + buffer: eff_stop = max(prev, maxSwingLow_conf - b*ATR[j-1]), b in {0.5,1.0}
Baseline A (+3R) e null (holding aleatório, mesma exposição) para separar edge de beta.
Horizontes 300 e FULL. Read-only RAW; sem produção/chart/commit. Output: l1_exit_trailing_result.json."""
import sys, json, statistics, random
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
SWING_N=scanner.SWING_N; random.seed(20260709)
S=scanner.build_series()
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

def sim_trail(tr,rule,H):
    """Devolve (R, exit_bar_k, kind). Stop ratchet causal (info<=j-1); saída intrabar no stop elevado.
    Também aplica floor estrutural stop0 desde o início."""
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]
    last=min(i+H,S.N-1); eff=st0; hh=S.H[i]; maxR=0.0
    for j in range(i+1,last+1):
        k=j-i
        aj=atr(j-1)                                   # ATR confirmado (<=j-1)
        # ---- nível do stop ATIVO durante o bar j (usa só info <= j-1) ----
        if rule.startswith("CHAND_"):
            kk=float(rule.split("_")[1]); cand=hh-kk*aj
        elif rule.startswith("ATRT_"):
            kk=float(rule.split("_")[1]); cand=S.C[j-1]-kk*aj
        elif rule=="RLAD":
            step=int(maxR)-1                          # trail 1R atrás do pico-R inteiro
            cand=e+step*risk if step>=1 else st0
        elif rule.startswith("SWBUF_"):
            bb=float(rule.split("_")[1]); sw=min(S.L[max(0,j-SWING_N):j]); cand=sw-bb*aj
        else: cand=st0
        eff=max(eff,cand,st0)                         # ratchet + nunca abaixo do stop0
        # ---- execução intrabar ----
        if S.L[j]<=eff:
            return round((eff-e)/risk,2),k,"trail_stop"
        # ---- atualizar picos CONFIRMADOS (para o próximo bar) ----
        hh=max(hh,S.H[j]); maxR=max(maxR,(S.H[j]-e)/risk)
    return round((S.C[last]-e)/risk,2),(last-i),"TIME"

def sim_A(tr,H):
    i,e,st0,risk,t3=tr["i"],tr["entry"],tr["stop0"],tr["risk"],tr["target3R"]
    last=min(i+H,S.N-1)
    for j in range(i+1,last+1):
        if S.L[j]<=st0: return -1.0
        if S.H[j]>=t3: return 3.0
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
def panel(Rs,bars,base3R,mfes):
    n=len(Rs); w=sum(1 for r in Rs if r>0); s=sum(Rs)
    g=sum(r for r in Rs if r>0); l=-sum(r for r in Rs if r<0)
    eq=0.0;peak=0.0;dd=0.0;stk=0;mst=0
    for r in Rs:
        eq+=r;peak=max(peak,eq);dd=min(dd,eq-peak); stk=stk+1 if r<=0 else 0; mst=max(mst,stk)
    return dict(n=n,sumR=round(s,1),WR=round(100*w/n),PF=round(g/l,2) if l>0 else None,
        avgR=round(s/n,2),maxDD_R=round(dd,1),streak=mst,exits_gt3R=sum(1 for r in Rs if r>3.0),
        base_winners_reverted=sum(1 for r,b in zip(Rs,base3R) if b and r<=0),
        avg_bars=round(sum(bars)/n,1),monumental_sumR=round(sum(Rs[k] for k in range(n) if mfes[k]>=6.0),1))

RULES=["CHAND_2","CHAND_3","CHAND_4","ATRT_2","ATRT_3","RLAD","SWBUF_0.5","SWBUF_1.0"]
s34=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_approved34.json"))) if t]
f24=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]) if t]
tr31=[t for t in (mk(S.T[i]) for i in range(S.N) if scanner.evaluate(S,i).get("state")=="operational_candidate") if t]
cris=json.load(open(HERE/"l1_cris_tp_extensions.json"))
extmap={u(x["ts"]):x for x in cris if x.get("extended")}
SETS=[("FINAL-24",f24),("SCANNER-31-V1",tr31),("ESTUDO-34",s34)]
res={"note":"trailing RATCHET real (Chandelier/ATR/R-ladder/swing+buffer) vs +3R + null","sets":{}}
TR=2000
for name,trs in SETS:
    base3R=[abs(sim_A(tr,60)-3.0)<1e-6 for tr in trs]
    mfes=[]
    for tr in trs:
        m=0.0
        for j in range(tr["i"]+1,min(tr["i"]+S.N,S.N-1)+1): m=max(m,(S.H[j]-tr["entry"])/tr["risk"])
        mfes.append(round(m,2))
    A48=round(sum(sim_A(tr,300) for tr in trs),1)
    o={"N":len(trs),"baseline_A_H300":A48,"by_horizon":{}}
    for H in [300,"FULL"]:
        HH=S.N if H=="FULL" else H; rr={}
        for rule in RULES:
            sims=[sim_trail(tr,rule,HH) for tr in trs]
            Rs=[x[0] for x in sims]; bars=[x[1] for x in sims]
            p=panel(Rs,bars,base3R,mfes)
            cap=sum(R for tr,(R,_,_) in zip(trs,sims) if tr["tsu"] in extmap)
            idl=sum(float(extmap[tr["tsu"]]["R_ideal"]) for tr in trs if tr["tsu"] in extmap)
            p["runner_capture_ratio"]=round(cap/idl,3) if idl>0 else None
            rr[rule]=p
        o["by_horizon"][str(H)]=rr
    # null + jackknife na melhor trailing por sumR @ H=300
    rr300=o["by_horizon"]["300"]
    best=max(RULES,key=lambda r:rr300[r]["sumR"])
    Rsb=[sim_trail(tr,best,300)[0] for tr in trs]; obs=sum(Rsb)
    per=[null_random(tr,300,TR) for tr in trs]
    nsum=[sum(per[k][t] for k in range(len(trs))) for t in range(TR)]
    pnull=sum(1 for x in nsum if x>=obs)/TR
    drops=[round(obs-r,1) for r in Rsb]
    o["robustness_H300"]=dict(best_rule=best,obs_sumR=round(obs,1),
        null_mean=round(statistics.mean(nsum),1),null_p95=round(sorted(nsum)[int(0.95*TR)],1),
        p_null_ge_obs=round(pnull,3),jack_min=min(drops),jack_max=max(drops),top_R=round(max(Rsb),1))
    res["sets"][name]=o
(HERE/"l1_exit_trailing_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
# print
for name,_ in SETS:
    o=res["sets"][name]; print(f"\n=== {name} N={o['N']} | baseline +3R (H300)={o['baseline_A_H300']}R ===")
    print(f"{'rule':>9} | {'H=300: sumR':>11} {'WR':>3} {'DD':>5} {'strk':>4} {'revW':>4} {'>3R':>3} {'monR':>6} {'rcr':>5} {'bars':>5} || {'FULL sumR':>9}")
    for rule in RULES:
        p=o['by_horizon']['300'][rule]; pf=o['by_horizon']['FULL'][rule]
        print(f"{rule:>9} | {p['sumR']:>11} {p['WR']:>3} {p['maxDD_R']:>5} {p['streak']:>4} {p['base_winners_reverted']:>4} {p['exits_gt3R']:>3} {p['monumental_sumR']:>6} {str(p['runner_capture_ratio']):>5} {p['avg_bars']:>5} || {pf['sumR']:>9}")
    rb=o['robustness_H300']
    print(f"  best@300={rb['best_rule']}: obs={rb['obs_sumR']}R  null_mean={rb['null_mean']} null_p95={rb['null_p95']} p(null>=obs)={rb['p_null_ge_obs']}  jack={rb['jack_min']}..{rb['jack_max']} top={rb['top_R']}")
print("\nsaved l1_exit_trailing_result.json")
