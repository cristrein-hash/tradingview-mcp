#!/usr/bin/env python3
"""ACHAR A DIFERENÇA MATEMÁTICA fundo-vs-não-fundo (2026-07-07, Cris: existe, N<=100 recall alto).
Sobre os 926 pivôs (perna+reversão), computar features ESTRUTURAIS ricas (trajetória, não snapshot),
marcar os 42 fundos, e rankear por separação (MWU). Núcleo suspeito: ESCALA (pivô aparece em zigzag
r=6?) + SWEEP + duração da perna. Achar convergência N<=100 incluindo ao máximo os fundos.
SANITY_PROBE: features estruturais/trajetória causais; MWU rank fundo-vs-não; convergência; não
snapshot; não métrica-FN."""
import json, bisect, glob, math
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src=(HERE/"macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
N=len(S); ATR=[b.get("atr") or 5.0 for b in S]; HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; VOL=[float(b.get("v") or 0) for b in S]
days={}
for b in S:
    k=b["t"]//86400; g=days.setdefault(k,{"c":b["c"],"h":b["h"],"l":b["l"],"t":k*86400})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]; DT=[days[k]["t"] for k in DK]
TRd=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
ATRd=[sum(TRd[max(1,i-13):i+1])/max(1,len(TRd[max(1,i-13):i+1])) for i in range(len(DK))]
def ema15(i,n):
    a=CL[max(0,i-3*n):i+1]; k=2/(n+1); e=a[0]
    for v in a[1:]: e=v*k+e*(1-k)
    return e
def zz(r):
    lows=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
        elif d<=0 and HI[i]-LO[elo]>=r*a and elo<i:
            lows.append(elo); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
    return set(lows)
Z3=zz(3.0); Z45=zz(4.5); Z6=zz(6.0); Z9=zz(9.0)
PIV=sorted(Z3)
def choch_after(li, maxb=24):
    tl=TS[li]; hi=bisect.bisect_right(ET, TS[min(N-1,li+maxb)])
    lo=bisect.bisect_right(ET, tl)
    for m in range(lo,hi):
        if events[m]["tok"]=="CHoCH+": return round((events[m]["t"]-tl)/900)
    return None
feats=[]
for li in PIV:
    a=ATR[li] or 5.0; flo=LO[li]
    hp=max(HI[max(0,li-192):li+1]); drop=(hp-flo)/a
    rl=None
    for k in range(li,min(N,li+48)):
        if CL[k]>ema15(k,21): rl=k-li; break
    if not (drop>=4 and (choch_after(li) is not None or (rl is not None and rl<=6))): continue  # base v4
    # ESCALA: maior r em que o pivô é low (dedup por proximidade <=4 barras)
    def in_z(Z): return any(abs(li-z)<=4 for z in [li] ) and (li in Z or any(abs(li-z)<=4 and z in Z for z in range(li-4,li+5)))
    scale=3.0
    for r,Z in ((4.5,Z45),(6.0,Z6),(9.0,Z9)):
        if any((li+dd) in Z for dd in range(-4,5)): scale=r
    # SWEEP: flo varre o low das 32-96 barras anteriores
    prevlow=min(LO[max(0,li-96):li]) if li>0 else flo
    sweep=(prevlow-flo)/a
    # DURAÇÃO da perna (do high ao low)
    hi_i=max(range(max(0,li-192),li+1),key=lambda k:HI[k]); perna_bars=li-hi_i
    # perna de alta macro + retr
    di=bisect.bisect_right(DT,tl:=TS[li]-86400)-1
    upleg=0; retr=None
    if di>=50:
        seg=range(max(0,di-126),di+1); loi=min(seg,key=lambda i:DL[i]); hia=max(range(loi,di+1),key=lambda i:DH[i]) if loi<di else di
        upleg=(DH[hia]-DL[loi])/max(0.01,ATRd[di]); retr=(DH[hia]-flo)/max(0.01,(DH[hia]-DL[loi])) if DH[hia]>DL[loi] else None
    # volume climax no low
    v48=VOL[max(0,li-48):li]; vclimax=VOL[li]/(sum(v48)/len(v48)) if v48 and VOL[li] else 1.0
    feats.append({"li":li,"pt":TS[li],"drop":round(drop,1),"reclaim":rl,"scale":scale,"sweep":round(sweep,1),
                  "perna_bars":perna_bars,"upleg":round(upleg,1),"retr":round(retr,2) if retr else 0,"vclimax":round(vclimax,2)})
print(f"base (perna+reversão): {len(feats)}")
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FT=fundos
def is_fund(pt):
    j=bisect.bisect_left(FT,pt-14*3600); return j<len(FT) and FT[j]<=pt+14*3600
for f in feats: f["fund"]=int(is_fund(f["pt"]))
F=[f for f in feats if f["fund"]]; NF=[f for f in feats if not f["fund"]]
print(f"fundos no base: {len(F)}/{len(feats)}")
import statistics as st
def mwu(a,b):
    na,nb=len(a),len(b)
    if na<5 or nb<5: return 1.0
    allv=sorted([(v,0) for v in a]+[(v,1) for v in b]); ranks=[0]*len(allv); i=0
    while i<len(allv):
        j=i
        while j+1<len(allv) and allv[j+1][0]==allv[i][0]: j+=1
        for k in range(i,j+1): ranks[k]=(i+j)/2+1
        i=j+1
    Ra=sum(ranks[k] for k in range(len(allv)) if allv[k][1]==0); Ua=Ra-na*(na+1)/2; U=min(Ua,na*nb-Ua)
    mu=na*nb/2; sd=math.sqrt(na*nb*(na+nb+1)/12)
    return math.erfc(abs((U-mu)/sd)/math.sqrt(2)) if sd else 1.0
print("\n=== SEPARAÇÃO fundo-vs-não (MWU) por feature estrutural ===")
for k in ("scale","drop","sweep","perna_bars","upleg","retr","reclaim","vclimax"):
    a=[f[k] for f in F if f[k] is not None]; b=[f[k] for f in NF if f[k] is not None]
    print(f"  {k:<12} fund med {st.median(a):>7.2f} · não med {st.median(b):>7.2f} · MWU p={mwu(a,b):.4f}")
# distribuição de ESCALA fundo vs não
from collections import Counter
print("\nESCALA: fundos", dict(Counter(f['scale'] for f in F)), "· não", dict(Counter(f['scale'] for f in NF)))
# convergência buscando N<=100
def rec(sel):
    got=set()
    for f in sel:
        if f["fund"]: got.add(round(f["pt"]/3600))
    # recall por fundo distinto
    T=sorted(f["pt"] for f in sel); g=0
    for ft in FT:
        j=bisect.bisect_left(T,ft-14*3600)
        if j<len(T) and T[j]<=ft+14*3600: g+=1
    return g
# regime medio por pivo (E20 vs E40 dia)
def ema(v,n):
    k=2/(n+1); e=v[0]; o=[e]
    for x in v[1:]: e=x*k+e*(1-k); o.append(e)
    return o
E20=ema(DC,20); E40=ema(DC,40)
def reg_mid_at(pt):
    di=bisect.bisect_right(DT,pt-86400)-1
    if di<40: return "WARM"
    slope=(E20[di]-E20[di-20])/max(0.01,ATRd[di])
    if E20[di]>E40[di] and slope>0.3: return "BULL"
    if E20[di]<E40[di] and slope<-0.3: return "BEAR"
    return "RANGE"
for f in feats: f["reg"]=reg_mid_at(f["pt"])
print("\n=== DISCRIMINANTE POR REGIME (fundo-vs-não, MWU) ===")
for reg in ("BULL","RANGE","BEAR"):
    Fr=[f for f in F if f["reg"]==reg]; NFr=[f for f in NF if f["reg"]==reg]
    if len(Fr)<3: print(f"  {reg}: fundos {len(Fr)} (poucos)"); continue
    print(f"  --- {reg}: fundos {len(Fr)} · não {len(NFr)} ---")
    for k in ("drop","perna_bars","sweep","retr","upleg","scale","reclaim","vclimax"):
        a=[f[k] for f in Fr if f[k] is not None]; b=[f[k] for f in NFr if f[k] is not None]
        p=mwu(a,b)
        if p<0.06: print(f"      {k:<12} fund {st.median(a):>7.2f} · não {st.median(b):>7.2f} · p={p:.4f}")
# criterio por regime: convergencia das discriminantes fortes de cada regime
def recall_of(sel):
    T=sorted(f["pt"] for f in sel); g=0
    for ft in FT:
        j=bisect.bisect_left(T,ft-14*3600)
        if j<len(T) and T[j]<=ft+14*3600: g+=1
    return g
print("\n=== CRITÉRIOS POR REGIME (buscar N total <=100) ===")
crit={
 "BULL": lambda f: f["reg"]=="BULL" and f["retr"]>=0.15 and f["perna_bars"]>=60 and f["sweep"]>=-2.0,
 "RANGE": lambda f: f["reg"]=="RANGE" and f["drop"]>=8 and f["sweep"]>=-2.0,
 "BEAR": lambda f: f["reg"]=="BEAR" and f["drop"]>=8 and f["retr"]>=0.4,
}
tot=[]
for reg,fn in crit.items():
    sel=[f for f in feats if fn(f)]; tot+=sel
    fr=sum(f["fund"] for f in sel)
    print(f"  {reg}: n{len(sel)} · fundos-pivô {fr} · recall-região {recall_of(sel)}")
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json")); mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
g=recall_of(tot)
print(f"\nUNIÃO CRITÉRIOS: N total {len(tot)} · recall {g}/42")
T=sorted(f["pt"] for f in tot); missed=[ft for ft in FT if not (lambda j:(j<len(T) and T[j]<=ft+14*3600))(bisect.bisect_left(T,ft-14*3600))]
print("MISSED:", ", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
json.dump({"n_total":len(tot),"recall":g,"missed":[ds(m) for m in missed]},
          open(HERE/"results"/"bottom_discriminant_byregime_20260707.json","w"),indent=1)
print("OK2")

# SCORE POR REGIME + budget alocado (N<=100)
REGF={"BULL":["drop","sweep","perna_bars","upleg","scale","retr"],
      "RANGE":["perna_bars","sweep","upleg","drop"],
      "BEAR":["retr","drop","perna_bars"]}
byreg={r:[f for f in feats if f["reg"]==r] for r in ("BULL","RANGE","BEAR")}
for r,pool in byreg.items():
    if len(pool)<5: continue
    Fr=[f for f in pool if f["fund"]]; NFr=[f for f in pool if not f["fund"]]
    if len(Fr)<3: continue
    ks=REGF[r]; mu={k:st.mean([f[k] for f in pool]) for k in ks}; sdv={k:(st.pstdev([f[k] for f in pool]) or 1) for k in ks}
    w={k:abs(st.mean([f[k] for f in Fr])-st.mean([f[k] for f in NFr]))/sdv[k] for k in ks}
    for f in pool: f["rscore"]=sum(w[k]*((f[k]-mu[k])/sdv[k]) for k in ks)
budget={"BULL":60,"BEAR":28,"RANGE":12}
SEL=[]
for r,K in budget.items():
    pool=sorted([f for f in byreg[r] if "rscore" in f], key=lambda f:-f["rscore"])
    SEL+=pool[:K]
gsel=recall_of(SEL)
print(f"\n=== SCORE POR REGIME + budget (BULL60/BEAR28/RANGE12) ===")
print(f"N total {len(SEL)} · recall {gsel}/42")
T=sorted(f["pt"] for f in SEL)
missed2=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print("MISSED:", ", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed2))
# tentar budgets maiores se recall baixo
for tot_budget in (100,120,150):
    b={"BULL":int(tot_budget*0.6),"BEAR":int(tot_budget*0.28),"RANGE":int(tot_budget*0.12)}
    SS=[]
    for r,K in b.items():
        pool=sorted([f for f in byreg[r] if "rscore" in f], key=lambda f:-f["rscore"]); SS+=pool[:K]
    print(f"  budget {tot_budget}: N{len(SS)} recall {recall_of(SS)}/42")
json.dump({"budget_recall":gsel,"n":len(SEL)},open(HERE/"results"/"bottom_discriminant_scored_20260707.json","w"))
# cache dos pivôs+features p/ iteração leve de filtros (zona OB etc)
json.dump([{k:f[k] for k in ("li","pt","drop","reclaim","scale","sweep","perna_bars","upleg","retr","vclimax","fund","reg")} for f in feats],
          open(HERE/"results"/"bottom_pivots_cache_20260707.json","w"))
print("cache -> results/bottom_pivots_cache_20260707.json")
print("OK3")

# SCORE ponderado das features discriminantes (z na direcao fundo, peso=|z_med|/sd)
SF=["drop","perna_bars","sweep","retr","upleg","scale"]
mu={k:st.mean([f[k] for f in feats]) for k in SF}; sd={k:(st.pstdev([f[k] for f in feats]) or 1) for k in SF}
# peso pela separacao fundo-vs-nao (diff de medias normalizada)
w={}
for k in SF:
    w[k]=abs(st.mean([f[k] for f in F])-st.mean([f[k] for f in NF]))/sd[k]
for f in feats:
    f["score"]=sum(w[k]*((f[k]-mu[k])/sd[k]) for k in SF)
ranked=sorted(feats,key=lambda f:-f["score"])
print("\n=== SCORE ponderado — recall no TOP-N (achar N<=100) ===")
for topn in (60,80,100,120,150):
    sel=ranked[:topn]; g=rec(sel); nf=sum(f["fund"] for f in sel)
    print(f"  top-{topn}: recall {g}/42 · fundos-pivô no top {nf}")
# detalhar top-100
sel=ranked[:100]; got=set()
T=sorted(f["pt"] for f in sel)
missed=[]
for ft in FT:
    j=bisect.bisect_left(T,ft-14*3600)
    if not (j<len(T) and T[j]<=ft+14*3600): missed.append(ft)
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json")); mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
print(f"\nTOP-100 missed ({len(missed)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
json.dump({"n_base":len(feats),"n_fund":len(F),"weights":{k:round(w[k],2) for k in SF},
           "top100_recall":42-len(missed),"top100_missed":[ds(m) for m in missed]},
          open(HERE/"results"/"bottom_discriminant_20260707.json","w"),indent=1)
print("OK")
