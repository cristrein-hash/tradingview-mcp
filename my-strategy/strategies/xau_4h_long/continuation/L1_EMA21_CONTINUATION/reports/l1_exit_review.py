#!/usr/bin/env python3
"""L1_EXIT_REVIEW — executa a matriz de exits do L1_EXIT_REVIEW_PREREG.md.
Baseline V1 (SL=zone_OB_low-0.1ATR, cutoff canónico H=60 barras recuperado empiricamente: reproduz
estudo-34 +35.2R 16T/16S/2TIME e FINAL-24 +45.2R byte-idênt). Exits A/B/B2/C/D/D2/E/C+E/D+E, todos
causais on-close, floor=SL0 intrabar. 3 conjuntos (FINAL-24 primário, Scanner-31 V1 secundário,
Estudo-34 terciário) rodados SEPARADO. Read-only sobre RAW; sem produção/chart/commit. Output:
l1_exit_review_result.json. Fail-loud: exit A tem de reproduzir baseline salvo (gate)."""
import sys, json, statistics
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
H=60                      # cutoff canónico (recuperado; ver _l1_exit_probe_horizon)
SWING_N=scanner.SWING_N   # 6
S=scanner.build_series()

def u(ts):
    if len(ts)==16: ts=ts+":00"
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())

def mk_trade(tsu):
    i=S.idx.get(tsu)
    if i is None: return None
    entry=S.C[i]; stop0=scanner.structural_sl(S,i)
    if not (entry-stop0>0): return None
    return dict(i=i,entry=entry,stop0=stop0,risk=entry-stop0,target3R=entry+3.0*(entry-stop0),tsu=tsu)

# ---------- exit engine (todos causais on-close; SL0 = floor intrabar sempre) ----------
def path_stats(tr):
    """MFE (R máx intrabar) + bar em que tocou 3R (para métricas de runner)."""
    i,e,st0,risk,t3=tr["i"],tr["entry"],tr["stop0"],tr["risk"],tr["target3R"]
    mfe=0.0; bar3=None; min_after3=None
    for k,j in enumerate(range(i+1,min(i+H,S.N-1)+1),1):
        r_hi=(S.H[j]-e)/risk; r_lo=(S.L[j]-e)/risk
        mfe=max(mfe,r_hi)
        if bar3 is None and S.H[j]>=t3: bar3=k
        if bar3 is not None:
            min_after3=r_lo if min_after3 is None else min(min_after3,r_lo)
    return dict(mfe=round(mfe,2),bar3=bar3,worst_after3=(round(min_after3,2) if min_after3 is not None else None))

def swing_low_before(j):
    lo=S.L[max(0,j-SWING_N):j]
    return min(lo) if lo else S.L[j]

def regime_before(j):
    st,_=scanner.latest_state_before(S.CLS,S.T[j]); return st

def sim(tr,rule):
    """Devolve (R, exit_bar_k, exit_kind). Regras causais; floor SL0 intrabar em TODAS."""
    i,e,st0,risk,t3=tr["i"],tr["entry"],tr["stop0"],tr["risk"],tr["target3R"]
    r1=e+1.0*risk                       # +1R price (activação de trails)
    activated=False; floor=st0; hit3=False
    last=min(i+H,S.N-1)
    for j in range(i+1,last+1):
        k=j-i; lo,hi,c=S.L[j],S.H[j],S.C[j]
        # activação +1R (intrabar) — para C/D/B2/D2
        if not activated and hi>=r1: activated=True
        if hi>=t3: hit3=True
        # 1) floor intrabar (SL0 ou breakeven elevado)
        if lo<=floor:
            return round((floor-e)/risk,2),k,"STOP"
        # 2) A: alvo fixo 3R intrabar
        if rule=="A" and hi>=t3:
            return 3.0,k,"TARGET"
        # 3) exits on-close (avaliados no close do bar j)
        exit_close=False; kind=None
        if rule in ("C","C+E") and activated and c<S.EMA21[j]:
            exit_close=True; kind="EMA21_close"
        if rule in ("D","D2","D+E") and activated and c<swing_low_before(j):
            exit_close=True; kind="swing_close"
        if rule in ("E","C+E","D+E") and regime_before(j)!="BULL":
            exit_close=True; kind="regime_flip"
        if exit_close:
            return round((c-e)/risk,2),k,kind
        # 4) elevar floor p/ breakeven (B2/D2) após +1R (a partir do próximo bar)
        if rule in ("B2","D2") and activated and floor<e:
            floor=e
    # horizonte: close do último bar
    R=(S.C[last]-e)/risk
    return round(R,2),(last-i),"TIME"

