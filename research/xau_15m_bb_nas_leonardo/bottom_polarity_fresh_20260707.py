#!/usr/bin/env python3
"""POLARIDADE — 1º RETEST FRESCO de BOS+ RECENTE (2026-07-07). Refinar a chave do Cris: o fundo BULL
é o PRIMEIRO retest de um topo rompido RECENTE (fresco), não qualquer toque. Combinar com o modo BEAR
(retração alta) já capturado. União por regime -> N<=100.
retest_fresh(li): existe BOS+ com breakout <= RECb barras antes de li, cujo nível P satisfaz
  LO[li] em [P-z, P+z]·ATR, e é o 1º retest (entre breakout e li o low nunca tocou P-z antes) e o
  preço subiu acima de P após o breakout (retest genuíno).
SANITY_PROBE: 1º retest fresco causal; união por regime; recall×N; trajetória; não snapshot."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
piv=json.load(open(HERE/"results"/"bottom_pivots_cache_20260707.json"))
series={}; EV=[]
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    EV+=[e for e in d["smc_events"] if e.get("t") and e.get("text")=="BOS" and e.get("price")]
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
def close_at(t):
    i=bisect.bisect_right(TS,t)-1; return CL[i] if i>=0 else None
seen=set(); BOSUP=[]
for e in sorted(EV,key=lambda x:x["t"]):
    key=(e["t"],round(e["price"],2))
    if key in seen: continue
    seen.add(key); c=close_at(e["t"])
    if c is not None and c>e["price"]:
        bi=bisect.bisect_right(TS,e["t"])-1
        BOSUP.append({"t":e["t"],"price":e["price"],"bi":bi})
BOSUP.sort(key=lambda x:x["bi"]); BB=[x["bi"] for x in BOSUP]
def retest_fresh(li, z=0.6, RECb=288):
    flo=LO[li]; a=ATR[li] or 5.0
    hi=bisect.bisect_right(BB, li)
    for idx in range(hi-1,-1,-1):
        b=BOSUP[idx]; bi=b["bi"]; P=b["price"]
        if li-bi > RECb: break   # rompimento não é recente
        if not (P-z*a <= flo <= P+z*a): continue
        # 1º retest: entre bi+1 e li-1 o low nunca entrou na zona (P-z)
        touched_before=any(LO[k] <= P+z*a and LO[k]>=P-2*z*a for k in range(bi+1, li))
        # preço subiu acima de P após breakout (genuíno)
        rose=max(HI[bi:li]) > P + 0.5*a if li>bi else False
        if (not touched_before) and rose:
            return round(abs(flo-P)/a,2)
    return None
for p in piv:
    d=retest_fresh(p["li"]); p["fresh"]=1 if d is not None else 0
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
print(f"BOS+ {len(BOSUP)} · retest-fresco: fundos-pivô {sum(p['fresh'] for p in Fp)}/{len(Fp)} · não {sum(p['fresh'] for p in NFp)}/{len(NFp)}")
print("\n=== FILTROS 1º-retest-fresco ===")
for tag,fn in [
    ("fresh só", lambda p:p["fresh"]==1),
    ("fresh & drop>=5", lambda p:p["fresh"]==1 and p["drop"]>=5),
    ("fresh (BULL) | retr>=0.5 (BEAR)", lambda p:(p["fresh"]==1 and p["reg"]=="BULL") or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
    ("fresh(BULL) | (BEAR retr>=0.5 & drop>=6) | (RANGE fresh)", lambda p:(p["fresh"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5 and p["drop"]>=6)),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<48} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
# variar z e RECb
print("\n=== variar z / RECb (fresh só) ===")
for z in (0.5,0.7):
    for RECb in (192,288,480):
        for p in piv:
            d=retest_fresh(p["li"],z,RECb); p["_f"]=1 if d is not None else 0
        sel=[p for p in piv if p["_f"]==1]; print(f"  z={z} RECb={RECb}: n{len(sel)} recall {recall(sel)}/42")
# melhor uniao + missed
SEL=[p for p in piv if (p["fresh"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5 and p["drop"]>=6)]
T=sorted(p["pt"] for p in SEL)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nMISSED (união, N{len(SEL)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
print("OK")
