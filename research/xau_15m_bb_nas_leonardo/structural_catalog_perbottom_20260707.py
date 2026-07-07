#!/usr/bin/env python3
"""CATÁLOGO ESTRUTURAL POR FUNDO (2026-07-07, correção Cris: compreender a estrutura ANTES de
detectar; nunca snapshot). Para CADA uma das 42 velas de fundo, descrever o CONTEXTO ESTRUTURAL
causal completo (leitura, não filtro): de onde veio o preço, a perna de queda que o precede, como
reverteu, a zona de demanda, e a entry correta. Objetivo: PERCEBER O PADRÃO por famílias.
Descrição por fundo (tudo causal, <= t_fundo exceto marcação da entry que é fato observado):
  - regime sec/mid (multi-escala dia)
  - PERNA ANTERIOR: swing-high macro de onde caiu, magnitude da queda (ATR), duração (barras/dias)
  - retr_up (posição na perna de alta macro)
  - REVERSÃO: 1ª CHoCH+ 15M após o low (lag barras); higher-low; reclaim EMA21
  - ZONA: o fundo está numa demanda revisitada? (nível de swing-low anterior a <=1ATR)
  - ENTRY correta pareada (nota) e lag
Organizar por FAMÍLIA (regime mid) + descrever padrão comum. NÃO é detector, é leitura estrutural.
SANITY_PROBE: catalogação/leitura estrutural causal (não teste de separação nem métrica-FN);
multi-fatorial descritivo; trajetória (perna+reversão sequencial)."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src=(HERE/"macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
N=len(S); ATR=[b.get("atr") or 5.0 for b in S]; HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; OP=[b.get("o",b["c"]) for b in S]
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
def ema15(i,n):
    a=CL[max(0,i-3*n):i+1]; k=2/(n+1); e=a[0]
    for v in a[1:]: e=v*k+e*(1-k)
    return e
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
fundos=sorted([n for n in cat["notes"]["FUNDO"] if n["t"]],key=lambda x:int(x["t"]))
entrys=sorted([n for n in cat["notes"]["ENTRY"] if n["t"]],key=lambda x:int(x["t"]))
ET_notes=[int(e["t"]) for e in entrys]
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json"))
mid_by_date={x["date"][:10]:x["mid"] for x in FMS}

def read_bottom(t):
    ci=bisect.bisect_right(TS,t)-1
    if ci<200: return None
    a=ATR[ci] or 5.0
    di=bisect.bisect_right(DT,t-86400)-1
    reg_sec="BULL" if E50[di]>E100[di] else "BEAR"
    slope=(E20[di]-E20[di-20])/max(0.01,ATRd[di]); reg_mid="BULL" if (E20[di]>E40[di] and slope>0.3) else ("BEAR" if (E20[di]<E40[di] and slope<-0.3) else "RANGE")
    # low local (o fundo): min low nas ±6 barras da marcação
    lo_i=min(range(max(0,ci-6),min(N,ci+6)),key=lambda k:LO[k]); flo=LO[lo_i]
    # PERNA ANTERIOR: swing-high nas ultimas 192 barras antes do low
    hi_i=max(range(max(0,lo_i-192),lo_i+1),key=lambda k:HI[k])
    drop=(HI[hi_i]-flo)/a; leg_bars=lo_i-hi_i
    # REVERSÃO: 1ª CHoCH+ 15M após o low
    hi_e=bisect.bisect_right(ET, TS[lo_i]); choch_lag=None
    for m in range(hi_e, len(events)):
        if events[m]["t"] > t + 48*3600: break
        if events[m]["tok"]=="CHoCH+": choch_lag=round((events[m]["t"]-TS[lo_i])/900); break
    # reclaim EMA21 (barras do low até reclaim)
    e21=ema15(lo_i,21); reclaim_lag=None
    for k in range(lo_i,min(N,lo_i+48)):
        if CL[k]>ema15(k,21): reclaim_lag=k-lo_i; break
    # ZONA demanda: swing-low anterior (192-1920 barras) a <=1.5ATR do flo?
    prior_lows=[LO[k] for k in range(max(0,lo_i-1920),lo_i-96) if LO[k]==min(LO[max(0,k-8):k+9])]
    revisit=any(abs(pl-flo)<=1.5*a for pl in prior_lows)
    # ENTRY pareada
    j=bisect.bisect_right(ET_notes,t); ent_lag=None
    for jj in range(max(0,j-1),min(len(ET_notes),j+2)):
        if 0<=ET_notes[jj]-t<=60*3600: ent_lag=round((ET_notes[jj]-t)/3600,1); break
    return {"reg_sec":reg_sec,"reg_mid":reg_mid,"drop_atr":round(drop,1),"leg_bars":leg_bars,
            "leg_days":round(leg_bars/96,1),"choch_lag_bars":choch_lag,"reclaim_lag_bars":reclaim_lag,
            "revisit_demand":int(revisit),"entry_lag_h":ent_lag}

print(f"{'fundo':<17}{'sec':<5}{'mid':<6}{'drop':>5}{'leg_d':>6}{'choch':>6}{'recl':>5}{'revis':>6}{'entryLag':>9}")
recs=[]
for f in fundos:
    r=read_bottom(int(f["t"]))
    if not r: continue
    recs.append({"date":ds(f["t"]),**r})
    print(f"{ds(f['t']):<17}{r['reg_sec']:<5}{r['reg_mid']:<6}{r['drop_atr']:>5}{r['leg_days']:>6}"
          f"{str(r['choch_lag_bars']):>6}{str(r['reclaim_lag_bars']):>5}{r['revisit_demand']:>6}{str(r['entry_lag_h']):>9}")
# padrão por família
import statistics as st
print("\n=== PADRÃO POR FAMÍLIA (regime mid) ===")
for fam in ("BULL","RANGE","BEAR"):
    g=[r for r in recs if r["reg_mid"]==fam]
    if not g: continue
    def med(k):
        v=[r[k] for r in g if r[k] is not None]; return round(st.median(v),1) if v else None
    print(f"  {fam} (n={len(g)}): drop {med('drop_atr')}ATR · leg {med('leg_days')}d · choch_lag {med('choch_lag_bars')}b · "
          f"reclaim_lag {med('reclaim_lag_bars')}b · revisit-demanda {sum(r['revisit_demand'] for r in g)}/{len(g)} · entry_lag {med('entry_lag_h')}h")
json.dump(recs,open(HERE/"results"/"structural_catalog_perbottom_20260707.json","w"),indent=1,default=str)
print("OK -> results/structural_catalog_perbottom_20260707.json")
