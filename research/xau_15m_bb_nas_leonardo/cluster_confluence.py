#!/usr/bin/env python3
"""CONFLUÊNCIA REAL bubbles-cluster × NAS × fundos/topos verdadeiros (M8). RAW-causal, leitura CONTÍNUA (não binária).
Tese (Cris): FUNDO verdadeiro = cluster SELL-bubbles (exaustão de venda absorvida) + presença NAS-LONG;
            TOPO verdadeiro = cluster BUY-bubbles (clímax de compra) + presença NAS-SHORT.
Para cada pivô, janela (t-PRE, t] (entrando no extremo): polaridade=sellw/(sellw+buyw) ponderada por tamanho(S1/M2/L3),
intensidade=sellw+buyw normalizada vs mediana-do-bloco, e contagem NAS LONG/SHORT. Compara FUNDOS vs TOPOS vs BASELINE
(barras aleatórias longe de pivôs). Reporta distribuição + combo-confluência + LIFT vs baseline. 2026-06-26."""
import json,random,statistics as st,datetime as dt
from pathlib import Path
random.seed(42)
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
SZ={"S":1,"M":2,"L":3}; PRE=16*900   # 16 barras (4h) entrando no extremo
def load_bubbles(key):
    f=HERE/"bubbles"/f"{key}.bubbles.jsonl"
    return [json.loads(l) for l in f.read_text().splitlines() if l]
BUB={k:load_bubbles(k) for k in PRIM}
NAS={k:[e for e in PRIM[k]["nas_events"] if e.get("t") and e.get("dir")] for k in PRIM}
# index por tempo (ordenado) p/ janela
for k in BUB: BUB[k].sort(key=lambda x:x["t"])
for k in NAS: NAS[k].sort(key=lambda x:x["t"])
import bisect
def win_metrics(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; lo=bisect.bisect_left(ts,t-PRE); hi=bisect.bisect_right(ts,t)
    sellw=buyw=0
    for x in bb[lo:hi]:
        w=SZ[x["size"]]
        if x["side"]=="SELL": sellw+=w
        else: buyw+=w
    pol=sellw/(sellw+buyw) if (sellw+buyw)>0 else None
    ne=NAS[key]; nts=[x["t"] for x in ne]; a=bisect.bisect_left(nts,t-PRE); b=bisect.bisect_right(nts,t)
    nl=sum(1 for x in ne[a:b] if x["dir"]=="LONG"); ns=sum(1 for x in ne[a:b] if x["dir"]=="SHORT")
    return pol,sellw+buyw,nl,ns
# mediana de intensidade por bloco (normalizar cluster)
blk_med={}
for k in PRIM:
    s=PRIM[k]["series"]; vals=[win_metrics(k,s[i]["t"])[1] for i in range(60,len(s),50)]
    vals=[v for v in vals if v>0]; blk_med[k]=st.median(vals) if vals else 1
rows=[r.split(",") for r in (HERE/"true_reversals_M8.csv").read_text().splitlines()[1:]]
H={h:i for i,h in enumerate(["date","t","kind","price","atr","in_atr","out_atr","bars_out","yr","block"])}
def blockkey_for(t):
    for k in PRIM:
        s=PRIM[k]["series"]
        if s[0]["t"]<=t<=s[-1]["t"]: return k
    return None
def collect(kind):
    out=[]
    for r in rows:
        if r[H["kind"]]!=kind: continue
        t=int(r[H["t"]]); key=blockkey_for(t)
        if not key: continue
        pol,tot,nl,ns=win_metrics(key,t)
        out.append({"pol":pol,"intens":tot/blk_med[key],"nl":nl,"ns":ns})
    return out
def baseline(n=1500):
    out=[]; piv_t=set(int(r[H["t"]]) for r in rows)
    keys=list(PRIM)
    for _ in range(n):
        k=random.choice(keys); s=PRIM[k]["series"]; i=random.randint(60,len(s)-1); t=s[i]["t"]
        if any(abs(t-pt)<60*900 for pt in piv_t): continue
        pol,tot,nl,ns=win_metrics(k,t)
        out.append({"pol":pol,"intens":tot/blk_med[k],"nl":nl,"ns":ns})
    return out
def summ(v,label,sell_side):
    pols=[x["pol"] for x in v if x["pol"] is not None]
    pol_dir=pols if sell_side else [1-p for p in pols]   # fração da cor da tese (SELL p/ fundo, BUY p/ topo)
    nas_dir=[x["nl"] if sell_side else x["ns"] for x in v]  # NAS na direção da reversão (LONG no fundo / SHORT no topo)
    # combo confluência: cluster da cor (fração>0.5) + intensidade>=1 + NAS-dir presente
    combo=sum(1 for x in v if x["pol"] is not None and ((x["pol"] if sell_side else 1-x["pol"])>0.5) and x["intens"]>=1.0 and (x["nl"] if sell_side else x["ns"])>=1)
    n=len(v)
    print(f"  {label:<10} n={n:>4} | cor-tese fração méd={st.mean(pol_dir):.2f} med={st.median(pol_dir):.2f} %>0.5={100*sum(1 for p in pol_dir if p>0.5)/len(pol_dir):.0f} "
          f"| intens méd={st.mean([x['intens'] for x in v]):.2f} | %NAS-dir>=1={100*sum(1 for x in nas_dir if x>=1)/n:.0f} | COMBO={100*combo/n:.0f}%")
bl=baseline()
print(f"=== CONFLUÊNCIA (janela {PRE//900} barras entrando no pivô) — 'cor-tese' = SELL p/ fundo / BUY p/ topo ===")
print("FUNDOS (tese: cluster SELL + NAS LONG):")
summ(collect("BOT"),"FUNDOS",sell_side=True); summ(bl,"baseline",sell_side=True)
print("TOPOS (tese: cluster BUY + NAS SHORT):")
summ(collect("TOP"),"TOPOS",sell_side=False); summ(bl,"baseline",sell_side=False)
print(f"\n[base bubbles] BUY={sum(1 for k in BUB for x in BUB[k] if x['side']=='BUY')} SELL={sum(1 for k in BUB for x in BUB[k] if x['side']=='SELL')} "
      f"| NAS LONG={sum(1 for k in NAS for x in NAS[k] if x['dir']=='LONG')} SHORT={sum(1 for k in NAS for x in NAS[k] if x['dir']=='SHORT')}")