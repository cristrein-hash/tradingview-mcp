#!/usr/bin/env python3
"""RTSE FASE 3 — EIXOS A-E + G COMPLETOS (o que faltou cumprir), testados na CLASSE flip-vs-dip + null por feature.
A regime-5TF · B velocidade(lead/div/micro-CHoCH/CUSUM/coil) · C aceitação(close-through/failed-break/absorção)
· D momentum(RSI-div/decel/thrust-stall/exhaust-clock) · E volatilidade(ATR-rebase/vov/climax-grind) · G priors(sessão/hazard).
Causal. n positiva pequena (macro raro). Execução do plano — sem conclusão. Determinístico."""
import json,csv,sys,io,contextlib,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo";REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
sys.path.insert(0,str(REV))
with contextlib.redirect_stdout(io.StringIO()): import engine_4h_regime_gate_RAW as eng
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)}
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S];V=[b.get("v") or 0 for b in S];RS=[b.get("rsi") for b in S]
def ema(c,n):
    a=2/(n+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
def emaTF(bars,n):
    c=[b["c"] for b in bars];return ema(c,n),[b["t"] for b in bars]
def load(p): b=[json.loads(l) for l in (p).read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
B30=load(GT/"raw_30m_ohlc.jsonl");B1=load(REV/"raw_1h_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
TF={}
for nm,bb in [("30M",B30),("1H",B1),("4H",B4)]:
    ef,tt=emaTF(bb,9);es,_=emaTF(bb,30);TF[nm]=(tt,[b["c"] for b in bb],ef,es)
e15f=ema(C,9);e15s=ema(C,30)
def tf_state(nm,ts):
    tt,cc,ef,es=TF[nm];j=bisect.bisect_right(tt,ts)-1
    if j<0: return 0
    return 1 if ef[j]>es[j] else -1
def st15(i): return 1 if e15f[i]>e15s[i] else -1
ret=[0.0]+[math.log(C[i]/C[i-1]) for i in range(1,len(C))]
au=set();sp=0.0
for i in range(1,len(C)):
    w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1
    z=(ret[i]-mu)/sg;sp=max(0,sp+(z-0.5))
    if sp>5: au.add(i);sp=0.0
def atr(i,n=14): return sum(max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-n+1,i+1))/n
def feats(i,kind):
    bot=(kind=="BOT");d={}
    # A regime 5-TF
    signs=[st15(i),tf_state("30M",T[i]),tf_state("1H",T[i]),tf_state("4H",T[i])]
    want=1 if bot else -1
    d["a_align"]=sum(1 for s in signs if s==want)/4.0
    # swing agree (HH/HL vs LH/LL aproximado por close vs media de 20)
    d["a_swing"]=1.0 if ((bot and C[i]>=Lo[i]) and st15(i)==want) else (1.0 if st15(i)==want else 0.0)
    # B velocidade
    d["b_lead"]=1.0 if (st15(i)==want and tf_state("4H",T[i])!=want) else 0.0
    d["b_div"]=1.0 if (st15(i)==want and tf_state("30M",T[i])!=want) else 0.0
    if bot:
        # micro-CHoCH: 1ª higher-low recente
        lows=[Lo[k] for k in range(i-12,i+1)];d["b_choch"]=1.0 if (Lo[i]>min(lows[:-3]) and C[i]>C[i-1]) else 0.0
    else:
        his=[H[k] for k in range(i-12,i+1)];d["b_choch"]=1.0 if (H[i]<max(his[:-3]) and C[i]<C[i-1]) else 0.0
    d["b_cusum"]=1.0 if (bot and any((i-w) in au for w in range(0,13))) else (1.0 if ((not bot) and any((i-w) in au for w in range(0,13))) else 0.0)
    atrm=st.mean([atr(x) for x in range(i-20,i)]);d["b_coil"]=1.0 if (any(atr(x)<0.8*atrm for x in range(i-6,i)) and (H[i]-Lo[i])>1.4*atrm and ((C[i]>C[i-1]) if bot else (C[i]<C[i-1]))) else 0.0
    # C aceitação
    lev=min(Lo[i-20:i-1]) if bot else max(H[i-20:i-1])
    body=min(C[i],S[i].get("o",C[i])) if bot else max(C[i],S[i].get("o",C[i]))
    d["c_accept"]=1.0 if ((bot and C[i]>lev) or ((not bot) and C[i]<lev)) else 0.0
    swept=(Lo[i]<lev) if bot else (H[i]>lev);d["c_failbreak"]=1.0 if (swept and ((C[i]>lev) if bot else (C[i]<lev))) else 0.0
    vr=sorted(V[i-20:i]);rank=bisect.bisect_left(vr,V[i])/max(1,len(vr));wick=((min(C[i],S[i].get('o',C[i]))-Lo[i]) if bot else (H[i]-max(C[i],S[i].get('o',C[i]))))/max(1e-9,H[i]-Lo[i])
    d["c_absorb"]=1.0 if (wick>0.4 and rank>0.6) else 0.0
    # D momentum
    r=RS[i] or 50;rp=RS[i-6] or 50
    d["d_rsidiv"]=1.0 if ((bot and Lo[i]<min(Lo[i-12:i-1]) and r>rp) or ((not bot) and H[i]>max(H[i-12:i-1]) and r<rp)) else 0.0
    v1=C[i]-C[i-3];v2=C[i-3]-C[i-6];d["d_decel"]=1.0 if ((bot and v1>v2 and v1<0) or ((not bot) and v1<v2 and v1>0)) else 0.0
    run=0
    for k in range(i,i-8,-1):
        if (C[k]<C[k-1]) if bot else (C[k]>C[k-1]): run+=1
        else: break
    d["d_thrust"]=1.0 if (run>=4 and (H[i]-Lo[i])<0.6*atr(i)) else 0.0
    ext=i
    for k in range(i,i-30,-1):
        if (Lo[k]<Lo[ext]) if bot else (H[k]>H[ext]): ext=k
    d["d_clock"]=(i-ext)/30.0
    # E volatilidade
    a14=atr(i);aprev=st.mean([atr(x) for x in range(i-40,i-20)]);d["e_rebase"]=a14/aprev if aprev else 1.0
    vv=st.pstdev([atr(x) for x in range(i-20,i)])/max(1e-9,a14);d["e_vov"]=vv
    spk=max(H[k]-Lo[k] for k in range(i-2,i+1))/max(1e-9,atrm);d["e_climax"]=1.0 if spk>=2.0 else 0.0
    # G priors
    hr=dt.datetime.utcfromtimestamp(T[i]).hour;d["g_session"]=1.0 if (7<=hr<=16) else 0.0  # London+NY
    return d
# classe
macro=[];pull=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"] in("BULL","BEAR"): macro.append((int(r["start"]),"BOT" if r["family"]=="BULL" else "TOP"))
    if r["role"]=="PULLBACK": pull.append((int(r["start"]),int(r["end"])))
m8=[(int(d["t"]),d["kind"]) for d in csv.DictReader(open(RX/"true_reversals_M8.csv"))]
W=5*86400
rows=[]
for t,kind in m8:
    i=idx.get(t)
    if i is None or i<45 or i+5>=len(S): continue
    pos=any(k==kind and abs(t-mt)<=W for mt,k in macro);neg=any(a-W<=t<=b+W for a,b in pull) and not pos
    if not(pos or neg): continue
    d=feats(i,kind);d["pos"]=pos;rows.append(d)
N=len(rows);npos=sum(r["pos"] for r in rows)
print(f"CLASSE flip {npos} / dip {N-npos} (n{N}) — eixos A-E+G completos, null por feature")
keys=[k for k in rows[0] if k!="pos"]
def nul(key):
    pv=[r[key] for r in rows if r["pos"]];ng=[r[key] for r in rows if not r["pos"]]
    real=st.mean(pv)-st.mean(ng);allv=[r[key] for r in rows];labs=[r["pos"] for r in rows];random.seed(4);dd=[]
    for _ in range(500):
        random.shuffle(labs);dd.append(st.mean([allv[i] for i in range(N) if labs[i]])-st.mean([allv[i] for i in range(N) if not labs[i]]))
    return real,sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
print(f"{'feature':14} {'flip':>7} {'dip':>7} {'diff':>7} {'null_p':>7}")
sig=[]
for k in keys:
    r,p=nul(k);fl=st.mean([x[k] for x in rows if x['pos']]);dp=st.mean([x[k] for x in rows if not x['pos']])
    print(f"{k:14} {fl:>7.3f} {dp:>7.3f} {r:>+7.3f} {p:>7.3f}{' *' if p<0.05 else ''}")
    if p<0.05: sig.append(k)
print(f"\nfeatures com null p<0.05: {sig if sig else 'nenhuma'}")
