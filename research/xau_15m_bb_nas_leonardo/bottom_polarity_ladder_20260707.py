#!/usr/bin/env python3
"""POLARIDADE v3 — ESCADA de markup + confluência DM (2026-07-07).
Aprendizado: PLT = topos ASCENDENTES sucessivos (higher-highs) da escada de markup (não qualquer topo);
DM = zona de demanda (reação). O fundo BULL retesta o ÚLTIMO higher-high rompido da escada.
1. medir retest DENTRO de cada regime (BULL deve discriminar; BEAR não retesta topo — está em novo mínimo).
2. suporte-escada = topo-rompido cujo nível > topo-rompido anterior (ladder ascendente de markup).
3. caracterizar DM (swing-low? reação pós-breakout?).
SANITY_PROBE: escada de markup causal (higher-highs known_at); retest do último; por-regime; DM=reação;
recall×N; trajetória; não snapshot."""
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
            highs.append({"pi":ehi,"H":HI[ehi],"ki":i}); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return highs
# suporte-escada: topos rompidos, cada nível marcado com se é higher-high vs topo rompido anterior
highs=zz_highs(3.0)
SUP=[]  # (broke_i, H, is_ladder)  is_ladder = H > último topo rompido
last_broken=None
for h in sorted(highs,key=lambda x:x["ki"]):
    H=h["H"]; bi=None
    for m in range(h["ki"], min(N,h["ki"]+1920)):
        if CL[m]>H+0.1*ATR[m]: bi=m; break
    if bi is None: continue
    SUP.append({"bi":bi,"H":H})
SUP.sort(key=lambda x:x["bi"]); SB=[x["bi"] for x in SUP]
def retest_ladder(li,z=0.7,ladder=False):
    flo=LO[li]; a=ATR[li] or 5.0; hi=bisect.bisect_right(SB,li)
    for idx in range(hi-1,-1,-1):
        q=SUP[idx]; bi,H=q["bi"],q["H"]
        if bi>=li: continue
        if li-bi>1920: break
        if not CL[bi:li] or min(CL[bi:li])<H-2.0*a: continue
        if ladder:
            # é higher-high? algum topo rompido anterior num nível MENOR (escada ascendente)
            prev=[s["H"] for s in SUP[:idx] if s["bi"]<bi and bi-s["bi"]<2880]
            if not prev or H<=max(prev): continue
        if H-z*a<=flo<=H+z*a: return round(abs(flo-H)/a,2)
    return None
for p in piv:
    p["sup"]=1 if retest_ladder(p["li"],ladder=False) is not None else 0
    p["lad"]=1 if retest_ladder(p["li"],ladder=True) is not None else 0
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
# 1. retest DENTRO de cada regime
print("=== retest (sup / ladder) por regime — fund vs não-fund ===")
for reg in ("BULL","RANGE","BEAR"):
    fr=[p for p in Fp if p["reg"]==reg]; nr=[p for p in NFp if p["reg"]==reg]
    if not fr: continue
    fs=sum(p["sup"] for p in fr)/len(fr); ns=sum(p["sup"] for p in nr)/max(1,len(nr))
    fl=sum(p["lad"] for p in fr)/len(fr); nl=sum(p["lad"] for p in nr)/max(1,len(nr))
    print(f"  {reg:<6} sup fund {fs:.0%} vs não {ns:.0%} | ladder fund {fl:.0%} vs não {nl:.0%} (Nf{len(fr)} Nnf{len(nr)})")
print("\n=== FILTROS (união por regime) ===")
for tag,fn in [
    ("ladder só", lambda p:p["lad"]==1),
    ("lad(BULL/RANGE) | (BEAR retr>=0.5)", lambda p:(p["lad"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
    ("lad(BULL/RANGE) | (BEAR retr>=0.5 & drop>=6)", lambda p:(p["lad"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5 and p["drop"]>=6)),
    ("lad&drop>=4 (BULL/RANGE) | (BEAR retr>=0.55&drop>=6)", lambda p:(p["lad"]==1 and p["drop"]>=4 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.55 and p["drop"]>=6)),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<52} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
SEL=[p for p in piv if (p["lad"]==1 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)]
T=sorted(p["pt"] for p in SEL)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nMISSED (ladder-união, N{len(SEL)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
print("OK")
