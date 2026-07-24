#!/usr/bin/env python3
"""CRUZAMENTO PROFUNDO (Cris 2026-07-24): reconstrói TODAS as features estruturais/fluxo/momentum para cada um dos
61 sinais (motor antigo) + 7 winners (Cris) a partir do store, cruza com o desfecho, e agrega macro/news como
backdrop. Multi-fatorial + trajetória + duplo-objetivo (WR E MFE/MAE) — não eixo único (PRINCIPAL_3).
DIAGNÓSTICO in-sample (N pequeno, verd dos 61 = proxy-MFE sem SL/TP fixo, 7 = reais) — NÃO é validação de edge.
Fontes 100% locais/live: bars_5m/15m, bubbles_15m, nas_15m, latest.json (macro), news_feed. py3.9."""
import json, datetime as dt, statistics as st
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon"); UTC = dt.timezone.utc
S = "my-strategy/core/bar_store/store/"
def jl(p):
    try: return [json.loads(x) for x in open(p) if x.strip()]
    except Exception: return []
b5 = sorted(jl(S+"bars_5m.jsonl"), key=lambda x:x["t"])
b15 = sorted(jl(S+"bars_15m.jsonl"), key=lambda x:x["t"])
bub = jl(S+"bubbles_15m.jsonl"); nas = jl(S+"nas_15m.jsonl")
BUB_BUY={"plot_0":1,"plot_2":2,"plot_4":3}; BUB_SELL={"plot_6":1,"plot_8":2,"plot_10":3}
NAS_MAP={"plot_0":"LONG","plot_1":"SHORT"}

