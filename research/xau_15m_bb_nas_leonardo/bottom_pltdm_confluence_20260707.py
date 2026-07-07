#!/usr/bin/env python3
"""CONFLUÊNCIA PLT + DM (2026-07-07) — detector do padrão assimilado do Cris.
PLT-escada: retest de higher-high de markup (DISCRIMINA BULL 15% vs 8%). Complemento DM-demanda:
zona de demanda fresca = origem de perna que ROMPE estrutura (BOS+), retestada em pullback.
BULL/RANGE fundo = PLT-escada OU DM-demanda (confluência de polaridade). BEAR = end-of-fall (retr alto).
1. caracterizar DM do Cris (são origens de perna? swing-lows?).
2. gerar DM_auto causal, medir retest por regime.
3. união (PLT-ladder ∪ DM) BULL/RANGE + BEAR-retr; recall × N.
SANITY_PROBE: multi-fatorial (ladder markup + demanda-origem + regime + drop trajetória); causal known_at;
trajetória lookback; dois objetivos (capturar fundo + evitar não-fundo); recall×N; não snapshot."""
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
def zz(r):
    hs=[]; ls=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: ls.append({"pi":elo,"L":LO[elo],"ki":i}); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: hs.append({"pi":ehi,"H":HI[ehi],"ki":i}); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return hs,ls
HS,LS=zz(3.0)
# ladder tops (PLT): topos rompidos ascendentes
SUP=[]
for h in sorted(HS,key=lambda x:x["ki"]):
    H=h["H"]; bi=None
    for m in range(h["ki"],min(N,h["ki"]+1920)):
        if CL[m]>H+0.1*ATR[m]: bi=m; break
    if bi is not None: SUP.append({"bi":bi,"H":H})
SUP.sort(key=lambda x:x["bi"]); SB=[x["bi"] for x in SUP]
def retest_ladder(li,z=0.7):
    flo=LO[li]; a=ATR[li] or 5.0; hi=bisect.bisect_right(SB,li)
    for idx in range(hi-1,-1,-1):
        q=SUP[idx]; bi,H=q["bi"],q["H"]
        if bi>=li or li-bi>1920:
            if li-bi>1920: break
            continue
        if not CL[bi:li] or min(CL[bi:li])<H-2.0*a: continue
        prev=[s["H"] for s in SUP[:idx] if s["bi"]<bi and bi-s["bi"]<2880]
        if not prev or H<=max(prev): continue
        if H-z*a<=flo<=H+z*a: return round(abs(flo-H)/a,2)
    return None
# DM demanda: swing-low origem de perna que rompe estrutura (BOS+ = close acima do swing-high anterior)
def prior_swing_high(ki):
    # último topo zigzag antes de ki
    hs=[h["H"] for h in HS if h["ki"]<=ki]; return max(hs[-3:]) if hs else None
DM=[]
for L in sorted(LS,key=lambda x:x["ki"]):
    li0=L["pi"]; ref=prior_swing_high(L["ki"])
    if ref is None: continue
    broke=None
    for m in range(L["ki"],min(N,L["ki"]+384)):
        if CL[m]>ref+0.1*ATR[m]: broke=m; break
    if broke is not None: DM.append({"lo_i":li0,"L":L["L"],"active_i":broke})
DM.sort(key=lambda x:x["active_i"]); DB=[x["active_i"] for x in DM]
def retest_dm(li,z=0.8):
    flo=LO[li]; a=ATR[li] or 5.0; hi=bisect.bisect_right(DB,li)
    for idx in range(hi-1,-1,-1):
        q=DM[idx]; ai,Lv=q["active_i"],q["L"]
        if ai>=li: continue
        if li-ai>1440: break
        if not CL[ai:li] or min(CL[ai:li])<Lv-2.0*a: continue
        if Lv-z*a<=flo<=Lv+z*a: return round(abs(flo-Lv)/a,2)
    return None
