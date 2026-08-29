#!/usr/bin/env python3
"""P1 v3 — FIDELIDADE: nas 13 âncoras do Cris, o lm_regions produz uma região VÁLIDA do lado certo a
<=TOL do nível dele? + NULL com níveis AFASTADOS (>=15pt de qualquer região do Cris) em instantes
aleatórios. Caso-a-caso. py3 stdlib."""
import json, sys, random, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/"alert-bridge"))
import lm_regions as LR
LX=dt.timezone(dt.timedelta(hours=1))
def jl(p):
    try: return [json.loads(l) for l in open(p) if l.strip()]
    except: return []
S=REPO/"my-strategy/core/bar_store/store"
b5=sorted(jl(S/"bars_5m.jsonl"),key=lambda x:x["t"])
b15=sorted(jl(S/"bars_15m.jsonl"),key=lambda x:x["t"])
gt=json.load(open(HERE/"ground_truth_v2.json"))
def hm(t): return dt.datetime.fromtimestamp(t,LX).strftime('%d/%m %H:%M')
def probe(t,px):
    c5=[x for x in b5 if x["t"]<=t]; c15=[x for x in b15 if x["t"]<=t]
    if len(c5)<200: return None
    return LR.regions_at(c5,c15,t,px)
print(f"{'limit':<6}{'âncora':<13}{'nível':>8}  região do lm_regions")
hit=tot=0
for l in sorted(gt["limits"],key=lambda x:x["anchor_t"]):
    ta,lv,side=l["anchor_t"],l["level"],l["side"]
    # preço no instante da âncora
    pxbar=next((x for x in reversed(b5) if x["t"]<=ta),None)
    if not pxbar: continue
    rs=probe(ta,pxbar["c"])
    if rs is None:
        print(f"{side:<6}{hm(ta):<13}{lv:>8.1f}  SEM-DADOS"); continue
    tot+=1
    match=[r for r in rs if r["side"]==side and abs(r["level"]-lv)<=LR.TOL]
    if match:
        hit+=1; m=match[0]
        print(f"{side:<6}{hm(ta):<13}{lv:>8.1f}  HIT {m['level']} score{m['score']} {m['factors']}")
    else:
        same=[r for r in rs if r["side"]==side]
        near=min(same,key=lambda r:abs(r["level"]-lv)) if same else None
        print(f"{side:<6}{hm(ta):<13}{lv:>8.1f}  miss ({len(same)} regiões {side}; mais perto {near['level'] if near else '—'} a {abs(near['level']-lv):.1f}pt)" if near else f"{side:<6}{hm(ta):<13}{lv:>8.1f}  miss (0 regiões {side})")
print(f"\nFIDELIDADE: {hit}/{tot} ({100*hit//max(tot,1)}%)")
# NULL: instantes aleatorios da semana; nivel de teste = preco +- offset aleatorio 15-40pt AFASTADO das regioes do Cris
rnd=random.Random(20260829)
gtlv=[l["level"] for l in gt["limits"]]
W0=dt.datetime(2026,8,24,tzinfo=dt.timezone.utc).timestamp()
week=[x for x in b5 if x["t"]>=W0]
nh=ntot=0
for _ in range(60):
    x=rnd.choice(week); off=rnd.choice([-1,1])*rnd.uniform(15,40)
    lv=x["c"]+off; side="SELL" if off>0 else "BUY"
    if any(abs(lv-g)<=8 for g in gtlv): continue          # afastado das regioes reais
    rs=probe(x["t"],x["c"])
    if rs is None: continue
    ntot+=1
    if any(r["side"]==side and abs(r["level"]-lv)<=LR.TOL for r in rs): nh+=1
print(f"NULL (níveis afastados, {ntot} sondas): {nh}/{ntot} ({100*nh//max(ntot,1)}%)")
