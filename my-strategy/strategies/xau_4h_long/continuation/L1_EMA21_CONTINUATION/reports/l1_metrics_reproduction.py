#!/usr/bin/env python3
"""L1_METRICS_REPRODUCTION_DA — reproduz fail-loud as metricas canonicas L1 EMA21 4H LONG Continuation.
Read-only, sem producao/runtime/telegram/chart. Fontes: l1_FINAL_regime_gated.json (FINAL-24),
l1_approved34.json (estudo-34), scanner.py (config SL/target + full-scan operacional). Reporta divergencias,
NAO corrige silenciosamente. Output: l1_metrics_reproduction_result.json."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
div=[]; res={}
def panel_R(Rs):
    n=len(Rs); w=sum(1 for r in Rs if r>0); s=sum(Rs)
    gains=sum(r for r in Rs if r>0); losses=-sum(r for r in Rs if r<0)
    pf=round(gains/losses,2) if losses>0 else None
    return dict(N=n,W=w,L=n-w,WR=round(100*w/n) if n else 0,sumR=round(s,1),PF=pf)

# ---- 1. FINAL-24 (saved) ----
f24=json.load(open(DATA/"l1_FINAL_regime_gated.json"))
R24=[t["R"] for t in f24["trades"]]; p24=panel_R(R24); res["FINAL24"]=p24
exp24=dict(N=24,W=18,L=6,WR=75)
if not (p24["N"]==24 and p24["W"]==18 and p24["L"]==6 and p24["WR"]==75):
    div.append(f"FINAL-24 counts divergem: {p24} vs esperado {exp24}")
if abs(p24["sumR"]-45.2)>0.5: div.append(f"FINAL-24 sumR={p24['sumR']} vs esperado +45.2R (dif {p24['sumR']-45.2:+.1f})")

# ---- 2. estudo-34 (saved) ----
s34=json.load(open(DATA/"l1_approved34.json"))
R34=[t["R"] for t in s34]; p34=panel_R(R34)
res_breakdown={}
for t in s34: res_breakdown[t.get("res","?")]=res_breakdown.get(t.get("res","?"),0)+1
p34["res"]=res_breakdown; res["ESTUDO34"]=p34
if p34["N"]!=34: div.append(f"estudo-34 N={p34['N']} vs 34")
if abs(p34["sumR"]-35.2)>0.5: div.append(f"estudo-34 sumR={p34['sumR']} vs esperado +35.2R (V1) (dif {p34['sumR']-35.2:+.1f})")

# ---- 3. SL / exit config (scanner.py) ----
import scanner
sl_code_max = ("max(zone_OB_low, swing6_low)" in open(L1/"scanner.py").read())
res["SL_config"]=dict(SL_ATR_BUFFER=scanner.SL_ATR_BUFFER, TARGET_R=scanner.TARGET_R,
                      scanner_SL_rule="max(zone_OB_low,swing6_low)-0.1ATR" if sl_code_max else "zone_OB_low-0.1ATR",
                      OFICIAL_V1="zone_OB_low-0.1ATR (Cris 2026-07-03)")
if sl_code_max:
    div.append("SL DIVERGENCIA: scanner.py implementa max(zone,swing6)-0.1ATR (SUPERSEDED); OFICIAL=V1 zone_OB_low-0.1ATR")
if scanner.TARGET_R!=3.0: div.append(f"TARGET_R={scanner.TARGET_R} vs +3R")

# ---- 4. scanner full-scan: contagem operacional (deterministica, SL do scanner=max) ----
try:
    S=scanner.build_series(); op=0; states={}
    for i in range(S.N):
        try: ev=scanner.evaluate(S,i)
        except Exception: continue
        st=ev.get("state","?"); states[st]=states.get(st,0)+1
        if st in ("operational","operational_candidate"): op+=1
    res["SCANNER_fullscan"]=dict(bars=S.N,operational_raw=op,states=states,
        NOTE="operacional RAW pre-cooldown; realizacao 31 (17T/13S/1T/+40R) exige harness+forward-sim sob SL do scanner (=max, NAO V1); nenhum artifact salvo canonico dos 31 encontrado (rebuild_v2=NOT_VALIDATION,3 trades)")
except Exception as e:
    res["SCANNER_fullscan"]=dict(error=str(e)); div.append(f"scanner full-scan falhou: {e}")

res["divergences"]=div
res["verdict"]="PASS" if not div else ("PARTIAL" if (res["FINAL24"]["N"]==24 and res["FINAL24"]["W"]==18) else "FAIL")
(HERE/"l1_metrics_reproduction_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
