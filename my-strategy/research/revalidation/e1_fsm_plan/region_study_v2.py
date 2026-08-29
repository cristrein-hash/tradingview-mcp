#!/usr/bin/env python3
"""ESTUDO DE REGIÃO v2 — convergência de TODOS os indicadores por área (ordem Cris 29/08).
Por região de limit: toques 5M respeitados + sessão + OB v11 + SMC zone/EQH + HTF PO3 + BOLHAS
(agressão no instante dos toques: bolha em t cuja barra 5M tocou o nível) + NAS. Caveat declarado:
zonas OB/SMC = snapshot ATUAL do store (podem ter mudado durante a semana). py3 stdlib."""
import json, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); HERE=Path(__file__).resolve().parent
S=REPO/"my-strategy/core/bar_store/store"
LX=dt.timezone(dt.timedelta(hours=1)); TOL=3.0; D3=3*86400
def jl(p):
    try: return [json.loads(l) for l in open(p) if l.strip()]
    except: return []
b5=sorted(jl(S/"bars_5m.jsonl"),key=lambda x:x["t"])
gt=json.load(open(HERE/"ground_truth_v2.json"))
def zones_of(fname,names):
    d=json.load(open(S/fname)).get('data') or {}
    out=[]
    for st in d.get('studies') or []:
        if any(n in (st.get('name') or '') for n in names):
            out+= [(z['low'],z['high']) for z in (st.get('zones') or []) if z.get('low') is not None]
    return out
ob=zones_of("pine_boxes_15.json",["OB Detector"])
smcz=zones_of("pine_boxes_15.json",["Smart Money"])
po3=zones_of("pine_boxes_15.json",["Power of Three"])
smc=json.load(open(S/"smc_labels_15.json")).get('data') or {}
eq=[(l['price'],l['text']) for st in (smc.get('studies') or []) for l in (st.get('labels') or [])
    if str(l.get('text','')).upper().startswith(('EQH','EQL'))]
bub={r['t'] for r in jl(S/"bubbles_15m.jsonl")}
nas={r['t'] for r in jl(S/"nas_15m.jsonl")}
def hm(t): return dt.datetime.fromtimestamp(t,LX).strftime('%d/%m %H:%M')
def near_zone(lv,zs): return any(z[0]-TOL<=lv<=z[1]+TOL for z in zs)
print(f"{'limit':<6}{'nível':>8}  convergências na REGIÃO (±3pt)")
summary=[]
for l in sorted(gt["limits"],key=lambda x:x["anchor_t"]):
    ta,lv,side=l["anchor_t"],l["level"],l["side"]
    conv=[]
    # toques respeitados (do estudo v1)
    t5=[x for x in b5 if ta-D3<=x["t"]<ta and abs((x["l"] if side=="BUY" else x["h"])-lv)<=TOL]
    resp=[x for x in t5 if not ((x["c"]<lv-TOL) if side=="BUY" else (x["c"]>lv+TOL))]
    if len(resp)>=3: conv.append(f"toques5M={len(resp)}")
    # bolhas nos instantes dos toques (agressão no nível)
    bt=sum(1 for x in resp for k in (x["t"], x["t"]-x["t"]%900) if k in bub)
    if bt: conv.append(f"BOLHAS@toques={bt}")
    if near_zone(lv,ob): conv.append("OB_v11")
    if near_zone(lv,smcz): conv.append("SMC_zone")
    if any(abs(p-lv)<=TOL for p,_ in eq): conv.append("EQH/EQL")
    if any(abs(lv-z[0])<=TOL or abs(lv-z[1])<=TOL for z in po3): conv.append("PO3_edge")
    # nas no toque
    nt=sum(1 for x in resp if (x["t"]-x["t"]%900) in nas)
    if nt: conv.append(f"NAS@toques={nt}")
    summary.append((side,lv,len(conv),conv))
    print(f"{side:<6}{lv:>8.1f}  [{len(conv)}] {' + '.join(conv) if conv else '(só projeção/HTF)'}")
from collections import Counter
c=Counter(x for _,_,_,cv in summary for x in cv if '=' not in x)
c2=Counter(x.split('=')[0] for _,_,_,cv in summary for x in cv if '=' in x)
print("\nfatores mais frequentes:",dict(c),dict(c2))
print("convergência mediana:",sorted(n for _,_,n,_ in summary)[len(summary)//2],"fatores/região")
