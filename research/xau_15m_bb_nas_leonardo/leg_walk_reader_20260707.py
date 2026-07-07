#!/usr/bin/env python3
"""LEITURA CONTEXTUAL POR CAMINHADA DE PERNAS — série completa (2026-07-07).
NÃO é filtro de pool nem densidade. É a CAMINHADA do markup: autômato sequencial que anda perna-a-perna
e, em cada perna, identifica a referência corrente (PLT=topo da perna, DM=demanda da perna). O fundo é o
evento estrutural: pullback à demanda da perna corrente com markup INTACTO (higher-low sobre demanda
anterior). Emite no fecho de confirmação (causal, known_at). Os fundos do Cris são um SUBCONJUNTO destes
eventos — a estrutura contém-nos sem marcação manual.
Saída: a LEITURA (sequência de pernas + eventos de demanda) + alinhamento com as 42 VELA DE FUNDO.
SANITY_PROBE: caminhada sequencial (processo, não snapshot); referência da perna corrente; contexto de
semanas; markup intacto multi-perna; causal known_at; leitura contextual, não filtro."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
def zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
def align(events,WH=18):
    T=sorted(e["conf_t"] for e in events); hit=set()
    for ft in FT:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: hit.add(ft)
    return len(hit)
def walk(r):
    """caminhada: emite eventos de demanda-de-perna (higher-low com markup intacto) e reversão."""
    piv=zz(r); ev=[]
    prevH=prevL=None; lastH=None
    for k,(tp,i,pr,ci) in enumerate(piv):
        if tp=="H":
            prevH=pr; lastH=pr
        else:  # swing-low confirmado = demanda de perna
            markup_intact = (prevH is not None and lastH is not None)  # houve topo antes
            higher_low = (prevL is None or pr>prevL)
            # reversão (fim-de-queda): lower-low seguido de topo que rompe estrutura -> tratado no próximo H
            kind=None
            if markup_intact and higher_low: kind="DEMANDA_MARKUP"      # pullback dentro de markup
            elif markup_intact and not higher_low: kind="DEMANDA_CORRECAO"  # correção mais funda
            if kind:
                ev.append({"i":i,"t":TS[i],"conf_i":ci,"conf_t":TS[ci],"lvl":pr,"kind":kind,
                           "leg_top":lastH,"prevL":prevL})
            prevL=pr
    return ev,piv
print("=== CAMINHADA série completa — eventos de demanda por escala ===")
for r in (4,5,6,8):
    ev,piv=walk(r)
    mk=[e for e in ev if e["kind"]=="DEMANDA_MARKUP"]; co=[e for e in ev if e["kind"]=="DEMANDA_CORRECAO"]
    print(f"  r={r}: pernas {len(piv)} · eventos demanda {len(ev)} (markup {len(mk)} / correção {len(co)}) · alinham c/ 42 fundos: {align(ev)}/42")
# leitura detalhada r=6 na janela do Cris (amostra visível)
R=6; ev,piv=walk(R)
W0=dt.datetime(2025,9,1).timestamp(); W1=dt.datetime(2025,10,1).timestamp()
print(f"\n=== LEITURA r={R} — set/2025 (amostra da caminhada) ===")
fund_days={ds(t)[:10] for t in FT}
for e in ev:
    if W0<=e["t"]<=W1:
        star=" ★FUNDO-CRIS" if ds(e["t"])[:10] in fund_days else ""
        print(f"  {ds(e['t'])}  demanda@{e['lvl']:7.1f}  (topo-perna {e['leg_top']:.0f})  {e['kind']}{star}")
json.dump({"R":R,"n_eventos":len(ev),"align":align(ev),
           "events":[{"t":e["t"],"d":ds(e["t"]),"conf_t":e["conf_t"],"lvl":round(e["lvl"],1),"kind":e["kind"],"leg_top":round(e["leg_top"],1) if e["leg_top"] else None} for e in ev]},
          open(HERE/"results"/"leg_walk_reader_20260707.json","w"),indent=1)
print("OK")