RULES=["A","B","B2","C","D","D2","E","C+E","D+E"]
RULE_DESC={"A":"fixed +3R (baseline)","B":"let-run raw (SL0+horizonte)",
  "B2":"let-run + breakeven pós+1R","C":"EMA21 close-trail pós+1R",
  "D":"swing-low close-trail pós+1R","D2":"swing-trail + breakeven pós+1R",
  "E":"regime-flip (BULL->não-BULL)","C+E":"EMA21-trail OU regime-flip","D+E":"swing-trail OU regime-flip"}

def panel(Rs,bars,kinds,base_win_flags,mfes):
    n=len(Rs); w=sum(1 for r in Rs if r>0); s=sum(Rs)
    g=sum(r for r in Rs if r>0); l=-sum(r for r in Rs if r<0)
    # maxDD (equity em R) + losing streak
    eq=0.0; peak=0.0; dd=0.0; st=0; mst=0
    for r in Rs:
        eq+=r; peak=max(peak,eq); dd=min(dd,eq-peak)
        if r<=0: st+=1; mst=max(mst,st)
        else: st=0
    over3=sum(1 for r in Rs if r>3.0)
    # winners baseline (R_A==3) revertidos a <=0
    reverted=sum(1 for r,bw in zip(Rs,base_win_flags) if bw and r<=0)
    monus=[i for i,m in enumerate(mfes) if m>=6.0]
    return dict(n=n,sumR=round(s,1),WR=round(100*w/n) if n else 0,
        PF=round(g/l,2) if l>0 else None,avgR=round(s/n,2) if n else 0,
        medianR=round(statistics.median(Rs),2) if Rs else 0,
        maxDD_R=round(dd,1),losing_streak=mst,exits_gt3R=over3,
        base_winners_reverted=reverted,avg_bars=round(sum(bars)/n,1) if n else 0)

def run_set(name,trades,cris_ext=None):
    # baseline A por trade (para flags de winner e reversão)
    baseA=[sim(tr,"A") for tr in trades]
    base_win=[R>0 for (R,_,_) in baseA]                    # winner baseline (R>0)
    base_3R=[abs(R-3.0)<1e-6 for (R,_,_) in baseA]         # exatamente +3R
    ps=[path_stats(tr) for tr in trades]
    mfes=[p["mfe"] for p in ps]
    out={"set":name,"N":len(trades),"H":H,"monumentals_mfe>=6R":sum(1 for m in mfes if m>=6.0),"rules":{}}
    for rule in RULES:
        sims=[sim(tr,rule) for tr in trades]
        Rs=[x[0] for x in sims]; bars=[x[1] for x in sims]; kinds=[x[2] for x in sims]
        pn=panel(Rs,bars,kinds,base_3R,mfes)
        # worst adverse after 3R (média sobre quem tocou 3R)
        wa=[p["worst_after3"] for p in ps if p["bar3"] is not None and p["worst_after3"] is not None]
        pn["worst_adv_after3R_avg"]=round(sum(wa)/len(wa),2) if wa else None
        # impacto monumentais (MFE>=6R): sumR desses trades sob a regra
        mon_idx=[i for i,m in enumerate(mfes) if m>=6.0]
        pn["monumental_sumR"]=round(sum(Rs[i] for i in mon_idx),1)
        pn["monumental_preserved"]=all(Rs[i]>0 for i in mon_idx)
        # runner-capture-ratio (só FINAL-24 c/ extensões)
        if cris_ext is not None:
            ext=[e for e in cris_ext if e.get("extended")]
            byu={u(e["ts"]):e for e in ext}
            cap=0.0; ideal=0.0
            for tr,(R,_,_) in zip(trades,sims):
                em=byu.get(tr["tsu"])
                if em: cap+=R; ideal+=float(em["R_ideal"])
            pn["runner_capture_ratio"]=round(cap/ideal,3) if ideal>0 else None
            pn["runner_captured_R"]=round(cap,1); pn["runner_ideal_R"]=round(ideal,1)
        out["rules"][rule]=pn
    return out,baseA

