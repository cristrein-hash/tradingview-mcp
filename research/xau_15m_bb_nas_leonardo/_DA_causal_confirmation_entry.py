#!/usr/bin/env python3
"""DA RECALIBRADO (XAU 15M) — TETO look-ahead dos pivôs M8 vs ENTRADA CAUSAL real.

CONTEXTO: strategy_pivots.py entra no CLOSE da barra do pivô M8 (fundo/topo) → WR95% avgR+4.30 sumR+1781.
Isso é look-ahead estrutural: o pivô M8 só é CONHECÍVEL depois que o preço já andou M*ATR (=8ATR) do extremo.
Entrar NA barra do extremo usa o futuro.

Este script re-roda os MESMOS pivôs mas entra na BARRA DE CONFIRMAÇÃO do zigzag em tempo real:
  - BOT confirmado no bar i quando (h[i]-lo) >= 8*atr  → o preço já SUBIU 8ATR do fundo.
  - TOP confirmado no bar i quando (hi-l[i]) >= 8*atr  → o preço já CAIU 8ATR do topo.
Entry = close da barra de confirmação. SL estrutural = extremo confirmado ∓0.1ATR. Let-run (mesmo engine).

Também: TASK3 (penalidade de entrada: barras + ATR/% entre extremo e confirmação),
         TASK4 (gatilhos causais mais rápidos: reclaim de R*ATR, R=1,2,3,4 em vez de 8).
RAW. Reprodutível. 2026-06-26."""
import json,csv,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480; M=8

