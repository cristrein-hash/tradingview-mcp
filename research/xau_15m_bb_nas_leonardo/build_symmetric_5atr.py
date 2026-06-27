#!/usr/bin/env python3
"""TESTE DIRECIONAL (Cris 2026-06-27): estrategia atual e LONG-only e dispara em topos.
Constroi o ESPELHO SHORT CAUSAL e mede se topo=short ganha (DA: simular, nao assumir).
LONG  = fractal-low  (L[i]==min i-4..i+4), confirma high>=low+M*atr -> compra, SL=flush_low-0.5atr,  let-run p/ cima.
SHORT = fractal-high (H[i]==max i-4..i+4), confirma low<=high-M*atr -> vende,  SL=flush_high+0.5atr, let-run p/ baixo.
Pivo confirmado ANTES do entry (cj>i+4) => sem look-ahead (check_fractal_causality: 0.5% imaterial).
M8 usado APENAS como rotulo de diagnostico (flagado look-ahead pelo DA), nunca como sinal.
Dedup: uma posicao por vez GLOBAL (long+short competem). SL=B(0.5atr). EXIT let-run. RAW-causal. M=5."""
import json, bisect, csv, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
        for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
RCAP=20.0; HMAX=480; M=5; SLk=0.5
# macro regime as-of (diag)
MR=json.load(open(HERE/"macro_regime_4h.json"))["bars_4h"]; MR.sort(key=lambda x:x["t_end"])
MRend=[x["t_end"] for x in MR]
def regime_asof(t):
    k=bisect.bisect_right(MRend,t)-1; return MR[k]["macro"] if k>=0 else "NA"
# M8 (diag only)
M8=[]
with open(HERE/"true_reversals_M8.csv") as f:
    for r in csv.DictReader(f): M8.append((int(r["t"]),r["kind"]))
M8.sort(); M8T=[x[0] for x in M8]
def near_m8(t):
    k=bisect.bisect_left(M8T,t); c=[M8[j] for j in (k-1,k) if 0<=j<len(M8)]
    if not c: return None
    return min(c,key=lambda x:abs(x[0]-t))[1]

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
def letrun_long(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1); exi=end
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; exi=k; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),exi
def letrun_short(s,cj,entry,sl,atr):
    risk=sl-entry
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1); exi=end
    for k in range(cj+1,end+1):
        if s[k]["h"]>=trail: ex=trail; exi=k; break
        if (entry-s[k]["l"])/risk>=1: r1=True
        if r1:
            sw=cf_high(s,k)
            if sw: trail=min(trail,sw+0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(entry-ex)/risk)),exi

def anchors(s):
    """gera (cj, side, R, exi, entry_t) p/ todos os sinais long e short."""
    nn=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]; out=[]
    for i in range(96,nn-4):
        atr=s[i]["atr"]
        if not atr: continue
        if L[i]==min(L[i-4:i+5]):  # fractal low -> LONG
            cj=None
            for q in range(i+1,min(i+HMAX,nn-2)):
                if s[q]["h"]>=s[i]["l"]+M*atr: cj=q; break
            if cj is not None and cj+2<nn:
                flush=min(x["l"] for x in s[i:cj+1]); entry=s[cj]["c"]; sl=flush-SLk*atr
                R,exi=letrun_long(s,cj,entry,sl,atr)
                if R is not None: out.append((cj,"L",R,exi,s[cj]["t"],entry,sl))
        if H[i]==max(H[i-4:i+5]):  # fractal high -> SHORT
            cj=None
            for q in range(i+1,min(i+HMAX,nn-2)):
                if s[q]["l"]<=s[i]["h"]-M*atr: cj=q; break
            if cj is not None and cj+2<nn:
                flush=max(x["h"] for x in s[i:cj+1]); entry=s[cj]["c"]; sl=flush+SLk*atr
                R,exi=letrun_short(s,cj,entry,sl,atr)
                if R is not None: out.append((cj,"S",R,exi,s[cj]["t"],entry,sl))
    return out

