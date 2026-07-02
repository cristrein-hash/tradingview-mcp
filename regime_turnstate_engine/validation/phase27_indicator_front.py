#!/usr/bin/env python3
"""Frente INDICADORES (Cris nomeou) — TESTE DISCIPLINADO nas 70 range-trades 2023+.
Fonte: raw_features_2020_2026.jsonl (full-bar, 70/70 cobertas). Outcome = letrun_struct − 0.35 (canónico let-run).
HIPÓTESE PRÉ-REGISTRADA (estrutural, Auction): um FUNDO comprável de range mostra EXAUSTÃO de venda (RSI baixo);
entrar com RSI alto = perseguir o topo/meio do range = chasing (os 13 losers). Regra: skip se rsi >= thr.
Secundárias (caracterização, exploratório): bubble_SELL cluster recente (plot_6/8/10=absorção-fundo), nas_long recente.
CAUSALIDADE: indicadores que REPINTAM (bubbles/nas/smc) lidos com SHIFT1 (bar i-1); rsi no close do bar i (fechado).
RIGOR anti-overfit (lição DA phase24): permutation-null-of-max — enumera TODAS as regras candidatas, pega o melhor sumR,
e testa contra 400 shuffles de R re-escolhendo o melhor. Se o melhor observado nao bate o null-of-max, NAO e real."""
import json,csv,io,contextlib,sys,datetime as dt,random
from pathlib import Path
random.seed(20260701)
COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
raw={int(json.loads(l)["ts_epoch"]):json.loads(l) for l in open(D/"repro_recovery/raw_features_2020_2026.jsonl")}
def rf(bi): return raw.get(int(T[bi]))
SELL={"plot_6","plot_8","plot_10"};BUY={"plot_0","plot_2","plot_4"}
def has_bubble(d,pset,within=12):
    return any(b.get("plot_id") in pset and b.get("bars_ago",99)<=within for b in (d.get("bubbles_recent") or []))
def nas_last(d):  # texto do NAS mais recente na janela (maior x = mais recente)
    ns=d.get("nas_recent") or []
    if not ns: return None
    return max(ns,key=lambda z:z.get("x",-1)).get("text")
tr=[]
for r in csv.DictReader(open(D/"results/l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    if not any(s['start']<=t<=s['end'] for s in segs): continue
    R=round(float(r["letrun_struct"])-COST,2)
    d_i=rf(bi) or {};d_s=rf(bi-1) or {}   # rsi no bar i; repaint-features com SHIFT1 (i-1)
    tr.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"R":R,"win":R>0,"yr":y,
               "rsi":d_i.get("rsi"),
               "bub_sell":has_bubble(d_s,SELL),"bub_buy":has_bubble(d_s,BUY),
               "nas_last":nas_last(d_s)})
W=[x for x in tr if x["win"]];Lz=[x for x in tr if not x["win"]]
import statistics as st
print(f"RANGE-trades 2023+: {len(tr)} ({len(W)}W/{len(Lz)}L) | sumR base {sum(x['R'] for x in tr):+.1f}")
print("\n### CARACTERIZAÇÃO (média WIN vs LOSS — exploratório, nao teste) ###")
rw=[x['rsi'] for x in W if x['rsi'] is not None];rl=[x['rsi'] for x in Lz if x['rsi'] is not None]
print(f"  rsi          WIN {st.mean(rw):+6.1f}  vs LOSS {st.mean(rl):+6.1f}")
for k,lab in [("bub_sell","bubble_SELL recente"),("bub_buy","bubble_BUY recente")]:
    ww=100*sum(1 for x in W if x[k])/len(W);ll=100*sum(1 for x in Lz if x[k])/len(Lz)
    print(f"  {lab:22} WIN {ww:4.0f}% vs LOSS {ll:4.0f}%")
for txt in ("LONG","SHORT"):
    ww=100*sum(1 for x in W if x['nas_last']==txt)/len(W);ll=100*sum(1 for x in Lz if x['nas_last']==txt)/len(Lz)
    print(f"  nas_last={txt:5}          WIN {ww:4.0f}% vs LOSS {ll:4.0f}%")
def curve(rs):
    rs=sorted(rs,key=lambda x:x["bi"]);n=len(rs)
    if not n: return (0,0,0,0)
    s=sum(x["R"] for x in rs);w=sum(1 for x in rs if x["win"]);cum=peak=dd=0
    for x in rs: cum+=x["R"];peak=max(peak,cum);dd=min(dd,cum-peak)
    return (n,100*w/n,s,dd)
def show(nm,rs):
    n,wr,s,dd=curve(rs);print(f"  {nm:34} N={n:2} WR={wr:3.0f}% sumR={s:+6.1f} DD={dd:6.1f}")
# regras candidatas (grid pre-registrado, honestas sobre a escolha)
rules={}
for thr in (45,50,55,60,65):
    rules[f"skip rsi>={thr}"]=[x for x in tr if not (x['rsi'] is not None and x['rsi']>=thr)]
rules["skip !bub_sell (so absorcao-fundo)"]=[x for x in tr if x['bub_sell']]
rules["skip nas_last==SHORT"]=[x for x in tr if x['nas_last']!="SHORT"]
rules["keep rsi<55 & bub_sell"]=[x for x in tr if (x['rsi'] is not None and x['rsi']<55) and x['bub_sell']]
print("\n### REGRAS CANDIDATAS (let-run canonico) ###")
show("BASE (sem filtro)",tr)
for nm,rs in rules.items(): show(nm,rs)
# permutation-null-of-max: o melhor sumR entre as regras bate o ruido?
def best_sum(Rmap):
    best=-1e9
    for rs in rules.values():
        s=sum(Rmap[x["bi"]] for x in rs)
        best=max(best,s)
    return best
obs_best=best_sum({x["bi"]:x["R"] for x in tr})
Rs=[x["R"] for x in tr];bis=[x["bi"] for x in tr]
ge=0;ND=400
for _ in range(ND):
    sh=Rs[:];random.shuffle(sh);Rmap=dict(zip(bis,sh))
    if best_sum(Rmap)>=obs_best: ge+=1
print(f"\n### PERMUTATION-NULL-OF-MAX ({ND} draws) ###")
print(f"  melhor sumR observado entre regras = {obs_best:+.1f}")
print(f"  P(null best-rule >= observado) = {ge/ND:.3f}   ({'NAO passa (overfit/ruido)' if ge/ND>0.10 else 'passa'})")
# por-ano da melhor regra RSI (robustez)
best_name=max(rules,key=lambda k:sum(x["R"] for x in rules[k]))
print(f"\n### melhor regra = '{best_name}' — por ano vs base ###")
for y in (2023,2024,2025,2026):
    b=[x for x in tr if x['yr']==y];f=[x for x in rules[best_name] if x['yr']==y]
    print(f"  {y}: base sumR {sum(x['R'] for x in b):+6.1f} (n{len(b)}) -> filtro {sum(x['R'] for x in f):+6.1f} (n{len(f)})")
