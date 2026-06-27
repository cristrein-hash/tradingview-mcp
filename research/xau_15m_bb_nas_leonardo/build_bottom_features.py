#!/usr/bin/env python3
"""PHASE 0 — Dataset CAUSAL de features dos 205 fundos M8 (engine de potência de fundo, Cris 2026-06-27).
Ancora em CADA pivô BOT do gabarito (reversal_power.csv), computa features AS-OF a barra do pivô (só barras<=i;
SHIFT1/known_at<=t p/ indicadores que repintam). Tier (MONSTRO/FORTE/MEDIO/FRACO) = label FORWARD (nunca feature).
10 famílias (F1 posicional · F2 path · F3 OB · F4 SVP-proxy · F5 regime · F6 flow/bubbles · F7 RSI/capit ·
F8 vol · F9 aceitação-no-fundo · F10 sessão). Reusa helpers de build_8atr_dataset. RAW-only. -> bottom_features.jsonl"""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in MR]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return MR[k]["macro"] if k>=0 else "WARMUP"
BUB={}
for bf in sorted((HERE/"bubbles").glob("*.bubbles.jsonl")):
    BUB[bf.name[:10]]=sorted([json.loads(l) for l in bf.read_text().splitlines() if l],key=lambda x:x["t"])
SZ={"S":1,"M":2,"L":3}
import csv as _csv
REV=[r for r in _csv.DictReader(open(HERE/"reversal_power.csv")) if r["kind"]=="BOT"]
# t -> blockkey (1a ocorrência vence em emendas)
T2B={}
for bkey,pr in PRIMK.items():
    for b in pr["series"]: T2B.setdefault(b["t"],bkey)

def ema(vals,n):
    if not vals: return None
    k=2/(n+1); e=vals[0]
    for v in vals[1:]: e=v*k+e*(1-k)
    return e
def htf_bars(s,period):
    g={}
    for b in s:
        kk=b["t"]//period; gg=g.setdefault(kk,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"],"t_end":b["t"]+900})
        gg["h"]=max(gg["h"],b["h"]); gg["l"]=min(gg["l"],b["l"]); gg["c"]=b["c"]; gg["t_end"]=b["t"]+900
    return [g[k] for k in sorted(g)]
def rsi_wilder(cl,n=14):
    if len(cl)<n+1: return None
    g=l=0.0
    for x in range(1,n+1):
        d=cl[x]-cl[x-1]; g+=max(d,0); l+=max(-d,0)
    ag=g/n; al=l/n
    for x in range(n+1,len(cl)):
        d=cl[x]-cl[x-1]; ag=(ag*(n-1)+max(d,0))/n; al=(al*(n-1)+max(-d,0))/n
    if al==0: return 100.0
    rs=ag/al; return 100-100/(1+rs)
def htf_feat(hb,tc,c,atr):
    done=[b for b in hb if b["t_end"]<=tc]
    if len(done)<25: return None
    cl=[b["c"] for b in done]; hi=[b["h"] for b in done]; lo=[b["l"] for b in done]
    e20=ema(cl[-60:],20); e50=ema(cl[-120:],50) if len(cl)>=50 else ema(cl,min(50,len(cl)))
    e20p=ema(cl[-65:-5],20) if len(cl)>=25 else e20; slope=e20-e20p
    trend=1 if(e20>e50 and slope>0)else(-1 if(e20<e50 and slope<0)else 0)
    rl=min(lo[-20:]); rh=max(hi[-20:]); pos=(c-rl)/(rh-rl) if rh>rl else .5   # dealing-range pos na TF
    seg=cl[-11:]; net=abs(seg[-1]-seg[0]); pth=sum(abs(seg[i]-seg[i-1]) for i in range(1,len(seg))); eff=net/pth if pth>0 else .5
    rsi=rsi_wilder(cl[-60:]);
    return {"trend":trend,"dist":round((c-e20)/atr,2),"pos":round(pos,2),"eff":round(eff,2),
            "slope_atr":round(slope/atr,2),"rsi":round(rsi,1) if rsi is not None else None}

def fractal_swing_low_before(s,i,k=2):
    """último swing-low confirmado antes de i (low[p]==min p-k..p+k, p+k<i)."""
    for p in range(i-1,k,-1):
        if p+k<i and s[p]["l"]==min(x["l"] for x in s[p-k:p+k+1]): return p
    return None
def fractal_swing_high_before(s,i,k=2):
    for p in range(i-1,k,-1):
        if p+k<i and s[p]["h"]==max(x["h"] for x in s[p-k:p+k+1]): return p
    return None