# ---------- let-run engine (idêntico ao strategy_pivots.py) ----------
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def cf_high(s,i):
    H=[b["h"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if H[p]==max(H[p-2:p+3]): bst=H[p]
    return bst
def letrun(s,ei,entry,sl,long,atr):
    risk=(entry-sl) if long else (sl-entry)
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if long:
            if s[i]["l"]<=trail: ex=trail; break
            if (s[i]["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if s[i]["h"]>=trail: ex=trail; break
            if (entry-s[i]["l"])/risk>=1: r1=True
            if r1:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,((ex-entry) if long else (entry-ex))/risk))

# ---------- zigzag que registra (pivô, confirmação) por threshold R ----------
def zigzag_with_confirm(s,R):
    """Replica tops_bottoms.zigzag mas devolve, p/ cada pivô: idx do extremo + idx do bar que confirmou.
    Confirmação = primeiro bar onde o movimento contrário atinge R*atr_DAQUELE_bar (causal, só dados <=i)."""
    n=len(s); start=0
    while start<n and not s[start]["atr"]: start+=1
    if start>=n: return []
    piv=[]; d=0; hi=s[start]["h"]; hi_i=start; lo=s[start]["l"]; lo_i=start
    for i in range(start+1,n):
        a=s[i]["atr"]
        if not a: continue
        thr=R*a
        if s[i]["h"]>hi: hi=s[i]["h"]; hi_i=i
        if s[i]["l"]<lo: lo=s[i]["l"]; lo_i=i
        if d>=0 and (hi-s[i]["l"])>=thr:
            # TOP no hi_i confirmado AGORA (bar i). Entry SHORT no close de i.
            piv.append({"pivot_i":hi_i,"confirm_i":i,"price":hi,"kind":"TOP","t":s[hi_i]["t"]}); d=-1; lo=s[i]["l"]; lo_i=i
        elif d<=0 and (s[i]["h"]-lo)>=thr:
            piv.append({"pivot_i":lo_i,"confirm_i":i,"price":lo,"kind":"BOT","t":s[lo_i]["t"]}); d=1; hi=s[i]["h"]; hi_i=i
    return piv

def run_causal(R):
    """Entra no CLOSE do bar de confirmação. SL estrutural no extremo confirmado ∓0.1ATR. let-run."""
    res={"LONG":[],"SHORT":[]}; pens=[]
    for b,pr in PRIM.items():
        s=pr["series"]; pv=zigzag_with_confirm(s,R)
        for p in pv:
            ci=p["confirm_i"]; pi=p["pivot_i"]
            if ci+2>=len(s): continue
            atr=s[ci]["atr"] or 1.0
            entry=s[ci]["c"]; ext=p["price"]
            # penalidade: quanto o preço já andou do extremo ao close de confirmação
            move=abs(entry-ext); pens.append({"bars":ci-pi,"atr":move/atr,"pct":100*move/ext,"kind":p["kind"]})
            if p["kind"]=="BOT":
                sl=ext-0.1*atr
                Rr=letrun(s,ci,entry,sl,True,atr); side="LONG"
            else:
                sl=ext+0.1*atr
                Rr=letrun(s,ci,entry,sl,False,atr); side="SHORT"
            if Rr is None: continue
            res[side].append({"R":Rr,"yr":dt.datetime.utcfromtimestamp(p["t"]).year,"t":p["t"]})
    return res,pens

def stats(v):
    if not v: return None
    n=len(v); sm=sum(x["R"] for x in v); wr=100*sum(1 for x in v if x["R"]>0)/n
    ts=sorted(v,key=lambda x:x["t"]); eq=pk=dd=0; stk=mstk=0
    for x in ts:
        eq+=x["R"];pk=max(pk,eq);dd=min(dd,eq-pk)
        if x["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    run=sum(1 for x in v if x["R"]>=5)
    return dict(n=n,wr=wr,avg=sm/n,sm=sm,dd=dd,stk=mstk,run=run)
def rep(v,lab):
    d=stats(v)
    if not d: print(f"  {lab}: vazio"); return
    print(f"  {lab:<16}: n={d['n']:>3} WR={d['wr']:>3.0f}% avgR={d['avg']:+.2f} sumR={d['sm']:+6.0f} maxDD={d['dd']:>4.0f}R streakL={d['stk']:>2} runners(>=5R)={d['run']}")

# ================== TASK 2: ENTRADA CAUSAL (confirmação total 8ATR) ==================
print("="*84)
print(f"TASK 2 — ENTRADA CAUSAL (confirma no zigzag M={M}; entry=close da confirmação; SL estrutural; let-run)")
print("="*84)
res,pens=run_causal(M)
print("LONG (fundos confirmados):"); rep(res["LONG"],"todos")
for y in (2024,2025,2026): rep([x for x in res["LONG"] if x["yr"]==y],f"{y}")
print("SHORT (topos confirmados):"); rep(res["SHORT"],"todos")
for y in (2024,2025,2026): rep([x for x in res["SHORT"] if x["yr"]==y],f"{y}")
print("COMBINADO:"); rep(res["LONG"]+res["SHORT"],"todos")
for y in (2024,2025,2026): rep([x for x in (res["LONG"]+res["SHORT"]) if x["yr"]==y],f"{y}")

# ================== TASK 3: PENALIDADE DE ENTRADA ==================
print("\n"+"="*84)
print("TASK 3 — PENALIDADE: distância extremo→confirmação (quanto o preço já andou)")
print("="*84)
allbars=[p["bars"] for p in pens]; allatr=[p["atr"] for p in pens]; allpct=[p["pct"] for p in pens]
print(f"  TODOS n={len(pens)}: mediana barras={st.median(allbars):.0f} ({st.median(allbars)/4:.1f}h) | "
      f"mediana ATR andado={st.median(allatr):.1f} | mediana %move={st.median(allpct):.2f}%")
for k in ("BOT","TOP"):
    sub=[p for p in pens if p["kind"]==k]
    print(f"  {k} n={len(sub)}: mediana barras={st.median([p['bars'] for p in sub]):.0f} | "
          f"mediana ATR={st.median([p['atr'] for p in sub]):.1f} | mediana %={st.median([p['pct'] for p in sub]):.2f}%")
print(f"  → o SL estrutural fica ~{st.median(allatr):.1f}ATR de distância do entry (risco por trade grande).")

# ================== TASK 4: GATILHOS CAUSAIS MAIS RÁPIDOS ==================
print("\n"+"="*84)
print("TASK 4 — GATILHOS CAUSAIS MAIS RÁPIDOS (reclaim R*ATR em vez de 8*ATR)")
print("  NOTA: zigzag com R menor gera MAIS pivôs (inclui traps que M8 filtraria).")
print("="*84)
for R in (1,2,3,4,6,8):
    r,_=run_causal(R); comb=r["LONG"]+r["SHORT"]; d=stats(comb)
    if d:
        print(f"  R={R}*ATR: n={d['n']:>4} WR={d['wr']:>3.0f}% avgR={d['avg']:+.2f} sumR={d['sm']:+6.0f} "
              f"maxDD={d['dd']:>4.0f}R streakL={d['stk']:>2} runners={d['run']}")
print("\nDONE.")
