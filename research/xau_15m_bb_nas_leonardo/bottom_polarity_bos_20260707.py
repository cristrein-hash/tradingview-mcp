#!/usr/bin/env python3
"""POLARIDADE via BOS+ (2026-07-07, chave Cris refinada). O topo rompido é um BOS+ (rompimento de
estrutura), não fractal genérico. Zona de demanda = nível do BOS+ (topo rompido). O fundo válido =
pivô-low que RETESTA o nível de um BOS+ anterior (causal). Mais estrutural/menos numeroso que fractais.
Feature: retest_bos (0/1) + distância. Testar recall × N. Meta N<=100.
SANITY_PROBE: BOS+ causal (t<cj); retest estrutural (nível do topo rompido); trajetória; recall×N;
não snapshot; não métrica-FN."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
piv=json.load(open(HERE/"results"/"bottom_pivots_cache_20260707.json"))
series={}; EV=[]
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    EV+=[e for e in d["smc_events"] if e.get("t") and e.get("text") and e.get("price")]
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
def close_at(t):
    i=bisect.bisect_right(TS,t)-1; return CL[i] if i>=0 else None
# BOS+ = BOS onde close(t) > price (rompimento de topo p/ cima). nível = price.
seen=set(); BOSUP=[]
for e in sorted(EV,key=lambda x:x["t"]):
    key=(e["t"],round(e["price"],2),e["text"])
    if key in seen or e["text"]!="BOS": continue
    seen.add(key); c=close_at(e["t"])
    if c is not None and c>e["price"]:
        BOSUP.append({"t":e["t"],"price":e["price"]})
BOSUP.sort(key=lambda x:x["t"]); BT=[x["t"] for x in BOSUP]
print(f"BOS+ (topos rompidos estruturais): {len(BOSUP)}")
def retest_bos(li, z=0.7, maxb=1920):
    flo=LO[li]; a=ATR[li] or 5.0; t=TS[li]
    hi=bisect.bisect_right(BT, t)   # BOS+ antes do pivô
    for idx in range(hi-1,-1,-1):
        if t - BOSUP[idx]["t"] > maxb*900: break
        P=BOSUP[idx]["price"]
        if P - z*a <= flo <= P + z*a:  # retesta o nível do topo rompido
            return round(abs(flo-P)/a,2)
    return None
for p in piv:
    d=retest_bos(p["li"]); p["rbos"]=1 if d is not None else 0
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json")); mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def recall(rows,WH=14):
    T=sorted(r["pt"] for r in rows); g=0
    for ft in FT:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: g+=1
    return g
Fp=[p for p in piv if p["fund"]]; NFp=[p for p in piv if not p["fund"]]
print(f"retest BOS+: fundos-pivô {sum(p['rbos'] for p in Fp)}/{len(Fp)} · não {sum(p['rbos'] for p in NFp)}/{len(NFp)}")
print("\n=== FILTROS retest-BOS ===")
for tag,fn in [
    ("rbos só", lambda p:p["rbos"]==1),
    ("rbos & drop>=5", lambda p:p["rbos"]==1 and p["drop"]>=5),
    ("rbos & drop>=6", lambda p:p["rbos"]==1 and p["drop"]>=6),
    ("rbos & scale>=4.5", lambda p:p["rbos"]==1 and p["scale"]>=4.5),
    ("rbos & drop>=6 & scale>=4.5", lambda p:p["rbos"]==1 and p["drop"]>=6 and p["scale"]>=4.5),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<30} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
# variar z
print("\n=== variar z (largura zona BOS), rbos só ===")
for z in (0.3,0.5,0.7,1.0):
    for p in piv:
        d=retest_bos(p["li"],z); p["_r"]=1 if d is not None else 0
    sel=[p for p in piv if p["_r"]==1]; print(f"  z={z}: n{len(sel)} recall {recall(sel)}/42")
# melhor filtro + missed
SEL=[p for p in piv if p["rbos"]==1 and p["drop"]>=5]
T=sorted(p["pt"] for p in SEL)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nMISSED (rbos & drop>=5, N{len(SEL)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
print("OK")
