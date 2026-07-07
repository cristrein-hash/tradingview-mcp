#!/usr/bin/env python3
"""VERIFICAR CAUSALIDADE de supply_above (2026-07-07) — ANTES de reportar (regra dura pós-fúria Cris).
Questoes de lookahead:
  A. zonas SUPPLY usadas = so as nascidas ANTES do entry? (born_t < entry)
  B. o filtro last_t>=entry-3d usa tempo FUTURO? (last_t pode ser depois do entry)
  C. o nivel z['low'] e o de NASCIMENTO ou o extent FINAL (futuro)?
Testo 3 versoes de supply_above e vejo se o R & supply>=0.35 = 72% sobrevive a estrito-causal:
  v_orig  : como no feature_battery (born<entry, filtro last_t>=entry-3d, nivel z.low)
  v_born  : SO born_t<entry (sem last_t), nivel z.low
  v_strict: born_t<entry AND last_t<=entry (zona ja completada antes = SEM extensao futura), nivel z.low
Se 72% cai muito no estrito -> havia leak; se aguenta -> causal."""
import json, glob, bisect
import datetime as dt
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
series={}; zones=[]
for p in sorted(glob.glob(HERE+"/primitives/*.primitives.json")):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    zones+=[z for z in d.get("zones",[]) if z.get("born_t")]
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]; EMA=[b.get("ema21") for b in S]
zones.sort(key=lambda z:z["born_t"]); ZT=[z["born_t"] for z in zones]
# diagnostico: quantas zonas SUPPLY tem last_t > born_t (extensao no tempo)? quantas last_t no futuro tipico?
supz=[z for z in zones if z["text"]=="SUPPLY"]
ext=sum(1 for z in supz if z.get("last_t",z["born_t"])>z["born_t"])
print(f"zonas SUPPLY total {len(supz)} · com last_t>born_t (estendem no tempo) {ext} ({ext/len(supz):.0%})")
def sup_above(t0, px, a, mode):
    hi=bisect.bisect_right(ZT,t0)
    out=[]
    for z in zones[:hi]:
        if z["text"]!="SUPPLY" or z["low"]<=px: continue
        lt=z.get("last_t",z["born_t"])
        if mode=="orig" and not (lt>=t0-3*86400): continue
        if mode=="strict" and not (lt<=t0): continue   # zona ja completada antes do entry
        out.append((z["low"]-px)/a)
    return min(out) if out else 99
def zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
piv=zz(6); EV=[]; prevH=prevL=None; lastH=None
for tp,i,pr,ci in piv:
    if tp=="H": prevH=pr; lastH=pr
    else:
        if prevH is not None and lastH is not None and (prevL is None or pr>prevL): EV.append({"i":i,"lo":pr})
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
    aj=ATR[j] or 5; px=CL[j]
    rows.append({"d":ds(TS[j]),"out":out,"sig2":1 if j-i<=4 else 0,
                 "s_orig":round(sup_above(TS[j],px,aj,"orig"),2),
                 "s_born":round(sup_above(TS[j],px,aj,"born"),2),
                 "s_strict":round(sup_above(TS[j],px,aj,"strict"),2)})
def panel(sel,tag):
    if not sel: print(f"    {tag:<34} N0"); return
    w=sum(x["out"] for x in sel); yb=" ".join(f"{y}:{sum(x['out'] for x in sel if yr(x['d'])==y)}/{sum(1 for x in sel if yr(x['d'])==y)}" for y in ("2025","2026"))
    print(f"    {tag:<34} N{len(sel):<3} hit-3R {w/len(sel):.1%} · {yb}")
R=[r for r in rows if r["sig2"]==1]
print(f"\nR-subset N{len(R)}")
for key in ("s_orig","s_born","s_strict"):
    print(f"  --- {key} ---")
    panel([r for r in R if r[key]>=0.35], f"R & {key}>=0.35")
# quantas mudam de bucket entre orig e strict?
diff=sum(1 for r in R if (r['s_orig']>=0.35)!=(r['s_strict']>=0.35))
print(f"\n  entries R que mudam de lado (orig vs strict >=0.35): {diff}/{len(R)}")
