#!/usr/bin/env python3
"""FILTRO POR FAMÍLIA COM FEATURES ESPECÍFICAS (2026-07-06). Correção: o envelope usava 9 features
genéricas p/ todas as famílias; cada família discrimina por features DIFERENTES (mapa RAW MWU).
Envelope por-família usando SÓ as features discriminantes daquela família = mais apertado (menos
dimensões irrelevantes) + mais recall (não penaliza por feature que não separa). Baixar densidade
mantendo top-60. Depois: aplicar E6 no pool. Curva recall×densidade + null causal.
FEATURES por família (do ranking MWU winner-vs-sósia causal):
  BANDA: rsi_min8, poc_dist, vol_climax, nas_dist, flow_divergence
  FUNDO: sell_climax4, poc_dist, rsi_min8
  RASO:  nas_dist, rsi_min8, below_poc, vol_climax, poc_dist
Envelope = [q_lo, q_hi] das features específicas por família; evento passa se dentro em TODAS.
SEM look-ahead (feats causais até 3º cand). SANITY_PROBE: feats causais; envelope calibração
declarada por família; null permuta rótulo-fundo; recall círculo distinto; agregação evento."""
import json, bisect, hashlib
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]; HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]; WK = len({u["g_week"] for u in U})
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
def agg(ev, key, how):
    F=[u["_F"] for u in ev[:3]]
    return (min if how=="min" else max)(f[key] for f in F)
FAMFEAT = {
    "BANDA": [("rsi_min8","min"),("poc_dist","min"),("vol_climax","max"),("nas_dist","min"),("flow_divergence","max")],
    "FUNDO": [("sell_climax4","max"),("poc_dist","min"),("rsi_min8","min")],
    "RASO":  [("nas_dist","min"),("rsi_min8","min"),("below_poc","max"),("vol_climax","max"),("poc_dist","min")],
}
for ev in EV:
    ev[0]["_efam"]=ev[0]["_fam"]; ev[0]["_isf"]=any(u["_circ"] for u in ev)
    c=set()
    for u in ev: c|=u["_circ"]
    ev[0]["_cs"]=c
    ev[0]["_fv"]={fam:{k:agg(ev,k,h) for k,h in fs} for fam,fs in FAMFEAT.items()}
isf=np.array([ev[0]["_isf"] for ev in EV]); NF=int(isf.sum()); efam=np.array([ev[0]["_efam"] for ev in EV])
def circ(mask):
    c=set()
    for k,ev in zip(mask,EV):
        if k: c|=ev[0]["_cs"]
    return len(c)
def rep(mask,tag):
    kept=int(mask.sum()); kf=int((mask&isf).sum()); pool=[u for k,ev in zip(mask,EV) if k for u in ev]
    h=100*sum(1 for u in pool if R3[u["cj_t"]]["R3"]>=3)/len(pool) if pool else 0
    print(f"  {tag:<20} ev {kept:>3} fund {kf}/{NF} círc {circ(mask):>2}/60 prec {100*kf/max(1,kept):>4.1f}% dens {(kept-kf)/max(1,kf):>4.1f}:1 poolhit {h:.1f}%")
    return {"ev":kept,"kf":kf,"circ":circ(mask),"dens":round((kept-kf)/max(1,kf),1)}
def build(qlo,qhi):
    mask=np.zeros(len(EV),bool)
    for fam in ("RASO","BANDA","FUNDO"):
        idx=[i for i in range(len(EV)) if efam[i]==fam]; fidx=[i for i in idx if isf[i]]
        if len(fidx)<3:
            for i in idx: mask[i]=True
            continue
        env={}
        for k,h in FAMFEAT[fam]:
            vals=sorted(EV[i][0]["_fv"][fam][k] for i in fidx)
            env[k]=(vals[int(qlo*(len(vals)-1))], vals[int(qhi*(len(vals)-1))])
        for i in idx:
            fv2=EV[i][0]["_fv"][fam]
            if all(env[k][0]<=fv2[k]<=env[k][1] for k,_ in FAMFEAT[fam]): mask[i]=True
    for i in range(len(EV)):
        if efam[i]=="SEM": mask[i]=True
    return mask
print(f"eventos {len(EV)} · fundo {NF} · densidade base {(len(EV)-NF)/NF:.1f}:1")
out={}
for qlo,qhi,lab in ((0.0,1.0,"q0-100"),(0.02,0.98,"q02-98"),(0.05,0.95,"q05-95"),(0.10,0.90,"q10-90")):
    out[lab]=rep(build(qlo,qhi), f"famspec {lab}")
# null causal p/ q0-100
maskobs=build(0.0,1.0); obs_cut=len(EV)-int(maskobs.sum())
rng=np.random.default_rng(990); ge=0; NP=500
allidx=np.arange(len(EV))
for _ in range(NP):
    fm=np.zeros(len(EV),bool); fm[rng.choice(len(EV),NF,replace=False)]=True
    m=np.zeros(len(EV),bool)
    for fam in ("RASO","BANDA","FUNDO"):
        idx=[i for i in range(len(EV)) if efam[i]==fam]; fidx=[i for i in idx if fm[i]]
        if len(fidx)<3:
            for i in idx: m[i]=True
            continue
        env={}
        for k,h in FAMFEAT[fam]:
            vals=sorted(EV[i][0]["_fv"][fam][k] for i in fidx); env[k]=(vals[0],vals[-1])
        for i in idx:
            fv2=EV[i][0]["_fv"][fam]
            if all(env[k][0]<=fv2[k]<=env[k][1] for k,_ in FAMFEAT[fam]): m[i]=True
    for i in range(len(EV)):
        if efam[i]=="SEM": m[i]=True
    if (len(EV)-int(m.sum()))>=obs_cut: ge+=1
print(f"\nNULL famspec-q0-100 (50 aleatórios, {NP}×): P(corta>=obs)={ge/NP:.4f}")
# pipeline E6 no melhor
for ev in EV:
    min_flo=1e18
    for pos,u in enumerate(ev,1):
        ci=bisect.bisect_right(TS,u["cj_t"])-1; prevmin=min_flo
        u["_hl"]=int(u["_flo"]>prevmin+0.05*u["_a"]) if pos>1 else 0; min_flo=min(min_flo,u["_flo"])
        u["_reclaim"]=int(ci>=1 and CL[ci]>HI[ci-1] and CL[ci]>OP[ci])
def pipeline(mask,tag):
    pe=[ev for k,ev in zip(mask,EV) if k]
    def fst(ev):
        for u in ev:
            if u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1: return u
        return None
    rows=[fst(ev) for ev in pe if fst(ev)]
    if not rows: print(f"  {tag}: 0"); return
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
    print(f"  {tag:<16} N{len(rows)} WR {100*w/len(rows):.1f}% hit3R {100*h/len(rows):.1f}% NET {sum(nets):+.1f} DD {dd:.1f} stk-{mL} círc {len(cc)}/60 | {yr}")
print("\nPIPELINE E6 nos pools famspec:")
pipeline(build(0.0,1.0),"q0-100"); pipeline(build(0.05,0.95),"q05-95"); pipeline(build(0.10,0.90),"q10-90")
json.dump(out, open(HERE/"results"/"event_famspecific_filter_20260706.json","w"), indent=1, default=float)
print("OK → results/event_famspecific_filter_20260706.json")