def metrics(rows):
    """rows: list of (t,side,R)"""
    rows=sorted(rows)
    n=len(rows)
    if not n: return None
    w=sum(1 for _,_,R in rows if R>0); sm=sum(R for _,_,R in rows)
    eq=pk=dd=0; stk=mstk=0
    for _,_,R in rows:
        eq+=R; pk=max(pk,eq); dd=min(dd,eq-pk)
        if R<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    span=(rows[-1][0]-rows[0][0])/(7*86400)
    yr={y:[0,0] for y in (2024,2025,2026)}
    for t,_,R in rows:
        y=dt.datetime.utcfromtimestamp(t).year
        if y in yr: yr[y][0]+=1; yr[y][1]+=(R>0)
    yrs="/".join(f"{(100*yr[y][1]/yr[y][0]):.0f}" if yr[y][0] else "-" for y in (2024,2025,2026))
    return dict(n=n,wr=100*w/n,sumr=sm,avgr=sm/n,dd=dd,streak=mstk,freq=n/span,yrs=yrs)

def fmt(name,m):
    if not m: return f"  {name:<34} (vazio)"
    return f"  {name:<34} N={m['n']:>3} WR={m['wr']:4.1f}% avgR={m['avgr']:+.2f} sumR={m['sumr']:+6.1f} DD={m['dd']:5.1f}R streak={m['streak']:>2} freq={m['freq']:.1f} | WR24/25/26 {m['yrs']}"

# coleta por bloco
ALL={"L":[],"S":[]}; COMB=[]
short_diag=[]  # (regime, m8kind, R)
for k,pr in PRIM.items():
    s=pr["series"]
    a=anchors(s)
    # standalone por lado (dedup proprio)
    for side in ("L","S"):
        side_a=sorted([x for x in a if x[1]==side],key=lambda x:x[0]); busy=-10**9
        for cj,sd,R,exi,t,en,sl in side_a:
            if cj<=busy: continue
            busy=exi; ALL[side].append((t,sd,R))
            if side=="S": short_diag.append((regime_asof(t),near_m8(t),R))
    # combinado (dedup global long+short)
    comb_a=sorted(a,key=lambda x:x[0]); busy=-10**9
    for cj,sd,R,exi,t,en,sl in comb_a:
        if cj<=busy: continue
        busy=exi; COMB.append((t,sd,R))

print("="*96)
print("ESPELHO SHORT CAUSAL — 5ATR confirm, SL=B(flush+-0.5ATR), let-run. Dedup uma-posicao.")
print("="*96)
print("STANDALONE (cada lado com seu proprio dedup):")
print(fmt("LONG-only (atual)", metrics(ALL["L"])))
print(fmt("SHORT-only (espelho novo)", metrics(ALL["S"])))
print()
print("COMBINADO simetrico (dedup global, long+short competem 1 posicao):")
cm=metrics(COMB)
print(fmt("LONG+SHORT", cm))
if cm:
    nl=sum(1 for _,sd,_ in COMB if sd=="L"); ns=sum(1 for _,sd,_ in COMB if sd=="S")
    print(f"     -> dos {cm['n']}: {nl} long, {ns} short")
print()
print("DIAGNOSTICO do SHORT-only por REGIME as-of (causal) e por M8 (flag look-ahead, so explica passado):")
for reg in ("BULL","NEUTRAL","BEAR"):
    g=[R for r,_,R in short_diag if r==reg]
    if g: print(f"  SHORT em {reg:<8} n={len(g):>3} WR={100*sum(1 for x in g if x>0)/len(g):4.1f}% sumR={sum(g):+6.1f}")
for kd in ("BOT","TOP"):
    g=[R for _,m,R in short_diag if m==kd]
    if g: print(f"  SHORT perto de {kd} n={len(g):>3} WR={100*sum(1 for x in g if x>0)/len(g):4.1f}% sumR={sum(g):+6.1f}")
