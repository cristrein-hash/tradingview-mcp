#!/usr/bin/env python3
"""Fecha o ponto (c) do DA: o benefício de DD/streak do CHAND_4 (tight chandelier) é robusto ou 2025?
Compara +3R vs CHAND_4 em: TODOS os anos · SÓ 2025 · EX-2025. Se em EX-2025 o CHAND_4 mantém DD/streak
melhores, o smoothing é robusto; se não, é artefato 2025. 3 conjuntos. Causal. Read-only. Output json."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent; REPO=L1.parents[4]
sys.path.insert(0,str(L1)); sys.path.insert(0,str(REPO/"my-strategy/core"))
import scanner
DATA=REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
S=scanner.build_series(); H=300
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
def sim_A(tr):
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]; t3=e+3*risk; last=min(i+H,S.N-1)
    for j in range(i+1,last+1):
        if S.L[j]<=st0: return -1.0
        if S.H[j]>=t3: return 3.0
    return round((S.C[last]-e)/risk,2)
def sim_c4(tr):
    i,e,st0,risk=tr["i"],tr["entry"],tr["stop0"],tr["risk"]; last=min(i+H,S.N-1); eff=st0; hh=S.H[i]
    for j in range(i+1,last+1):
        eff=max(eff,hh-4.0*atr(j-1),st0)
        if S.L[j]<=eff: return round((eff-e)/risk,2)
        hh=max(hh,S.H[j])
    return round((S.C[last]-e)/risk,2)
def panel(Rs):
    if not Rs: return dict(n=0)
    n=len(Rs);w=sum(1 for r in Rs if r>0);s=sum(Rs);eq=0.0;pk=0.0;dd=0.0;stk=0;mst=0
    for r in Rs:
        eq+=r;pk=max(pk,eq);dd=min(dd,eq-pk);stk=stk+1 if r<=0 else 0;mst=max(mst,stk)
    return dict(n=n,sumR=round(s,1),WR=round(100*w/n),maxDD_R=round(dd,1),streak=mst,ret_DD=round(s/(abs(dd) or .1),1))
f24=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_FINAL_regime_gated.json"))["trades"]) if t]
tr31=[t for t in (mk(S.T[i]) for i in range(S.N) if scanner.evaluate(S,i).get("state")=="operational_candidate") if t]
s34=[t for t in (mk(u(x["ts"])) for x in json.load(open(DATA/"l1_approved34.json"))) if t]
res={"H":H,"sets":{}}
for name,trs in [("FINAL-24",f24),("SCANNER-31-V1",tr31),("ESTUDO-34",s34)]:
    seg={}
    for lbl,sub in [("ALL",trs),("2025",[t for t in trs if t["year"]==2025]),("EX-2025",[t for t in trs if t["year"]!=2025])]:
        seg[lbl]=dict(A=panel([sim_A(t) for t in sub]),CHAND_4=panel([sim_c4(t) for t in sub]))
    res["sets"][name]=seg
(HERE/"l1_exit_chand4_ex2025_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
for name in res["sets"]:
    print(f"\n=== {name} ===")
    print(f"{'segmento':>9} {'exit':>8} {'n':>3} {'sumR':>6} {'WR':>3} {'DD':>5} {'strk':>4} {'ret/DD':>6}")
    for lbl in ["ALL","2025","EX-2025"]:
        for ex in ["A","CHAND_4"]:
            p=res["sets"][name][lbl][ex]
            if p.get("n"): print(f"{lbl:>9} {ex:>8} {p['n']:>3} {p['sumR']:>6} {p['WR']:>3} {p['maxDD_R']:>5} {p['streak']:>4} {p['ret_DD']:>6}")
print("\nsaved l1_exit_chand4_ex2025_result.json")
