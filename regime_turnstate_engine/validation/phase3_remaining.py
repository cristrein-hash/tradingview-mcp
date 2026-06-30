#!/usr/bin/env python3
"""RTSE FASE 3 — cumpre o que faltava: b_cross (cross-asset), eixo H (entropia/corr-break/fractal),
b_lead/b_div corrigidos (janela causal), e CONFLUÊNCIA-CONTAGEM agregada na classe flip-vs-dip.
Causal. n positiva pequena (macro). Execução do plano — sem conclusão. Determinístico."""
import json,csv,sys,io,contextlib,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo";REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth";EF=ROOT/"external_factors_v2/snapshots"
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)};C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S]
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
B30=load(GT/"raw_30m_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
def ema(c,n):
    a=2/(n+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
e15f=ema(C,9);e15s=ema(C,30)
def stTF(bars,ts):
    c=[b["c"] for b in bars];ef=ema(c,9);es=ema(c,30);j=bisect.bisect_right([b["t"] for b in bars],ts)-1
    return (1 if ef[j]>es[j] else -1) if j>=0 else 0
# macro diário (D-1) p/ b_cross + corr-break
PAN={}
for l in (EF/"macro_panel.jsonl").read_text().splitlines():
    r=json.loads(l);PAN.setdefault(r["series_id"],{})[r["obs_date"]]=r["value"]
def daily(series):
    d=PAN[series];return sorted(d.items())
USD=daily("usd_broad");RY=daily("us10y_real")
usd_t=[x[0] for x in USD];ry_t=[x[0] for x in RY]
def val_asof(arr_t,arr,ts):
    j=bisect.bisect_right(arr_t,ts-86400)-1  # D-1
    return arr[j][1] if j>=0 else None
def mom(arr_t,arr,ts,days):
    j=bisect.bisect_right(arr_t,ts-86400)-1
    if j-days<0: return None
    return arr[j][1]-arr[j-days][1]
# gold diário p/ corr
gold_d={}
for b in B4: gold_d[dt.datetime.utcfromtimestamp(b["t"]).strftime("%Y-%m-%d")]=b["c"]
gd=sorted(gold_d.items());gd_t=[x[0] for x in gd];gd_v=[x[1] for x in gd]
# CUSUM 15M (reusa)
ret=[0.0]+[math.log(C[i]/C[i-1]) for i in range(1,len(C))];au=set();sp=0.0
for i in range(1,len(C)):
    w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1;z=(ret[i]-mu)/sg;sp=max(0,sp+(z-0.5))
    if sp>5: au.add(i);sp=0.0
def feats(i,kind):
    bot=(kind=="BOT");want=1 if bot else -1;ts=T[i];d={}
    # b_lead/b_div CORRIGIDOS: 15M virou na janela [-8,0] enquanto TF maior ainda oposto
    s15w=any((1 if e15f[i-w]>e15s[i-w] else -1)==want for w in range(0,8))
    d["b_lead"]=1.0 if (s15w and stTF(B4,ts)!=want) else 0.0
    d["b_div"]=1.0 if (s15w and stTF(B30,ts)!=want) else 0.0
    d["b_cusum"]=1.0 if any((i-w) in au for w in range(0,13)) else 0.0
    # b_cross: USD/real-yield 5d a favor (BOT: ambos caindo)
    mu5=mom(usd_t,USD,ts,5);ry5=mom(ry_t,RY,ts,5)
    fav=lambda x:(x is not None and ((x<0) if bot else (x>0)))
    d["b_cross"]=1.0 if (fav(mu5) or fav(ry5)) else 0.0
    # H entropia: surpresa do símbolo (sinal-corpo x range-bucket) vs markov trailing
    def sym(k):
        rg=H[k]-Lo[k];o=S[k].get("o",C[k]);bs=1 if C[k]>=o else 0;rb=0 if rg< (st.mean([H[x]-Lo[x] for x in range(k-10,k)]) or rg) else 1
        return bs*2+rb
    seq=[sym(k) for k in range(i-30,i+1)]
    from collections import Counter
    cnt=Counter(seq[:-1]);p=(cnt[seq[-1]]+1)/(len(seq)-1+4);d["h_surprise"]=1.0 if -math.log(p)>1.6 else 0.0
    # H corr-break: corr(gold,USD) 20d perto de 0 (decoupled)
    jg=bisect.bisect_right(gd_t,dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"))-1
    cb=0.0
    if jg>=21:
        gr=[gd_v[x]-gd_v[x-1] for x in range(jg-19,jg+1)]
        uu=[val_asof(usd_t,USD,ts)]  # simplificado: usa série usd alinhada por data
        ur=[]
        for x in range(jg-19,jg+1):
            a=PAN["usd_broad"].get(gd_t[x]);b=PAN["usd_broad"].get(gd_t[x-1]);ur.append((a-b) if (a and b) else 0)
        if st.pstdev(gr) and st.pstdev(ur):
            cr=sum((gr[m]-st.mean(gr))*(ur[m]-st.mean(ur)) for m in range(len(gr)))/(len(gr)*st.pstdev(gr)*st.pstdev(ur))
            cb=1.0 if abs(cr)<0.3 else 0.0
    d["h_corrbreak"]=cb
    # H fractal: >=3 TFs concordam na direção want (15M/30M/1H/4H)
    agree=sum(1 for s in [(1 if e15f[i]>e15s[i] else -1),stTF(B30,ts),stTF(load.__self__ if False else B4,ts)] if s==want)  # 15M,30M,4H
    d["h_fractal"]=1.0 if agree>=2 else 0.0
    return d
# classe
macro=[];pull=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"] in("BULL","BEAR"): macro.append((int(r["start"]),"BOT" if r["family"]=="BULL" else "TOP"))
    if r["role"]=="PULLBACK": pull.append((int(r["start"]),int(r["end"])))
m8=[(int(d["t"]),d["kind"]) for d in csv.DictReader(open(RX/"true_reversals_M8.csv"))];W=5*86400
rows=[]
for t,kind in m8:
    i=idx.get(t)
    if i is None or i<45 or i+5>=len(S): continue
    pos=any(k==kind and abs(t-mt)<=W for mt,k in macro);neg=any(a-W<=t<=b+W for a,b in pull) and not pos
    if not(pos or neg): continue
    d=feats(i,kind);d["pos"]=pos;d["conf"]=sum(v for k,v in d.items() if k.startswith(("b_","h_")));rows.append(d)
N=len(rows);npos=sum(r["pos"] for r in rows)
print(f"CLASSE flip {npos}/dip {N-npos} (n{N}) — b_cross + H + b_lead/div corrigidos + confluência")
def nul(key):
    pv=[r[key] for r in rows if r["pos"]];ng=[r[key] for r in rows if not r["pos"]]
    real=st.mean(pv)-st.mean(ng);allv=[r[key] for r in rows];labs=[r["pos"] for r in rows];random.seed(4);dd=[]
    for _ in range(500):
        random.shuffle(labs);dd.append(st.mean([allv[i] for i in range(N) if labs[i]])-st.mean([allv[i] for i in range(N) if not labs[i]]))
    return real,sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
print(f"{'feature':14}{'flip':>7}{'dip':>7}{'diff':>8}{'null_p':>8}")
for k in ["b_lead","b_div","b_cusum","b_cross","h_surprise","h_corrbreak","h_fractal"]:
    r,p=nul(k);print(f"{k:14}{st.mean([x[k] for x in rows if x['pos']]):>7.2f}{st.mean([x[k] for x in rows if not x['pos']]):>7.2f}{r:>+8.3f}{p:>8.3f}{' *' if p<0.05 else ''}")
print("\n-- CONFLUÊNCIA (contagem b_+h_) por nível: WR-flip (dose) --")
for c in range(0,int(max(r['conf'] for r in rows))+1):
    g=[x for x in rows if int(x['conf'])==c]
    if g: print(f"  conf={c}: flip {100*sum(x['pos'] for x in g)/len(g):.0f}% (n{len(g)})")
hi=[x for x in rows if x['conf']>=3];lo=[x for x in rows if x['conf']<=1]
rl=(sum(x['pos'] for x in hi)/len(hi) if hi else 0)-(sum(x['pos'] for x in lo)/len(lo) if lo else 0)
random.seed(8);labs=[x['pos'] for x in rows];ks=[x['conf'] for x in rows];dd=[]
for _ in range(500):
    random.shuffle(labs);a=[labs[i] for i in range(N) if ks[i]>=3];b=[labs[i] for i in range(N) if ks[i]<=1];dd.append((sum(a)/len(a) if a else 0)-(sum(b)/len(b) if b else 0))
print(f"  conf>=3({len(hi)}) vs<=1({len(lo)}): flip-rate lift {100*rl:+.0f}pp | null p={sum(1 for x in dd if abs(x)>=abs(rl))/len(dd):.3f}")
