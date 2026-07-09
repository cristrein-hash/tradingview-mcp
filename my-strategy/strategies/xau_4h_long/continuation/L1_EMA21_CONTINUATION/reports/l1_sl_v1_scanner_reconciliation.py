#!/usr/bin/env python3
"""L1 SL V1 SCANNER RECONCILIATION — pós-alinhamento do scanner.py ao SL oficial V1 (zone_OB_low-0.1ATR).
Corre o scanner (V1) -> 31 operacionais; casa com outcomes canónicos V1 do estudo-34 (l1_approved34.json);
cross-check por forward-sim first-touch (H/L do RAW); gera artifact salvo scanner-31 sob V1. Reproduz
FINAL-24 + estudo-34 (inalterados). Read-only sobre dados; sem produção/runtime/chart. Fail-loud."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
def to_unix(ts):
    if len(ts)==16: ts=ts+":00"
    return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def panel(Rs):
    n=len(Rs); w=sum(1 for r in Rs if r>0); s=sum(Rs)
    g=sum(r for r in Rs if r>0); l=-sum(r for r in Rs if r<0)
    return dict(N=n,W=w,L=n-w,WR=round(100*w/n) if n else 0,sumR=round(s,1),PF=round(g/l,2) if l>0 else None)
div=[]; res={}

# ---- confirmar V1 no scanner ----
sl_src=open(L1/"scanner.py").read()
v1_ok = ("V1: zone_OB_low APENAS" in sl_src) and ("base = dz[1]" in sl_src)
res["scanner_SL_rule"]="V1 zone_OB_low-0.1ATR" if v1_ok else "NAO-V1"
if not v1_ok: div.append("scanner.py NÃO está em V1 após edição")
res["TARGET_R"]=scanner.TARGET_R
if scanner.TARGET_R!=3.0: div.append(f"TARGET_R={scanner.TARGET_R} != 3.0")

# ---- FINAL-24 + estudo-34 (saved, inalterados) ----
f24=json.load(open(DATA/"l1_FINAL_regime_gated.json")); R24=[t["R"] for t in f24["trades"]]
res["FINAL24"]=panel(R24)
if abs(res["FINAL24"]["sumR"]-45.2)>0.5: div.append(f"FINAL-24 sumR={res['FINAL24']['sumR']} != +45.2")
s34=json.load(open(DATA/"l1_approved34.json")); R34=[t["R"] for t in s34]
res["ESTUDO34"]=panel(R34)
if abs(res["ESTUDO34"]["sumR"]-35.2)>0.5: div.append(f"estudo-34 sumR={res['ESTUDO34']['sumR']} != +35.2")
study_by_u={to_unix(t["ts"]):t for t in s34}

# ---- scanner (V1) full-scan -> 31 operacionais ----
S=scanner.build_series()
opers=[]
for i in range(S.N):
    try: ev=scanner.evaluate(S,i)
    except Exception: continue
    if ev.get("state")=="operational_candidate":
        opers.append(dict(i=i,ts=ev["timestamp"],entry=ev["entry_price"],sl_v1=ev["stop_price"],target=ev["target_price"],unix=S.T[i]))
res["scanner_operational_count"]=len(opers)
if len(opers)!=31: div.append(f"scanner operacionais={len(opers)} != 31")

# forward-sim first-touch (cross-check) + match ao estudo-34 (outcome canónico V1)
def firsttouch(i,entry,stop,target,cap=200):
    for j in range(i+1,min(i+cap,S.N-1)+1):
        lo=S.L[j]; hi=S.H[j]
        if lo<=stop and hi>=target: return "STOP"   # conservador
        if lo<=stop: return "STOP"
        if hi>=target: return "TARGET"
    return "TIME"
art=[]; mismatch=[]; unmatched=[]
for o in opers:
    st=study_by_u.get(o["unix"])
    ft=firsttouch(o["i"],o["entry"],o["sl_v1"],o["target"]) if (o["sl_v1"] and o["target"]) else "NA"
    if st is None:
        unmatched.append(o["ts"]); outcome=None; R=None; mfe=None
    else:
        outcome=st.get("res"); R=st.get("R"); mfe=st.get("mfe")
        if outcome!=ft: mismatch.append({"ts":o["ts"],"study_res":outcome,"forwardsim":ft})
    art.append(dict(ts=o["ts"],entry=o["entry"],sl_v1=o["sl_v1"],target=o["target"],
                    outcome=outcome,R=R,mfe=mfe,forwardsim_check=ft,
                    source="scanner.py(V1) entry/sl/target + outcome canónico V1 de l1_approved34.json (match by unix ts)"))
res["scanner31_v1"]=panel([a["R"] for a in art if a["R"] is not None])
res["scanner31_v1"]["res"]={}
for a in art:
    if a["outcome"]: res["scanner31_v1"]["res"][a["outcome"]]=res["scanner31_v1"]["res"].get(a["outcome"],0)+1
res["scanner31_v1"]["monumentais_mfe>=6R"]=sum(1 for a in art if (a["mfe"] or 0)>=6)
res["scanner31_v1"]["unmatched_ts"]=unmatched
res["scanner31_v1"]["forwardsim_mismatches"]=mismatch
# os 3 do estudo-34 fora dos 31 (exhaustion esperado #26/#31/#47)
oper_u=set(o["unix"] for o in opers); extra34=[t["ts"] for t in s34 if to_unix(t["ts"]) not in oper_u]
res["estudo34_menos_scanner31"]=extra34
if len(unmatched)>0: div.append(f"scanner-31: {len(unmatched)} operacionais SEM match no estudo-34: {unmatched}")

res["divergences"]=div
res["verdict"]="PASS" if (v1_ok and len(opers)==31 and len(unmatched)==0 and abs(res['FINAL24']['sumR']-45.2)<0.5 and abs(res['ESTUDO34']['sumR']-35.2)<0.5) else "PARTIAL"
(HERE/"l1_sl_v1_scanner_reconciliation_result.json").write_text(json.dumps({**res,"scanner31_v1_trades":art},indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
