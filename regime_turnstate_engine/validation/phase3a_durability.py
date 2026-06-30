#!/usr/bin/env python3
"""RTSE FASE 3a (desenho corrigido) — CARACTERIZAÇÃO: que features NO INSTANTE do pivô separam virada
DURÁVEL de FIZZLE? Label abundante e regime-relevante = MFE forward em ATR (não M8-proximidade, não 75min).
Preditores CAUSAIS no pivô (≤ pivô): rsi, dist_ema, atr_compress, leg_depth, velocity_decel, swept.
Cross-check: pivôs duráveis batem com bordas MACRO do Cris? null por feature. n=414 (bem-powered).
⚠️ caracterização forward (M8/MFE = gabarito, NÃO detector live) → calibração, não promoção. Determinístico."""
import json,csv,statistics as st,random,bisect
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
PR=ROOT/"research/xau_15m_bb_nas_leonardo/primitives"; GT=ROOT/"regime_turnstate_engine/ground_truth"
bars={}
for f in sorted(PR.glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: bars[b["t"]]=b
S=[bars[t] for t in sorted(bars)]; T=[b["t"] for b in S]
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S]
idx={t:i for i,t in enumerate(T)}
def atr_at(i,n=14):
    if i<n: return None
    tr=[max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-n+1,i+1)]
    return sum(tr)/len(tr)
m8=[(int(d["t"]),d["kind"]) for d in csv.DictReader(open(ROOT/"research/xau_15m_bb_nas_leonardo/true_reversals_M8.csv"))]
K=96  # 1 dia de 15M p/ MFE
rows=[]
for t,kind in m8:
    i=idx.get(t)
    if i is None or i<30 or i+K>=len(S): continue
    a=atr_at(i)
    if not a or a<=0: continue
    rsi=S[i].get("rsi"); ema=S[i].get("ema21")
    if rsi is None or ema is None: continue
    # LABEL: MFE forward na direção da reversão, em ATR
    # LABEL em % do preço (NÃO /ATR_atual) -> independe do denominador dos preditores (evita correlação espúria)
    if kind=="BOT": mfe=100*(max(H[i+1:i+K+1])-Lo[i])/C[i]
    else:           mfe=100*(H[i]-min(Lo[i+1:i+K+1]))/C[i]
    # PREDITORES no pivô (causal), orientados: maior = mais favorável à reversão
    dist_ema=(C[i]-ema)/a;  dist_ema = -dist_ema if kind=="BOT" else dist_ema   # BOT abaixo da ema = +
    rsi_exh = (50-rsi) if kind=="BOT" else (rsi-50)                              # oversold/overbought
    atr_comp = a/ (st.mean([atr_at(j) or a for j in range(i-20,i)]) or a)        # baixo=comprimido (inverter)
    atr_comp = 1/atr_comp
    leg = (max(H[i-20:i])-Lo[i])/a if kind=="BOT" else (H[i]-min(Lo[i-20:i]))/a  # profundidade da perna
    velo = (C[i]-C[i-6])/a; velo = -velo if kind=="BOT" else velo                # perna a favor
    swept = 1.0 if ((kind=="BOT" and Lo[i]<min(Lo[i-20:i-1])) or (kind=="TOP" and H[i]>max(H[i-20:i-1]))) else 0.0
    rows.append({"t":t,"kind":kind,"mfe":mfe,"dist_ema":dist_ema,"rsi_exh":rsi_exh,"atr_comp":atr_comp,"leg":leg,"velo":velo,"swept":swept})
mfes=sorted(r["mfe"] for r in rows); med=mfes[len(mfes)//2]
for r in rows: r["durable"]= r["mfe"]>=med
nd=sum(r["durable"] for r in rows); print(f"FASE 3a corrigida — pivôs M8 usáveis: {len(rows)} | DURÁVEL(>={med:.1f}% MFE) {nd} / FIZZLE {len(rows)-nd}")
print(f"\nfeature | média DURÁVEL | média FIZZLE | diff | null p(|>=|real|)")
feats=["dist_ema","rsi_exh","atr_comp","leg","velo","swept"]
random.seed(7)
for fkey in feats:
    dv=[r[fkey] for r in rows if r["durable"]];fz=[r[fkey] for r in rows if not r["durable"]]
    real=st.mean(dv)-st.mean(fz)
    allv=[r[fkey] for r in rows];labs=[r["durable"] for r in rows];diffs=[]
    for _ in range(300):
        random.shuffle(labs)
        diffs.append(st.mean([allv[i] for i in range(len(allv)) if labs[i]])-st.mean([allv[i] for i in range(len(allv)) if not labs[i]]))
    p=sum(1 for x in diffs if abs(x)>=abs(real))/len(diffs)
    print(f"  {fkey:9} | {st.mean(dv):+.3f}      | {st.mean(fz):+.3f}      | {real:+.3f} | {p:.3f} {'*' if p<0.05 else ''}")
# cross-check: pivôs duráveis perto de bordas MACRO do Cris?
edges=[int(r["start"]) for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")) if r["role"]=="MACRO" and r["family"] in("BULL","BEAR")]
edges.sort()
def neard(ts,W=5*86400):
    j=bisect.bisect_left(edges,ts-W);return j<len(edges) and edges[j]<=ts+W
dn=sum(1 for r in rows if r["durable"] and neard(r["t"]));fn=sum(1 for r in rows if (not r["durable"]) and neard(r["t"]))
print(f"\ncross-check Cris MACRO: duráveis perto de borda {dn}/{nd} ({100*dn/nd:.0f}%) vs fizzle {fn}/{len(rows)-nd} ({100*fn/(len(rows)-nd):.0f}%)")
print("LEITURA: features com p<0.05 = separam durável de fizzle no pivô (sinal causal real p/ o detector). Sem nenhuma = parede.")
