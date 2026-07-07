#!/usr/bin/env python3
"""POLARIDADE via EQH — teto de consolidação rompido (2026-07-07, interpretação: o topo relevante é
o teto do range/consolidação anterior, não qualquer swing-high). EQH = equal highs = resistência
testada várias vezes. Quando o EQH é rompido (BOS+ através dele), o teto vira zona de demanda; o
fundo válido retesta esse nível. Muito mais seletivo (EQH são poucos, = consolidações reais).
Também testo: último swing-high significativo (zigzag r>=3) rompido, como alternativa.
SANITY_PROBE: EQH/topo-consolidação causal rompido; retest do nível; recall×N; trajetória; não snapshot."""
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
# EQH events (teto de consolidação); quando rompido (close>price depois) vira demanda
seen=set(); EQH=[]
for e in sorted(EV,key=lambda x:x["t"]):
    if e["text"]!="EQH": continue
    key=(e["t"],round(e["price"],2))
    if key in seen: continue
    seen.add(key)
    # breakout: 1º close > price depois do EQH
    ei=bisect.bisect_right(TS,e["t"])-1; bi=None
    for m in range(ei+1, min(N,ei+960)):
        if CL[m]>e["price"]+0.1*ATR[m]: bi=m; break
        if CL[m]<e["price"]-8*ATR[m]: break
    if bi is not None: EQH.append({"price":e["price"],"bi":bi,"eqh_i":ei})
EQH.sort(key=lambda x:x["bi"]); EB=[x["bi"] for x in EQH]
print(f"EQH rompidos (tetos de consolidação): {len(EQH)}")
def retest_eqh(li, z=0.7, maxb=1920):
    flo=LO[li]; a=ATR[li] or 5.0
    hi=bisect.bisect_right(EB, li)
    for idx in range(hi-1,-1,-1):
        q=EQH[idx]
        if li-q["bi"]>maxb: break
        P=q["price"]
        if P-z*a<=flo<=P+z*a: return round(abs(flo-P)/a,2)
    return None
for p in piv:
    d=retest_eqh(p["li"]); p["eqh"]=1 if d is not None else 0
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
print(f"retest EQH: fundos-pivô {sum(p['eqh'] for p in Fp)}/{len(Fp)} · não {sum(p['eqh'] for p in NFp)}/{len(NFp)}")
print("\n=== FILTROS retest-EQH ===")
for tag,fn in [
    ("eqh só", lambda p:p["eqh"]==1),
    ("eqh & drop>=5", lambda p:p["eqh"]==1 and p["drop"]>=5),
    ("eqh (BULL/RANGE) | (BEAR retr>=0.5)", lambda p:(p["eqh"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<40} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
for z in (0.5,0.7,1.0,1.5):
    for p in piv:
        d=retest_eqh(p["li"],z); p["_e"]=1 if d is not None else 0
    sel=[p for p in piv if p["_e"]==1]; print(f"  z={z}: n{len(sel)} recall {recall(sel)}/42")
SEL=[p for p in piv if (p["eqh"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)]
T=sorted(p["pt"] for p in SEL)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nMISSED (união EQH, N{len(SEL)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
print("OK")
