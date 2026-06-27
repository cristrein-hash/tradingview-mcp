#!/usr/bin/env python3
"""DATASET RICO p/ engine específico da entrada 8ATR: separar winner×loser com leitura ESTRUTURAL INTEGRADA + MULTI-TF.
Universo = mínimas fractais com confirmação 8ATR (entry no bar cj). Outcome R_8atr (winner=R>0). Features CAUSAIS as-of cj:
  MULTI-TF 1H/4H/1D (só barras HTF FECHADAS, t_end<=tc): trend(up/range/down), dist_close_ema_atr, pos_in_range, range_eff.
  OB zonas RAW: dist_demand_below_atr, dist_supply_above_atr, in_demand, n_demand_near, demand_fresh.
  Volatilidade: atr_regime_15m, atr_expand. Volume: vol_low_vs_med, vol_climax, vpnode_dist_atr.
  Perna macro: macro_drop_atr, macro_retr, bars_since_4hflip. Geometria: bars_to_8atr, path_eff. + 15M base (rsi/disp/sweep).
Emite dataset_8atr.jsonl. RAW-causal (HTF shift = sem look-ahead). 2026-06-26."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in MR]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return MR[k]["macro"] if k>=0 else "WARMUP"
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun_long(s,ei,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def htf_bars(s,period):
    """agrupa 15M por epoch//period; retorna barras HTF completas [{key,o,h,l,c,t_end}] (t_end=último t do grupo+900)."""
    groups={}
    for b in s:
        kk=b["t"]//period; g=groups.setdefault(kk,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"],"t_end":b["t"]+900})
        g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]; g["t_end"]=b["t"]+900
    return [groups[k] for k in sorted(groups)]
def ema(vals,n):
    if not vals: return None
    k=2/(n+1); e=vals[0]
    for v in vals[1:]: e=v*k+e*(1-k)
    return e
def htf_feat(hb,tc,c15,atr15):
    """features de uma TF as-of tc (só barras com t_end<=tc)."""
    done=[b for b in hb if b["t_end"]<=tc]
    if len(done)<25: return None
    closes=[b["c"] for b in done]; highs=[b["h"] for b in done]; lows=[b["l"] for b in done]
    e20=ema(closes[-60:],20); e50=ema(closes[-120:],50) if len(closes)>=50 else ema(closes,min(50,len(closes)))
    e20p=ema(closes[-65:-5],20) if len(closes)>=25 else e20
    slope=(e20-e20p)
    trend=1 if (e20>e50 and slope>0) else (-1 if (e20<e50 and slope<0) else 0)
    dist=(c15-e20)/atr15
    rl=min(lows[-20:]); rh=max(highs[-20:]); pos=(c15-rl)/(rh-rl) if rh>rl else 0.5
    # range efficiency últimas 10 barras: |net|/soma|moves|
    seg=closes[-11:]
    if len(seg)>=3:
        net=abs(seg[-1]-seg[0]); path=sum(abs(seg[i]-seg[i-1]) for i in range(1,len(seg))); eff=net/path if path>0 else 0
    else: eff=0.5
    return {"trend":trend,"dist":round(dist,2),"pos":round(pos,2),"eff":round(eff,2)}