rows=[]
for r in REV:
    t0=int(r["t"]); bkey=T2B.get(t0); pr=PRIMK.get(bkey)
    if not pr: continue
    s=pr["series"]; nn=len(s); t=int(r["t"])
    tmap={b["t"]:idx for idx,b in enumerate(s)}; i=tmap.get(t)
    if i is None or i<96 or not s[i]["atr"]: continue
    atr=s[i]["atr"]; c=s[i]["c"]; lo=s[i]["l"]; hi=s[i]["h"]; tc=t
    zones=pr.get("zones",[]); zd=[z for z in zones if "DEMAND" in str(z.get("text","")).upper()]; zs=[z for z in zones if "SUPPLY" in str(z.get("text","")).upper()]
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); nas_t=[e["t"] for e in nas]
    smc=sorted([e for e in pr["smc_events"] if e.get("t")],key=lambda e:e["t"])
    bub=BUB.get(bkey,[]); bub_t=[x["t"] for x in bub]
    h1=htf_bars(s,3600); h4=htf_bars(s,14400); hd=htf_bars(s,86400)
    f={}
    # F1 POSICIONAL
    for N in (30,60,90):
        a=max(0,i-N); lw=min(x["l"] for x in s[a:i+1]); hw=max(x["h"] for x in s[a:i+1])
        f[f"legpos{N}"]=round((lo-lw)/(hw-lw),3) if hw>lw else .5   # baixo=fundo da perna
    shi=fractal_swing_high_before(s,i); sli=fractal_swing_low_before(s,i)
    if shi is not None and sli is not None and s[shi]["h"]>s[sli]["l"]:
        f["dealing_range_pos"]=round((lo-s[sli]["l"])/(s[shi]["h"]-s[sli]["l"]),3)
    else: f["dealing_range_pos"]=None
    # F2 PATH (perna de baixa até o fundo)
    a20=max(0,i-20); leg=s[a20:i+1]
    drops=[leg[x-1]["c"]-leg[x]["c"] for x in range(1,len(leg))]
    f["drop20_atr"]=round((max(x["h"] for x in leg)-lo)/atr,2)
    f["flush_v_ratio"]=round(max(drops+[0])/((max(x["h"] for x in leg)-lo) or 1),2)   # 1 barra domina=V; baixo=grind
    cd=0
    for x in range(i,0,-1):
        if s[x]["c"]<s[x-1]["c"]: cd+=1
        else: break
    f["consec_down"]=cd
    segp=[x["c"] for x in leg]; net=abs(segp[-1]-segp[0]); pth=sum(abs(segp[x]-segp[x-1]) for x in range(1,len(segp))); f["downleg_eff"]=round(net/pth,2) if pth>0 else .5
    # sweep: pierce do swing-low anterior (CAUSAL — só barra i). sweep_reclaim_bars REMOVIDO (varria i+1..i+8=futuro, DA).
    f["sweep_depth_atr"]=round((s[sli]["l"]-lo)/atr,2) if (sli is not None and lo<s[sli]["l"]) else 0.0  # >0=furou abaixo
    # F3 OB (causal born_t<=tc)
    dem_below=[z for z in zd if z["born_t"]<=tc and z["high"]<=c+0.3*atr]; sup_above=[z for z in zs if z["born_t"]<=tc and z["low"]>=c-0.3*atr]
    f["dist_demand_atr"]=round(min((c-z["high"])/atr for z in dem_below),2) if dem_below else 99
    f["dist_supply_atr"]=round(min((z["low"]-c)/atr for z in sup_above),2) if sup_above else 99   # clean_sky proxy (alto=longe)
    f["in_demand"]=1 if any(z["born_t"]<=tc and z["low"]-0.3*atr<=lo<=z["high"]+0.3*atr for z in zd) else 0
    f["n_demand_near"]=sum(1 for z in zd if z["born_t"]<=tc and abs((z["high"]+z["low"])/2-c)<=3*atr)
    f["demand_fresh"]=1 if any(z["born_t"]<=tc and tc-z["born_t"]<=96*900 and z["high"]<=c+atr for z in zd) else 0
    f["n_supply_overhead"]=sum(1 for z in zs if z["born_t"]<=tc and z["low"]>c)
    # demand virgin: zona ainda não tocada entre born e i
    vz=0
    for z in zd:
        if z["born_t"]<=tc and z["high"]<=c+0.3*atr:
            bi=tmap.get(z["born_t"])
            if bi is not None and not any(s[x]["l"]<=z["high"] for x in range(bi+1,i)): vz=1; break
    f["demand_virgin"]=vz
    # F4 SVP-proxy (volume-by-price node; histograma VA real BLOQUEADO no 15M)
    seg96=s[max(0,i-96):i+1]; pmin=min(b["l"] for b in seg96); pmax=max(b["h"] for b in seg96)
    if pmax>pmin:
        nb=30; step=(pmax-pmin)/nb; vol=[0.0]*nb
        for b in seg96:
            mid=(b["h"]+b["l"])/2; kb=min(nb-1,int((mid-pmin)/step)); vol[kb]+=b.get("v",0) or 0
        poc=pmin+(max(range(nb),key=lambda x:vol[x])+.5)*step; f["vpnode_dist_atr"]=round((c-poc)/atr,2)
    else: f["vpnode_dist_atr"]=0
    # F5 REGIME
    for tag,hb in (("h1",h1),("h4",h4),("hd",hd)):
        hf=htf_feat(hb,tc,c,atr)
        if hf:
            for kk,vv in hf.items(): f[f"{tag}_{kk}"]=vv
        else:
            for kk in ("trend","dist","pos","eff","slope_atr","rsi"): f[f"{tag}_{kk}"]=None
    f["macro_bull"]=1 if macro_at(tc)=="BULL" else 0; f["macro_bear"]=1 if macro_at(tc)=="BEAR" else 0
    # F6 FLOW/BUBBLES (known_at<=tc)
    a=bisect.bisect_left(bub_t,s[max(0,i-24)]["t"]); bw=sw_=bl=sl_=0; recent_sell=old_sell=0
    half=s[max(0,i-12)]["t"]
    for x in bub[a:]:
        if x["t"]>tc: break
        if (x.get("known_at") or x["t"])>tc: continue
        wt=SZ[x["size"]]
        if x["side"]=="BUY": bw+=wt; bl+= (1 if x["size"]=="L" else 0)
        else:
            sw_+=wt; sl_+= (1 if x["size"]=="L" else 0)
            if x["t"]>=half: recent_sell+=wt
            else: old_sell+=wt
    f["buy_bub_w"]=bw; f["sell_bub_w"]=sw_; f["buy_bub_L"]=bl; f["sell_bub_L"]=sl_
    f["sell_decel"]=round(old_sell-recent_sell,1)   # >0 = venda secando
    na=bisect.bisect_left(nas_t,s[max(0,i-16)]["t"]); nb_=bisect.bisect_right(nas_t,tc)
    f["nas_long_16"]=sum(1 for e in nas[na:nb_] if e["dir"]=="LONG"); f["nas_short_16"]=sum(1 for e in nas[na:nb_] if e["dir"]=="SHORT")
    f["smc_bos"]=1 if any(e["t"]<=tc and "BOS" in str(e.get("text","")) for e in smc[-30:]) else 0
    # F7 RSI/CAPIT
    f["rsi_low"]=round(s[i].get("rsi") or 50,1)
    r8=[s[x].get("rsi") for x in range(max(0,i-8),i+1) if s[x].get("rsi") is not None]; f["rsi_min8"]=round(min(r8),1) if r8 else 50
    f["rsi_head"]=round((70-(s[i].get("rsi") or 50))/40,2)
    # bull div: low<swing-low anterior mas rsi[i]>rsi[swing-low]
    f["rsi_bull_div"]=0
    if sli is not None and s[i].get("rsi") and s[sli].get("rsi") and lo<s[sli]["l"] and s[i]["rsi"]>s[sli]["rsi"]: f["rsi_bull_div"]=1
    # F8 VOL
    a50=[s[b]["atr"] for b in range(max(0,i-50),i+1) if s[b]["atr"]]; f["atr_regime"]=round(atr/st.median(a50),2) if a50 else 1
    a10pre=[s[b]["atr"] for b in range(max(0,i-15),max(1,i-5)) if s[b]["atr"]]; f["atr_compression_pre"]=round(st.median(a10pre)/atr,2) if a10pre else 1  # >1 = comprimido antes
    v50=[s[b].get("v",0) for b in range(max(0,i-50),i+1)]; mv=st.median(v50) if v50 else 0
    f["vol_climax"]=round((s[i].get("v",0)/mv),2) if mv>0 else 1
    f["range_exp"]=round((hi-lo)/st.median([s[b]["h"]-s[b]["l"] for b in range(max(0,i-14),i+1)]),2)
    # F9 ACEITAÇÃO NO FUNDO
    rng=hi-lo
    f["low_closepos"]=round((c-lo)/rng,2) if rng>0 else .5   # alto=fecha no topo (rejeição)
    f["lower_wick_ratio"]=round((min(s[i]["o"],c)-lo)/rng,2) if rng>0 else 0
    f["low_revisit"]=sum(1 for x in range(max(0,i-12),i) if abs(s[x]["l"]-lo)<=0.5*atr)
    # F10 SESSÃO
    hh=dt.datetime.utcfromtimestamp(tc).hour
    f["session"]=("ASIA" if hh<7 else "LONDON" if hh<12 else "NY" if hh<18 else "LATE")
    f["killzone"]=1 if (7<=hh<12 or 13<=hh<18) else 0
    rec={"block":bkey,"t":t,"yr":int(r["yr"]),"tier":r["tier"],"tier_clean":r["tier_clean"],
         "leg_atr":float(r["leg_atr"]),"power_score":float(r["power_score"]) if r["power_score"] not in("","None") else None}
    rec.update(f); rows.append(rec)

with open(HERE/"bottom_features.jsonl","w") as fo:
    for r in rows: fo.write(json.dumps(r)+"\n")
from collections import Counter
print(f"bottom_features.jsonl: {len(rows)} fundos | tiers {dict(Counter(r['tier'] for r in rows))}")
print(f"features ({len([k for k in rows[0] if k not in ('block','t','yr','tier','tier_clean','leg_atr','power_score')])}):",
      [k for k in rows[0] if k not in ('block','t','yr','tier','tier_clean','leg_atr','power_score')])
miss=sum(1 for r in rows if r.get("dealing_range_pos") is None); print(f"dealing_range_pos None: {miss}")
