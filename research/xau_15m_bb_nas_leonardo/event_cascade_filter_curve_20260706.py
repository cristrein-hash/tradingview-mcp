#!/usr/bin/env python3
"""CASCATA COMO FILTRO DE EVENTO — curva por limiar (2026-07-06). A cascata SMC é o degrau causal.
Como FILTRO de evento (evento contém candidato com cascade>=T entre os 1os), varrer T e combinar com
família p/ achar densidade baixa com recall alto. Depois E6 no pool. TUDO causal (cascade t<=cj).
+ combinar cascade-filter com o envelope-família e medir a curva recall×densidade×WR-final.
SANITY_PROBE: cascade causal; envelope família causal; recall círculo; pipeline E6 (cascade&hl&reclaim)
com null-episódio; sub-ano."""
import json, bisect, hashlib, random
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N=len(S); ATR=[b.get("atr") or 5.0 for b in S]; HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; OP=[b.get("o",b["c"]) for b in S]
CACHE={r["cj_t"]:r for r in (json.loads(l) for l in open(HERE/"results"/"raw_feature_cache_20260706.jsonl"))}
UNIV=sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u:u["cj_t"]); UT=[u["cj_t"] for u in UNIV]; WK=len({u["g_week"] for u in U})
LOWS=[]; d0=0; ehi=elo=0
for i in range(1,N):
    if HI[i]>HI[ehi]: ehi=i
    if LO[i]<LO[elo]: elo=i
    if d0>=0 and HI[ehi]-LO[i]>=6*ATR[i] and ehi<i: d0=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    elif d0<=0 and HI[i]-LO[elo]>=6*ATR[i] and elo<i: LOWS.append((i,elo)); d0=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
KLOW=[x[0] for x in LOWS]
for u in UNIV:
    u["_flo"]=u["g_sl"]+0.1*(u.get("g_atr") or 5.0); u["_a"]=u.get("g_atr") or 5.0; u["_circ"]=set(); u["_F"]=CACHE[u["cj_t"]]; u["_casc"]=cascade(u["cj_t"])
    ci=bisect.bisect_right(TS,u["cj_t"])-1; j=bisect.bisect_right(KLOW,ci)-1; u["_fam"]="SEM"
    if j>=0:
        _,l0i=LOWS[j]; L0=LO[l0i]; H1=max(HI[k] for k in range(l0i,ci+1))
        if H1-L0>1e-9:
            r=(H1-u["_flo"])/(H1-L0); u["_fam"]="RASO" if r<0.5 else ("BANDA" if r<=1.3 else "FUNDO")
for gi,g in enumerate(GT):
    j=bisect.bisect_left(UT,g["flush_t"]-8*3600)
    while j<len(UNIV) and UT[j]<=g["flush_t"]+8*3600:
        u=UNIV[j]; dd=u["_flo"]-g["flush_low"]
        if -3*u["_a"]<=dd<=1*u["_a"]: u["_circ"].add(gi)
        j+=1
EV=[]; cur=[]
for u in UNIV:
    if cur and u["cj_t"]-cur[-1]["cj_t"]<=48*3600 and abs(u["_flo"]-cur[-1]["_flo"])<=3*u["_a"]: cur.append(u)
    else:
        if cur: EV.append(cur)
        cur=[u]
if cur: EV.append(cur)
FEATS=["rsi_min8","nas_dist","sell_climax4","below_poc","poc_dist","nas_long_rec","vol_climax","flow_divergence"]
def vec(ev):
    F=[u["_F"] for u in ev[:3]]; st_i=bisect.bisect_right(TS,ev[0]["cj_t"])-1; a=ev[0]["_a"]; pre_hi=max(HI[max(0,st_i-96):st_i+1]); ei=bisect.bisect_right(TS,ev[:3][-1]["cj_t"])-1
    return [min(f["rsi_min8"] for f in F),min(f["nas_dist"] for f in F),max(f["sell_climax4"] for f in F),max(f["below_poc"] for f in F),min(f["poc_dist"] for f in F),max(f["nas_long_rec"] for f in F),max(f["vol_climax"] for f in F),max(f["flow_divergence"] for f in F),(pre_hi-min(LO[max(0,st_i-8):ei+1]))/a]
