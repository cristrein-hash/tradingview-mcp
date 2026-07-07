#!/usr/bin/env python3
"""DETECTOR DE FUNDO v3 — CONTEXTO ESTRUTURAL PRÉVIO primeiro (2026-07-07, correção Cris: nunca
snapshot sem contexto estrutural). Para CADA pivô-low candidato (zigzag causal), computar o CONTEXTO
ESTRUTURAL dos ~6-9 meses anteriores (causal, agregação dia) ANTES de qualquer discriminação:
  - regime multi-escala (secular/médio) no known_at
  - retração da perna de ALTA macro (retr_up): onde o pivô está na estrutura macro
  - a perna de BAIXA de médio prazo TERMINOU? (o pivô é o fim, não intermediário) — via CHoCH+ 15M
    desde o pivô-low até o known_at + o pivô é o menor low desde o último swing-high macro
Classificar por CONTEXTO: BULL-pullback / BEAR-reversal / RANGE / ruído. Recall vs 42 por classe +
densidade. A discriminação é ESTRUTURAL (regime + posição na perna macro + fim-da-perna), não drop
local. Ordem: ESTRUTURA -> (indicadores/entry depois).
SANITY_PROBE: pivô causal known_at; contexto macro causal dia; classificação estrutural não-snapshot;
recall por classe; não métrica-FN."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src=(HERE/"macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # S,TS,events,ET(tok),close_at
N=len(S); ATR=[b.get("atr") or 5.0 for b in S]; HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
days={}
for b in S:
    k=b["t"]//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"],"t":k*86400})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]; DT=[days[k]["t"] for k in DK]
def ema(v,n):
    k=2/(n+1); e=v[0]; o=[e]
    for x in v[1:]: e=x*k+e*(1-k); o.append(e)
    return o
E20=ema(DC,20); E40=ema(DC,40); E50=ema(DC,50); E100=ema(DC,100)
TRd=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
ATRd=[sum(TRd[max(1,i-13):i+1])/max(1,len(TRd[max(1,i-13):i+1])) for i in range(len(DK))]
def struct_context(kt, pi):
    """CONTEXTO ESTRUTURAL PRÉVIO no known_at kt, para o pivô-low na barra pi (causal)."""
    di=bisect.bisect_right(DT, kt-86400)-1
    if di<50: return None
    slope=(E20[di]-E20[di-20])/max(0.01,ATRd[di])
    reg_mid = "BULL" if (E20[di]>E40[di] and slope>0.3) else ("BEAR" if (E20[di]<E40[di] and slope<-0.3) else "RANGE")
    reg_sec = "BULL" if E50[di]>E100[di] else "BEAR"
    # perna de ALTA macro (6m): ultimo swing-low macro dia -> high -> retração ao pivô
    seg6=range(max(0,di-126),di+1); loi=min(seg6,key=lambda i:DL[i]); hia=max(range(loi,di+1),key=lambda i:DH[i]) if loi<di else di
    upleg=DH[hia]-DL[loi]; flo=LO[pi]
    retr_up=(DH[hia]-flo)/max(0.01,upleg) if upleg>0 else None
    # a perna de BAIXA terminou? CHoCH+ 15M entre pivô-low e known_at
    t_low=TS[pi]; hi=bisect.bisect_right(ET,kt); choch_up=0
    for m in range(hi-1,-1,-1):
        if events[m]["t"]<=t_low: break
        if events[m]["tok"]=="CHoCH+": choch_up=1; break
    # o pivô é o menor low desde o ultimo swing-high macro? (fim da perna, nao intermediario)
    is_leg_bottom = int(flo <= min(LO[max(0,pi-192):pi+1])+1e-9)
    return {"reg_mid":reg_mid,"reg_sec":reg_sec,"retr_up":round(retr_up,2) if retr_up else None,
            "choch_up":choch_up,"is_leg_bottom":is_leg_bottom,
            "drop_mid_day": round((max(DH[max(0,di-40):di+1])-DL[di])/max(0.01,ATRd[di]),1)}
def zz(r):
    lows=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
        elif d<=0 and HI[i]-LO[elo]>=r*a and elo<i:
            assert i>elo; lows.append({"pi":elo,"ki":i,"pt":TS[elo],"kt":TS[i]}); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
    return lows
piv=zz(3.0)   # base r=3: swings estruturais (não micro-ruído r=1.5)
for p in piv:
    p["ctx"]=struct_context(p["kt"],p["pi"])
piv=[p for p in piv if p["ctx"]]
print(f"pivôs-low r=3 (candidatos estruturais): {len(piv)}")
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json"))
mid_by_date={x["date"]:x["mid"] for x in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
PT=[p["pt"] for p in piv]
def recall(rows, WH=14):
    T=sorted(r["pt"] for r in rows); h=0; got=[]
    for ft in fundos:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: h+=1; got.append(ft)
    return h, got
r0,_=recall(piv); print(f"recall base r=3: {r0}/42 · densidade {(len(piv)-r0)/max(1,r0):.0f}:1")
# CLASSIFICAÇÃO ESTRUTURAL (contexto prévio, não snapshot)
def classe(p):
    c=p["ctx"]
    if c["reg_mid"]=="BULL" and c["is_leg_bottom"] and (c["retr_up"] is not None and c["retr_up"]<=0.55):
        return "BULL_pullback"
    if c["reg_mid"] in ("BEAR","RANGE") and c["choch_up"]==1 and c["is_leg_bottom"] and (c["retr_up"] is not None and c["retr_up"]>=0.45):
        return "BEAR_reversal"
    return "ruido"
from collections import Counter
for p in piv: p["classe"]=classe(p)
print("classes:", dict(Counter(p["classe"] for p in piv)))
for cl in ("BULL_pullback","BEAR_reversal"):
    sub=[p for p in piv if p["classe"]==cl]; rc,got=recall(sub)
    print(f"  {cl}: n{len(sub)} · recall {rc}/42 · densidade {(len(sub)-rc)/max(1,rc):.0f}:1")
uni=[p for p in piv if p["classe"]!="ruido"]; ru,gu=recall(uni)
print(f"  UNIÃO estrutural: n{len(uni)} · recall {ru}/42 · densidade {(len(uni)-ru)/max(1,ru):.0f}:1")
gs=set(gu); missed=[ft for ft in fundos if ft not in gs]
print(f"\nMISSED pela classificação estrutural ({len(missed)}):")
for ft in missed: print(f"  {ds(ft)} [{mid_by_date.get(ds(ft),'?')}]")
json.dump({"n_piv":len(piv),"recall_base":r0,
           "classes":{k:v for k,v in Counter(p['classe'] for p in piv).items()},
           "union_n":len(uni),"union_recall":ru,"missed":[ds(ft) for ft in missed]},
          open(HERE/"results"/"bottom_detector_structural_20260707.json","w"),indent=1,default=str)
print("OK -> results/bottom_detector_structural_20260707.json")
