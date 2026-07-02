#!/usr/bin/env python3
"""PISTA (phase21): entradas near-demand em range-HELD perdem NÃO por falha de entrada, mas porque o SL (demanda-0.1ATR)
é colado demais — oscilação do range enfia pavio, stopa, e o range bounce sem a entrada. = Ponto B do Cris.
TESTA alargar o SL abaixo da demanda (buffer 0.1[orig]/0.5/1.0/1.5 ATR) nas near-demand, e mede se converte losers→winners.
SL mais largo = risco maior = R-múltiplo menor por trade (RxR pior) — mede o NET. Simulo let-run (wick, HZ120). Custo 0.35.
CAUSAL: demanda=running-min-so-far; SL abaixo dela é conhecido no entry (não hindsight). let-run forward=execução real."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
COST=0.35;HZ=120;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
def sim_letrun(bi,entry,sl):
    risk=entry-sl
    if risk<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/risk
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
near=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t)
    if not box: continue
    i0=bisect.bisect_left(T,box['start']);floor=min(L[i0:bi+1]);a=atr(bi);entry=float(r["entry"])
    if (entry-floor)/a>1.5: continue     # só near-demand
    near.append({"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"bi":bi,"entry":entry,"floor":floor,"atr":a,"orig_sl":float(r["sl"])})
print("="*94);print("NEAR-DEMAND (dist<=1.5ATR) — alargar SL abaixo da DEMANDA (running-min): converte losers→winners?");print("="*94)
print(f"  N near-demand = {len(near)}")
print(f"  {'buffer SL':22}{'sumR':>8}{'WR':>6}{'winners':>9}  (SL = demanda − buffer*ATR)")
for lab,buf in [("orig (~demanda−0.1)",None),("demanda−0.5ATR",0.5),("demanda−1.0ATR",1.0),("demanda−1.5ATR",1.5)]:
    tot=0;w=0;rs=[]
    for x in near:
        sl=x["orig_sl"] if buf is None else x["floor"]-buf*x["atr"]
        R=sim_letrun(x["bi"],x["entry"],sl)
        R=round((R if R is not None else 0)-COST,2);rs.append(R);tot+=R;w+=(R>0)
    print(f"  {lab:22}{tot:>+8.1f}{100*w/len(near):>5.0f}%{w:>9}")
print("\n-- por-trade: orig vs demanda−1.0ATR --")
for x in sorted(near,key=lambda z:z['bi']):
    ro=round((sim_letrun(x['bi'],x['entry'],x['orig_sl']) or 0)-COST,2)
    rw=round((sim_letrun(x['bi'],x['entry'],x['floor']-1.0*x['atr']) or 0)-COST,2)
    print(f"    {x['date']} entry {x['entry']:.0f} demanda {x['floor']:.0f} | orig R {ro:+.2f} -> demanda−1ATR R {rw:+.2f}  {'SALVOU' if rw>0 and ro<=0 else ('piorou' if rw<ro-0.2 else '')}")