for p in piv:
    p["lad"]=1 if retest_ladder(p["li"]) is not None else 0
    p["dm"]=1 if retest_dm(p["li"]) is not None else 0
    p["pltdm"]=1 if (p["lad"] or p["dm"]) else 0
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
print("=== retest por regime (fund vs não) — ladder / dm / pltdm ===")
for reg in ("BULL","RANGE","BEAR"):
    fr=[p for p in Fp if p["reg"]==reg]; nr=[p for p in NFp if p["reg"]==reg]
    if not fr: continue
    def rt(rows,k): return sum(p[k] for p in rows)/max(1,len(rows))
    print(f"  {reg:<6} lad {rt(fr,'lad'):.0%}/{rt(nr,'lad'):.0%}  dm {rt(fr,'dm'):.0%}/{rt(nr,'dm'):.0%}  pltdm {rt(fr,'pltdm'):.0%}/{rt(nr,'pltdm'):.0%} (Nf{len(fr)})")
print(f"\nDM zonas: {len(DM)} · SUP-ladder: {len(SUP)}")
print("\n=== FILTROS união ===")
for tag,fn in [
    ("pltdm (BULL/RANGE) | BEAR retr>=0.5", lambda p:(p["pltdm"] and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
    ("pltdm&drop>=4 (BULL/RANGE) | BEAR retr>=0.5&drop>=6", lambda p:(p["pltdm"] and p["drop"]>=4 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5 and p["drop"]>=6)),
    ("pltdm&drop>=5 (BULL/RANGE) | BEAR retr>=0.55&drop>=6", lambda p:(p["pltdm"] and p["drop"]>=5 and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.55 and p["drop"]>=6)),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<54} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
print("\n=== APERTAR BULL: confluência + trajetória (rumo a N<=100) ===")
# medianas fund BULL para calibrar gate de trajetória
fb=[p for p in Fp if p["reg"]=="BULL"]
import statistics as st
for k in ("drop","sweep","retr","reclaim","perna_bars"):
    vals=[p.get(k) for p in fb if p.get(k) is not None]
    if vals: print(f"    BULL-fund {k}: med {st.median(vals):.2f} p20 {sorted(vals)[len(vals)//5]:.2f}")
for tag,fn in [
    ("confluência dupla lad&dm (BULL/RANGE) | BEAR retr>=0.5",
       lambda p:(p["lad"] and p["dm"] and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
    ("pltdm & sweep>0 (BULL) | pltdm(RANGE) | BEAR retr>=0.5",
       lambda p:(p["pltdm"] and p.get("sweep",0)>0 and p["reg"]=="BULL") or (p["pltdm"] and p["reg"]=="RANGE") or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
    ("pltdm & drop>=6 (BULL) | pltdm(RANGE) | BEAR retr>=0.55&drop>=6",
       lambda p:(p["pltdm"] and p["drop"]>=6 and p["reg"]=="BULL") or (p["pltdm"] and p["reg"]=="RANGE") or (p["reg"]=="BEAR" and p["retr"]>=0.55 and p["drop"]>=6)),
    ("pltdm & (lad | sweep>0) (BULL) | pltdm(RANGE) | BEAR retr>=0.5",
       lambda p:(p["pltdm"] and (p["lad"] or p.get("sweep",0)>0) and p["reg"]=="BULL") or (p["pltdm"] and p["reg"]=="RANGE") or (p["reg"]=="BEAR" and p["retr"]>=0.5)),
    ("pltdm&sweep>0&drop>=5 (BULL) | pltdm(RANGE) | BEAR retr>=0.55&drop>=6",
       lambda p:(p["pltdm"] and p.get("sweep",0)>0 and p["drop"]>=5 and p["reg"]=="BULL") or (p["pltdm"] and p["reg"]=="RANGE") or (p["reg"]=="BEAR" and p["retr"]>=0.55 and p["drop"]>=6)),
]:
    sel=[p for p in piv if fn(p)]; print(f"  {tag:<58} n{len(sel):>4} recall {recall(sel)}/42 · fundos-pivô {sum(p['fund'] for p in sel)}")
SEL=[p for p in piv if (p["pltdm"] and p["reg"] in ("BULL","RANGE")) or (p["reg"]=="BEAR" and p["retr"]>=0.5)]
T=sorted(p["pt"] for p in SEL)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nMISSED (pltdm-união, N{len(SEL)}): "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
json.dump({"selN":len(SEL),"recall":recall(SEL),"missed":[ds(m) for m in missed]},open(HERE/"results"/"pltdm_confluence_20260707.json","w"),indent=1)
print("OK")
