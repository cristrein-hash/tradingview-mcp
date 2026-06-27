#!/usr/bin/env python3
"""LAB DIAGNOSTICO entry/SL/exit dos 170 trades (Cris 2026-06-27): so MEDE, nao decide.
Reconstroi o caminho de barras (cj..exi) de cada trade na regua APROVADA (SL=A flush-0.1ATR, let-run).
Mede por trade:
  - MAE_R  = (min low em (cj,exi] - entry)/risk        (quao fundo foi contra; -1 = bateu SL)
  - MFE_R  = (max high em (cj,exi] - entry)/risk
  - near_sl = min low chegou a que fracao do caminho ate o SL (1.0 = encostou no SL)
  - bars_underwater = barras com close<entry antes de 1o high>=entry+1R (ou ate exit)
  - hold_bars = exi-cj
  Demanda 15M pre-existente (causal, born_t<=tc):
  - dem_top_below_atr = distancia (entry - topo da DEMAND mais proxima ABAIXO/contendo entry)/atr
  - mae_reached_dem   = o MAE pos-entrada tocou esse topo de demanda? (limit ali encheria)
RAW-causal. Junta aos 170 por entry_t. Nada de veredito."""
import json, csv, bisect, statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}   # block key = prefixo data inicio (igual ao build)
# filter_dataset tem cj/exi/i/block por entry_t (=t)
FD={}
for l in (HERE/"filter_dataset.jsonl").read_text().splitlines():
    r=json.loads(l); FD[r["t"]]=r
# 170 trades finais
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))

def nearest_demand_below(zones, entry, tc, atr):
    """topo da DEMAND mais proxima que esta ABAIXO de entry ou contem entry (causal born_t<=tc)."""
    best=None
    for z in zones:
        if z.get("text")!="DEMAND": continue
        if z.get("born_t",1e18)>tc: continue
        top=z["high"]
        if top<=entry+1e-9:           # topo abaixo (ou no) preco de entrada
            d=(entry-top)/atr
            if best is None or d<best[0]: best=(d,z["low"],z["high"])
    return best  # (dist_atr, low, high) ou None

rows=[]
ndem_blocks=sum(1 for pr in PRIM.values() for z in pr["zones"] if z.get("text")=="DEMAND")
for tr in T170:
    t=int(tr["entry_t"]); fd=FD.get(t)
    if not fd: rows.append({"num":tr["num"],"missing":True}); continue
    blk=fd["block"]; pr=PRIM[blk]; s=pr["series"]
    cj=fd["cj"]; exi=fd["exi"]; i=fd["i"]
    entry=float(tr["entry"]); sl=float(tr["sl"]); R=float(tr["R"]); win=tr["win"]=="1"
    risk=entry-sl; atr=s[i]["atr"] or (risk/ ( (entry-min(x['l'] for x in s[i:cj+1]))/ (s[i]['atr'] or 1) ) if False else risk)
    atr=s[i]["atr"]
    path=s[cj+1:exi+1] or [s[cj]]
    lows=[b["l"] for b in path]; highs=[b["h"] for b in path]
    minlow=min(lows); maxhigh=max(highs)
    mae_R=(minlow-entry)/risk; mfe_R=(maxhigh-entry)/risk
    near_sl=(entry-minlow)/risk            # 1.0 = encostou no SL (antes do -0.1ATR buffer ja conta)
    # bars underwater antes de 'desenvolver' (1o high>=entry+1R)
    bu=0; dev=None
    for k,b in enumerate(path):
        if b["h"]>=entry+risk: dev=k; break
        if b["c"]<entry: bu+=1
    hold=exi-cj
    nd=nearest_demand_below(pr["zones"], entry, t, atr)
    dem_atr = round(nd[0],2) if nd else None
    mae_reached_dem = bool(nd and minlow<=nd[2]+1e-9)   # MAE tocou topo da demanda
    rows.append({"num":int(tr["num"]),"yr":tr["yr"],"win":win,"R":round(R,2),
                 "mae_R":round(mae_R,2),"mfe_R":round(mfe_R,2),"near_sl":round(near_sl,2),
                 "bars_uw":bu,"hold":hold,"dem_atr":dem_atr,"mae_in_dem":mae_reached_dem})

