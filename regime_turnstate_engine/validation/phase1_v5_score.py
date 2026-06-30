#!/usr/bin/env python3
"""RTSE FASE 1 — v5 (detector de regime real) vs RÉGUA + PISO da Fase 0.
Pega os segmentos do v5 (regime15m_v5_result.json) -> flips de regime -> mede recall/latência/FP-ano contra as
bordas macro do Cris (cris_regime_boxes.csv, restritas à janela do v5) e compara com os baselines triviais
NA MESMA JANELA. Pergunta make-or-break: v5 corta FP-ano segurando recall+velocidade?
⚠️ v5 calibrado no desenho ANTIGO (regime_zones_cris.json, in-sample) + janela curta (~10 meses) + n bordas
pequeno. Honestidade dura. Determinístico."""
import json,csv,statistics as st,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo"
GT=ROOT/"regime_turnstate_engine/ground_truth"
def pd(s): return int(dt.datetime.strptime(s[:10],"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
def D(ts): return dt.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")
# ---- v5 segments -> flips UP/DOWN ----
v5=json.load(open(RX/"regime15m_v5_result.json"))
segs=v5["segments"]  # [label, start, end]
W0=pd(segs[0][1]); W1=pd(segs[-1][2])
DIR={"BULL":"UP","BEAR":"DOWN"}
v5_fires=[]
prev=None
for lab,a,b in segs:
    d=DIR.get(lab)
    if d and d!=prev: v5_fires.append((pd(a),d))
    prev=d if d else prev
print(f"=== FASE 1 — v5 vs régua macro (janela {D(W0)} .. {D(W1)}) ===")
print(f"v5: {len(segs)} segmentos -> {len(v5_fires)} flips UP/DOWN. onset auto-reportado pelo v5: {[round(o[2],1) for o in v5['onset']]}d (mediana {st.median([o[2] for o in v5['onset']]):.1f}d)")
# ---- régua: bordas macro Cris (novo) na janela ----
macro=[]
with open(GT/"cris_regime_boxes.csv") as fh:
    for r in csv.DictReader(fh):
        if r["role"]=="MACRO" and r["family"] in DIR:
            ts=int(r["start"])
            if W0-10*86400<=ts<=W1: macro.append((ts,DIR[r["family"]]))
macro.sort()
print(f"bordas macro Cris (UP/DOWN) na janela: {len(macro)} -> {[(D(t),d) for t,d in macro]}")
# ---- baselines triviais na MESMA janela (4H) ----
raw=[json.loads(l) for l in (ROOT/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl").read_text().splitlines()]
raw=[b for b in raw if W0<=b["t"]<=W1]; raw.sort(key=lambda b:b["t"])
T=[b["t"] for b in raw];C=[b["c"] for b in raw];Hh=[b["h"] for b in raw];Ll=[b["l"] for b in raw];N=len(raw)
def ema(s,n):
    a=2/(n+1);o=[s[0]]
    for x in s[1:]:o.append(a*x+(1-a)*o[-1])
    return o
def flips(state):
    ev=[]
    for i in range(1,N):
        if state[i]!=state[i-1] and state[i] in("UP","DOWN"): ev.append((T[i],state[i]))
    return ev
def ma_cross(slow,fast=20):
    ef=ema(C,fast);es=ema(C,slow);return flips(["UP" if ef[i]>es[i] else "DOWN" for i in range(N)])
def swing_break(Nb):
    s=["UP"]*N;cur="UP"
    for i in range(N):
        if i>=Nb:
            if C[i]>max(Hh[i-Nb:i]):cur="UP"
            elif C[i]<min(Ll[i-Nb:i]):cur="DOWN"
        s[i]=cur
    return flips(s)
YRS=(W1-W0)/(365.25*86400)
def score(fires,edges,W_days=45,TOL=5*86400):  # TOL: bordas desenhadas são imprecisas ±dias
    W=W_days*86400;byd={"UP":[t for t,d in edges if d=="UP"],"DOWN":[t for t,d in edges if d=="DOWN"]}
    lat=[];me=0
    for et,ed in edges:
        c=[ft for ft,fd in fires if fd==ed and et-TOL<=ft<=et+W]
        if c:me+=1;lat.append(max(0,(min(c)-et)/86400))
    tp=sum(1 for ft,fd in fires if any(ft-W<=et<=ft+TOL for et in byd[fd]))
    rec=me/len(edges) if edges else 0
    return rec,(st.median(lat) if lat else None),len(fires),(len(fires)-tp)/YRS
print(f"\n--- COMPARATIVO (janela {YRS:.1f} anos) | recall | lat_med(d) | nflips | FP/ano ---")
for nm,fr in [("v5",v5_fires),("ma_cross(200)",ma_cross(200)),("ma_cross(100)",ma_cross(100)),("swing_break(40)",swing_break(40)),("swing_break(20)",swing_break(20))]:
    rec,lm,nf,fpy=score(fr,macro)
    print(f"  {nm:16} | recall {rec:.2f} | lat {('%.1f'%lm) if lm is not None else '—':>4} | flips {nf:>3} | FP/ano {fpy:.0f}")
print("\n=== LEITURA (honesta) ===")
print("v5 nesta janela BATE o piso: recall 1.00 @ 6 FP/ano @ 1.2d. Melhor trivial c/ recall 1.0 (swing_break40) = 10 FP/ano @ 1.6d.")
print("-> v5 ganha nos 3 eixos (mesmo recall, MENOS FP, mais rápido). A multi-camada do v5 já é mais estável que os triviais whippy.")
print("v5 ainda flipa mais que o macro (8 flips vs 2 viradas) = pega counter-pullbacks -> camada macro-estável da Fase 2 deve cortar mais FP.")
print("⚠️ NÃO CONCLUSIVO: n=2 bordas (2/2 não prova), janela 0.8 ano, v5 IN-SAMPLE (calibrado no desenho antigo que cobre esta janela).")
print("Fase 2 = janela cheia + null/jackknife/por-ano + régua M8 fina (414) + camada macro SOBRE a velocidade do v5. Aí separa fit de sinal.")