def resample_1h(b):
    bk={}
    for x in b:
        k=(x["t"]//3600)*3600; d=bk.setdefault(k,{"t":k,"o":x["o"],"h":x["h"],"l":x["l"],"c":x["c"]})
        d["h"]=max(d["h"],x["h"]); d["l"]=min(d["l"],x["l"]); d["c"]=x["c"]
    return [bk[k] for k in sorted(bk)]
b1h=resample_1h(b15)

def ema(v,n):
    k=2/(n+1); e=v[0]
    for x in v[1:]: e=x*k+e*(1-k)
    return e
def rsi(cl,n=14):
    if len(cl)<n+1: return None
    g=l=0.0
    for i in range(-n,0):
        d=cl[i]-cl[i-1]; g+=max(d,0); l+=max(-d,0)
    if l==0: return 100.0
    return 100-100/(1+(g/n)/(l/n))
def dmi(bars,n=14):
    if len(bars)<n+2: return None,None
    tp=pdm=ndm=0.0
    for i in range(-n,0):
        up=bars[i]["h"]-bars[i-1]["h"]; dn=bars[i-1]["l"]-bars[i]["l"]
        pdm+=up if (up>dn and up>0) else 0; ndm+=dn if (dn>up and dn>0) else 0
        tr=max(bars[i]["h"]-bars[i]["l"],abs(bars[i]["h"]-bars[i-1]["c"]),abs(bars[i]["l"]-bars[i-1]["c"])); tp+=tr
    if tp==0: return None,None
    return round(100*pdm/tp,1),round(100*ndm/tp,1)
def pivots(bars,k=2):
    hi,lo=[],[]
    for i in range(k,len(bars)-k):
        w=bars[i-k:i]+bars[i+1:i+1+k]
        if bars[i]["h"]>max(x["h"] for x in w): hi.append(i)
        if bars[i]["l"]<min(x["l"] for x in w): lo.append(i)
    return hi,lo

def feat(ts, dirn):
    """vetor de features no instante ts (perna/EMA/RSI/DMI/fluxo/sessão) — TRAJETÓRIA, não snapshot."""
    h1=[b for b in b1h if b["t"]<=ts]; b15t=[b for b in b15 if b["t"]<=ts]
    f={}
    if len(h1)<8 or len(b15t)<22: return None
    hi,lo=pivots(h1,2)
    pb="up" if (lo and (not hi or lo[-1]>hi[-1])) else "down"
    cl=[b["c"] for b in b15t]; e9,e21,e50=ema(cl,9),ema(cl,21),ema(cl,50); px=cl[-1]
    ec="up" if px>e21 else "down"
    net=h1[-1]["c"]-h1[max(0,len(h1)-20)]["c"]; dom="up" if net>0 else "down"
    leg="BULL" if (pb=="up" and ec=="up") else ("BEAR" if (pb=="down" and ec=="down") else ("BULL" if dom=="up" else "BEAR"))
    f["leg"]=leg
    # alinhamento perna×trade
    wl=(dirn=="LONG" and leg=="BULL") or (dirn=="SHORT" and leg=="BEAR")
    f["align"]="COM-perna" if wl else "CONTRA-perna"
    f["ema_pos"]="acima" if px>e21 else "abaixo"; f["ema_dist_atr"]=round((px-e21),1)
    r=rsi(cl); rmm=rsi(cl[:-1]) if len(cl)>15 else None
    f["rsi"]=round(r,0) if r else None
    f["rsi_side"]=("bull" if r and r>50 else "bear") if r else "?"
    pdi,ndi=dmi(b15t); f["di"]=("+DI" if (pdi and ndi and pdi>ndi) else "-DI") if pdi else "?"
    f["di_align"]=(dirn=="LONG" and f["di"]=="+DI") or (dirn=="SHORT" and f["di"]=="-DI")
    # fluxo bubbles janela ±90min
    lo_t,hi_t=ts-5400,ts+300; bb=sb=0
    for r0 in bub:
        if lo_t<=r0.get("t",0)<=hi_t:
            p=r0.get("plot"); bb+=BUB_BUY.get(p,0); sb+=BUB_SELL.get(p,0)
    f["bub_buy"]=bb; f["bub_sell"]=sb
    f["flow_side"]="buy" if bb>sb else ("sell" if sb>bb else "flat")
    f["flow_align"]=(dirn=="LONG" and bb>sb) or (dirn=="SHORT" and sb>bb)
    # nas recente ±90min
    nn=[NAS_MAP[r0["plot"]] for r0 in nas if lo_t<=r0.get("t",0)<=hi_t and r0.get("plot") in NAS_MAP]
    f["nas"]=nn[-1] if nn else "-"; f["nas_align"]=(f["nas"]==dirn)
    # sessão (hora UTC)
    hr=dt.datetime.fromtimestamp(ts,UTC).hour
    f["sess"]=("asia" if 0<=hr<6 else "london" if 6<=hr<12 else "ny" if 12<=hr<20 else "late")
    return f

# ---- eventos: 61 sinais + 7 winners ----
sig=json.load(open("research/groundtruth_20260723/signals_measured.json"))
EV=[]
for s in sig:
    EV.append({"src":"sig61","dir":s["dir"],"ts":s["ts"],"q":s["q"],"mode":s["mode"],
               "verd":s["verd"],"mfe":s["mfe"],"mae":s["mae"],
               "win":1 if s["verd"] in ("WIN","ok") else 0})
# 7 winners (extraídos do MCP no cruzamento anterior; ts Lisboa→epoch)
W=[("LONG",4010.21,"2026-07-21 00:00"),("LONG",4036.39,"2026-07-24 07:15"),("LONG",4048.95,"2026-07-24 12:30"),
   ("LONG",4053.43,"2026-07-21 14:45"),("LONG",4078.13,"2026-07-21 23:00"),("SHORT",4092.86,"2026-07-23 11:30"),
   ("SHORT",4127.39,"2026-07-23 03:45")]
for d,e,tstr in W:
    ts=int(dt.datetime.strptime(tstr,"%Y-%m-%d %H:%M").replace(tzinfo=LX).timestamp())
    EV.append({"src":"win7","dir":d,"ts":ts,"q":"MASTER","mode":"master","verd":"WIN","mfe":None,"mae":None,"win":1})

for e in EV: e["f"]=feat(e["ts"],e["dir"])
EV=[e for e in EV if e["f"]]

def wr(rows):
    n=len(rows); w=sum(r["win"] for r in rows)
    return n,w,(100*w//n if n else 0)
def tab(name, keyfn, universe=None):
    rows=universe if universe is not None else EV
    print(f"\n── {name} ──")
    groups={}
    for r in rows: groups.setdefault(keyfn(r),[]).append(r)
    for k in sorted(groups, key=lambda k:-wr(groups[k])[2]):
        n,w,p=wr(groups[k])
        mfes=[r["mfe"] for r in groups[k] if r.get("mfe") is not None]
        mm=f" · MFE méd {round(st.mean(mfes),1)}" if mfes else ""
        print(f"   {str(k):16} N={n:2} · WIN {w} ({p}%){mm}")

print("="*70)
print("CRUZAMENTO PROFUNDO — 61 sinais (motor antigo) + 7 winners (Cris)")
print(f"Total eventos com features reconstruídas: {len(EV)}")
print("="*70)

# BACKDROP macro (constante na semana?)
mac=json.load(open("external_factors_v2/snapshots/latest.json")).get("tier1_macro_recorded_context",{})
print(f"\n[BACKDROP MACRO — constante na semana] real_yield {mac.get('us10y_real',{}).get('value')} · "
      f"DXY {mac.get('usd_broad',{}).get('value')} · VIX {mac.get('vix',{}).get('value')} · "
      f"oil {mac.get('wti_oil',{}).get('value')} (chg20 +{mac.get('wti_oil',{}).get('chg20')}) — "
      f"mesmo regime todos os 68 eventos → NÃO diferencia winner/loser DENTRO da semana.")

# EIXO CENTRAL: alinhamento perna
tab("★ ALINHAMENTO PERNA 1H × desfecho (o eixo central)", lambda r:r["f"]["align"])
tab("   ↳ só os 61 sinais do motor antigo", lambda r:r["f"]["align"], [e for e in EV if e["src"]=="sig61"])
tab("   ↳ só os 7 winners (perfil)", lambda r:r["f"]["align"], [e for e in EV if e["src"]=="win7"])
# rótulo antigo vs desfecho (a inversão)
tab("Q antigo (FORTE/FRACO) × desfecho", lambda r:r["q"])
tab("modo antigo × desfecho", lambda r:r["mode"])
# fatores estruturais/fluxo/momentum
tab("EMA pos (px vs EMA21 15M) × desfecho", lambda r:r["f"]["ema_pos"])
tab("fluxo bubbles alinhado ao trade × desfecho", lambda r:"flow COM" if r["f"]["flow_align"] else "flow contra/flat")
tab("DMI (+DI/-DI) alinhado × desfecho", lambda r:"DI COM" if r["f"]["di_align"] else "DI contra")
tab("RSI side alinhado × desfecho", lambda r:"RSI COM" if ((r["dir"]=="LONG")==(r["f"]["rsi_side"]=="bull")) else "RSI contra")
tab("NAS alinhado × desfecho", lambda r:"NAS COM" if r["f"]["nas_align"] else ("NAS -" if r["f"]["nas"]=="-" else "NAS contra"))
tab("sessão × desfecho", lambda r:r["f"]["sess"])
tab("direção × desfecho", lambda r:r["dir"])

# CONVERGÊNCIA multi-fatorial (nº de confluências COM o trade)
def conv(r):
    f=r["f"]; c=0
    c+=(f["align"]=="COM-perna"); c+=f["flow_align"]; c+=f["di_align"]
    c+=((r["dir"]=="LONG")==(f["rsi_side"]=="bull")); c+=f["nas_align"]
    return c
tab("CONVERGÊNCIA (nº de 5 fatores COM o trade: perna+fluxo+DI+RSI+NAS)", lambda r:f"{conv(r)}/5")
print("\n" + "="*70)
