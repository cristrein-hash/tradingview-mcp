#!/usr/bin/env python3
"""FUNDOS/TOPOS VERDADEIROS (não-traps) — 15M XAU 2024-05→2026-05, RAW.
ZIGZAG por ATR: confirma um FUNDO só quando o preço sobe >= M*ATR a partir do extremo (e TOPO simétrico ao cair M*ATR).
→ cada pivô confirmado tem perna-de-entrada E perna-de-saída >= M*ATR = REVERSÃO VERDADEIRA por construção; M é o
threshold que separa reversão real de TRAP (extremo que não entregou perna). Labeling de ground-truth (usa info forward
p/ CATALOGAR o que de fato foi fundo/topo — o teste de ENTRADA causal vem depois). Reporta distribuição p/ perceber M.
2026-06-26."""
import json,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
def zigzag(s,M):
    """CORRIGIDO 2026-06-26 (bugs: dir=0 corrompia extremo + atr=None→fallback$1 = cluster falso no seam + ZERO pivôs
    em tendência forte). Pula warmup (atr None, sem fallback), trilha hi/lo separados, alternância por dir; dispara TOP
    ao cair M*atr do topo corrente, BOT ao subir M*atr do fundo corrente. Funciona em tendência E range."""
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
def legs(s,piv):
    """anexa perna_in/perna_out em ATR a cada pivô (move da/para o pivô vizinho)."""
    for j,pv in enumerate(piv):
        a=s[pv["idx"]]["atr"] or 1.0
        pin=abs(pv["price"]-piv[j-1]["price"])/a if j>0 else None
        pout=abs(piv[j+1]["price"]-pv["price"])/a if j<len(piv)-1 else None
        pv["in_atr"]=pin; pv["out_atr"]=pout
    return piv
def collect(M):
    allp=[]
    for b,pr in PRIM.items():
        s=pr["series"]; pv=legs(s,zigzag(s,M))
        med_atr=st.median([x["atr"] for x in s if x["atr"]]) if any(x["atr"] for x in s) else 1.0
        for p in pv: p["block"]=b; p["yr"]=dt.datetime.utcfromtimestamp(p["t"]).year; p["sidx"]=p["idx"]; p["atr"]=s[p["idx"]]["atr"] or med_atr
        # barras da perna-out (até o próximo pivô)
        for j,p in enumerate(pv): p["bars_out"]=(pv[j+1]["idx"]-p["idx"]) if j<len(pv)-1 else None
        allp+=pv
    return allp
print("M(ATR) |  #TOPOS  #FUNDOS  /ano | mediana perna_out(ATR) | mediana barras_out")
for M in (3,5,8,12,16):
    allp=collect(M); tops=[p for p in allp if p["kind"]=="TOP"]; bots=[p for p in allp if p["kind"]=="BOT"]
    outs=[p["out_atr"] for p in allp if p["out_atr"]]; bo=[p["bars_out"] for p in allp if p["bars_out"]]
    print(f"  {M:>4}  |   {len(tops):>4}    {len(bots):>4}   {(len(tops)+len(bots))/2:>4.0f} |   {st.median(outs):>4.1f}                | {st.median(bo):>4.0f} ({st.median(bo)/4:.0f}h)")
# ---- escolha operacional: M=8 (reversão significativa ~5/mês, perna mediana ~14ATR) ----
import csv
M=8; allp=collect(M)
allp=[p for p in allp if p["out_atr"] is not None and p["atr"]]  # perna-out completa (atr c/ fallback mediano)
allp.sort(key=lambda x:x["t"])
with open(HERE/"true_reversals_M8.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["date","t","kind","price","atr","in_atr","out_atr","bars_out","yr","block"])
    for p in allp:
        w.writerow([dt.datetime.utcfromtimestamp(p["t"]).strftime("%Y-%m-%d %H:%M"),p["t"],p["kind"],round(p["price"],2),round(p["atr"],3),
                    round(p["in_atr"],1) if p["in_atr"] else "",round(p["out_atr"],1),p["bars_out"],p["yr"],p["block"][:10]])
bots=[p for p in allp if p["kind"]=="BOT"]; tops=[p for p in allp if p["kind"]=="TOP"]
print(f"\n=== M=8 ATR (RECOMENDADO p/ 'reversão verdadeira'): {len(bots)} FUNDOS + {len(tops)} TOPOS verdadeiros (2 anos) → true_reversals_M8.csv ===")
for yr in (2024,2025,2026):
    print(f"  {yr}: fundos={sum(1 for p in bots if p['yr']==yr)} topos={sum(1 for p in tops if p['yr']==yr)}")
print("\n  MAJORES (perna-out >= 25 ATR, os movimentos mais fortes):")
for p in sorted([p for p in allp if p["out_atr"]>=25],key=lambda x:x["t"]):
    print(f"   {dt.datetime.utcfromtimestamp(p['t']).strftime('%Y-%m-%d %H:%M')}  {p['kind']:>3} @ {p['price']:>8.2f}  perna_out={p['out_atr']:>4.0f}ATR ({p['bars_out']}b)")
