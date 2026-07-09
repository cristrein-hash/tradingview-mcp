#!/usr/bin/env python3
"""SALVAGE ESTRUTURA→INDICADORES (ordem Cris: máximo resgate honesto, lógica anterior).
Sobre os DOIS universos CAUSAIS (B live-fireable n166; A pós-confirmação n97):
ESTRUTURA primeiro (protocolo 15M): regime v5 causal (+ filtro capitulation já validado) → baldes.
INDICADORES depois, DENTRO do balde de qualidade (BULL): hipóteses PRÉ-DECLARADAS das lições já
validadas (NÃO mining novo): H1 BULL-only · H2 entry rápido (reclaim_lag<=4, lead 61% do estudo
anterior) · H3 buy_recent>0 (carrier do RWS) · H4 rsi_above_ma · H5 NAS long recente.
LOOKS CONTADOS = 5 hipóteses × 2 universos + 2 combos declarados = 12. Null: permutação de outcomes
dentro do balde (2000×) para o melhor de cada universo. Sem tuning de thresholds. Fail-loud.
Output: xau_15m_salvage_structure_indicators_result.json."""
import json, sys, csv, glob, bisect, random
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE)); RD=HERE.parent
import xau_15m_n83_sl_exit_lib as L
random.seed(20260709)
TS=L.TS

# ---- indicadores causais (mesmas fontes do engine: RSI série, bubbles, NAS events) ----
RSI=[None]*L.N
series={}
for p in sorted(glob.glob(str(RD/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
for idx,t in enumerate(TS):
    RSI[idx]=series[t].get("rsi")
RSIMA=[None]*L.N
for i in range(L.N):
    w=[RSI[j] for j in range(max(0,i-13),i+1) if RSI[j] is not None]
    RSIMA[i]=sum(w)/len(w) if w else None
BUB=[]; NASE=[]
for p in sorted(glob.glob(str(RD/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    NASE+= [e for e in d.get("nas_events",[]) if e.get("t")]
for p in glob.glob(str(RD/"bubbles"/"*.bubbles.jsonl")):
    for ln in open(p): BUB.append(json.loads(ln))
BUB.sort(key=lambda x:(x.get("known_at") or x["t"])); BUBK=[(x.get("known_at") or x["t"]) for x in BUB]
NASE.sort(key=lambda e:e["t"]); NAST=[e["t"] for e in NASE]
W={"S":1,"M":2,"L":3}
def buy_recent(t0):
    hi=bisect.bisect_right(BUBK,t0)
    return sum(W[x["size"]] for x in (BUB[k] for k in range(hi)) if x["side"]=="BUY" and t0-4*900<=x["t"]<=t0)
def nas_long_rec(t0):
    hi=bisect.bisect_right(NAST,t0)
    return int(any(e["dir"]=="LONG" and t0-e["t"]<=8*900 for e in NASE[max(0,hi-12):hi]))

def load(fn):
    rows=list(csv.DictReader(open(HERE/fn)))
    for r in rows:
        for k in ("i","j","t","out"): r[k]=int(float(r[k]))
        r["px_vs_ema_1d"]=float(r["px_vs_ema_1d"]) if r.get("px_vs_ema_1d") else None
        jj=r["j"]
        r["reclaim_lag"]=r["j"]-r["i"] if "conf_i" not in r else int(float(r.get("entry_lag_from_low",r["j"]-r["i"])))
        r["rsi_above_ma"]=int(RSI[jj] is not None and RSIMA[jj] is not None and RSI[jj]>RSIMA[jj])
        r["buy_recent"]=buy_recent(TS[jj]); r["nas_rec"]=nas_long_rec(TS[jj])
    return rows
def R_of(r): return 3.0 if r["out"]==1 else -1.0
def cap_keep(rows):
    return [r for r in rows if not (r["regime"]=="BEAR" and r["px_vs_ema_1d"] is not None and r["px_vs_ema_1d"]>=0)]
def panel(rs):
    p=L.panel([R_of(r) for r in rs])
    yr={}
    for r in rs: yr.setdefault(L.dstr(r["t"])[:4],[]).append(R_of(r))
    p["per_year"]={k:{"n":len(v),"sumR":round(sum(v),1)} for k,v in sorted(yr.items())}
    return p

UNI={"B_live_fireable":cap_keep(load("xau_15m_live_fireable_candidates.csv")),
     "A_post_confirmation":cap_keep(load("xau_15m_option_a_candidates.csv"))}
HYP={"H1_BULL_only":lambda r:r["regime"]=="BULL",
     "H2_fast_entry(le4_from_low... A: le conf window? uses reclaim_lag col)":lambda r:r["reclaim_lag"]<=4,
     "H3_buy_recent_gt0":lambda r:r["buy_recent"]>0,
     "H4_rsi_above_ma":lambda r:r["rsi_above_ma"]==1,
     "H5_nas_long_recent":lambda r:r["nas_rec"]==1}
COMBOS={"C1_BULL_and_rsi_above":lambda r:r["regime"]=="BULL" and r["rsi_above_ma"]==1,
        "C2_BULL_and_buyrec":lambda r:r["regime"]=="BULL" and r["buy_recent"]>0}
res={"design":"5 hipóteses pré-declaradas + 2 combos × 2 universos = 12 looks (contados)","universes":{}}
for un,rows in UNI.items():
    o={"kept_baseline":panel(rows)}
    for name,fn in {**HYP,**COMBOS}.items():
        sel=[r for r in rows if fn(r)]
        if len(sel)>=10: o[name]=panel(sel)
        else: o[name]={"n":len(sel),"note":"n<10"}
    # null do melhor (por sumR, n>=20): permutação de outcomes dentro do universo kept
    best=None
    for name in list(HYP)+list(COMBOS):
        p=o.get(name,{})
        if p.get("n",0)>=20 and (best is None or p["sumR"]>o[best]["sumR"]): best=name
    if best:
        sel_fn={**HYP,**COMBOS}[best]
        mask=[sel_fn(r) for r in rows]; outs=[r["out"] for r in rows]; nsel=sum(mask)
        obs=o[best]["sumR"]; cnt=0; TRI=2000
        for _ in range(TRI):
            random.shuffle(outs)
            s=sum(3.0 if outs[k]==1 else -1.0 for k in range(len(rows)) if mask[k])
            if s>=obs: cnt+=1
        o["null_best"]={"best":best,"obs":obs,"p_perm":round(cnt/TRI,4),
                        "note":"permutação de outcomes; NÃO paga multiplicidade dos 12 looks (declarado)"}
    res["universes"][un]=o
(HERE/"xau_15m_salvage_structure_indicators_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
for un,o in res["universes"].items():
    print(f"\n=== {un} kept baseline: {o['kept_baseline']['n']} WR{o['kept_baseline']['WR']} {o['kept_baseline']['sumR']}R DD{o['kept_baseline']['maxDD_R']} stk{o['kept_baseline']['streak']} ===")
    for name in list(HYP)+list(COMBOS):
        p=o.get(name,{})
        if p.get("n",0)>=10:
            yb=" ".join(f"{y}:{v['sumR']}" for y,v in p["per_year"].items())
            print(f"  {name:<42} n={p['n']:<4} WR={p['WR']:<5} sumR={p['sumR']:<7} DD={p['maxDD_R']:<6} stk={p['streak']:<3} {yb}")
    if "null_best" in o: print("  null:",o["null_best"])
