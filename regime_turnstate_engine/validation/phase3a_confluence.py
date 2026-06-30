#!/usr/bin/env python3
"""RTSE FASE 3a — HARNESS MULTI-CAMADA / CONFLUÊNCIA (anti-miopia). Começa pelos INDICADORES (RSI/NAS/SMC/OB),
que estavam ausentes. Cada camada = voto contextual por pivô (causal, travas: NAS dir LONG/SHORT por t;
SMC CHoCH/BOS SHIFT1; OB zone born_t). READER = confluência (contagem de camadas alinhadas).
Testa a TESE DO CRIS: confluência > melhor-single. Rótulo LIMPO = MFE forward em % (não /ATR, não M8-prox).
⚠️ caracterização (M8=gabarito), não detector live. Anti-bug: NUNCA concluir 'feature morta' de single isolado.
Determinístico, causal."""
import json,csv,statistics as st,random,bisect
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
PR=ROOT/"research/xau_15m_bb_nas_leonardo/primitives"; GT=ROOT/"regime_turnstate_engine/ground_truth"
# ---- carrega series + streams (dedup: series por t, eventos/zonas por id) ----
S={};NAS={};SMC={};ZON={}
for f in sorted(PR.glob("*.primitives.json")):
    d=json.loads(f.read_text())
    for b in d["series"]: S[b["t"]]=b
    for e in d.get("nas_events",[]): NAS[e["id"]]=e
    for e in d.get("smc_events",[]): SMC[e["id"]]=e
    for z in d.get("zones",[]): ZON[z["id"]]=z
S=[S[t] for t in sorted(S)]; T=[b["t"] for b in S]; idx={t:i for i,t in enumerate(T)}
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S]
nas=sorted(NAS.values(),key=lambda e:e["t"]); nas_t=[e["t"] for e in nas]
smc=sorted(SMC.values(),key=lambda e:e["t"]); smc_t=[e["t"] for e in smc]
zones=list(ZON.values())
def atr_at(i,n=14):
    tr=[max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-n+1,i+1)]
    return sum(tr)/len(tr)
def ev_in(arr_t,arr,ts,W,dirkey=None,dirval=None,textset=None):
    lo=bisect.bisect_left(arr_t,ts-W); hi=bisect.bisect_right(arr_t,ts)  # ESTRITO: só eventos <= pivô (causal)
    for e in arr[lo:hi]:
        if dirkey and e.get(dirkey)!=dirval: continue
        if textset and e.get("text") not in textset: continue
        return True
    return False
m8=[(int(d["t"]),d["kind"]) for d in csv.DictReader(open(ROOT/"research/xau_15m_bb_nas_leonardo/true_reversals_M8.csv"))]
K=96;Wd=12*3600
rows=[]
for t,kind in m8:
    i=idx.get(t)
    if i is None or i<30 or i+K>=len(S): continue
    rsi=S[i].get("rsi")
    if rsi is None: continue
    mfe=100*((max(H[i+1:i+K+1])-Lo[i]) if kind=="BOT" else (H[i]-min(Lo[i+1:i+K+1])))/C[i]
    # CAMADAS-INDICADOR (voto contextual a favor da reversão, causal)
    v_rsi = 1 if ((kind=="BOT" and rsi<45) or (kind=="TOP" and rsi>55)) else 0
    v_nas = 1 if ev_in(nas_t,nas,t,Wd,"dir",("LONG" if kind=="BOT" else "SHORT")) else 0
    v_smc = 1 if ev_in(smc_t,smc,t,Wd,textset={"CHoCH","BOS"}) else 0
    # OB: pivô dentro de zona DEMAND(BOT)/SUPPLY(TOP) nascida antes do pivô
    want="DEMAND" if kind=="BOT" else "SUPPLY"; px=Lo[i] if kind=="BOT" else H[i]; v_ob=0
    for z in zones:
        if z.get("text")==want and z.get("born_t",1e18)<=t and z["low"]<=px<=z["high"]: v_ob=1;break
    rows.append({"t":t,"kind":kind,"mfe":mfe,"v_rsi":v_rsi,"v_nas":v_nas,"v_smc":v_smc,"v_ob":v_ob,
                 "conf":v_rsi+v_nas+v_smc+v_ob})
