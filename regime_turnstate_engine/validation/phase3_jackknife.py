#!/usr/bin/env python3
"""RTSE Fase 3 — cumpre: JACKKNIFE por-ano (faltava) no separador b_cusum + h_fractal/h_corrbreak CORRIGIDOS
(estavam degenerados) com teste justo. Classe flip-vs-dip. Causal. Execução do plano — sem conclusão."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo";REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth";EF=ROOT/"external_factors_v2/snapshots"
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)};C=[b["c"] for b in S]
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
# macro/gold diário p/ corr-break corrigido
PAN={}
for l in (EF/"macro_panel.jsonl").read_text().splitlines():
    r=json.loads(l);PAN.setdefault(r["series_id"],{})[r["obs_date"]]=r["value"]
# macro_panel obs_date = EPOCH INT. Tudo em epoch.
usd_items=sorted((int(k),v) for k,v in PAN["usd_broad"].items())
usd_e=[x[0] for x in usd_items];usd_v=[x[1] for x in usd_items]
def usd_asof(ts):  # último USD <= ts (epoch, as-of)
    j=bisect.bisect_right(usd_e,ts)-1
    return usd_v[j] if j>=0 else None
# gold diário (1 close por dia, epoch do dia)
gd={}
for b in B4:
    day=int(b["t"]//86400*86400);gd[day]=b["c"]
gold_items=sorted(gd.items());gdt=[x[0] for x in gold_items];gdv=[x[1] for x in gold_items]
def feats(i,kind):
    bot=(kind=="BOT");want=1 if bot else -1;ts=T[i];ds=dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
    v_cusum=1.0 if any((i-w) in au for w in range(0,13)) else 0.0
    # h_fractal CORRIGIDO: 4 TFs (15M/30M/1H/4H) concordam na direção want
    s=[(1 if e15f[i]>e15s[i] else -1),stTF(B30,ts),stTF(B1,ts),stTF(B4,ts)]
    v_fractal=1.0 if sum(1 for x in s if x==want)>=3 else 0.0
    # h_corrbreak CORRIGIDO: corr 20d gold vs usd; decoupled = corr > -0.2 (perde a anti-correlação típica)
    j=bisect.bisect_right(gdt,ts)-1;v_corr=0.0;cr=None
    if j>=21:
        gr=[gdv[x]-gdv[x-1] for x in range(j-19,j+1)]
        ur=[]
        for x in range(j-19,j+1):
            a=usd_asof(gdt[x]);b=usd_asof(gdt[x-1]);ur.append((a-b) if (a is not None and b is not None) else 0)
        if st.pstdev(gr) and st.pstdev(ur):
            cr=sum((gr[m]-st.mean(gr))*(ur[m]-st.mean(ur)) for m in range(20))/(20*st.pstdev(gr)*st.pstdev(ur))
            v_corr=1.0 if cr>-0.2 else 0.0
    return {"b_cusum":v_cusum,"h_fractal":v_fractal,"h_corrbreak":v_corr,"cr":cr}
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
    d=feats(i,kind);d["pos"]=pos;d["yr"]=dt.datetime.utcfromtimestamp(t).year;rows.append(d)
N=len(rows);npos=sum(r["pos"] for r in rows)
print(f"CLASSE flip {npos}/dip {N-npos} (n{N})")
crv=[r["cr"] for r in rows if r["cr"] is not None]
print(f"h_corrbreak: fire-rate {100*sum(r['h_corrbreak'] for r in rows)/N:.0f}% | corr 20d médio {st.mean(crv):+.2f} (gold vs USD) | h_fractal fire {100*sum(r['h_fractal'] for r in rows)/N:.0f}%")
def nul(rs,key):
    pv=[r[key] for r in rs if r["pos"]];ng=[r[key] for r in rs if not r["pos"]]
    if not pv or not ng: return None,None
    real=st.mean(pv)-st.mean(ng);allv=[r[key] for r in rs];labs=[r["pos"] for r in rs];random.seed(4);dd=[];n=len(rs)
    for _ in range(500):
        random.shuffle(labs);dd.append(st.mean([allv[i] for i in range(n) if labs[i]])-st.mean([allv[i] for i in range(n) if not labs[i]]))
    return real,sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
print(f"\n{'feature':12}{'diff':>8}{'null_p':>8}  | por-ano diff (flip n/dip n) | jackknife (dropa ano)")
for k in ["b_cusum","h_fractal","h_corrbreak"]:
    r,p=nul(rows,k)
    py=[]
    for y in sorted(set(x["yr"] for x in rows)):
        ry=[x for x in rows if x["yr"]==y];pv=[x[k] for x in ry if x["pos"]];ng=[x[k] for x in ry if not x["pos"]]
        py.append(f"{y}:{(st.mean(pv)-st.mean(ng)):+.2f}({len(pv)}/{len(ng)})" if pv and ng else f"{y}:-")
    jk=[]
    for y in sorted(set(x["yr"] for x in rows)):
        rj=[x for x in rows if x["yr"]!=y];rr,pp=nul(rj,k);jk.append(f"{rr:+.2f}" if rr is not None else "-")
    print(f"{k:12}{r:>+8.3f}{p:>8.3f}  | {' '.join(py)} | jk[{','.join(jk)}]")
