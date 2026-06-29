#!/usr/bin/env python3
"""EVENT-STUDY (Camada A): o OURO reage ao NFP? Alinha timestamps de release do NFP (1ª sexta, 8:30 ET) ao RAW de
ouro (1H 2024+ e 4H 2020+) e mede a REAÇÃO (range/|retorno| na janela pós-release) vs BASELINE (janelas não-evento).
Testa a tese do Cris (payroll move o ouro realtime). Backtestável, determinístico, causal."""
import json,statistics as st,datetime as dt,random
from pathlib import Path
H=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
B1=[json.loads(l) for l in (H/"raw_1h_ohlc.jsonl").read_text().splitlines()]
B4=[json.loads(l) for l in (H/"raw_4h_ohlc.jsonl").read_text().splitlines()]
def nfp_times(y0=2020,y1=2026):
    out=[]
    for y in range(y0,y1+1):
        for m in range(1,13):
            d=dt.date(y,m,1)
            while d.weekday()!=4: d+=dt.timedelta(days=1)  # 1ª sexta
            hh=12 if 4<=m<=10 else 13  # 8:30 ET -> 12:30 UTC (EDT) / 13:30 (EST) aprox
            out.append(int(dt.datetime(y,m,d.day,hh,30,tzinfo=dt.timezone.utc).timestamp()))
    return out
NFP=nfp_times()
def study(bars,barsec,win,label):
    T=[b["t"] for b in bars]; O=[b["o"] for b in bars]; Hh=[b["h"] for b in bars]; Lo=[b["l"] for b in bars]; C=[b["c"] for b in bars]
    import bisect
    def react(i0):  # range absoluto e |retorno| na janela [i0, i0+win)
        if i0<0 or i0+win>len(bars): return None
        hi=max(Hh[i0:i0+win]); lo=min(Lo[i0:i0+win]); rng=(hi-lo)/C[i0]*100
        ret=abs(C[i0+win-1]-O[i0])/O[i0]*100
        return rng,ret
    ev=[]; evset=set(); nval=0
    for ts in NFP:
        if ts<T[0] or ts>T[-1]-win*barsec: continue   # só NFP dentro da cobertura do dataset
        nval+=1
        i0=bisect.bisect_right(T,ts)-1                  # barra que CONTÉM o release
        if i0<0: continue
        r=react(i0)
        if r: ev.append(r)
        for k in range(max(0,i0-win),i0+win): evset.add(k)
    # baseline: janelas aleatórias não-evento
    rng_ev=[r[0] for r in ev]; ret_ev=[r[1] for r in ev]
    rnd=random.Random(3); base=[]
    cand=[i for i in range(win,len(bars)-win) if i not in evset]
    for i in rnd.sample(cand,min(2000,len(cand))):
        r=react(i)
        if r: base.append(r)
    rng_b=[r[0] for r in base]; ret_b=[r[1] for r in base]
    me=st.median(rng_ev); mb=st.median(rng_b)
    big=sum(1 for x in rng_ev if x>=2*mb)  # reações "grandes" = >=2x baseline mediana
    # p empírico: fração de amostras baseline com range médio >= médio dos eventos
    avg_ev=st.mean(rng_ev); cnt=0
    for _ in range(2000):
        s=rnd.sample(rng_b,len(rng_ev));
        if st.mean(s)>=avg_ev: cnt+=1
    p=cnt/2000
    print(f"[{label}] janela={win} bars (~{win*barsec//3600}h) | N_NFP={len(ev)}")
    print(f"  range%  evento mediana {me:.2f} vs baseline {mb:.2f}  -> {me/mb:.2f}x | média evento {avg_ev:.2f} vs base {st.mean(rng_b):.2f} (null p={p:.3f})")
    print(f"  |retorno|% evento mediana {st.median(ret_ev):.2f} vs baseline {st.median(ret_b):.2f} -> {st.median(ret_ev)/st.median(ret_b):.2f}x")
    print(f"  reações GRANDES (>=2x baseline): {big}/{len(ev)} = {100*big/len(ev):.0f}%")
    return me/mb,p
print("EVENT-STUDY OURO x NFP (tese: payroll move o ouro)\n")
study(B1,3600,3,"1H 2024+")   # 3h pós release
study(B1,3600,6,"1H 2024+")   # 6h
study(B4,14400,2,"4H 2020+")  # 8h (2 barras 4H)
print("\nReação >1.0x = ouro reage mais no NFP que em janelas normais. p<0.05 = significativo. Confirma Camada A se sim.")