ok=[r for r in rows if not r.get("missing")]
wins=[r for r in ok if r["win"]]; loss=[r for r in ok if not r["win"]]
def pct(xs,c): return f"{100*sum(1 for x in xs if c(x))/len(xs):.0f}%" if xs else "-"
def med(xs,k): v=[x[k] for x in xs if x[k] is not None]; return round(st.median(v),2) if v else None

print(f"DEMAND zones no RAW (8 blocos): {ndem_blocks}  | trades casados: {len(ok)}/{len(rows)}")
print("\n=== MAE (quao fundo foi contra antes do resultado) ===")
print(f"{'grupo':<10}{'n':>4}{'medMAE_R':>9}{'medMFE_R':>9}{'medNearSL':>10}{'medUW':>7}{'medHold':>8}")
for name,g in (("TODOS",ok),("WINNERS",wins),("LOSERS",loss)):
    print(f"{name:<10}{len(g):>4}{med(g,'mae_R'):>9}{med(g,'mfe_R'):>9}{med(g,'near_sl'):>10}{med(g,'bars_uw'):>7}{med(g,'hold'):>8}")

print("\n=== 'passa velas em SL antes de desenvolver' (so WINNERS) ===")
print(f"  winners que foram <= -0.3R contra antes de andar: {pct(wins,lambda x:x['mae_R']<=-0.3)}")
print(f"  winners que foram <= -0.5R contra:                {pct(wins,lambda x:x['mae_R']<=-0.5)}")
print(f"  winners que chegaram a >=90% do SL (quase stop):  {pct(wins,lambda x:x['near_sl']>=0.9)}")
print(f"  winners com >=3 barras underwater antes de andar: {pct(wins,lambda x:x['bars_uw']>=3)}")
print(f"  winners com >=6 barras underwater:                {pct(wins,lambda x:x['bars_uw']>=6)}")

print("\n=== demanda 15M pre-existente ABAIXO/na entrada (refino de entry, causal) ===")
withdem=[r for r in ok if r["dem_atr"] is not None]
print(f"  trades com DEMAND pre-existente abaixo/na entrada: {len(withdem)}/{len(ok)}")
print(f"  distancia mediana entry->topo demanda (ATR):       {med(withdem,'dem_atr')}")
print(f"  trades cujo MAE TOCOU o topo dessa demanda (limit ali encheria): {pct(withdem,lambda x:x['mae_in_dem'])}")
wd_w=[r for r in withdem if r['win']]
print(f"    idem so WINNERS: {pct(wd_w,lambda x:x['mae_in_dem'])}  (= pullback a demanda conhecida e ainda venceu)")

print("\n=== amostra 15 trades (ordenado por MAE mais fundo) ===")
print(f"{'#':>4}{'win':>4}{'R':>6}{'MAE_R':>7}{'MFE_R':>7}{'nearSL':>7}{'UW':>4}{'hold':>5}{'demATR':>7}{'inDem':>6}")
for r in sorted(ok,key=lambda x:x['mae_R'])[:15]:
    print(f"{r['num']:>4}{('W' if r['win'] else 'L'):>4}{r['R']:>6}{r['mae_R']:>7}{r['mfe_R']:>7}{r['near_sl']:>7}{r['bars_uw']:>4}{r['hold']:>5}{str(r['dem_atr']):>7}{('Y' if r['mae_in_dem'] else '-'):>6}")

# salva CSV completo
with open(HERE/"lab_entry_diag.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["num","yr","win","R","mae_R","mfe_R","near_sl","bars_uw","hold","dem_atr","mae_in_dem"])
    for r in ok: w.writerow([r["num"],r["yr"],int(r["win"]),r["R"],r["mae_R"],r["mfe_R"],r["near_sl"],r["bars_uw"],r["hold"],r["dem_atr"],int(r["mae_in_dem"])])
print("\n-> lab_entry_diag.csv (170 linhas)")