# DURABILIDADE RELATIVA AO ANO (evita confound de volatilidade do período: 2024 rangy vs 2026 bull)
import datetime as dt
def _yr(ts): return dt.datetime.utcfromtimestamp(ts).year
medy={}
for y in set(_yr(r["t"]) for r in rows):
    mm=sorted(r["mfe"] for r in rows if _yr(r["t"])==y); medy[y]=mm[len(mm)//2]
for r in rows: r["dur"]=r["mfe"]>=medy[_yr(r["t"])]
med=mfes_global=sorted(r["mfe"] for r in rows)[len(rows)//2]
nd=sum(r["dur"] for r in rows);N=len(rows)
print(f"FASE 3a CONFLUÊNCIA (indicadores) — pivôs {N} | durável(>={med:.1f}%) {nd} ({100*nd/N:.0f}%)")
print("\n-- SINGLE: taxa-durável quando voto=1 vs voto=0 (cobertura) --")
for v in ["v_rsi","v_nas","v_smc","v_ob"]:
    on=[r for r in rows if r[v]==1];off=[r for r in rows if r[v]==0]
    dr_on=sum(x["dur"] for x in on)/len(on) if on else 0; dr_off=sum(x["dur"] for x in off)/len(off) if off else 0
    print(f"  {v}: voto=1 -> {100*dr_on:.0f}% durável (n{len(on)}) | voto=0 -> {100*dr_off:.0f}% (n{len(off)}) | lift {100*(dr_on-dr_off):+.0f}pp")
print("\n-- CONFLUÊNCIA: taxa-durável por nº de camadas alinhadas (dose-resposta) --")
for c in range(0,5):
    g=[r for r in rows if r["conf"]==c]
    if g: print(f"  conf={c}: {100*sum(x['dur'] for x in g)/len(g):.0f}% durável (n{len(g)})")
# tese: conf alto (>=3) vs baixo (<=1)
hi=[r for r in rows if r["conf"]>=3];lo=[r for r in rows if r["conf"]<=1]
realdiff=(sum(x["dur"] for x in hi)/len(hi) if hi else 0)-(sum(x["dur"] for x in lo)/len(lo) if lo else 0)
# null: embaralha rótulo durável
random.seed(11);labs=[r["dur"] for r in rows];confs=[r["conf"] for r in rows];diffs=[]
for _ in range(400):
    random.shuffle(labs)
    h=[labs[i] for i in range(N) if confs[i]>=3];l=[labs[i] for i in range(N) if confs[i]<=1]
    diffs.append((sum(h)/len(h) if h else 0)-(sum(l)/len(l) if l else 0))
p=sum(1 for x in diffs if abs(x)>=abs(realdiff))/len(diffs)
bestsingle=max(abs(sum(x["dur"] for x in [r for r in rows if r[v]==1])/max(1,len([r for r in rows if r[v]==1]))-sum(x["dur"] for x in [r for r in rows if r[v]==0])/max(1,len([r for r in rows if r[v]==0]))) for v in ["v_rsi","v_nas","v_smc","v_ob"])
print(f"\nTESE confluência>single: conf>=3 ({len(hi)}) vs conf<=1 ({len(lo)}) -> lift {100*realdiff:+.0f}pp | null p={p:.3f} | melhor-single lift {100*bestsingle:.0f}pp")
import datetime as dt
def yr(ts): return dt.datetime.utcfromtimestamp(ts).year
print("\n-- POR ANO: taxa-durável conf>=3 vs conf<=1 --")
for y in sorted(set(yr(r["t"]) for r in rows)):
    ry=[r for r in rows if yr(r["t"])==y]
    h=[r for r in ry if r["conf"]>=3];l=[r for r in ry if r["conf"]<=1]
    drh=sum(x["dur"] for x in h)/len(h) if h else None; drl=sum(x["dur"] for x in l)/len(l) if l else None
    print(f"  {y}: conf>=3 {(f'{100*drh:.0f}%' if drh is not None else '-'):>5} (n{len(h)}) | conf<=1 {(f'{100*drl:.0f}%' if drl is not None else '-'):>5} (n{len(l)}) | lift {f'{100*(drh-drl):+.0f}pp' if (drh is not None and drl is not None) else '-'}")
print("-- JACKKNIFE (dropa 1 ano): lift conf>=3 vs <=1 do resto --")
lifts=[]
for y in sorted(set(yr(r["t"]) for r in rows)):
    rj=[r for r in rows if yr(r["t"])!=y]
    h=[r for r in rj if r["conf"]>=3];l=[r for r in rj if r["conf"]<=1]
    if h and l:
        lf=sum(x["dur"] for x in h)/len(h)-sum(x["dur"] for x in l)/len(l);lifts.append(lf)
        print(f"  sem {y}: lift {100*lf:+.0f}pp")
if lifts: print(f"  jackknife lift: min {100*min(lifts):+.0f}pp / max {100*max(lifts):+.0f}pp (robusto se todos positivos e ~constantes)")
print("\nLEITURA: confluência robusta = lift positivo TODO ano + jackknife estável + p<0.05 + > melhor-single. Aí a tese Cris está provada.")