# ---------- montar os 3 conjuntos ----------
res={"H_cutoff":H,"rule_desc":RULE_DESC,"sets":{}}
gate_div=[]

# Estudo-34
s34=json.load(open(DATA/"l1_approved34.json"))
tr34=[mk_trade(u(t["ts"])) for t in s34]; tr34=[t for t in tr34 if t]
o34,_=run_set("ESTUDO-34",tr34)
if abs(o34["rules"]["A"]["sumR"]-35.2)>0.3: gate_div.append(f"A(estudo-34)={o34['rules']['A']['sumR']} != +35.2 baseline")
res["sets"]["ESTUDO-34"]=o34

# FINAL-24 (primário) + cris extensions
f24=json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]
cris=json.load(open(HERE/"l1_cris_tp_extensions.json"))
tr24=[mk_trade(u(t["ts"])) for t in f24]; tr24=[t for t in tr24 if t]
o24,_=run_set("FINAL-24",tr24,cris_ext=cris)
if abs(o24["rules"]["A"]["sumR"]-45.2)>0.3: gate_div.append(f"A(FINAL-24)={o24['rules']['A']['sumR']} != +45.2 baseline")
res["sets"]["FINAL-24"]=o24

# Scanner-31 V1 (secundário) — full-scan operacional
opers=[]
for i in range(S.N):
    try: ev=scanner.evaluate(S,i)
    except Exception: continue
    if ev.get("state")=="operational_candidate": opers.append(S.T[i])
tr31=[mk_trade(t) for t in opers]; tr31=[t for t in tr31 if t]
o31,_=run_set("SCANNER-31-V1",tr31)
if len(tr31)!=31: gate_div.append(f"scanner operacionais={len(tr31)} != 31")
if abs(o31["rules"]["A"]["sumR"]-34.2)>0.3: gate_div.append(f"A(scanner-31)={o31['rules']['A']['sumR']} != +34.2 baseline")
res["sets"]["SCANNER-31-V1"]=o31

res["gate_divergences"]=gate_div
res["gate"]="PASS" if not gate_div else "FAIL"
(HERE/"l1_exit_review_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))

# ---------- print resumo ----------
print(f"GATE (A reproduz baseline): {res['gate']}  div={gate_div}")
for sn in ["FINAL-24","SCANNER-31-V1","ESTUDO-34"]:
    o=res["sets"][sn]; A=o["rules"]["A"]
    print(f"\n=== {sn}  N={o['N']}  monumentais(MFE>=6R)={o['monumentals_mfe>=6R']}  baselineA sumR={A['sumR']} ===")
    print(f"{'rule':>4} {'sumR':>7} {'WR':>4} {'PF':>6} {'avgR':>6} {'medR':>6} {'maxDD':>7} {'strk':>5} {'>3R':>4} {'revW':>5} {'monR':>6} {'bars':>5}")
    for rule in RULES:
        p=o["rules"][rule]
        rc=f" rcr={p.get('runner_capture_ratio')}" if p.get('runner_capture_ratio') is not None else ""
        print(f"{rule:>4} {p['sumR']:>7} {p['WR']:>4} {str(p['PF']):>6} {p['avgR']:>6} {p['medianR']:>6} {p['maxDD_R']:>7} {p['losing_streak']:>5} {p['exits_gt3R']:>4} {p['base_winners_reverted']:>5} {p['monumental_sumR']:>6} {p['avg_bars']:>5}{rc}")
print("\nsaved l1_exit_review_result.json")