for ev in EV:
    ev[0]["_vec"]=vec(ev); ev[0]["_isf"]=any(u["_circ"] for u in ev); ev[0]["_efam"]=ev[0]["_fam"]
    ev[0]["_cmax"]=max(u["_casc"] for u in ev[:6])
    c=set()
    for u in ev: c|=u["_circ"]
    ev[0]["_cs"]=c
    min_flo=1e18
    for pos,u in enumerate(ev,1):
        ci=bisect.bisect_right(TS,u["cj_t"])-1; prevmin=min_flo
        u["_hl"]=int(u["_flo"]>prevmin+0.05*u["_a"]) if pos>1 else 0; min_flo=min(min_flo,u["_flo"])
        u["_reclaim"]=int(ci>=1 and CL[ci]>HI[ci-1] and CL[ci]>OP[ci])
X=np.array([ev[0]["_vec"] for ev in EV]); isf=np.array([ev[0]["_isf"] for ev in EV]); efam=np.array([ev[0]["_efam"] for ev in EV]); cmax=np.array([ev[0]["_cmax"] for ev in EV]); NF=int(isf.sum())
def fam_env(fund_mask):
    m=np.zeros(len(EV),bool)
    for fam in ("RASO","BANDA","FUNDO","SEM"):
        idx=np.where(efam==fam)[0]; fidx=np.where((efam==fam)&fund_mask)[0]
        if len(fidx)<3: m[idx]=True; continue
        lo=X[fidx].min(0); hi=X[fidx].max(0)
        for i in idx:
            if np.all((X[i]>=lo)&(X[i]<=hi)): m[i]=True
    return m
FAM=fam_env(isf)
def circ(mask):
    c=set()
    for k,ev in zip(mask,EV):
        if k: c|=ev[0]["_cs"]
    return len(c)
def pipeline(mask):
    pe=[ev for k,ev in zip(mask,EV) if k]
    def fst(ev):
        for u in ev:
            if u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1: return u
        return None
    return [fst(ev) for ev in pe if fst(ev)]
def wr(rows):
    if not rows: return None
    nets=[R3[r["cj_t"]]["net3"] for r in sorted(rows,key=lambda x:x["cj_t"])]
    h=sum(1 for r in rows if R3[r["cj_t"]]["R3"]>=3); w=sum(1 for x in nets if x>0); eq=pk=dd=0.0; mL=cl=0
    for x in nets:
        eq+=x;pk=max(pk,eq);dd=min(dd,eq-pk)
        if x<=0: cl+=1;mL=max(mL,cl)
        else: cl=0
    yr={}
    for r in rows: yr[r["yr"]]=round(yr.get(r["yr"],0)+R3[r["cj_t"]]["net3"],1)
    cc=set()
    for r in rows: cc|=r["_circ"]
    return dict(n=len(rows),wr=round(100*w/len(rows),1),hit=round(100*h/len(rows),1),net=round(sum(nets),1),dd=round(dd,1),stk=mL,circ=len(cc),yr=yr)
print(f"eventos {len(EV)} · fundo {NF}")
print(f"\nCASCADE-FILTER (evento tem cascade>=T) × FAMÍLIA — filtro + pipeline E6:")
for T in (2,3,4):
    mask=FAM & (cmax>=T)
    kept=int(mask.sum()); kf=int((mask&isf).sum())
    p=wr(pipeline(mask))
    print(f"  família & casc>={T}: ev {kept:>3} fund {kf}/{NF} círc {circ(mask):>2}/60 dens {(kept-kf)/max(1,kf):>4.1f}:1")
    if p: print(f"      pipeline E6: N{p['n']} WR {p['wr']}% hit3R {p['hit']}% NET {p['net']:+} DD {p['dd']} stk-{p['stk']} círc {p['circ']}/60 | {p['yr']}")
# só cascade-filter (sem família)
print("\nCASCADE-FILTER só (sem família):")
for T in (2,3,4):
    mask=(cmax>=T)
    p=wr(pipeline(mask))
    kept=int(mask.sum()); kf=int((mask&isf).sum())
    print(f"  casc>={T}: ev {kept} fund {kf}/{NF} círc {circ(mask)}/60 dens {(kept-kf)/max(1,kf):.1f}:1"
          + (f" · E6 N{p['n']} WR {p['wr']}% stk-{p['stk']} círc {p['circ']} | {p['yr']}" if p else ""))
print("OK")
