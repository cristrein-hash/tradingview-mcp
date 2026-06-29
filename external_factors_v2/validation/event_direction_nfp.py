#!/usr/bin/env python3
"""DIREÇÃO da reação NFP — surpresa (proxy keyless: actual FRED PAYEMS MoM vs expectativa=média 6m anteriores) vs
DIREÇÃO do ouro pós-release. Hipótese: surpresa POSITIVA (jobs fortes) -> USD↑ -> ouro DESCE (correlação NEGATIVA).
Backtest com nosso RAW de ouro. ⚠️ PROXY (não é consenso real; consenso real = fonte de calendário, live). Honesto."""
import json,subprocess,bisect,datetime as dt,statistics as st
from pathlib import Path
RV=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
B1=[json.loads(l) for l in (RV/"raw_1h_ohlc.jsonl").read_text().splitlines()]
B4=[json.loads(l) for l in (RV/"raw_4h_ohlc.jsonl").read_text().splitlines()]
# PAYEMS keyless (actual NFP level mensal)
r=subprocess.run(["curl","-sS","--http1.1","--max-time","60","https://fred.stlouisfed.org/graph/fredgraph.csv?id=PAYEMS&cosd=2018-01-01"],capture_output=True,text=True)
pay=[]
for ln in r.stdout.splitlines()[1:]:
    p=ln.split(",")
    if len(p)<2 or p[1] in("",".","NA"): continue
    pay.append((dt.datetime.strptime(p[0],"%Y-%m-%d").date(),float(p[1])))
pay.sort()
chg={pay[i][0]:pay[i][1]-pay[i-1][1] for i in range(1,len(pay))}  # MoM change (= NFP headline, milhares)
dates=[d for d,_ in pay]
def surprise(month_date):  # month_date = mês reportado (M-1 do release)
    if month_date not in chg: return None
    idx=dates.index(month_date)
    prev=[chg[dates[j]] for j in range(max(1,idx-6),idx) if dates[j] in chg]
    if len(prev)<3: return None
    return chg[month_date]-st.mean(prev)
def first_friday(y,m):
    d=dt.date(y,m,1)
    while d.weekday()!=4: d+=dt.timedelta(days=1)
    return d
def releases(y0=2020,y1=2026):
    out=[]
    for y in range(y0,y1+1):
        for m in range(1,13):
            d=first_friday(y,m); hh=12 if 4<=m<=10 else 13
            ts=int(dt.datetime(y,m,d.day,hh,30,tzinfo=dt.timezone.utc).timestamp())
            rep=(dt.date(y,m,1)-dt.timedelta(days=1)).replace(day=1)  # mês reportado = M-1
            out.append((ts,rep))
    return out
def study(bars,win,lab):
    T=[b["t"] for b in bars]; O=[b["o"] for b in bars]; C=[b["c"] for b in bars]
    pairs=[]
    for ts,rep in releases():
        if ts<T[0] or ts>T[-1]-win*86400: continue
        s=surprise(rep)
        if s is None: continue
        i0=bisect.bisect_right(T,ts)-1
        if i0<0 or i0+win>len(C): continue
        ret=(C[i0+win-1]-O[i0])/O[i0]*100  # retorno do ouro pós-release (%)
        pairs.append((s,ret))
    if len(pairs)<10: print(f"[{lab}] n insuficiente ({len(pairs)})"); return
    xs=[p[0] for p in pairs]; ys=[p[1] for p in pairs]
    mx=st.mean(xs); my=st.mean(ys); sx=st.pstdev(xs) or 1; sy=st.pstdev(ys) or 1
    corr=sum((x-mx)*(y-my) for x,y in pairs)/(len(pairs)*sx*sy)
    strong=[y for x,y in pairs if x>0]; weak=[y for x,y in pairs if x<=0]
    # hit: surpresa>0 -> ouro desce (ret<0); surpresa<=0 -> ouro sobe
    hit=sum(1 for x,y in pairs if (x>0 and y<0) or (x<=0 and y>=0))
    print(f"[{lab}] N={len(pairs)} | corr(surpresa,retorno_ouro)={corr:+.2f} (esperado NEGATIVO)")
    print(f"  surpresa+ (jobs fortes) -> ouro avg {st.mean(strong):+.2f}% (n{len(strong)}) | surpresa- -> ouro avg {st.mean(weak):+.2f}% (n{len(weak)})")
    print(f"  acerto direcional (surpresa-prevê-direção): {hit}/{len(pairs)} = {100*hit/len(pairs):.0f}%")
print("DIREÇÃO NFP (surpresa-proxy PAYEMS vs direção do ouro pós-release)\n")
study(B1,3,"1H 2024+ (3h)")
study(B4,2,"4H 2020+ (8h)")
print("\n⚠️ surpresa=PROXY (actual vs média-6m, não consenso real). Consenso real = fonte calendário (live). corr<0 + acerto>55% = direção tem sinal.")
