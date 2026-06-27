#!/usr/bin/env python3
"""LAB SL + EXIT (Cris 2026-06-27): aproximar o SL e o EXIT que o Cris desenhou nos 170 long_position.
Fonte: cris_ground_truth.csv (cris_sl/cris_exit) + RAW path (cj/exi/i/block de filter_dataset) + zones.
PARTE 1 — SL: erro de regras causais vs cris_sl (flush atual, demanda 15M, swing). Tighter/wider?
PARTE 2 — BRACKET: simula causal SL=cris_sl & TP=cris_exit no caminho real (HMAX), checa se TP foi
          atingido ANTES do SL (achievable). sumR/WR/DD vs regua atual (let-run, +66.3R).
PARTE 3 — alvo causal p/ EXIT: TP = proxima SUPPLY pre-existente acima (born<=tc) — quao perto do cris_exit.
So MEDE. RAW-causal. Sem veredito."""
import json, csv, bisect, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))

def f(x): return float(x) if x not in (None,"","None") else None

def nearest_demand_low(zones, entry, tc):
    """low da DEMAND mais proxima abaixo/na entrada (causal). Retorna (low,high) ou None."""
    best=None
    for z in zones:
        if z.get("text")!="DEMAND" or z.get("born_t",1e18)>tc: continue
        if z["high"]<=entry+1e-9:
            d=entry-z["high"]
            if best is None or d<best[0]: best=(d,z["low"],z["high"])
    return (best[1],best[2]) if best else None
def nearest_supply_above(zones, entry, tc):
    best=None
    for z in zones:
        if z.get("text")!="SUPPLY" or z.get("born_t",1e18)>tc: continue
        if z["low"]>entry:
            d=z["low"]-entry
            if best is None or d<best[0]: best=(d,z["low"])
    return best[1] if best else None
def swing_low(s,i,cj):
    """menor low na perna ancora i..cj (estrutural)."""
    return min(x["l"] for x in s[i:cj+1])

rows=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); gt=GT.get(num)
    if not fd or not gt: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; z=pr["zones"]
    i=fd["i"]; cj=fd["cj"]; atr=s[i]["atr"]; tc=s[cj]["t"]
    entry=f(gt["entry"]); csv_sl=f(gt["csv_sl"]); cris_sl=f(gt["cris_sl"]); cris_exit=f(gt["cris_exit"])
    win=gt["win"]=="1"
    # candidatas SL
    dl=nearest_demand_low(z,entry,tc)
    sl_dem = round(dl[0]-0.1*atr,2) if dl else None       # demanda low - 0.1ATR
    sl_swing = round(swing_low(s,i,cj)-0.1*atr,2)
    sup = nearest_supply_above(z,entry,tc)
    # bracket sim com cris_sl & cris_exit
    end=min(cj+HMAX,len(s)-1); res=None; rch=None
    for k in range(cj+1,end+1):
        lo,hi=s[k]["l"],s[k]["h"]
        hit_sl = cris_sl is not None and lo<=cris_sl
        hit_tp = cris_exit is not None and hi>=cris_exit
        if hit_sl and hit_tp: res=("ambos",k); break      # mesma barra: conservador=SL primeiro
        if hit_sl: res=("SL",k); break
        if hit_tp: res=("TP",k); break
    risk=entry-cris_sl if cris_sl else None
    if res is None: res=("timeout",end)
    if res[0]=="TP": br_R=(cris_exit-entry)/risk
    elif res[0] in ("SL","ambos"): br_R=-1.0
    else: br_R=(s[end]["c"]-entry)/risk if risk else 0.0   # timeout = fecha no fim
    rows.append({"num":num,"win":win,"entry":entry,"csv_sl":csv_sl,"cris_sl":cris_sl,"cris_exit":cris_exit,
                 "csv_R":f(tr["R"]),"atr":round(atr,2),"sl_dem":sl_dem,"sl_swing":sl_swing,"sup_above":round(sup,2) if sup else None,
                 "br_out":res[0],"br_R":round(br_R,3) if br_R is not None else None,
                 "tp_reached":res[0]=="TP"})

