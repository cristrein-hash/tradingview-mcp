#!/usr/bin/env python3
"""APROFUNDAMENTO (não-conclusão) — o que distingue ENTRADA-boa de ENTRADA-ruim no candidato v2? Contrasta winners vs
losers em CARÁTER DE MERCADO no entry (causal): força de tendência (slope EMA21/ATR), regime de volatilidade (ATR
percentil), follow-through (taxa de breakouts que seguem), extensão (dist ao swing-low/ATR), hora. Objetivo: achar a
variável que condiciona o edge (regime-character) p/ a PRÓXIMA camada — não para concluir. Verified 2026-06-26."""
import csv, json, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}; TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
import datetime as dt
def char(b, t):
    s = SER.get(b); i = TID.get(b, {}).get(t)
    if s is None or i is None or i < 60: return None
    atr = s[i]["atr"]; ema = s[i]["ema21"]
    if not atr or not ema: return None
    # força de tendência: slope EMA21 sobre 20 barras / ATR
    slope = (ema - s[i-20]["ema21"]) / atr
    # vol regime: ATR atual vs mediana das ult 100 barras
    atrs = [s[k]["atr"] for k in range(max(0,i-100),i) if s[k]["atr"]]
    atr_p = atr / st.median(atrs) if atrs else 1.0
    # follow-through: dos breakouts de 20b nas ult 40 barras, % que seguiram (não re-fechou dentro em 4b)
    bos=0; foll=0
    for j in range(max(40,i-40),i+1):
        rh=max(x["h"] for x in s[j-20:j])
        if s[j]["c"]>rh:
            bos+=1
            if not any(s[k]["c"]<rh for k in range(j+1,min(j+5,i+1))): foll+=1
    foll_rate = foll/bos if bos else 0.5
    # extensão: dist do close ao menor low das ult 20 barras / ATR
    ext = (s[i]["c"] - min(x["l"] for x in s[i-20:i+1])) / atr
    hr = dt.datetime.utcfromtimestamp(t).hour
    return {"slope": slope, "atr_p": atr_p, "foll": foll_rate, "ext": ext, "hour": hr}
rows = [r for r in csv.DictReader(open(HERE / "candidates_v2_final.csv")) if r["t"] != "t"]
W=[]; L=[]
for r in rows:
    c = char(r["block"], int(r["t"]))
    if not c: continue
    (W if r["win"]=="True" else L).append(c)
print(f"v2 candidato: winners={len(W)} losers={len(L)}")
print("\n=== CARÁTER no entry: winner vs loser (mediana) ===")
def cmp(k, fmt="{:+.2f}"):
    wv=[x[k] for x in W]; lv=[x[k] for x in L]
    print(f"  {k:>10}: winner {fmt.format(st.median(wv))}  | loser {fmt.format(st.median(lv))}  | Δ {fmt.format(st.median(wv)-st.median(lv))}")
for k in ["slope","atr_p","foll","ext"]: cmp(k)
print(f"  {'hour':>10}: winner {st.median([x['hour'] for x in W]):.0f}h | loser {st.median([x['hour'] for x in L]):.0f}h")
# busca de condição que separa (não-gate, diagnóstico): slope alto + foll alto = caráter de tendência limpa?
print("\n=== teste de condicionamento (diagnóstico): trade em CARÁTER de tendência-limpa ===")
def cond(x): return x["slope"]>=0.5 and x["foll"]>=0.5
import itertools
all_=[(x,True) for x in W]+[(x,False) for x in L]
keep=[(x,w) for x,w in all_ if cond(x)]
if keep:
    kw=sum(1 for x,w in keep if w); print(f"  slope≥0.5 & foll≥0.5: n={len(keep)} WR={100*kw/len(keep):.0f}% (base WR={100*len(W)/(len(W)+len(L)):.0f}%)")
print("\nLeitura: se algum eixo de caráter separar winner/loser, é a variável de condicionamento da PRÓXIMA camada.")
