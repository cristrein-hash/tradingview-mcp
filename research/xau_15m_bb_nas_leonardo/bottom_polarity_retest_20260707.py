#!/usr/bin/env python3
"""DISCRIMINADOR POLARIDADE — retest do TOPO ROMPIDO (2026-07-07, chave do Cris).
O fundo válido = pullback que testa a ZONA DE DEMANDA criada no RETEST DO TOPO ROMPIDO ANTERIOR
(polaridade: resistência rompida vira suporte). Causal:
  1. swing-high H (fractal w=8), known_at = k+w
  2. ROMPIDO: 1º close > H + 0,1·ATR depois de k+w (breakout_bar)
  3. o pivô-low li TESTA a polaridade se LO[li] em [H - z·ATR, H + z·ATR] e breakout_bar < li e o
     preço subiu acima de H antes de voltar (retest genuíno: max HI entre breakout e li > H + z·ATR)
Feature retest_broken_high (0/1) + distância à zona. Testar recall × N sobre os 954 pivôs. Meta N<=100.
SANITY_PROBE: polaridade estrutural causal (topo rompido antes do pivô); trajetória (rompe→sobe→
retesta); recall×N; não snapshot; não métrica-FN."""
import json, bisect, glob
import numpy as np
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
piv=json.load(open(HERE/"results"/"bottom_pivots_cache_20260707.json"))
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
# swing-highs fractais w=8 + breakout bar
W=8
SH=[]  # (k, H)
for k in range(W,N-W):
    if HI[k]==max(HI[k-W:k+W+1]) and HI[k-W:k].count(HI[k])==0: SH.append((k,HI[k]))
# breakout de cada swing-high: 1º close > H+0,1ATR depois de k+W
BRK=[]  # (k, H, breakout_i)
for k,H in SH:
    bi=None
    for m in range(k+W, min(N, k+W+1920)):
        if CL[m] > H + 0.1*ATR[m]: bi=m; break
        if CL[m] < H - 8*ATR[m]: break
    if bi is not None: BRK.append((k,H,bi))
BRK.sort(key=lambda x:x[2])  # por breakout bar
BRK_bi=[x[2] for x in BRK]
def retest_broken(li, z=0.7):
    """o pivô-low li está no retest de um topo rompido? (causal)"""
    flo=LO[li]; a=ATR[li] or 5.0
    hi=bisect.bisect_right(BRK_bi, li)   # topos rompidos ANTES de li
    best=None
    for idx in range(hi-1, -1, -1):
        k,H,bi = BRK[idx]
        if li - bi > 1920: break   # rompimento muito antigo
        if H - z*a <= flo <= H + z*a:  # o low testa o nível do topo
            # retest genuíno: entre breakout e li o preço subiu acima de H (rompeu) e depois voltou
            seg_hi = max(HI[bi:li]) if li>bi else HI[bi]
            if seg_hi > H + 0.3*a:
                d=abs(flo-H)/a; best=d if (best is None or d<best) else best
    return best
for p in piv:
    d=retest_broken(p["li"]); p["retest"]=1 if d is not None else 0; p["retest_dist"]=round(d,2) if d is not None else 99
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
print(f"swing-highs {len(SH)} · rompidos {len(BRK)}")
print(f"\nRETEST do topo rompido: fundos-pivô {sum(p['retest'] for p in Fp)}/{len(Fp)} · não-fundos {sum(p['retest'] for p in NFp)}/{len(NFp)}")
print("\n=== FILTROS polaridade ===")
for tag,fn in [
    ("retest só", lambda p:p["retest"]==1),
    ("retest & drop>=5", lambda p:p["retest"]==1 and p["drop"]>=5),
    ("retest & scale>=4.5", lambda p:p["retest"]==1 and p["scale"]>=4.5),
    ("retest & drop>=6", lambda p:p["retest"]==1 and p["drop"]>=6),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<26} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
# variar z (largura da zona)
print("\n=== variar z (largura da zona de polaridade), retest só ===")
for z in (0.4,0.7,1.0,1.5):
    for p in piv:
        d=retest_broken(p["li"],z); p["_r"]=1 if d is not None else 0
    sel=[p for p in piv if p["_r"]==1]; print(f"  z={z}: n{len(sel)} recall {recall(sel)}/42")
SEL=[p for p in piv if p["retest"]==1]
T=sorted(p["pt"] for p in SEL)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nMISSED (retest z=0.7, N{len(SEL)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
json.dump([{k:p[k] for k in ("li","pt","fund","reg","retest","retest_dist","drop","scale")} for p in piv],
          open(HERE/"results"/"bottom_polarity_cache_20260707.json","w"))
print("OK")
