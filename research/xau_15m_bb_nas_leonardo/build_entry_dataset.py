#!/usr/bin/env python3
"""DATASET CAUSAL p/ engine de descoberta de ENTRADAS perto dos pivôs M8 (sem look-ahead).
Universo = todas as mínimas fractais (candidatos a fundo). Entrada-modelo = RECLAIM (1º close acima do low+0.25ATR).
~35 features CAUSAIS (info<=bar do reclaim; bubbles known_at-filtradas): RSI, NAS, SMC, sweep, bubbles s/m/L, macro 4H
multi-TF, momentum, estrutura, volatilidade, sessão, volume, EMA. Outcomes: R reclaim (let-run, SL estrutural), held@8,
runner. Alvo: near_M8 (perto de pivô M8 confirmado). + entrada-tipo-1 (8ATR-confirm) R p/ referência. Emite entry_dataset.jsonl.
RAW-causal. 2026-06-26."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in MR]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return MR[k]["macro"] if k>=0 else "WARMUP"
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
SZ={"S":1,"M":2,"L":3}; RCAP=20.0; HMAX=480; PRE=16*900
def zigzag(s,M=8):
    n=len(s); start=0
    while start<n and not s[start]["atr"]: start+=1
    if start>=n: return []
    piv=[]; d=0; hi=s[start]["h"]; hi_i=start; lo=s[start]["l"]; lo_i=start
    for i in range(start+1,n):
        a=s[i]["atr"]
        if not a: continue
        thr=M*a
        if s[i]["h"]>hi: hi=s[i]["h"]; hi_i=i
        if s[i]["l"]<lo: lo=s[i]["l"]; lo_i=i
        if d>=0 and (hi-s[i]["l"])>=thr: piv.append((hi_i,"TOP",i)); d=-1; lo=s[i]["l"]; lo_i=i
        elif d<=0 and (s[i]["h"]-lo)>=thr: piv.append((lo_i,"BOT",i)); d=1; hi=s[i]["h"]; hi_i=i
    return piv
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun_long(s,ei,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1); disp8=None
    for i in range(ei+1,end+1):
        if i-ei==8: disp8=(s[i]["c"]-entry)/risk
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)), disp8
def swlow(L,i,K=2,LB=50):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if L[p]==min(L[p-K:p+K+1]): return L[p]
    return None
def feats(s,i,j,k,nas,nas_ts,smc,bub_t,bub):
    """features causais no bar do reclaim j (info<=j); i=low bar."""
    t=s[j]["t"]; atr=s[j]["atr"] or 1.0; c=s[j]["c"]
    f={}
    # RSI
    f["rsi"]=s[j].get("rsi") or 50; f["rsi_low"]=s[i].get("rsi") or 50
    f["rsi_head"]=max(0,min(1,(70-f["rsi"])/40))
    # EMA
    e=s[j]["ema21"]; e10=s[j-10]["ema21"] if j>=10 else e
    f["dist_ema_atr"]=(c-e)/atr; f["ema_slope_atr"]=(e-e10)/atr
    # macro 4H
    f["macro_bull"]=1 if macro_at(t)=="BULL" else 0; f["macro_bear"]=1 if macro_at(t)=="BEAR" else 0
    lo192=max(0,i-192); f["macro_drop_atr"]=(max(b["h"] for b in s[lo192:i+1])-s[i]["l"])/atr
    hi192=max(s[b]["h"] for b in range(lo192,i+1)); lo_run=min(s[b]["l"] for b in range(lo192,i+1))
    f["macro_retr"]=(c-lo_run)/(hi192-lo_run) if hi192>lo_run else 0.5
    # sweep
    L=[x["l"] for x in s]; sl=swlow(L,i); f["sweep_depth_atr"]=((sl-s[i]["l"])/atr) if sl else 0
    f["reclaim_speed"]=j-i
    # momentum / structure
    f["disp4_atr"]=(c-s[j-4]["c"])/atr if j>=4 else 0; f["disp8_atr"]=(c-s[j-8]["c"])/atr if j>=8 else 0
    f["up_closes8"]=sum(1 for q in range(max(1,j-7),j+1) if s[q]["c"]>s[q-1]["c"])
    rng=[s[q]["h"]-s[q]["l"] for q in range(max(0,j-5),j+1)]; f["range_exp"]=(st.mean(rng[-2:])/st.mean(rng[:2])) if len(rng)>=4 and st.mean(rng[:2])>0 else 1
    lo20=min(L[max(0,i-20):i+1]); hi20=max(s[b]["h"] for b in range(max(0,i-20),i+1)); f["leg_ext"]=(s[i]["c"]-lo20)/(hi20-lo20) if hi20>lo20 else 0.5
    opp=max(s[b]["h"] for b in range(max(0,j-120),j+1)); f["room_atr"]=(opp-c)/atr
    # wick / rejection no low
    lb=s[i]; lrng=max(lb["h"]-lb["l"],1e-9); f["low_wick"]=(min(lb["o"],lb["c"])-lb["l"])/lrng; f["low_closepos"]=(lb["c"]-lb["l"])/lrng
    # volatility
    a50=[s[b]["atr"] for b in range(max(0,j-50),j+1) if s[b]["atr"]]; f["atr_regime"]=atr/st.median(a50) if a50 else 1
    # session
    hr=dt.datetime.utcfromtimestamp(t).hour; f["hour"]=hr; f["killzone"]=1 if (7<=hr<12 or 13<=hr<18) else 0
    # volume
    v50=[s[b].get("v",0) for b in range(max(0,j-50),j+1)]; f["vol_low_vs_med"]=(s[i].get("v",0)/st.median(v50)) if v50 and st.median(v50)>0 else 1
    # NAS
    a16=bisect.bisect_left(nas_ts,t-PRE); b16=bisect.bisect_right(nas_ts,t)
    f["nas_long_16"]=sum(1 for e in nas[a16:b16] if e["dir"]=="LONG"); f["nas_short_16"]=sum(1 for e in nas[a16:b16] if e["dir"]=="SHORT")
    a48=bisect.bisect_left(nas_ts,t-48*900); f["nas_long_48"]=sum(1 for e in nas[a48:b16] if e["dir"]=="LONG")
    last_nas=[e for e in nas if e["t"]<=t]; f["nas_last_long"]=1 if (last_nas and last_nas[-1]["dir"]=="LONG") else 0
    # SMC recent
    rsmc=[e for e in smc if e["t"] and e["t"]<=t and e["t"]>=t-48*900]
    f["smc_choch"]=sum(1 for e in rsmc if "CHoCH" in str(e["text"])); f["smc_bos"]=sum(1 for e in rsmc if "BOS" in str(e["text"]))
    # bubbles known_at<=t (na janela antes do low)
    ts=bub_t; lo_b=bisect.bisect_left(ts,s[i]["t"]-PRE); hi_b=bisect.bisect_right(ts,s[i]["t"])
    sS=sM=sL=bS=bM=bL=0
    for x in bub[lo_b:hi_b]:
        if (x.get("known_at") or x["t"])>t: continue
        if x["side"]=="SELL": sS+=x["size"]=="S"; sM+=x["size"]=="M"; sL+=x["size"]=="L"
        else: bS+=x["size"]=="S"; bM+=x["size"]=="M"; bL+=x["size"]=="L"
    f["sell_S"]=sS;f["sell_M"]=sM;f["sell_L"]=sL;f["buy_S"]=bS;f["buy_M"]=bM;f["buy_L"]=bL
    f["sell_w"]=sS+2*sM+3*sL; f["buy_w"]=bS+2*bM+3*bL
    tot=f["sell_w"]+f["buy_w"]; f["sell_pol"]=f["sell_w"]/tot if tot>0 else 0.5
    return f
def fractal_lows(s,K=4):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-K:p+K+1])]
out=open(HERE/"entry_dataset.jsonl","w"); n=0
for k,pr in PRIM.items():
    s=pr["series"]; nn=len(s)
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); nas_ts=[e["t"] for e in nas]
    smc=pr["smc_events"]; bub=BUB[k]; bub_t=[x["t"] for x in bub]
    zones_d=[z for z in pr.get("zones",[]) if "DEMAND" in str(z.get("text","")).upper()]
    zones_s=[z for z in pr.get("zones",[]) if "SUPPLY" in str(z.get("text","")).upper()]
    m8_bots=set(idx for idx,kind,_ in zigzag(s) if kind=="BOT")
    m8_conf={}  # low_idx -> confirm_idx (bar onde zigzag confirma)
    for idx,kind,ci in zigzag(s):
        if kind=="BOT": m8_conf[idx]=ci
    for i in fractal_lows(s):
        atr=s[i]["atr"]
        if not atr: continue
        # reclaim
        j=None
        for q in range(i+1,min(i+48,nn-2)):
            if s[q]["c"]>s[i]["l"]+0.25*atr: j=q; break
        if j is None or j+2>=nn: continue
        entry=s[j]["c"]; R,disp8=letrun_long(s,j,entry,s[i]["l"]-0.1*atr,atr)
        if R is None: continue
        # entrada-tipo-1: 8ATR confirm (entra quando preço sobe 8ATR do low)
        cj=None
        for q in range(i+1,min(i+HMAX,nn-2)):
            if s[q]["h"]>=s[i]["l"]+8*atr: cj=q; break
        R8=None
        if cj is not None and cj+2<nn:
            R8,_=letrun_long(s,cj,s[cj]["c"],min(x["l"] for x in s[i:cj+1])-0.1*atr,atr)
        near=any(abs(i-b)<=24 for b in m8_bots)
        lt=s[i]["t"]; lL=s[i]["l"]
        in_demand=1 if any(z["born_t"]<=lt and z["low"]-0.3*atr<=lL<=z["high"]+0.3*atr for z in zones_d) else 0
        in_supply=1 if any(z["born_t"]<=lt and z["low"]-0.3*atr<=lL<=z["high"]+0.3*atr for z in zones_s) else 0
        F=feats(s,i,j,k,nas,nas_ts,smc,bub_t,bub)
        F["in_demand"]=in_demand; F["in_supply"]=in_supply
        rec={"block":k[:10],"low_t":s[i]["t"],"yr":dt.datetime.utcfromtimestamp(s[i]["t"]).year,
             "R_reclaim":round(R,2),"held8":int(disp8 is not None and disp8>=1),"runner":int(R>=5),
             "R_8atr":round(R8,2) if R8 is not None else None,"near_M8":int(near),"reclaim_idx":j,"low_idx":i}
        rec.update({kk:(round(vv,3) if isinstance(vv,float) else vv) for kk,vv in F.items()})
        out.write(json.dumps(rec)+"\n"); n+=1
out.close()
print(f"entry_dataset.jsonl: {n} candidatos (mínimas fractais) | features causais + outcomes + alvo near_M8")
# resumo base
import statistics as st
rows=[json.loads(l) for l in (HERE/"entry_dataset.jsonl").read_text().splitlines()]
nearr=[r for r in rows if r["near_M8"]]
print(f"  near_M8={len(nearr)} ({100*len(nearr)/len(rows):.0f}%) | base R_reclaim avg={st.mean(r['R_reclaim'] for r in rows):+.2f} WR={100*sum(1 for r in rows if r['R_reclaim']>0)/len(rows):.0f}%")
r8=[r for r in rows if r["R_8atr"] is not None]
print(f"  entrada-tipo-1 (8ATR): n={len(r8)} avgR={st.mean(r['R_8atr'] for r in r8):+.2f} WR={100*sum(1 for r in r8 if r['R_8atr']>0)/len(r8):.0f}%")