# ---------- PARTE 1: SL ----------
def mae(rs,a,b):
    v=[abs(r[a]-r[b]) for r in rs if r[a] is not None and r[b] is not None]; return round(st.mean(v),2),round(st.median(v),2)
print("=== PARTE 1: SL — regras causais vs SEU SL (erro absoluto $) ===")
for name,col in (("flush-0.1ATR (atual=csv_sl)","csv_sl"),("demanda 15M low-0.1ATR","sl_dem"),("swing perna low-0.1ATR","sl_swing")):
    m,md=mae(rows,col,"cris_sl");
    # erro em ATR
    eatr=[abs(r[col]-r["cris_sl"])/r["atr"] for r in rows if r[col] is not None and r["cris_sl"] is not None]
    print(f"  {name:<32} erro medio ${m:<6} mediana ${md:<6} ({st.median(eatr):.2f} ATR mediano)")
tighter=sum(1 for r in rows if r["cris_sl"] and r["cris_sl"]>r["csv_sl"]+0.05)
wider=sum(1 for r in rows if r["cris_sl"] and r["cris_sl"]<r["csv_sl"]-0.05)
print(f"  Seu SL vs flush atual: {tighter} mais APERTADO (risco menor) | {wider} mais LARGO | {170-tighter-wider} igual")

# ---------- PARTE 2: BRACKET ----------
print("\n=== PARTE 2: seu bracket (SL=cris_sl, TP=cris_exit) no caminho REAL (causal, HMAX=480) ===")
def metr(rs):
    n=len(rs); sm=sum(r["br_R"] for r in rs); w=sum(1 for r in rs if r["br_R"]>0)
    eq=pk=dd=0
    for r in sorted(rs,key=lambda x:x["num"]):
        eq+=r["br_R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
    return n,round(100*w/n,1),round(sm,1),round(dd,1)
n,wr,sm,dd=metr(rows)
out_ct={}
for r in rows: out_ct[r["br_out"]]=out_ct.get(r["br_out"],0)+1
print(f"  bracket Cris: N={n} WR={wr}% sumR={sm:+} DD={dd}  | desfechos {out_ct}")
print(f"  regua ATUAL (let-run, csv):        sumR=+66.3  WR=64.1%  (referencia)")
tp_reach=[r for r in rows if r["tp_reached"]]
print(f"  TPs do Cris efetivamente atingidos no caminho: {len(tp_reach)}/170 ({100*len(tp_reach)/170:.0f}%)")
# entre os que voce marcou exit MAIOR (cris_exit > csv_exit), quantos o caminho alcancou
big=[r for r in rows if r["cris_exit"] and f(GT[r["num"]]["csv_exit"]) and r["cris_exit"]>f(GT[r["num"]]["csv_exit"])+0.05]
big_reach=[r for r in big if r["tp_reached"]]
print(f"  dos {len(big)} com EXIT maior que voce desenhou: {len(big_reach)} alcancaram no caminho real")

# ---------- PARTE 3: alvo causal p/ EXIT ----------
print("\n=== PARTE 3: SUPPLY pre-existente acima como alvo causal vs seu cris_exit ===")
hassup=[r for r in rows if r["sup_above"] is not None and r["cris_exit"] is not None]
err=[abs(r["sup_above"]-r["cris_exit"]) for r in hassup]
print(f"  trades com SUPPLY acima (causal): {len(hassup)}/170 | erro mediano supply vs seu exit: ${st.median(err):.1f}")
above=sum(1 for r in hassup if r["sup_above"]>=r["cris_exit"]-0.05)
print(f"  SUPPLY fica ACIMA/igual do seu exit em {above}/{len(hassup)} (alvo natural >= seu alvo)")

with open(HERE/"lab_sl_exit.csv","w",newline="") as fcsv:
    w=csv.DictWriter(fcsv,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("\n-> lab_sl_exit.csv")
