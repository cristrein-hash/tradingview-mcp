#!/usr/bin/env python3
"""VENCER O MURO como no PLT/DM: PROCESSO sequencial, não feature-snapshot (2026-07-07).
Lição PLT/DM: a distinção não é propriedade da barra, é ESTADO da CAMINHADA. O "momentum para romper"
= a perna ANTES deste pullback JÁ fez um higher-high (rutura PROVADA sequencialmente) vs falhou
(lower-high = topo/range) vs sequência descendente (bear). Modelo o estado da escada de leg-tops.
Para cada entry, no momento do pullback, o autômato sabe (causal, só swings confirmados antes):
  - hh_confirmed: a perna imediatamente anterior fez leg-top > leg-top anterior (higher-high = rompeu).
  - n_hh_streak: quantos leg-tops consecutivos ascendentes (comprimento da escada = momentum acumulado).
  - broke_prior: o rally antes deste low EXCEDEU o último swing-high confirmado (BOS-up real).
  - since_last_hh: nº de pernas desde o último higher-high (0=acabou de romper; grande=escada parada=topo/range).
Testar: hh_confirmed / n_hh_streak separam winner/loser SEM envenenar? (winner=escada viva; loser=escada quebrada).
SANITY_PROBE: PROCESSO sequencial (estado da caminhada multi-perna, NÃO snapshot); escada de leg-tops;
higher-high como rutura provada; trajetória; causal known_at; representação-processo como no PLT/DM."""
import json, glob, bisect
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
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
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def build(rscale):
    piv=zz(rscale)
    # sequência de leg-tops confirmados (tipo H) com barra de confirmação
    highs=[(ci,pr) for tp,i,pr,ci in piv if tp=="H"]  # (conf_bar, price)
    highs.sort()
    HC=[c for c,_ in highs]; HP=[p for _,p in highs]
    # eventos de demanda (higher-low) — a MASTER caminhada
    EV=[]; prevH=prevL=None; lastH=None
    for tp,i,pr,ci in piv:
        if tp=="H": prevH=pr; lastH=pr
        else:
            if prevH is not None and lastH is not None and (prevL is None or pr>prevL): EV.append({"i":i,"lo":pr,"leg_top":lastH})
            prevL=pr
    return EV, HC, HP
def state_at(entry_bar, HC, HP):
    # leg-tops confirmados ANTES do entry
    k=bisect.bisect_right(HC, entry_bar)
    seq=HP[max(0,k-4):k]   # últimos até 4 leg-tops confirmados
    if len(seq)<2: return {"hh_confirmed":0,"n_hh_streak":0,"since_last_hh":9,"seqn":len(seq)}
    hh_confirmed=1 if seq[-1]>seq[-2] else 0
    # streak de higher-highs consecutivos (de trás p/ frente)
    streak=0
    for m in range(len(seq)-1,0,-1):
        if seq[m]>seq[m-1]: streak+=1
        else: break
    # pernas desde o último higher-high
    since=0
    for m in range(len(seq)-1,0,-1):
        if seq[m]>seq[m-1]: break
        since+=1
    return {"hh_confirmed":hh_confirmed,"n_hh_streak":streak,"since_last_hh":since,"seqn":len(seq)}
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
def rate(sel): return sum(x["out"] for x in sel)/len(sel) if sel else 0
for rscale in (6,9,12):
    EV,HC,HP=build(rscale)
    rows=[]; n=0
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
        n+=1; stt=state_at(j,HC,HP)
        rows.append({"n":n,"d":ds(TS[j]),"out":out,"sig2":1 if j-i<=4 else 0,**stt})
    if rscale==6: json.dump(rows,open(HERE/"results"/"sequential_walk_state_20260707.json","w"),indent=1)
    W=[r for r in rows if r["out"]==1]; L=[r for r in rows if r["out"]==0]
    print(f"\n########## ESCALA r={rscale} — N{len(rows)} ({len(W)}W/{len(L)}L) ##########")
    print("  hh_confirmed (perna anterior fez higher-high = rompeu):")
    for v in (1,0):
        sel=[r for r in rows if r["hh_confirmed"]==v]
        if sel: print(f"    hh={v}: N{len(sel):<3} hit-3R {rate(sel):.1%} · W{sum(x['out'] for x in sel)}/L{len(sel)-sum(x['out'] for x in sel)}")
    print("  n_hh_streak (comprimento da escada ascendente):")
    for lo,hi in [(0,0),(1,1),(2,2),(3,9)]:
        sel=[r for r in rows if lo<=r["n_hh_streak"]<=hi]
        if sel: print(f"    streak {lo}-{hi}: N{len(sel):<3} hit-3R {rate(sel):.1%} · W{sum(x['out'] for x in sel)}/L{len(sel)-sum(x['out'] for x in sel)}")
    print("  since_last_hh (0=acabou de romper; grande=escada parada=topo/range):")
    for lo,hi in [(0,0),(1,1),(2,9)]:
        sel=[r for r in rows if lo<=r["since_last_hh"]<=hi]
        if sel: print(f"    since {lo}-{hi}: N{len(sel):<3} hit-3R {rate(sel):.1%} · W{sum(x['out'] for x in sel)}/L{len(sel)-sum(x['out'] for x in sel)}")
print("\nsaved · OK")
