#!/usr/bin/env python3
"""RTSE FASE 3a — ALVO REAL: confluência vs OUTCOME das estratégias (win vs SL/BE), não proxy MFE.
Trades = swept-runner aprovada (substrate4_flow.jsonl, N448, cj_t+R+flow dict). Todos LONG (BOT).
CAMADA 1 = features RICAS no bar de entrada (causal). CAMADA 2 = indicadores POSTERIOR do flow dict
(NAS/OB/demand/BUBBLES/CHoCH/clean-sky) condicionais ao subconjunto rich-favorável (não isolados).
Label: loser=R<=0 (SL/BE), win=R>0. null + por-ano. Determinístico, causal."""
import json,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo"; GT=ROOT/"regime_turnstate_engine/ground_truth"
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)}
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S]
B30=[json.loads(l) for l in (GT/"raw_30m_ohlc.jsonl").read_text().splitlines()];B30.sort(key=lambda b:b["t"])
t30=[b["t"] for b in B30];c30=[b["c"] for b in B30]
def ema(c,n):
    a=2/(n+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
e15f=ema(C,9);e30s=ema(c30,30)
ret=[0.0]+[math.log(C[i]/C[i-1]) for i in range(1,len(C))]
alarm_up=set();sp=0.0
for i in range(1,len(C)):
    w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1
    z=(ret[i]-mu)/sg;sp=max(0,sp+(z-0.5))
    if sp>5: alarm_up.add(i);sp=0.0
def atr_at(i,n=14): return sum(max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-n+1,i+1))/n
def rich_votes(i):
    j=bisect.bisect_right(t30,T[i])-1; d30_up=(c30[j]>e30s[j]) if j>=0 else True
    v_div=1 if (C[i]>e15f[i] and not d30_up) else 0
    v_cusum=1 if any((i-w) in alarm_up for w in range(0,13)) else 0
    swept=Lo[i]<min(Lo[i-20:i-1]);lev=min(Lo[i-20:i-1]); v_gram=1 if (swept and C[i]>lev and C[i-1]>=Lo[i]) else 0
    v1=C[i]-C[i-3];v2=C[i-3]-C[i-6]; v_decel=1 if (v1>v2 and v1<0) else 0
    atrm=st.mean([atr_at(x) for x in range(i-20,i)]); v_coil=1 if (any(atr_at(x)<0.8*atrm for x in range(i-6,i)) and (H[i]-Lo[i])>1.4*atrm and C[i]>C[i-1]) else 0
    return v_div+v_cusum+v_gram+v_decel+v_coil
rows=[]
clean=[json.loads(l) for l in (RX/"substrate4_flow.jsonl").read_text().splitlines()]
cleansky=sorted(r["flow"].get("clean_sky_atr",0) for r in clean); csmed=cleansky[len(cleansky)//2]
for r in clean:
    i=idx.get(r["cj_t"])
    if i is None or i<40: continue
    fl=r["flow"]
    rich=rich_votes(i)
    # CAMADA 2 indicadores (flow, causal): NAS, demand, bubbles, CHoCH, HTF, clean-sky
    ind = (1 if fl.get("nas_any_rec") else 0)+(1 if fl.get("in_demand") else 0)+(1 if fl.get("buy_bub_w",0)>fl.get("sell_bub_w",0) else 0)+(1 if fl.get("choch_any_rec") else 0)+(1 if fl.get("htf_demand_any") else 0)+(1 if fl.get("clean_sky_atr",0)>=csmed else 0)
    rows.append({"yr":r["yr"],"R":r["R"],"win":r["R"]>0,"rich":rich,"ind":ind})
N=len(rows);wr=sum(r["win"] for r in rows)/N
print(f"FASE 3a OUTCOME REAL (swept-runner) — N{N} | WR base {100*wr:.0f}%")
def block(key,label,maxc):
    print(f"-- {label}: WR por nível (dose) + null + por-ano --")
    for c in range(0,maxc+1):
        g=[r for r in rows if r[key]==c]
        if g: print(f"  {key}={c}: WR {100*sum(x['win'] for x in g)/len(g):.0f}% (n{len(g)})")
    hi=[r for r in rows if r[key]>=max(2,maxc-1)];lo=[r for r in rows if r[key]<=1]
    rl=(sum(x["win"] for x in hi)/len(hi) if hi else 0)-(sum(x["win"] for x in lo)/len(lo) if lo else 0)
    random.seed(9);labs=[r["win"] for r in rows];ks=[r[key] for r in rows];dd=[]
    for _ in range(500):
        random.shuffle(labs);a=[labs[i] for i in range(N) if ks[i]>=max(2,maxc-1)];b=[labs[i] for i in range(N) if ks[i]<=1]
        dd.append((sum(a)/len(a) if a else 0)-(sum(b)/len(b) if b else 0))
    p=sum(1 for x in dd if abs(x)>=abs(rl))/len(dd)
    print(f"  hi vs lo: WR lift {100*rl:+.0f}pp (n{len(hi)}/{len(lo)}) | null p={p:.3f}")
    for y in sorted(set(r["yr"] for r in rows)):
        h=[r for r in hi if r["yr"]==y];l=[r for r in lo if r["yr"]==y]
        if h and l: print(f"    {y}: {100*(sum(x['win'] for x in h)/len(h)-sum(x['win'] for x in l)/len(l)):+.0f}pp (h{len(h)}/l{len(l)})")
block("rich","CAMADA1 RICAS",5)
# CAMADA 2: indicadores condicionais ao rich-favorável
print("\n-- CAMADA2 INDICADORES condicionais (ajudam DEPOIS das ricas?) --")
rf=[r for r in rows if r["rich"]>=2]
print(f"  rich-fav(rich>=2): n{len(rf)} WR {100*sum(x['win'] for x in rf)/len(rf) if rf else 0:.0f}%")
for thr in (3,4):
    a=[r for r in rf if r["ind"]>=thr];b=[r for r in rf if r["ind"]<thr]
    print(f"    rich-fav & ind>={thr}: WR {100*sum(x['win'] for x in a)/len(a) if a else 0:.0f}% (n{len(a)}) | & ind<{thr}: {100*sum(x['win'] for x in b)/len(b) if b else 0:.0f}% (n{len(b)})")
# indicadores SOZINHOS tb (referência)
block("ind","REF INDICADORES sozinhos",6)
print("\nVEREDITO: filtro útil = subconjunto com WR>>base, null p<0.05, positivo em >=2 anos. Sem isso = não filtra SL/BE.")
