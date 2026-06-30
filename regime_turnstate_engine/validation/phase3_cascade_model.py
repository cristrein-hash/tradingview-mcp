#!/usr/bin/env python3
"""RTSE Fase 3 — últimos itens do plano: CASCADE turn_state (EARLY/MATURING/CONFIRMED) + MODELO regularizado
(logística manual L2, leave-one-year-out, AUC vs b_cusum-sozinho = check de interação). Classe flip-vs-dip.
Causal. Execução do plano — sem conclusão. Determinístico."""
import json,csv,math,statistics as st,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo";REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth";EF=ROOT/"external_factors_v2/snapshots"
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)};C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S];RS=[b.get("rsi") for b in S]
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
B30=load(GT/"raw_30m_ohlc.jsonl");B1=load(REV/"raw_1h_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
def ema(c,n):
    a=2/(n+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
e15f=ema(C,9);e15s=ema(C,30)
def stTF(bars,ts):
    c=[b["c"] for b in bars];ef=ema(c,9);es=ema(c,30);j=bisect.bisect_right([b["t"] for b in bars],ts)-1
    return (1 if ef[j]>es[j] else -1) if j>=0 else 0
ret=[0.0]+[math.log(C[i]/C[i-1]) for i in range(1,len(C))];au=set();sp=0.0
for i in range(1,len(C)):
    w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1;z=(ret[i]-mu)/sg;sp=max(0,sp+(z-0.5))
    if sp>5: au.add(i);sp=0.0
PAN={}
for l in (EF/"macro_panel.jsonl").read_text().splitlines():
    r=json.loads(l);PAN.setdefault(r["series_id"],{})[r["obs_date"]]=r["value"]
usd_items=sorted((int(k),v) for k,v in PAN["usd_broad"].items());ue=[x[0] for x in usd_items];uv=[x[1] for x in usd_items]
ry_items=sorted((int(k),v) for k,v in PAN["us10y_real"].items());re_=[x[0] for x in ry_items];rv=[x[1] for x in ry_items]
def asof(e,v,ts,days=0):
    j=bisect.bisect_right(e,ts-86400)-1;return v[j] if j>=0 else None
def mom(e,v,ts,days):
    j=bisect.bisect_right(e,ts-86400)-1
    return (v[j]-v[j-days]) if j-days>=0 else None
def atr(i,n=14): return sum(max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-n+1,i+1))/n
def feats(i,kind):
    bot=(kind=="BOT");want=1 if bot else -1;ts=T[i];d={}
    sgn=[(1 if e15f[i]>e15s[i] else -1),stTF(B30,ts),stTF(B1,ts),stTF(B4,ts)]
    d["a_align"]=sum(1 for s in sgn if s==want)/4.0
    d["b_cusum"]=1.0 if any((i-w) in au for w in range(0,13)) else 0.0
    mu5=mom(ue,uv,ts,5);ry5=mom(re_,rv,ts,5)
    d["b_cross"]=1.0 if (((mu5 is not None and ((mu5<0)==bot)) or (ry5 is not None and ((ry5<0)==bot)))) else 0.0
    lev=min(Lo[i-20:i-1]) if bot else max(H[i-20:i-1])
    d["c_accept"]=1.0 if ((bot and C[i]>lev) or ((not bot) and C[i]<lev)) else 0.0
    d["c_swept"]=1.0 if ((bot and Lo[i]<lev) or ((not bot) and H[i]>lev)) else 0.0
    r=RS[i] or 50;rp=RS[i-6] or 50
    d["d_rsidiv"]=1.0 if ((bot and Lo[i]<min(Lo[i-12:i-1]) and r>rp) or ((not bot) and H[i]>max(H[i-12:i-1]) and r<rp)) else 0.0
    atrm=st.mean([atr(x) for x in range(i-20,i)]);d["e_climax"]=1.0 if max(H[k]-Lo[k] for k in range(i-2,i+1))>=2.0*atrm else 0.0
    hr=dt.datetime.utcfromtimestamp(ts).hour;d["g_session"]=1.0 if (7<=hr<=16) else 0.0
    d["cascade"]=sum(1 for s in sgn if s==want)  # 0-4 (TF-cascade depth)
    return d
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
    d=feats(i,kind);d["pos"]=1 if pos else 0;d["yr"]=dt.datetime.utcfromtimestamp(t).year;rows.append(d)
N=len(rows)
print(f"CLASSE flip {sum(r['pos'] for r in rows)}/dip {N-sum(r['pos'] for r in rows)} (n{N})")
# CASCADE turn_state
print("-- CASCADE turn_state (TF-depth) vs flip-rate --")
for c in range(0,5):
    g=[r for r in rows if r["cascade"]==c]
    if g: print(f"  depth={c} ({'EARLY' if c<=1 else 'MATURING' if c==2 else 'CONFIRMED'}): flip {100*sum(r['pos'] for r in g)/len(g):.0f}% (n{len(g)})")
# AUC
def auc(scores,labs):
    pos=[scores[i] for i in range(len(labs)) if labs[i]];neg=[scores[i] for i in range(len(labs)) if not labs[i]]
    if not pos or not neg: return None
    c=sum((1 if p>n else 0.5 if p==n else 0) for p in pos for n in neg);return c/(len(pos)*len(neg))
FK=["a_align","b_cusum","b_cross","c_accept","c_swept","d_rsidiv","e_climax","g_session"]
def logit_cv():
    yrs=sorted(set(r["yr"] for r in rows));oof=[0.0]*N;lab=[r["pos"] for r in rows]
    for ty in yrs:
        tr=[k for k in range(N) if rows[k]["yr"]!=ty];te=[k for k in range(N) if rows[k]["yr"]==ty]
        mean={f:st.mean([rows[k][f] for k in tr]) for f in FK};sd={f:(st.pstdev([rows[k][f] for k in tr]) or 1) for f in FK}
        w={f:0.0 for f in FK};b=0.0;lr=0.1;lam=1.0
        for _ in range(300):
            for k in tr:
                z=b+sum(w[f]*(rows[k][f]-mean[f])/sd[f] for f in FK);pr=1/(1+math.exp(-max(-30,min(30,z))));g=pr-lab[k]
                for f in FK: w[f]-=lr*(g*(rows[k][f]-mean[f])/sd[f]+lam*w[f]/len(tr))
                b-=lr*g
        for k in te:
            z=b+sum(w[f]*(rows[k][f]-mean[f])/sd[f] for f in FK);oof[k]=1/(1+math.exp(-max(-30,min(30,z))))
    return auc(oof,lab)
print("\n-- MODELO regularizado (logística L2, leave-one-year-out) --")
print(f"  AUC modelo (todas features, interação): {logit_cv():.3f}")
print(f"  AUC b_cusum sozinho: {auc([r['b_cusum'] for r in rows],[r['pos'] for r in rows]):.3f}")
print(f"  AUC a_align sozinho: {auc([r['a_align'] for r in rows],[r['pos'] for r in rows]):.3f}")
print("  (0.5=acaso; modelo>>single => interação carrega sinal)")
