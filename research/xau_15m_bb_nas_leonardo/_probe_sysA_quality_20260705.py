#!/usr/bin/env python3
"""Classifica os 53 do Sistema A por QUALIDADE ESTRUTURAL real (não por outcome):
- posição no range recente (box96): fundo <0,33 / meio 0,33-0,66 / topo >0,66
- esticamento acima da EMA21 (g_ema21_dist): comprou puxado?
- distância abaixo do high-96 em ATR (dip real vs topo)
- MFE em R e nº de barras de continuidade até o pico (imaturidade = pico cedo e some)
- outcome let-run (g_R) e sob 3R
Objetivo: ver quantos são 'fundo genuíno com corrida' vs 'meio/topo de chop contado como win'."""
import json, glob, bisect, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
CANON=HERE/"results"/"lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest()==(HERE/"results"/"lab_g_candidates.sha256").read_text().split()[0]
U=[json.loads(l) for l in open(CANON)]
R3={json.loads(l)["cj_t"]:json.loads(l) for l in open(HERE/"results"/"r3_target_universe_20260704.jsonl")}
def fv(r,k,d=0):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
def sysA(r):
    return (r["g_v5h"]=="BULL" and fv(r,"h1_trend")==1 and fv(r,"h1_pos",0)>=0.33
        and (fv(r,"above_ema21",1)==0 or fv(r,"reclaim_ema_bars",99)<=3)
        and (fv(r,"g_atr_spike")>=1.27 or fv(r,"g_downrun")>=3)
        and (fv(r,"in_demand")==1 or fv(r,"htf_demand_any")==1)
        and (fv(r,"g_rec_speed")>=0.69 or fv(r,"reclaim_atr")>=2.0) and r["g_knife"]==0)
A=sorted([r for r in U if sysA(r)],key=lambda r:r["cj_t"])
def mfe(i,entry,sl):
    risk=entry-sl; end=min(i+480,N-1); mx=0; kpk=i
    for k in range(i+1,end+1):
        r=(S[k]["h"]-entry)/risk
        if r>mx: mx=r; kpk=k
        if S[k]["l"]<=sl: break
    return mx,kpk-i
buckets={"fundo":0,"meio":0,"topo":0}
q_fundo=[]; q_top=[]
print("  #  box96  ema_d  dip_atr  MFE  bars_pico  R_letrun  R3")
for n,r in enumerate(A,1):
    i=bisect.bisect_right(TS,r["cj_t"])-1
    box=fv(r,"g_box96",0.5)
    zone="fundo" if box<0.33 else ("topo" if box>0.66 else "meio")
    buckets[zone]+=1
    m,bp=mfe(i,r["g_entry"],r["g_sl"])
    dd=fv(r,"g_ema21_dist"); dip=None
    lab="F" if zone=="fundo" else ("T" if zone=="topo" else "m")
    (q_fundo if zone=="fundo" else q_top if zone=="topo" else []).append(r["g_R"])
    print(f"{n:>3} {box:>5.2f} {dd:>5.2f}  {r.get('g_downrun',0):>3}   {m:>4.1f}  {bp:>4}      {r['g_R']:>5.2f}  {R3[r['cj_t']]['R3']:>4.1f} [{lab}]")
print(f"\nDISTRIBUICAO ESTRUTURAL dos 53: fundo(box<0.33)={buckets['fundo']} meio={buckets['meio']} topo(box>0.66)={buckets['topo']}")
def rate(xs): 
    return f"N{len(xs)} hitR3>=3 {sum(1 for x in xs if x>=3)} winPos {sum(1 for x in xs if x>0)}" if xs else "vazio"
print(f"  FUNDO: {rate(q_fundo)}")
print(f"  TOPO : {rate(q_top)}")
import statistics as st
allmfe=[mfe(bisect.bisect_right(TS,r['cj_t'])-1,r['g_entry'],r['g_sl']) for r in A]
pe-1
