#!/usr/bin/env python3
"""ASSIMILAR padrão PLT (polaridade de topo) / DM (demanda) do Cris (2026-07-07, guia dele).
1. Extrair níveis PLT/DM (preço + timestamp de criação).
2. VALIDAR: os 42 fundos retestam um nível PLT/DM criado ANTES deles? (a chave)
3. CARACTERIZAR PLT: que estrutura causal gera um PLT? (cruzar com swing-high/BOS+/EQH) — p/ aprender
   a regra que reproduz os PLT automaticamente.
4. Idem DM (swing-low).
SANITY_PROBE: assimilação/leitura de guia manual (não teste métrica); níveis causais; cruzamento
com estrutura para aprender a regra."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
rows=json.load(open(HERE/"results"/"manual_shapes_pltdm_20260707.json"))
def t0(r):
    pts=r.get("points") or []; return int(pts[0]["time"]) if pts and pts[0].get("time") else None
def pr(r):
    pts=r.get("points") or []; return pts[0]["price"] if pts and pts[0].get("price") else None
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M") if t else "??"
PLT=sorted([{"t":t0(r),"p":pr(r)} for r in rows if r["name"]=="text_note" and r["text"].strip().upper()=="PLT" and t0(r)],key=lambda x:x["t"])
DM=sorted([{"t":t0(r),"p":pr(r)} for r in rows if r["name"]=="text_note" and r["text"].strip().upper()=="DM" and t0(r)],key=lambda x:x["t"])
print(f"PLT {len(PLT)} · DM {len(DM)}")
# séries + estrutura
series={}; EV=[]
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    EV+=[e for e in d["smc_events"] if e.get("t") and e.get("text") and e.get("price")]
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([n for n in cat["notes"]["FUNDO"] if n["t"]],key=lambda x:int(x["t"]))
# 2. fundos retestam PLT/DM criado antes?
LV=sorted([("PLT",l["t"],l["p"]) for l in PLT]+[("DM",l["t"],l["p"]) for l in DM],key=lambda x:x[1])
print("\n=== FUNDOS que retestam um nível PLT/DM criado antes (±0,8 ATR, nível anterior ao fundo) ===")
hit=0
for f in fundos:
    ft=int(f["t"]); ci=bisect.bisect_right(TS,ft)-1; a=ATR[ci] or 5.0; flo=LO[max(0,ci-4):ci+4]
    flo_v=min(LO[max(0,ci-6):ci+6])
    near=None
    for typ,lt,lp in LV:
        if lt < ft and abs(lp-flo_v)<=0.8*a and ft-lt <= 40*86400:
            near=(typ,ds(lt),lp,round((lp-flo_v)/a,2)); break
    if near: hit+=1; print(f"  {ds(ft)[:10]} fundo@{flo_v:.0f} <- {near[0]} @{near[2]:.0f} ({near[1][:10]}, Δ{near[3]}ATR)")
    # só imprime os que tem, resumo dos sem depois
print(f"\nfundos que retestam PLT/DM anterior: {hit}/{len(fundos)}")
# 3. caracterizar PLT: é um swing-high? rompido? EQH?
def close_at(t):
    i=bisect.bisect_right(TS,t)-1; return CL[i] if i>=0 else None
BOS=set(); EQHs=set()
for e in EV:
    if e["text"]=="BOS": BOS.add((e["t"],round(e["price"],1)))
    if e["text"]=="EQH": EQHs.add((e["t"],round(e["price"],1)))
def is_swinghigh(t,p,w=8):
    i=bisect.bisect_right(TS,t)-1
    return any(abs(HI[k]-p)<=0.5*(ATR[k] or 5) and HI[k]==max(HI[max(0,k-w):k+w+1]) for k in range(max(0,i-8),min(N,i+8)))
print("\n=== CARACTERIZAR PLT (que estrutura são) ===")
for l in PLT:
    i=bisect.bisect_right(TS,l["t"])-1; a=ATR[i] or 5
    sh=is_swinghigh(l["t"],l["p"])
    # é EQH próximo?
    eqh=any(abs(ep-l["p"])<=0.5*a and abs(et-l["t"])<=48*3600 for et,ep in EQHs)
    # foi rompido depois? (close > p+0.1ATR nas 480 barras seguintes)
    broke=any(CL[k]>l["p"]+0.1*ATR[k] for k in range(i, min(N,i+480)))
    print(f"  PLT {ds(l['t'])[:10]} @{l['p']:.0f}: swing-high={int(sh)} EQH-perto={int(eqh)} rompido-depois={int(broke)}")
print("OK")
