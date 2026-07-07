#!/usr/bin/env python3
"""DISCRIMINADOR ZONA OB DEMAND (2026-07-07). Os fundos do Cris sentam em zonas OB de demanda
institucionais (Custom OB Detector v11, no chart), não swing-lows genéricos. Testar: pivô-base em
zona OB DEMAND (causal, born<=t_pivo) -> recall × N. Combinar com score-regime. Meta N<=100.
Leve (lê cache de pivôs + zonas dos primitives)."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
piv=json.load(open(HERE/"results"/"bottom_pivots_cache_20260707.json"))
# séries (LO) e zonas DEMAND
series={}; ZD=[]
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    for z in d.get("zones",[]):
        if "DEMAND" in str(z.get("text","")).upper() and z.get("born_t") is not None and z.get("low") is not None:
            ZD.append(z)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; LO=[b["l"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
ZD.sort(key=lambda z:z["born_t"]); ZDB=[z["born_t"] for z in ZD]
print(f"pivôs {len(piv)} · zonas OB DEMAND {len(ZD)}")
def in_ob(li, pt, tol=0.5):
    a=ATR[li] or 5.0; flo=LO[li]
    hi=bisect.bisect_right(ZDB, pt)  # zona nascida antes do pivô (causal)
    for i in range(hi):
        z=ZD[i]
        if (z.get("last_t") or pt) < pt - 96*900*3:  # zona muito velha/expirada (>~3 semanas sem toque)
            continue
        if z["low"]-tol*a <= flo <= z["high"]+tol*a: return 1
    return 0
for p in piv: p["ob"]=in_ob(p["li"], p["pt"])
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
def recall(rows,WH=14):
    T=sorted(r["pt"] for r in rows); g=0
    for ft in FT:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: g+=1
    return g
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json")); mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
Fp=[p for p in piv if p["fund"]]
print(f"\nem zona OB DEMAND: fundos-pivô {sum(p['ob'] for p in Fp)}/{len(Fp)} · todos {sum(p['ob'] for p in piv)}/{len(piv)}")
print("\n=== FILTROS com zona OB ===")
for tag,fn in [
    ("OB só", lambda p:p["ob"]==1),
    ("OB & drop>=6", lambda p:p["ob"]==1 and p["drop"]>=6),
    ("OB & scale>=4.5", lambda p:p["ob"]==1 and p["scale"]>=4.5),
    ("OB & sweep>=-1.5", lambda p:p["ob"]==1 and p["sweep"]>=-1.5),
    ("OB & drop>=6 & sweep>=-1.5", lambda p:p["ob"]==1 and p["drop"]>=6 and p["sweep"]>=-1.5),
    ("OB & (scale>=4.5 | drop>=8)", lambda p:p["ob"]==1 and (p["scale"]>=4.5 or p["drop"]>=8)),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<32} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
# melhor: OB & drop>=6 & sweep>=-1.5 — detalhar missed
SEL=[p for p in piv if p["ob"]==1 and p["drop"]>=6 and p["sweep"]>=-1.5]
T=sorted(p["pt"] for p in SEL)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nMISSED (OB&drop>=6&sweep>=-1.5, N{len(SEL)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
json.dump({"n_zd":len(ZD),"filters_done":True},open(HERE/"results"/"bottom_ob_zone_20260707.json","w"))
print("OK")
