#!/usr/bin/env python3
"""POLARIDADE v2 — retest do ÚLTIMO topo-de-ESCALA rompido (2026-07-07, padrão PLT assimilado).
Aprendizado dos PLT do Cris: são topos SUCESSIVOS da escada de alta (topos de PERNA, ~1/sem), cada
um rompido vira suporte, o pullback retesta o ÚLTIMO topo rompido. Não micro-swings nem qualquer BOS+.
Implementação:
  1. zigzag nos HIGHS (escala r) -> pivôs-high = topos de perna.
  2. suporte ativo = último pivô-high ROMPIDO (close acima) ainda não violado por baixo (close < H-z).
  3. fundo válido = pivô-low perto (<=z·ATR) do suporte ativo (retest do último topo rompido).
Testar: quantos PLT são pivôs-high da escala? recall dos fundos que retestam suporte ativo × N.
SANITY_PROBE: topo-de-escala causal known_at; suporte ativo = último rompido; retest; recall×N;
trajetória; não snapshot."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
piv=json.load(open(HERE/"results"/"bottom_pivots_cache_20260707.json"))
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
def zz_highs(r):
    highs=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i:
            highs.append({"pi":ehi,"H":HI[ehi],"ki":i,"kt":TS[i]}); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return highs
# PLT levels p/ validar escala
rows=json.load(open(HERE/"results"/"manual_shapes_pltdm_20260707.json"))
def t0(r):
    pts=r.get("points") or []; return int(pts[0]["time"]) if pts and pts[0].get("time") else None
def pr(r):
    pts=r.get("points") or []; return pts[0]["price"] if pts and pts[0].get("price") else None
PLT=[{"t":t0(x),"p":pr(x)} for x in rows if x["name"]=="text_note" and x["text"].strip().upper()=="PLT" and t0(x)]
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
# quantos PLT coincidem com pivô-high de cada escala?
print("=== PLT coincidem com pivô-high de qual escala? ===")
for r in (2.0,3.0,4.0,5.0):
    highs=zz_highs(r); HP=sorted(h["H"] for h in highs)
    HT=[h["pi"] for h in highs]; import bisect as bs
    match=0
    for l in PLT:
        # há um pivô-high com preço ~= PLT.p perto no tempo?
        pi=bisect.bisect_right(TS,l["t"])-1
        if any(abs(h["H"]-l["p"])<=0.6*(ATR[h["pi"]] or 5) and abs(h["pi"]-pi)<=32 for h in highs): match+=1
    print(f"  r={r}: {len(highs)} pivôs-high · PLT casados {match}/{len(PLT)}")
# construir suporte-ativo com r=3 e testar retest
def build_support(r, z=0.7):
    highs=zz_highs(r)
    # marcar rompimento de cada high e violação
    events=[]  # (i, H, 'broke'/'viol')
    for h in highs:
        H=h["H"]; bi=None
        for m in range(h["ki"], min(N,h["ki"]+1920)):
            if CL[m]>H+0.1*ATR[m]: bi=m; break
        if bi is not None: h["broke_i"]=bi; events.append((bi,H))
    events.sort()
    return sorted(events)  # (broke_i, H)
SUP=build_support(3.0); SB=[e[0] for e in SUP]
def retest_support(li, z=0.7):
    flo=LO[li]; a=ATR[li] or 5.0
    hi=bisect.bisect_right(SB, li)  # topos rompidos antes de li
    # último topo rompido cujo nível o preço ainda respeita (não violou muito por baixo antes)
    for idx in range(hi-1,-1,-1):
        bi,H=SUP[idx]
        if bi>=li: continue
        if li-bi>1920: break
        # o suporte é "ativo" se o preço não fechou muito abaixo de H entre bi e li (senão foi perdido)
        if min(CL[bi:li]) < H - 2.0*a: continue
        if H-z*a<=flo<=H+z*a: return round(abs(flo-H)/a,2)
    return None
for p in piv:
    d=retest_support(p["li"]); p["sup"]=1 if d is not None else 0
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json")); mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
def recall(rows,WH=14):
    T=sorted(r["pt"] for r in rows); g=0
    for ft in FT:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: g+=1
    return g
Fp=[p for p in piv if p["fund"]]; NFp=[p for p in piv if not p["fund"]]
print(f"\nsuporte-ativo (r=3): topos rompidos {len(SUP)}")
print(f"retest suporte-ativo: fundos-pivô {sum(p['sup'] for p in Fp)}/{len(Fp)} · não {sum(p['sup'] for p in NFp)}/{len(NFp)}")
print("\n=== FILTROS ===")
for tag,fn in [
    ("sup só", lambda p:p["sup"]==1),
    ("sup & drop>=5", lambda p:p["sup"]==1 and p["drop"]>=5),
    ("sup(BULL/RANGE) | (BEAR retr>=0.5)", lambda p:(p["sup"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<40} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
print("OK")
