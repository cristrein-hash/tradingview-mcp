#!/usr/bin/env python3
"""Features ORTOGONAIS NOVAS (mapa scout) sobre trades 8ATR, p/ lapidar R2. Causal (bubbles known_at<=tc, series barras fechadas).
Eixos: vol_absorption (volume real no fundo), sell_decel (derivada temporal da venda), flow_accel (2a deriv),
smc_flow_lag (estrutura→fluxo), bubble_silence, buy_takeover (cross SELL->BUY), regime_age_h (idade regime 4H),
flow_skew_mig (migração tamanho), session_phase. Junta r2_keep de dataset_8atr.jsonl. Emite dataset_r2refine.jsonl."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]
# transições de regime 4H (causal): lista (t_end, macro)
TRANS=[]; prev=None
for b in MR:
    if b["macro"]!=prev: TRANS.append(b["t_end"]); prev=b["macro"]
def regime_age_h(t):
    k=bisect.bisect_right(TRANS,t)-1
    return (t-TRANS[k])/3600 if k>=0 else 0
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
SZ={"S":1,"M":2,"L":3}; HMAX=480; RCAP=20.0
# join r2_keep
D8={}
for l in (HERE/"dataset_8atr.jsonl").read_text().splitlines():
    r=json.loads(l); D8[(r["block"],r["low_t"])]=r
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,ei,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl;r1=False;ex=None;end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if s[i]["l"]<=trail: ex=trail;break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def known_bubbles(bub,bt,t0,t1,tc):
    a=bisect.bisect_left(bt,t0); b=bisect.bisect_right(bt,t1)
    return [x for x in bub[a:b] if (x.get("known_at") or x["t"])<=tc]
def feats(s,i,cj,bub,bt,nas,smc):
    tc=s[cj]["t"]; atr=s[cj]["atr"] or 1.0; f={}
    # vol_absorption: volume real no/perto do low + closepos do low bar + barras desde o menor low
    v50=[s[b].get("v",0) for b in range(max(0,cj-50),cj+1)]; med=st.median(v50) if v50 else 1
    lb=s[i]; lrng=max(lb["h"]-lb["l"],1e-9)
    f["low_vol_rel"]=round((lb.get("v",0)/med),2) if med>0 else 1
    f["low_closepos"]=round((lb["c"]-lb["l"])/lrng,2)
    seg=s[max(0,i-12):i+1]; mlow=min(b["l"] for b in seg)
    f["bars_since_lowest"]=cj-max(b for b in range(max(0,i-12),i+1) if s[b]["l"]==mlow)
    f["absorption"]=1 if (f["low_vol_rel"]>=1.2 and f["low_closepos"]>=0.66) else 0
    # sell_decel (24 barras, 2 semi-janelas) + flow_accel (3 terços)
    t0=s[max(0,i-24)]["t"]; sells=[x for x in known_bubbles(bub,bt,t0,tc,tc) if x["side"]=="SELL"]
    def wsum(lst): return sum(SZ[x["size"]] for x in lst)
    half=(t0+tc)//2; old=wsum([x for x in sells if x["t"]<half]); rec=wsum([x for x in sells if x["t"]>=half])
    f["sell_decel"]=round((old-rec)/(old+1e-6),2)
    th=[t0+(tc-t0)*q/3 for q in (1,2,3)]
    w3=[wsum([x for x in sells if (th[q-1] if q>0 else t0)<=x["t"]<th[q]]) for q in range(1,3+1) if True]
    w3=[wsum([x for x in sells if (t0 if q==0 else th[q-1])<=x["t"]<th[q]]) for q in range(3)]
    f["flow_accel"]=round((w3[0]-w3[1])-(w3[1]-w3[2]),2)  # 2a derivada (curvatura)
    last_sell=max((x["t"] for x in sells),default=None)
    f["bars_since_sell"]=round((tc-last_sell)/900) if last_sell else 99
    # buy_takeover (cross rolling-4 buy>sell)
    allb=known_bubbles(bub,bt,s[max(0,i-20)]["t"],tc,tc)
    by_bar={}
    for x in allb: by_bar.setdefault(x["t"]//900,{"b":0,"s":0}); by_bar[x["t"]//900]["b" if x["side"]=="BUY" else "s"]+=SZ[x["size"]]
    bars=sorted(by_bar); cross=None
    for bi in range(3,len(bars)):
        rb=sum(by_bar[bars[q]]["b"] for q in range(bi-3,bi+1)); rs=sum(by_bar[bars[q]]["s"] for q in range(bi-3,bi+1))
        if rb>rs: cross=bars[bi]; break
    f["bars_since_buycross"]=round((tc//900-cross)) if cross else 99
    r4b=sum(by_bar[k]["b"] for k in bars[-4:]) if bars else 0; r4s=sum(by_bar[k]["s"] for k in bars[-4:]) if bars else 0
    f["buy_sell_ratio4"]=round(r4b/(r4s+1),2)
    # bubble_silence (maior run sem bubble nas ult 20 barras)
    present=set(x["t"]//900 for x in allb); run=mx=0
    for bb in range(i-20,i+1):
        if bb<0: continue
        if bb in present: run=0
        else: run+=1; mx=max(mx,run)
    f["max_silence"]=mx
    # smc_flow_lag (estrutura bull -> fluxo)
    bull_smc=[e for e in smc if e.get("t") and e["t"]<=tc and ("BOS" in str(e.get("text","")) or "CHoCH" in str(e.get("text","")))]
    if bull_smc:
        ev=max(bull_smc,key=lambda e:e["t"]); f["smc_lag_bars"]=round((tc-ev["t"])/900)
        f["buy_after_smc"]=1 if any(x["side"]=="BUY" and x["t"]>ev["t"] for x in allb) else 0
        f["naslong_after_smc"]=1 if any(e["dir"]=="LONG" and e["t"]>ev["t"] and e["t"]<=tc for e in nas) else 0
    else: f["smc_lag_bars"]=999; f["buy_after_smc"]=0; f["naslong_after_smc"]=0
    # flow_skew_mig (SELL L/(S+1) 1a vs 2a metade)
    s_old=[x for x in sells if x["t"]<half]; s_rec=[x for x in sells if x["t"]>=half]
    def skew(lst): L=sum(1 for x in lst if x["size"]=="L"); S=sum(1 for x in lst if x["size"]=="S"); return L/(S+1)
    f["sell_skew_mig"]=round(skew(s_old)-skew(s_rec),2)  # >0 = afinando L->S (exaustão)
    f["buy_L_recent"]=1 if any(x["side"]=="BUY" and x["size"]=="L" for x in s_rec) or any(x["side"]=="BUY" and x["size"]=="L" and x["t"]>=half for x in allb) else 0
    # regime_age + session
    f["regime_age_h"]=round(regime_age_h(tc),1)
    hh=dt.datetime.utcfromtimestamp(tc).hour
    f["is_london_open"]=1 if 7<=hh<10 else 0; f["is_ny_overlap"]=1 if 12<=hh<16 else 0; f["is_deadzone"]=1 if (hh<7 or hh>=20) else 0
    return f
out=open(HERE/"dataset_r2refine.jsonl","w"); n=0; kept=0
for k,pr in PRIM.items():
    s=pr["series"]; nn=len(s); L=[x["l"] for x in s]; bub=BUB[k]; bt=[x["t"] for x in bub]
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); smc=pr["smc_events"]
    for i in range(96,nn-4):
        atr=s[i]["atr"]
        if not atr or L[i]!=min(L[i-4:i+5]): continue
        cj=None
        for q in range(i+1,min(i+HMAX,nn-2)):
            if s[q]["h"]>=s[i]["l"]+8*atr: cj=q; break
        if cj is None or cj+2>=nn: continue
        entry=s[cj]["c"]; sl=min(x["l"] for x in s[i:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
        if R is None: continue
        d8=D8.get((k[:10],s[i]["t"]))
        if not d8: continue
        h1e=d8.get("h1_eff"); h4p=d8.get("h4_pos")
        r2_keep=0 if (h1e is not None and h1e<0.20 and h4p is not None and h4p<1.02) else 1
        f=feats(s,i,cj,bub,bt,nas,smc)
        rec={"block":k[:10],"low_t":s[i]["t"],"yr":dt.datetime.utcfromtimestamp(s[i]["t"]).year,"R":round(R,2),"win":int(R>0),"r2_keep":r2_keep}
        rec.update(f); out.write(json.dumps(rec)+"\n"); n+=1; kept+=r2_keep
out.close()
rows=[json.loads(l) for l in (HERE/"dataset_r2refine.jsonl").read_text().splitlines()]
r2=[r for r in rows if r["r2_keep"]]
print(f"dataset_r2refine.jsonl: {n} trades 8ATR | R2-kept={kept} WR_r2={100*sum(r['win'] for r in r2)/len(r2):.1f}%")
print("  features novas:",[x for x in rows[0] if x not in ('block','low_t','yr','R','win','r2_keep')])
