#!/usr/bin/env python3
"""BUSCA EXAUSTIVA de threshold COMPLEXO de bubbles (Cris: peso MUITO maior p/ grandes, menor p/ pequenas; quantidade
de cada tamanho como definidora). Pergunta decisiva p/ CADA feature: prediz o RALI PRA FRENTE (fwd_rev) CONTROLANDO
pela perna-de-queda anterior? (corr média dentro de quartis de down_leg). Se nenhuma dá corr controlada >0 robusta →
bubbles não discriminam fundo verdadeiro além da queda. RAW-causal. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900; K=4; HOR=192; BUF=0.25
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
NAS={k:sorted([e for e in PRIM[k]["nas_events"] if e.get("t") and e.get("dir")],key=lambda x:x["t"]) for k in PRIM}
def counts(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    c={"sS":0,"sM":0,"sL":0,"bS":0,"bM":0,"bL":0}
    for x in bb[a:b]:
        key2=("s" if x["side"]=="SELL" else "b")+x["size"]; c[key2]+=1
    ne=NAS[key]; nt=[x["t"] for x in ne]; i=bisect.bisect_left(nt,t-PRE); j=bisect.bisect_right(nt,t)
    c["nl"]=sum(1 for x in ne[i:j] if x["dir"]=="LONG")
    return c
def fwd_rev(s,p):
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; ext=Lp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["l"]<Lp-BUF*a: break
        ext=max(ext,s[i]["h"])
    return (ext-Lp)/a
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(max(K,PRE//900),len(s)-K) if L[p]==min(L[p-K:p+K+1])]
def rank(xs):
    order=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0]*len(xs)
    for pos,i in enumerate(order): r[i]=pos
    return r
def pearson(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n; cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a)**.5; vb=sum((x-mb)**2 for x in b)**.5
    return cov/(va*vb) if va*vb else 0
def spearman(a,b): return pearson(rank(a),rank(b))
# coleta
data=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        c=counts(k,s[p]["t"]); a=s[p]["atr"] or 1.0
        dl=(s[p-PRE//900]["c"]-s[p]["l"])/a
        c["fwd"]=fwd_rev(s,p); c["dl"]=dl; data.append(c)
n=len(data); print(f"candidatos fractais: {n}")
# FEATURES (peso grande>>pequena + contagens)
def F(c,name):
    sS,sM,sL,bS,bM,bL=c["sS"],c["sM"],c["sL"],c["bS"],c["bM"],c["bL"]
    tot=sS+sM+sL+bS+bM+bL+1e-9
    return {
      "sell_w_1_3_10": (sS+3*sM+10*sL),
      "sell_w_0_1_5": (sM+5*sL),
      "sell_only_L": sL,
      "sell_w_1_4_16": (sS+4*sM+16*sL),
      "sellL_minus_buyL": (sL-bL),
      "sellL_frac": sL/tot,
      "sell_heavy_frac": (sM+5*sL)/(tot+4*(sM+sL)+1e-9),
      "sellL_dom": sL/(sL+bL+1),
      "sell_w_div_buy_w": (sS+3*sM+10*sL)/(bS+3*bM+10*bL+1),
      "climax_sellL_ge2": 1.0 if sL>=2 else 0.0,
      "climax_sellL_ge3": 1.0 if sL>=3 else 0.0,
      "n_sell_total": (sS+sM+sL),
      "sellL_x_nas": sL*(1 if c["nl"]>=1 else 0),
      "sell_w_x_nas": (sM+5*sL)*(1 if c["nl"]>=1 else 0),
    }[name]
feats=["sell_w_1_3_10","sell_w_0_1_5","sell_only_L","sell_w_1_4_16","sellL_minus_buyL","sellL_frac","sell_heavy_frac","sellL_dom","sell_w_div_buy_w","climax_sellL_ge2","climax_sellL_ge3","n_sell_total","sellL_x_nas","sell_w_x_nas"]
fwd=[c["fwd"] for c in data]; dls=[c["dl"] for c in data]
# quartis de down_leg
qs=sorted(dls); q=[qs[int(0.25*n)],qs[int(0.5*n)],qs[int(0.75*n)]]
def bucket(dl): return 0 if dl<q[0] else 1 if dl<q[1] else 2 if dl<q[2] else 3
buckets=[[] for _ in range(4)]
for i,c in enumerate(data): buckets[bucket(c["dl"])].append(i)
print(f"{'feature':<20} corr_bruta  corr_CONTROLADA(média4 buckets dl)   [+ = prediz rali além da queda]")
res=[]
for f in feats:
    vals=[F(c,f) for c in data]
    raw=spearman(vals,fwd)
    cs=[]
    for bi in buckets:
        if len(bi)>30:
            cs.append(spearman([vals[i] for i in bi],[fwd[i] for i in bi]))
    ctrl=sum(cs)/len(cs) if cs else 0
    res.append((f,raw,ctrl))
for f,raw,ctrl in sorted(res,key=lambda x:-x[2]):
    flag="  <== sinal" if ctrl>0.06 else ""
    print(f"  {f:<20} {raw:+.3f}      {ctrl:+.3f}{flag}")
print("\n  veredito: se TODAS corr_CONTROLADA ≈0 (|.|<0.06) → bubbles (mesmo grandes) NÃO discriminam fundo além da queda.")
print("  alguma corr_CONTROLADA >0 robusta e consistente nos 4 buckets → candidata REAL (verificar com DA).")
