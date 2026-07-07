#!/usr/bin/env python3
"""STEP 0b — CONTEXTO via ESTRUTURA DE MERCADO SMC (BOS/CHoCH), = o que o chart mostra (2026-07-07).
O classificador de swing diário (HH-HL) não reproduziu o visual. Troco pela máquina de estado de
estrutura (SMC): bull enquanto close rompe o último swing-high (bull-BOS); bear ao romper o último
swing-low (bear-BOS); CHoCH = 1º rompimento contra a tendência corrente. Estado = direção HTF real.
Deriva por entry:
  - struct: BULL / BEAR (estado corrente da estrutura no momento do entry).
  - choch_up_recent: houve CHoCH-up (bear->bull) nas últimas ~48 barras? (bull genuíno dentro de bear).
  - legs_up_since_flip: nº de bull-BOS desde a última virada p/ bull (maturidade: 1-2 jovem, muitos=esticado).
  - hh_broken_recent: fez novo higher-high estrutural há <=~24 barras (tendência viva) vs a falhar.
Verifica: winners em BULL-struct jovem; losers em BEAR-struct sem CHoCH-up e em bull-struct esticado.
SANITY_PROBE: estrutura SMC sequencial (o que o chart mostra); BOS/CHoCH state machine; direção HTF;
maturidade por nº de legs; trajetória; NÃO snapshot, NÃO EMA/HH-HL-diário; master preservado."""
import json, glob, bisect
import datetime as dt
from pathlib import Path
import statistics as st
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
# swings de estrutura (escala intermédia r=6) + BOS/CHoCH state machine causal
SW=zz(6)
# construir eventos de estrutura barra-a-barra: percorrer, manter último SH/SL confirmados
SH=None; SL=None; state=None
struct_ev=[]   # (bar_index, type 'bullBOS'/'bearBOS'/'chochUp'/'chochDown', level)
swi=0
confirmed=[]   # swings confirmados até barra i: list of (type,idx,price,conf_i)
# pré-ordenar swings por barra de confirmação
SWc=sorted([(ci,tp,pr,i) for tp,i,pr,ci in SW])
ptr=0
last_sh=None; last_sl=None; cur=None
flips=[]   # (bar_i, new_state)
bull_bos_bars=[]  # bar indices de bull-BOS
choch_up_bars=[]  # bar indices de CHoCH-up
for i in range(N):
    while ptr<len(SWc) and SWc[ptr][0]<=i:
        ci,tp,pr,si=SWc[ptr]
        if tp=="H": last_sh=pr
        else: last_sl=pr
        ptr+=1
    # BOS/CHoCH por close vs último SH/SL
    if last_sh is not None and CL[i]>last_sh+0.05*ATR[i]:
        if cur!="BULL":
            cur="BULL"; flips.append((i,"BULL")); choch_up_bars.append(i)  # bear->bull = CHoCH up
        bull_bos_bars.append(i); last_sh=CL[i]  # rompeu -> sobe a referência
    elif last_sl is not None and CL[i]<last_sl-0.05*ATR[i]:
        if cur!="BEAR": cur="BEAR"; flips.append((i,"BEAR"))
        last_sl=CL[i]
    struct_ev.append(cur)
bull_bos_set=bull_bos_bars; import bisect as bs
def struct_at(j):
    st_=struct_ev[j] or "NA"
    # choch_up recente (<=48 barras)
    cu=1 if any(j-48<=b<=j for b in choch_up_bars) else 0
    # legs_up desde a última virada p/ bull
    last_flip_bull=None
    for fi,fs in flips:
        if fi<=j and fs=="BULL": last_flip_bull=fi
    legs=sum(1 for b in bull_bos_bars if last_flip_bull is not None and last_flip_bull<=b<=j) if last_flip_bull is not None else 0
    # hh_broken_recent: houve bull-BOS <=24 barras
    hh=1 if any(j-24<=b<=j for b in bull_bos_bars) else 0
    return {"struct":st_,"choch_up":cu,"legs_up":legs,"hh_recent":hh}
# reconstruir 96 entries
piv=zz(6); EV=[]; prevH=prevL=None; lastH=None
for tp,i,pr,ci in piv:
    if tp=="H": prevH=pr; lastH=pr
    else:
        if prevH is not None and lastH is not None and (prevL is None or pr>prevL): EV.append({"i":i,"lo":pr,"leg_top":lastH})
        prevL=pr
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
rows=[]; n=0
for e in EV:
    i=e["i"]
    if not (W0<=TS[i]<=W1): continue
    lo=e["lo"]; a=ATR[i] or 5
    j=None
    for k in range(i+1,min(N,i+25)):
        if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
    if j is None: continue
    ent=CL[j]; sl=lo-0.1*a; risk=ent-sl
    if risk<=0.05*a: continue
    tgt=ent+3*risk; out=0
    for m in range(j+1,min(N,j+1440)):
        if LO[m]<=sl: out=0; break
        if HI[m]>=tgt: out=1; break
    n+=1; sa=struct_at(j)
    rows.append({"n":n,"d":ds(TS[j]),"t":TS[j],"out":out,"sig2":1 if j-i<=4 else 0,**sa})
json.dump(rows,open(HERE/"results"/"entry_struct_state_20260707.json","w"),indent=1)
def rate(sel): return sum(x["out"] for x in sel)/len(sel) if sel else 0
print("96 entries — contexto por ESTRUTURA SMC (state machine)")
print("\n=== struct x outcome (verificar vs visual) ===")
for c in ("BULL","BEAR","NA"):
    sel=[r for r in rows if r["struct"]==c]
    if sel: print(f"  {c:<5} N{len(sel):<3} hit-3R {rate(sel):.1%} · winners {sum(x['out'] for x in sel)}")
print("\n=== STEP1 — BULL genuíno DENTRO de BEAR: choch_up separa? ===")
BE=[r for r in rows if r["struct"]=="BEAR"]
for cu in (1,0):
    sel=[r for r in BE if r["choch_up"]==cu]
    if sel: print(f"  BEAR & choch_up={cu}: N{len(sel):<3} hit-3R {rate(sel):.1%} · winners {sum(x['out'] for x in sel)} · #{[r['n'] for r in sel]}")
print("\n=== STEP3(b) — maturidade: legs_up (winner vs loser em BULL-struct) ===")
BU=[r for r in rows if r["struct"]=="BULL"]
for lo,hi in [(1,2),(3,5),(6,99)]:
    sel=[r for r in BU if lo<=r["legs_up"]<=hi]
    if sel: print(f"  BULL legs_up {lo}-{hi}: N{len(sel):<3} hit-3R {rate(sel):.1%} · winners {sum(x['out'] for x in sel)}")
print("  hh_recent (tendência viva):")
for hh in (1,0):
    sel=[r for r in BU if r["hh_recent"]==hh]
    if sel: print(f"    BULL hh_recent={hh}: N{len(sel):<3} hit-3R {rate(sel):.1%}")
print("\nsaved · OK")