def build():
    out=open(HERE/"dataset_8atr.jsonl","w"); n=0
    for k,pr in PRIM.items():
        s=pr["series"]; nn=len(s); L=[x["l"] for x in s]
        h1=htf_bars(s,3600); h4=htf_bars(s,14400); hd=htf_bars(s,86400)
        zones=pr.get("zones",[]); zd=[z for z in zones if "DEMAND" in str(z.get("text","")).upper()]; zs=[z for z in zones if "SUPPLY" in str(z.get("text","")).upper()]
        nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"])
        # 4H flip index (macro)
        for i in range(96,nn-4):
            atr=s[i]["atr"]
            if not atr or L[i]!=min(L[i-4:i+5]): continue
            # confirmação 8ATR
            cj=None
            for q in range(i+1,min(i+HMAX,nn-2)):
                if s[q]["h"]>=s[i]["l"]+8*atr: cj=q; break
            if cj is None or cj+2>=nn: continue
            tc=s[cj]["t"]; c15=s[cj]["c"]; atrc=s[cj]["atr"] or atr
            entry=c15; sl=min(x["l"] for x in s[i:cj+1])-0.1*atr
            R=letrun_long(s,cj,entry,sl,atr)
            if R is None: continue
            f={}
            # multi-TF
            for tag,hb in (("h1",h1),("h4",h4),("hd",hd)):
                hf=htf_feat(hb,tc,c15,atrc)
                if hf:
                    for kk,vv in hf.items(): f[f"{tag}_{kk}"]=vv
                else:
                    for kk in ("trend","dist","pos","eff"): f[f"{tag}_{kk}"]=None
            # OB zonas (causal: born_t<=tc)
            dem_below=[z for z in zd if z["born_t"]<=tc and z["high"]<=c15+0.3*atrc]
            sup_above=[z for z in zs if z["born_t"]<=tc and z["low"]>=c15-0.3*atrc]
            f["dist_demand_atr"]=round(min((c15-z["high"])/atrc for z in dem_below),2) if dem_below else 99
            f["dist_supply_atr"]=round(min((z["low"]-c15)/atrc for z in sup_above),2) if sup_above else 99
            f["in_demand"]=1 if any(z["born_t"]<=tc and z["low"]-0.3*atrc<=s[i]["l"]<=z["high"]+0.3*atrc for z in zd) else 0
            f["n_demand_near"]=sum(1 for z in zd if z["born_t"]<=tc and abs((z["high"]+z["low"])/2-c15)<=3*atrc)
            f["demand_fresh"]=1 if any(z["born_t"]<=tc and tc-z["born_t"]<=96*900 and z["high"]<=c15+atrc for z in zd) else 0
            # volatilidade/volume
            a50=[s[b]["atr"] for b in range(max(0,cj-50),cj+1) if s[b]["atr"]]; f["atr_regime"]=round(atrc/st.median(a50),2) if a50 else 1
            a10=[s[b]["atr"] for b in range(max(0,cj-10),cj+1) if s[b]["atr"]]; f["atr_expand"]=round(atrc/st.median(a10),2) if a10 else 1
            v50=[s[b].get("v",0) for b in range(max(0,cj-50),cj+1)]; f["vol_low_vs_med"]=round((s[i].get("v",0)/st.median(v50)),2) if v50 and st.median(v50)>0 else 1
            f["vol_climax"]=round(max(s[b].get("v",0) for b in range(i,min(i+3,nn)))/st.median(v50),2) if v50 and st.median(v50)>0 else 1
            # volume-by-price node (RAW volume, últimas 96 barras)
            seg=s[max(0,cj-96):cj+1]; pmin=min(b["l"] for b in seg); pmax=max(b["h"] for b in seg)
            if pmax>pmin:
                nb=30; step=(pmax-pmin)/nb; vol=[0.0]*nb
                for b in seg:
                    mid=(b["h"]+b["l"])/2; kb=min(nb-1,int((mid-pmin)/step)); vol[kb]+=b.get("v",0) or 0
                poc=pmin+(max(range(nb),key=lambda x:vol[x])+0.5)*step; f["vpnode_dist_atr"]=round((c15-poc)/atrc,2)
            else: f["vpnode_dist_atr"]=0
            # perna macro / geometria
            lo192=max(0,i-192); f["macro_drop_atr"]=round((max(b["h"] for b in s[lo192:i+1])-s[i]["l"])/atr,2)
            hi192=max(s[b]["h"] for b in range(lo192,i+1)); lr=min(s[b]["l"] for b in range(lo192,i+1)); f["macro_retr"]=round((c15-lr)/(hi192-lr),2) if hi192>lr else 0.5
            f["macro_bull"]=1 if macro_at(tc)=="BULL" else 0; f["macro_bear"]=1 if macro_at(tc)=="BEAR" else 0
            f["bars_to_8atr"]=cj-i
            mv=s[cj]["h"]-s[i]["l"]; pth=sum(abs(s[b]["c"]-s[b-1]["c"]) for b in range(i+1,cj+1)); f["path_eff"]=round(mv/pth,2) if pth>0 else 1
            # 15M base
            f["rsi"]=round(s[cj].get("rsi") or 50,1); f["rsi_low"]=round(s[i].get("rsi") or 50,1)
            f["disp4_atr"]=round((s[cj]["c"]-s[cj-4]["c"])/atrc,2) if cj>=4 else 0
            f["killzone"]=1 if (7<=dt.datetime.utcfromtimestamp(tc).hour<12 or 13<=dt.datetime.utcfromtimestamp(tc).hour<18) else 0
            rec={"block":k[:10],"low_t":s[i]["t"],"yr":dt.datetime.utcfromtimestamp(s[i]["t"]).year,"R":round(R,2),"win":int(R>0)}
            rec.update(f); out.write(json.dumps(rec)+"\n"); n+=1
    out.close(); return n
n=build()
rows=[json.loads(l) for l in (HERE/"dataset_8atr.jsonl").read_text().splitlines()]
import statistics as st
wr=100*sum(r["win"] for r in rows)/len(rows)
print(f"dataset_8atr.jsonl: {n} trades 8ATR | WR base={wr:.0f}% | features multi-TF+OB+vol+volume+geom")
print("  features:",[k for k in rows[0] if k not in ('block','low_t','yr','R','win')])
