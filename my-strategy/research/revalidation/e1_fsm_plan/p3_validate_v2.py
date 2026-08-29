#!/usr/bin/env python3
"""P3 v2 — Nos 13 momentos-âncora dos ENTRY_LIMITs do Cris: os pools causais (lm_pools) produzem o
nível? BUY→pools SSL (topo=limit); SELL→pools BSL (fundo=limit). Hit=|nível_pool − nível_Cris|<=0.5ATR.
Null: mesmos testes em 100 âncoras aleatórias da mesma semana. Caso-a-caso. py3 stdlib."""
import json, sys, random, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/"my-strategy/core")); sys.path.insert(0,str(REPO/"alert-bridge"))
import lm_pools as LP, liquidity_map as LM
LX=dt.timezone(dt.timedelta(hours=1))
def jl(p):
    try: return [json.loads(l) for l in open(p) if l.strip()]
    except: return []
store=sorted(jl(REPO/"my-strategy/core/bar_store/store/bars_15m.jsonl"),key=lambda x:x["t"])
gt=json.load(open(HERE/"ground_truth_v2.json"))
def probe(t,side,level):
    upto=[b for b in store if b["t"]<=t][-450:]
    if len(upto)<120: return None,None
    atr=LM._atr(upto[-400:])
    pools=LP.pools_asof(upto,side="SSL" if side=="BUY" else "BSL")
    if not pools: return None,atr
    edge=lambda p: p["hi"] if side=="BUY" else p["lo"]
    best=min(pools,key=lambda p:abs(edge(p)-level))
    return (abs(edge(best)-level),best,edge(best)),atr
def hm(t): return dt.datetime.fromtimestamp(t,LX).strftime('%d/%m %H:%M')
print(f"{'limit':<6}{'âncora':<13}{'nível':>8}  pool causal mais próximo")
hit=tot=0
for l in sorted(gt["limits"],key=lambda x:x["anchor_t"]):
    r,atr=probe(l["anchor_t"],l["side"],l["level"])
    if r is None: print(f"{l['side']:<6}{hm(l['anchor_t']):<13}{l['level']:>8.1f}  SEM-DADOS"); continue
    d,best,e=r; tot+=1; ok=d<=0.5*atr; hit+=ok
    print(f"{l['side']:<6}{hm(l['anchor_t']):<13}{l['level']:>8.1f}  {e:.1f} (dist {d:.1f} = {d/atr:.2f}ATR) "
          f"{'HIT' if ok else 'miss'} [{best['status']},resp={best['respected_left']}]")
print(f"\nCASOS: {hit}/{tot} ({100*hit//max(tot,1)}%)")
# null: 100 ancoras aleatorias da mesma semana, side aleatorio, nivel = pool? nao — nivel do null deve
# ser um preco de referencia neutro: usamos o CLOSE da barra aleatoria como "nivel" pedido
rnd=random.Random(20260829)
W0=dt.datetime(2026,8,21,tzinfo=dt.timezone.utc).timestamp()
week=[b for b in store if b["t"]>=W0]
nh=ntot=0
for _ in range(100):
    b=rnd.choice(week); side=rnd.choice(["BUY","SELL"])
    r,atr=probe(b["t"],side,b["c"])
    if r is None: continue
    d,_,_=r; ntot+=1; nh+=(d<=0.5*atr)
print(f"NULL (100 âncoras aleatórias, nível=close): {nh}/{ntot} ({100*nh//max(ntot,1)}%)")
