#!/usr/bin/env python3
"""ESTUDO DE REGIÃO (ordem Cris 29/08): cada região de ENTRY_LIMIT estudada A FUNDO com 5M+15M
cruzados — CONTEXTO da região, não snapshot da vela. SEM ATR como régua (distâncias em PONTOS).
Por região: (a) história de toques 5M/15M no nível (±3pt) nos 3 dias antes da âncora — quando tocou,
wick exato, respeitou ou furou; (b) extremos de sessão (Asia 00-08, London 08-13, NY 13-21 Lisboa)
dos 2 dias antes que coincidem com o nível (±3pt); (c) posição do nível no range dos últimos 2 dias;
(d) da âncora ao fill: quanto tempo, quantos toques. Materializado. py3 stdlib."""
import json, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); HERE=Path(__file__).resolve().parent
LX=dt.timezone(dt.timedelta(hours=1))
def jl(p):
    try: return [json.loads(l) for l in open(p) if l.strip()]
    except: return []
b5=sorted(jl(REPO/"my-strategy/core/bar_store/store/bars_5m.jsonl"),key=lambda x:x["t"])
b15=sorted(jl(REPO/"my-strategy/core/bar_store/store/bars_15m.jsonl"),key=lambda x:x["t"])
gt=json.load(open(HERE/"ground_truth_v2.json"))
TOL=3.0; D3=3*86400
def hm(t): return dt.datetime.fromtimestamp(t,LX).strftime('%d/%m %H:%M')
def sess_of(t):
    h=dt.datetime.fromtimestamp(t,LX).hour
    return "ASIA" if h<8 else ("LONDON" if h<13 else "NY")
def touches(bars,level,t0,t1,side):
    out=[]
    for x in bars:
        if not(t0<=x["t"]<t1): continue
        wick = x["l"] if side=="BUY" else x["h"]
        if abs(wick-level)<=TOL:
            pierced = (x["l"]<level-TOL) if side=="BUY" else (x["h"]>level+TOL)
            closed_beyond = (x["c"]<level-TOL) if side=="BUY" else (x["c"]>level+TOL)
            out.append(dict(t=x["t"],wick=round(wick,1),pierced=pierced,closed_beyond=closed_beyond))
    return out
def sess_extremes(t_anchor):
    """extremos por sessão dos 2 dias antes da âncora (5M)."""
    out=[]
    start=t_anchor-2*86400
    cur=None
    for x in b5:
        if not(start<=x["t"]<t_anchor): continue
        d=dt.datetime.fromtimestamp(x["t"],LX); key=(d.date(),sess_of(x["t"]))
        if cur is None or cur[0]!=key:
            if cur: out.append(cur)
            cur=[key,x["h"],x["l"]]
        else:
            cur[1]=max(cur[1],x["h"]); cur[2]=min(cur[2],x["l"])
    if cur: out.append(cur)
    return out
print("="*100)
for l in sorted(gt["limits"],key=lambda x:x["anchor_t"]):
    ta,lv,side=l["anchor_t"],l["level"],l["side"]
    t5=touches(b5,lv,ta-D3,ta,side); t15=touches(b15,lv,ta-D3,ta,side)
    resp5=sum(1 for x in t5 if not x["closed_beyond"]); fur5=sum(1 for x in t5 if x["closed_beyond"])
    se=[s for s in sess_extremes(ta) if abs(s[1]-lv)<=TOL or abs(s[2]-lv)<=TOL]
    # range 2d e posicao do nivel
    w2=[x for x in b15 if ta-2*86400<=x["t"]<ta]
    hi2=max(x["h"] for x in w2); lo2=min(x["l"] for x in w2)
    pos=round(100*(lv-lo2)/(hi2-lo2)) if hi2>lo2 else 50
    # da ancora ao 1o toque do nivel (fill)
    fill=next((x for x in b5 if x["t"]>ta and ((x["l"]<=lv) if side=="BUY" else (x["h"]>=lv))),None)
    lag=round((fill["t"]-ta)/3600,1) if fill else None
    print(f"{side} {lv:.1f} · âncora {hm(ta)} [{sess_of(ta)}] · nível a {pos}% do range-2d")
    print(f"  toques prévios 3d: 5M={len(t5)} ({resp5} respeitos, {fur5} furos-com-fecho) · 15M={len(t15)}")
    if se:
        for s in se[:3]:
            lbl="HIGH" if abs(s[1]-lv)<=TOL else "LOW"
            print(f"  = extremo de sessão: {s[0][1]} {s[0][0].strftime('%d/%m')} {lbl} ({(s[1] if lbl=='HIGH' else s[2]):.1f})")
    else:
        print(f"  (não coincide com extremo de sessão ±{TOL}pt)")
    print(f"  fill: {'+'+str(lag)+'h após âncora' if lag else 'não tocado'}")
    print("-"*100)
