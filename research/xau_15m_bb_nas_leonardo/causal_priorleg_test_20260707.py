#!/usr/bin/env python3
"""Teste de CAUSALIDADE do 'momentum de escala' (2026-07-07). O ganho r=12 pode ser LOOKAHEAD (a subida
de 12-ATR que confirma o pivô É a subida vencedora). A parte causal do momentum = a PERNA ANTERIOR
(passado). Testo se prior_up_leg CAUSAL (perna de alta completada e confirmada ANTES do entry) reproduz
a melhoria sem lookahead.
SANITY_PROBE: momentum sequencial CAUSAL (perna anterior=passado, não subida futura); trajetória
multi-barra; markup master; testar lookahead; dois objetivos."""
import json, glob, bisect
import datetime as dt
import statistics as st
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
series={}
for p in sorted(glob.glob(HERE+"/primitives/*.primitives.json")):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]; EMA=[b.get("ema21") for b in S]
def zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
piv=zz(6)
Hpiv=sorted([(ci,i,pr) for tp,i,pr,ci in piv if tp=="H"])
Lpiv=sorted([(ci,i,pr) for tp,i,pr,ci in piv if tp=="L"])
def prior_up_leg_causal(j):
    hs=[(ci,idx,pr) for ci,idx,pr in Hpiv if ci<=j]
    if not hs: return None
    ci,hidx,hpr=hs[-1]
    ls=[(idx,pr) for ci2,idx,pr in Lpiv if idx<hidx and ci2<=j]
    if not ls: return None
    a=ATR[j] or 5
    return (hpr-ls[-1][1])/a
EV=[]; prevH=prevL=None; lastH=None
for tp,i,pr,ci in piv:
    if tp=="H": prevH=pr; lastH=pr
    else:
        if prevH is not None and lastH is not None and (prevL is None or pr>prevL): EV.append({"i":i,"lo":pr,"leg_top":lastH,"prevL":prevL})
        prevL=pr
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def yr(d): return d[:4]
rows=[]
for e in EV:
    i=e["i"]
    if not (W0<=TS[i]<=W1): continue
    lo=e["lo"]; a=ATR[i] or 5; j=None
    for k in range(i+1,min(N,i+25)):
        if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
    if j is None: continue
    ent=CL[j]; sl=lo-0.1*a; risk=ent-sl
    if risk<=0.05*a: continue
    tgt=ent+3*risk; out=0
    for m in range(j+1,min(N,j+1440)):
        if LO[m]<=sl: out=0; break
        if HI[m]>=tgt: out=1; break
    pul=prior_up_leg_causal(j)
    pul2=(e["leg_top"]-e["prevL"])/a if e["prevL"] else None
    rows.append({"d":ds(TS[j]),"out":out,"pul_causal":round(pul,2) if pul else 0,"pul_walk":round(pul2,2) if pul2 else 0})
W=[r for r in rows if r["out"]==1]; L=[r for r in rows if r["out"]==0]
print(f"N{len(rows)} {len(W)}W/{len(L)}L")
for k in ("pul_causal","pul_walk"):
    print(f"  {k}: WIN med {st.median([r[k] for r in W]):.2f}  LOSE med {st.median([r[k] for r in L]):.2f}")
def panel(sel,tag):
    if not sel: print(f"    {tag:<22} N0"); return
    w=sum(x["out"] for x in sel); yb=" ".join(f"{y}:{sum(x['out'] for x in sel if yr(x['d'])==y)}/{sum(1 for x in sel if yr(x['d'])==y)}" for y in ("2025","2026"))
    print(f"    {tag:<22} N{len(sel):<3} hit-3R {w/len(sel):.1%} · {yb}")
print("  --- prior_up_leg CAUSAL (perna anterior confirmada = passado) ---")
for thr in (5,8,10,12,15):
    panel([r for r in rows if r["pul_causal"]>=thr], f"pul_causal>={thr}")
print("  --- prior_up_leg via walk (leg_top-prevL, passado) ---")
for thr in (5,8,10,12,15):
    panel([r for r in rows if r["pul_walk"]>=thr], f"pul_walk>={thr}")
