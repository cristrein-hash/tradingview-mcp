#!/usr/bin/env python3
"""DIAGNÓSTICO: por que os 16 fundos do Cris ficaram fora da seleção M8 + investigar a ABERRAÇÃO de cluster F#/T#
no seam de bloco 2026-02-25. RAW-causal. Reusa o mesmo zigzag M8 de tops_bottoms.py."""
import json,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
M=8; HOR=192; BUF=0.25
def zigzag(s,M):
    """CORRIGIDO: pula warmup (atr=None, sem fallback 1.0), trilha hi/lo separados, alternância por dir.
    Dispara TOP quando cai M*atr do topo corrente; BOT quando sobe M*atr do fundo corrente. Funciona em tendência."""
    n=len(s); start=0
    while start<n and not s[start]["atr"]: start+=1
    if start>=n: return []
    piv=[]; d=0; hi=s[start]["h"]; hi_i=start; lo=s[start]["l"]; lo_i=start
    for i in range(start+1,n):
        a=s[i]["atr"]
        if not a: continue
        thr=M*a
        if s[i]["h"]>hi: hi=s[i]["h"]; hi_i=i
        if s[i]["l"]<lo: lo=s[i]["l"]; lo_i=i
        if d>=0 and (hi-s[i]["l"])>=thr:
            piv.append({"idx":hi_i,"t":s[hi_i]["t"],"price":hi,"kind":"TOP"}); d=-1; lo=s[i]["l"]; lo_i=i
        elif d<=0 and (s[i]["h"]-lo)>=thr:
            piv.append({"idx":lo_i,"t":s[lo_i]["t"],"price":lo,"kind":"BOT"}); d=1; hi=s[i]["h"]; hi_i=i
    return piv
def rev_excursion(s,p):
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; ext=Lp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["l"]<Lp-BUF*a: break
        ext=max(ext,s[i]["h"])
    return (ext-Lp)/a
def blk_for(t):
    for k,pr in PRIM.items():
        s=pr["series"]
        if s[0]["t"]<=t<=s[-1]["t"]: return k
    return None
def nearest_idx(s,t):
    best=0; bd=9e18
    for i,b in enumerate(s):
        d=abs(b["t"]-t)
        if d<bd: bd=d; best=i
    return best
PIV={k:zigzag(PRIM[k]["series"],M) for k in PRIM}
def local_low_idx(s,i,w=6):
    lo=max(0,i-w); hi=min(len(s),i+w+1); return min(range(lo,hi),key=lambda j:s[j]["l"])
his=[("yXh6On",3326.83,1755867600),("HUHVBo",3375.62,1756271700),("tWx6Y1",3516.03,1756955700),("KWbWzV",3623.49,1757466900),
("dmaIk6",3631.35,1757897100),("DMCuXa",3725.33,1758744900),("PtcxMz",3802.45,1759224600),
("AYumWt",3830.9,1759421700),("66L8mM",3946.28,1759827600),("TmoRmD",3950,1760038200),
("I7AeS6",4204.32,1760722200),("DnYTob",3888.33,1761638400),("CP35Pa",4015.8,1763445600),
("9qKuw3",4277.91,1765877400),("1HjVOB",4324.59,1767371400),("0xwWk2",4427.94,1770005700),
("csoI2F",4671.74,1770338700)]
his.sort(key=lambda x:x[2])
print("pivôs por bloco:", {k[:10]:len(PIV[k]) for k in PIV})
print("=== PARTE A — teus 17 fundos vs minha seleção M=8 ===")
for eid,price,t in his:
    k=blk_for(t)
    if not k: print(f"  {dt.datetime.utcfromtimestamp(t):%Y-%m-%d %H:%M} @ {price}  → fora do range RAW"); continue
    s=PRIM[k]["series"]; i0=nearest_idx(s,t); i=local_low_idx(s,i0,6); rev=rev_excursion(s,i); atr=s[i]["atr"] or 1.0
    REGION=24  # ~6h
    # match REGIONAL: meu BOT na mesma região (±REGION bars) E preço dentro de ~1.5 ATR (Cris: vale a região, não a barra)
    cand=[p for p in PIV[k] if p["kind"]=="BOT" and abs(p["idx"]-i)<=REGION and abs(p["price"]-s[i]["l"])<=1.5*atr]
    near=min(PIV[k],key=lambda p:abs(p["idx"]-i)) if PIV[k] else None; db=(near["idx"]-i) if near else 0
    if cand:
        m=min(cand,key=lambda p:abs(p["idx"]-i)); verdict=f"CAPTURADO regional (meu BOT @ {m['price']:.2f}, {m['idx']-i:+d}b)"
    elif rev<M: verdict=f"NÃO capturado: perna {rev:.1f}ATR < {M} (abaixo do threshold)"
    elif near: verdict=f"NÃO capturado (vizinho={near['kind']} @ {near['price']:.2f}, {db:+d}b fora da região/preço)"
    else: verdict="NÃO capturado"
    print(f"  {dt.datetime.utcfromtimestamp(s[i]['t']):%Y-%m-%d %H:%M} [{k[:10]}] low={s[i]['l']:.2f} (teu {price}) | perna_fwd={rev:.1f}ATR | {verdict}")
print("\n=== PARTE B — ABERRAÇÃO seam 2026-02-25 (cluster F#/T#) ===")
# bloco 8 = rerun; bloco 7 termina 2026-02-25
b7=[k for k in PRIM if k.startswith("2025-11-25")][0]; b8=[k for k in PRIM if k.startswith("2026-02-25")][0]
s7=PRIM[b7]["series"]; s8=PRIM[b8]["series"]
print(f"  bloco7 {b7[:10]} último bar: {dt.datetime.utcfromtimestamp(s7[-1]['t']):%Y-%m-%d %H:%M} close={s7[-1]['c']:.2f}")
print(f"  bloco8 {b8[:16]} primeiros 12 bars (preço + atr):")
for b in s8[:12]:
    print(f"    {dt.datetime.utcfromtimestamp(b['t']):%Y-%m-%d %H:%M} o={b['o']:.1f} h={b['h']:.1f} l={b['l']:.1f} c={b['c']:.1f} atr={b['atr']}")
print(f"  → salto seam: bloco7.close {s7[-1]['c']:.1f} → bloco8.open {s8[0]['o']:.1f} = {s8[0]['o']-s7[-1]['c']:+.1f}")
print(f"  meus pivôs M8 nos primeiros 60 bars do bloco8 (legs em ATR — procurar absurdos):")
piv8=zigzag(s8,M)
for p in piv8:
    if p["idx"]<=60:
        rev=rev_excursion(s8,p["idx"]) if p["kind"]=="BOT" else None
        a=s8[p["idx"]]["atr"]
        print(f"    idx{p['idx']:>3} {dt.datetime.utcfromtimestamp(p['t']):%Y-%m-%d %H:%M} {p['kind']} @ {p['price']:.2f} atr={a} {'rev='+format(rev,'.0f')+'ATR' if rev else ''}")
print(f"  quantos bars do bloco8 têm atr None/0 (warmup): {sum(1 for b in s8[:60] if not b['atr'])}/60")
