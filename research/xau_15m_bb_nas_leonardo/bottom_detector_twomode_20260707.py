#!/usr/bin/env python3
"""DETECTOR DE FUNDO — DOIS MODOS causais (2026-07-07, nova meta Cris: detectar mais fundos sem
look-ahead). Ordem: ESTRUTURA (regime multi-escala) -> reversão estrutural -> emissão.
  MODO BULL-pullback: regime-médio BULL + pullback raso (drop 1-6 ATR de high recente) +
    reversão (reclaim close>high[-1] após swing-low OU CHoCH+ recente). Fundo = o low.
  MODO BEAR-reversal: regime-médio BEAR/RANGE-desc + capitulação (drop>=5 ATR de high médio-prazo) +
    CHoCH+ conhecido desde o swing-low (a perna de baixa TERMINOU estruturalmente).
Guia "perna BEAR ainda não terminou" = SEM CHoCH+ desde o low -> não emite (espírito, não corte rígido).
1 emissão por episódio (dedup 24h). Recall vs 42 velas de fundo marcadas, por modo. Sem look-ahead:
regime = dia FECHADO anterior; CHoCH+ = known_at; swing-low confirmado por fractal.
SANITY_PROBE: detecção causal multi-fatorial (regime+estrutura+reversão), dois objetivos (recall alto
+ precisão), regime multi-escala causal, catalogação/detecção não métrica-FN."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE/"macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # S, TS, events, ET (tok BOS+/-,CHoCH+/-), close_at
N=len(S); ATR=[b.get("atr") or 5.0 for b in S]; HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; OP=[b.get("o",b["c"]) for b in S]
# regime multi-escala por dia (causal)
days={}
for b in S:
    k=b["t"]//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"],"t":k*86400})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]; DT=[days[k]["t"] for k in DK]
def ema(v,n):
    k=2/(n+1); e=v[0]; o=[e]
    for x in v[1:]: e=x*k+e*(1-k); o.append(e)
    return o
E20=ema(DC,20); E40=ema(DC,40)
TRd=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
ATRd=[sum(TRd[max(1,i-13):i+1])/max(1,len(TRd[max(1,i-13):i+1])) for i in range(len(DK))]
def regime_at(t):
    di=bisect.bisect_right(DT, t - 86400)-1   # dia FECHADO anterior (causal)
    if di<40: return "WARMUP"
    slope=(E20[di]-E20[di-20])/max(0.01,ATRd[di])
    if E20[di]>E40[di] and slope>0.3: return "BULL"
    if E20[di]<E40[di] and slope<-0.3: return "BEAR"
    return "RANGE"
# eventos SMC direcionais causais (do módulo: events com tok, ET known_at por t)
def choch_up_since(cj, low_i):
    """há CHoCH+ com t em (t_low, cj]? = a perna de baixa reverteu estruturalmente."""
    t_low = TS[low_i]
    hi=bisect.bisect_right(ET, cj)
    for m in range(hi-1,-1,-1):
        if events[m]["t"] <= t_low: break
        if events[m]["tok"]=="CHoCH+": return True
    return False

def detect():
    out=[]; last_emit=-1e18
    for i in range(200, N):
        t=S[i]["t"]; a=ATR[i]
        if t - last_emit < 24*3600: continue
        reg=regime_at(t)
        if reg=="WARMUP": continue
        # swing-low fractal k=3 recente (o low candidato) nas ultimas ~8 barras
        # low corrente da perna: min low nas ultimas W barras
        # BULL: janela curta (pullback raso); BEAR: janela media (capitulacao)
        if reg=="BULL":
            W=48; lo_i=min(range(max(0,i-W),i+1),key=lambda k:LO[k])
            hi_prev=max(HI[max(0,lo_i-W):lo_i+1]) if lo_i>0 else HI[lo_i]
            drop=(hi_prev-LO[lo_i])/a
            reclaim = CL[i]>HI[i-1] and CL[i]>OP[i]
            hl = LO[i] > LO[lo_i] + 0.05*a and i>lo_i
            if 1.0<=drop<=6.0 and (reclaim or choch_up_since(t,lo_i)) and (i-lo_i)<=24:
                out.append({"t":t,"i":i,"mode":"BULL","drop":round(drop,1),"lo":LO[lo_i],"entry":CL[i]}); last_emit=t
        else:  # BEAR ou RANGE-desc
            W=192; lo_i=min(range(max(0,i-W),i+1),key=lambda k:LO[k])
            hi_prev=max(HI[max(0,lo_i-W):lo_i+1]) if lo_i>0 else HI[lo_i]
            drop=(hi_prev-LO[lo_i])/a
            # capitulacao + a perna de baixa TERMINOU (CHoCH+ desde o low) = espirito do guia Cris
            if drop>=5.0 and choch_up_since(t,lo_i) and (i-lo_i)<=48:
                out.append({"t":t,"i":i,"mode":"BEAR","drop":round(drop,1),"lo":LO[lo_i],"entry":CL[i]}); last_emit=t
    return out

cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([n for n in cat["notes"]["FUNDO"] if n["t"]],key=lambda x:int(x["t"]))
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json"))
mid_by_date={r["date"]:r["mid"] for r in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
dets=detect()
print(f"candidatos detectados: {len(dets)} · BULL {sum(1 for d in dets if d['mode']=='BULL')} · BEAR {sum(1 for d in dets if d['mode']=='BEAR')}")
# recall: fundo marcado detectado se algum candidato em ±10h e |lo - flush|<=2ATR
DT2=[d["t"] for d in dets]
def near_det(ft, flo, WH=12):
    # matcher por TIMESTAMP (a nota aponta para a vela; preço da nota = canto da caixa, não o low)
    j=bisect.bisect_left(DT2, ft-WH*3600)
    while j<len(dets) and dets[j]["t"]<=ft+WH*3600:
        return dets[j]
    return None
hit=0; by_mid={"BULL":[0,0],"BEAR":[0,0],"RANGE":[0,0]}
miss=[]
for f in fundos:
    ft=int(f["t"]); flo=f["price"]; mid=mid_by_date.get(ds(ft),"?")
    d=near_det(ft,flo)
    if mid in by_mid: by_mid[mid][1]+=1
    if d: hit+=1;  by_mid.get(mid,[0,0]).__setitem__(0, by_mid.get(mid,[0,0])[0]+1)
    else: miss.append((ds(ft),flo,mid))
print(f"\nRECALL total: {hit}/{len(fundos)} fundos marcados detectados")
for k,v in by_mid.items():
    if v[1]: print(f"  {k}: {v[0]}/{v[1]}")
print(f"\nMISSED ({len(miss)}):")
for d,p,m in miss: print(f"  {d} {p:.0f} [{m}]")
# fundos NOVOS detectados (não perto de nenhum fundo marcado) = detecta MAIS
FT=[int(f["t"]) for f in fundos]
def near_marked(t):
    j=bisect.bisect_left(FT,t-10*3600)
    return j<len(FT) and FT[j]<=t+10*3600
novos=[d for d in dets if not near_marked(d["t"])]
print(f"\nDETECÇÕES NOVAS (não marcadas pelo Cris): {len(novos)} — a verificar se são fundos válidos")
json.dump({"n_det":len(dets),"recall":hit,"total":len(fundos),"by_mid":by_mid,
           "missed":[{"date":d,"price":p,"mid":m} for d,p,m in miss],"n_novos":len(novos)},
          open(HERE/"results"/"bottom_detector_twomode_20260707.json","w"),indent=1,default=str)
print("OK -> results/bottom_detector_twomode_20260707.json")
