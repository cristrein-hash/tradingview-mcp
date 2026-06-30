#!/usr/bin/env python3
"""RTSE FASE 3 — BACKBONE que foi pulado: CLASSE POSITIVA vs NEGATIVA (dip-vs-flip) + EIXO F (counter-pullback).
POSITIVA = pivô M8 que coincide com borda MACRO do Cris (virada de regime real / FLIP).
NEGATIVA = pivô M8 dentro de um box PULLBACK do Cris (counter-pullback que reverte / DIP).
EIXO F (nested counter-pullback, causal no pivô): HTF regime (regime_at 4H), profundidade-da-perna/ATR-4H,
swept+reclaim, flush-vs-grind. Testa se F separa POSITIVA de NEGATIVA. null por sub-feature + por-ano.
n macro pequeno = aceito (validação por convergência+jackknife). Determinístico, causal."""
import json,csv,sys,io,contextlib,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo"; REV=ROOT/"my-strategy/research/revalidation"; GT=ROOT/"regime_turnstate_engine/ground_truth"
sys.path.insert(0,str(REV))
with contextlib.redirect_stdout(io.StringIO()):
    import engine_4h_regime_gate_RAW as eng   # regime_at(ts) 4H-nativo
# 15M series
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)}
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S]
# 4H p/ ATR HTF
B4=[json.loads(l) for l in (REV/"raw_4h_ohlc.jsonl").read_text().splitlines()];B4.sort(key=lambda b:b["t"])
t4=[b["t"] for b in B4]
def atr4h(ts,n=14):
    j=bisect.bisect_right(t4,ts)-1
    if j<n: return None
    tr=[max(B4[k]["h"]-B4[k]["l"],abs(B4[k]["h"]-B4[k-1]["c"]),abs(B4[k]["l"]-B4[k-1]["c"])) for k in range(j-n+1,j+1)]
    return sum(tr)/len(tr)
# CLASSE a partir das 2 réguas
macro=[];pull=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"] in("BULL","BEAR"): macro.append((int(r["start"]),"BOT" if r["family"]=="BULL" else "TOP"))
    if r["role"]=="PULLBACK": pull.append((int(r["start"]),int(r["end"]),r["family"]))
m8=[(int(d["t"]),d["kind"]) for d in csv.DictReader(open(RX/"true_reversals_M8.csv"))]
W=5*86400
def is_macro(t,kind): return any(k==kind and abs(t-mt)<=W for mt,k in macro)
def in_pull(t): return any(a-W<=t<=b+W for a,b,_ in pull)
rows=[]
for t,kind in m8:
    i=idx.get(t)
    if i is None or i<30 or i+5>=len(S): continue
    pos=is_macro(t,kind); neg=in_pull(t) and not pos
    if not (pos or neg): continue          # só classe limpa (flip vs dip)
    a4=atr4h(t) or 1.0; reg=eng.regime_at(t)
    bot=(kind=="BOT")
    # EIXO F (causal)
    f_htf_intact = 1 if ((bot and reg in("BULL","RANGE")) or ((not bot) and reg in("BEAR","RANGE"))) else 0
    leg = (max(H[i-20:i])-Lo[i]) if bot else (H[i]-min(Lo[i-20:i])); f_legdepth = leg/a4   # vs ATR 4H
    swept = (Lo[i]<min(Lo[i-20:i-1])) if bot else (H[i]>max(H[i-20:i-1]))
    reclaim = (C[i]>min(Lo[i-20:i-1])) if bot else (C[i]<max(H[i-20:i-1]))
    f_sweepreclaim = 1 if (swept and reclaim) else 0
    # flush (poucas barras da extrema-local até o pivô) vs grind
    if bot:
        hi_idx=max(range(i-20,i),key=lambda k:H[k]); f_flush = 1 if (i-hi_idx)<=8 else 0
    else:
        lo_idx=min(range(i-20,i),key=lambda k:Lo[k]); f_flush = 1 if (i-lo_idx)<=8 else 0
    rows.append({"t":t,"kind":kind,"yr":dt.datetime.utcfromtimestamp(t).year,"pos":pos,
                 "f_htf_intact":f_htf_intact,"f_legdepth":f_legdepth,"f_sweepreclaim":f_sweepreclaim,"f_flush":f_flush,
                 "Fconf":f_htf_intact+f_sweepreclaim+f_flush+(1 if f_legdepth>=1.0 else 0)})
npos=sum(r["pos"] for r in rows);N=len(rows)
print(f"CLASSE: positiva(FLIP, M8∩MACRO) {npos} | negativa(DIP, M8 em PULLBACK) {N-npos} | total {N}")
print(f"macro edges {len(macro)} | pullback boxes {len(pull)} | (janela 15M={dt.datetime.utcfromtimestamp(T[0]).year}+)")
if npos<3 or N-npos<3: print("n insuficiente p/ separação — reportando composição apenas.");
print("\n-- EIXO F: média POSITIVA(flip) vs NEGATIVA(dip) + null por sub-feature --")
def nul(key):
    pv=[r[key] for r in rows if r["pos"]];ng=[r[key] for r in rows if not r["pos"]]
    if not pv or not ng: return
    real=st.mean(pv)-st.mean(ng);allv=[r[key] for r in rows];labs=[r["pos"] for r in rows];random.seed(4);dd=[]
    for _ in range(500):
        random.shuffle(labs);dd.append(st.mean([allv[i] for i in range(N) if labs[i]])-st.mean([allv[i] for i in range(N) if not labs[i]]))
    p=sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
    print(f"  {key:14}: flip {st.mean(pv):+.3f} vs dip {st.mean(ng):+.3f} | diff {real:+.3f} | null p={p:.3f} {'*' if p<0.05 else ''}")
for k in ["f_htf_intact","f_legdepth","f_sweepreclaim","f_flush","Fconf"]: nul(k)
print("\n-- composição por ano (flip/dip) --")
for y in sorted(set(r["yr"] for r in rows)):
    ry=[r for r in rows if r["yr"]==y];print(f"  {y}: flip {sum(r['pos'] for r in ry)} / dip {sum(not r['pos'] for r in ry)}")
