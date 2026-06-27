#!/usr/bin/env python3
"""DATASET 5ATR completo (multi-TF + OB + vol + volume + geometria + flow-ortogonais) p/ RE-OTIMIZAR filtros (R2'+R_B')
nesta base. Entrada=5ATR-confirm; outcome=let-run com SL=A (flush-0.1ATR); SEM dedup (full candidate p/ mineração).
Todas features causais (HTF barras fechadas, bubbles known_at<=tc). Emite dataset_5atr.jsonl. RAW. 2026-06-27."""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
MRj=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in MRj]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return MRj[k]["macro"] if k>=0 else "WARMUP"
TRANS=[]; prev=None
for b in MRj:
    if b["macro"]!=prev: TRANS.append(b["t_end"]); prev=b["macro"]
def regime_age_h(t): k=bisect.bisect_right(TRANS,t)-1; return (t-TRANS[k])/3600 if k>=0 else 0
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
SZ={"S":1,"M":2,"L":3}; RCAP=20.0; HMAX=480; PRE=16*900; MBASE=5
def htf_bars(s,period):
    g={}
    for b in s:
        kk=b["t"]//period; d=g.setdefault(kk,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"],"t_end":b["t"]+900})
        d["h"]=max(d["h"],b["h"]); d["l"]=min(d["l"],b["l"]); d["c"]=b["c"]; d["t_end"]=b["t"]+900
    return [g[k] for k in sorted(g)]
def ema(v,n):
    if not v: return None
    k=2/(n+1); e=v[0]
    for x in v[1:]: e=x*k+e*(1-k)
    return e
def htf_feat(hb,tc,c15,atr15):
    done=[b for b in hb if b["t_end"]<=tc]
    if len(done)<25: return None
    cl=[b["c"] for b in done]; hi=[b["h"] for b in done]; lo=[b["l"] for b in done]
    e20=ema(cl[-60:],20); e50=ema(cl[-120:],50) if len(cl)>=50 else ema(cl,min(50,len(cl)))
    e20p=ema(cl[-65:-5],20) if len(cl)>=25 else e20; slope=e20-e20p
    trend=1 if (e20>e50 and slope>0) else (-1 if (e20<e50 and slope<0) else 0)
    rl=min(lo[-20:]); rh=max(hi[-20:]); pos=(c15-rl)/(rh-rl) if rh>rl else 0.5
    seg=cl[-11:]; net=abs(seg[-1]-seg[0]); path=sum(abs(seg[i]-seg[i-1]) for i in range(1,len(seg))); eff=net/path if path>0 else 0.5
    return {"trend":trend,"dist":round((c15-e20)/atr15,2),"pos":round(pos,2),"eff":round(eff,2)}
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1); d8=None
    for k in range(cj+1,end+1):
        if k-cj==8: d8=(s[k]["c"]-entry)/risk
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),d8
def kb(bub,bt,t0,t1,tc):
    a=bisect.bisect_left(bt,t0); b=bisect.bisect_right(bt,t1); return [x for x in bub[a:b] if (x.get("known_at") or x["t"])<=tc]
out=open(HERE/"dataset_5atr.jsonl","w"); n=0
for k,pr in PRIM.items():
    s=pr["series"]; nn=len(s); L=[x["l"] for x in s]; bub=BUB[k]; bt=[x["t"] for x in bub]
    h1=htf_bars(s,3600); h4=htf_bars(s,14400); hd=htf_bars(s,86400)
    zones=pr.get("zones",[]); zd=[z for z in zones if "DEMAND" in str(z.get("text","")).upper()]; zs=[z for z in zones if "SUPPLY" in str(z.get("text","")).upper()]
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); smc=pr["smc_events"]
    for i in range(96,nn-4):
        atr=s[i]["atr"]
        if not atr or L[i]!=min(L[i-4:i+5]): continue
        cj=None
        for q in range(i+1,min(i+HMAX,nn-2)):
            if s[q]["h"]>=s[i]["l"]+MBASE*atr: cj=q; break
        if cj is None or cj+2>=nn: continue
        tc=s[cj]["t"]; c15=s[cj]["c"]; atrc=s[cj]["atr"] or atr
        flush=min(x["l"] for x in s[i:cj+1]); sl=flush-0.1*atr; entry=c15
        R,d8=letrun(s,cj,entry,sl,atr)
        if R is None: continue
        f={}
        for tag,hb in (("h1",h1),("h4",h4),("hd",hd)):
            hf=htf_feat(hb,tc,c15,atrc)
            for kk in ("trend","dist","pos","eff"): f[f"{tag}_{kk}"]=hf[kk] if hf else None
        dem_below=[z for z in zd if z["born_t"]<=tc and z["high"]<=c15+0.3*atrc]; sup_above=[z for z in zs if z["born_t"]<=tc and z["low"]>=c15-0.3*atrc]
        f["dist_demand_atr"]=round(min((c15-z["high"])/atrc for z in dem_below),2) if dem_below else 99
        f["dist_supply_atr"]=round(min((z["low"]-c15)/atrc for z in sup_above),2) if sup_above else 99
        f["in_demand"]=1 if any(z["born_t"]<=tc and z["low"]-0.3*atrc<=s[i]["l"]<=z["high"]+0.3*atrc for z in zd) else 0
        f["demand_fresh"]=1 if any(z["born_t"]<=tc and tc-z["born_t"]<=96*900 and z["high"]<=c15+atrc for z in zd) else 0
        v50=[s[b].get("v",0) for b in range(max(0,cj-50),cj+1)]; med=st.median(v50) if v50 else 1
        f["atr_regime"]=round(atrc/st.median([s[b]["atr"] for b in range(max(0,cj-50),cj+1) if s[b]["atr"]] or [atrc]),2)
        f["vol_low_vs_med"]=round((s[i].get("v",0)/med),2) if med>0 else 1
        f["vol_climax"]=round(max(s[b].get("v",0) for b in range(i,min(i+3,nn)))/med,2) if med>0 else 1
        seg=s[max(0,cj-96):cj+1]; pmin=min(b["l"] for b in seg); pmax=max(b["h"] for b in seg)
        if pmax>pmin:
            nb=30; step=(pmax-pmin)/nb; vol=[0.0]*nb
            for b in seg:
                kb2=min(nb-1,int(((b["h"]+b["l"])/2-pmin)/step)); vol[kb2]+=b.get("v",0) or 0
            f["vpnode_dist_atr"]=round((c15-(pmin+(max(range(nb),key=lambda x:vol[x])+0.5)*step))/atrc,2)
        else: f["vpnode_dist_atr"]=0
        lo192=max(0,i-192); f["macro_drop_atr"]=round((max(b["h"] for b in s[lo192:i+1])-s[i]["l"])/atr,2)
        hi192=max(s[b]["h"] for b in range(lo192,i+1)); lr=min(s[b]["l"] for b in range(lo192,i+1)); f["macro_retr"]=round((c15-lr)/(hi192-lr),2) if hi192>lr else 0.5
        f["macro_bull"]=1 if macro_at(tc)=="BULL" else 0; f["macro_bear"]=1 if macro_at(tc)=="BEAR" else 0
        f["bars_to_base"]=cj-i; mv=s[cj]["h"]-s[i]["l"]; pth=sum(abs(s[b]["c"]-s[b-1]["c"]) for b in range(i+1,cj+1)); f["path_eff"]=round(mv/pth,2) if pth>0 else 1
        f["rsi"]=round(s[cj].get("rsi") or 50,1); f["rsi_low"]=round(s[i].get("rsi") or 50,1); f["disp4_atr"]=round((s[cj]["c"]-s[cj-4]["c"])/atrc,2) if cj>=4 else 0
        hh=dt.datetime.utcfromtimestamp(tc).hour; f["killzone"]=1 if (7<=hh<12 or 13<=hh<18) else 0
        f["is_london_open"]=1 if 7<=hh<10 else 0; f["is_ny_overlap"]=1 if 12<=hh<16 else 0; f["is_deadzone"]=1 if (hh<7 or hh>=20) else 0
        # flow-ortogonais
        lb=s[i]; lr2=max(lb["h"]-lb["l"],1e-9); low_cp=(lb["c"]-lb["l"])/lr2
        f["low_closepos"]=round(low_cp,2); f["absorption"]=1 if (f["vol_low_vs_med"]>=1.2 and low_cp>=0.66) else 0
        seg2=s[max(0,i-12):i+1]; mlow=min(b["l"] for b in seg2); f["bars_since_lowest"]=cj-max(b for b in range(max(0,i-12),i+1) if s[b]["l"]==mlow)
        t0=s[max(0,i-24)]["t"]; sells=[x for x in kb(bub,bt,t0,tc,tc) if x["side"]=="SELL"]; half=(t0+tc)//2
        old=sum(SZ[x["size"]] for x in sells if x["t"]<half); rec=sum(SZ[x["size"]] for x in sells if x["t"]>=half)
        f["sell_decel"]=round((old-rec)/(old+1e-6),2)
        th=[t0+(tc-t0)*q/3 for q in range(4)]; w3=[sum(SZ[x["size"]] for x in sells if th[q]<=x["t"]<th[q+1]) for q in range(3)]
        f["flow_accel"]=round((w3[0]-w3[1])-(w3[1]-w3[2]),2)
        last_sell=max((x["t"] for x in sells),default=None); f["bars_since_sell"]=round((tc-last_sell)/900) if last_sell else 99
        allb=kb(bub,bt,s[max(0,i-20)]["t"],tc,tc); bbar={}
        for x in allb: bbar.setdefault(x["t"]//900,{"b":0,"s":0}); bbar[x["t"]//900]["b" if x["side"]=="BUY" else "s"]+=SZ[x["size"]]
        bars=sorted(bbar); r4b=sum(bbar[kk]["b"] for kk in bars[-4:]) if bars else 0; r4s=sum(bbar[kk]["s"] for kk in bars[-4:]) if bars else 0
        f["buy_sell_ratio4"]=round(r4b/(r4s+1),2)
        present=set(x["t"]//900 for x in allb); run=mx=0
        for bb2 in range(i-20,i+1):
            if bb2<0: continue
            if bb2 in present: run=0
            else: run+=1; mx=max(mx,run)
        f["max_silence"]=mx
        bull=[e for e in smc if e.get("t") and e["t"]<=tc and ("BOS" in str(e.get("text","")) or "CHoCH" in str(e.get("text","")))]
        if bull:
            ev=max(bull,key=lambda e:e["t"]); f["smc_lag_bars"]=round((tc-ev["t"])/900); f["buy_after_smc"]=1 if any(x["side"]=="BUY" and x["t"]>ev["t"] for x in allb) else 0
            f["naslong_after_smc"]=1 if any(e["dir"]=="LONG" and ev["t"]<e["t"]<=tc for e in nas) else 0
        else: f["smc_lag_bars"]=999; f["buy_after_smc"]=0; f["naslong_after_smc"]=0
        def skew(lst): Lc=sum(1 for x in lst if x["size"]=="L"); Sc=sum(1 for x in lst if x["size"]=="S"); return Lc/(Sc+1)
        f["sell_skew_mig"]=round(skew([x for x in sells if x["t"]<half])-skew([x for x in sells if x["t"]>=half]),2)
        f["buy_L_recent"]=1 if any(x["side"]=="BUY" and x["size"]=="L" and x["t"]>=half for x in allb) else 0
        f["regime_age_h"]=round(regime_age_h(tc),1); f["smc_bos"]=sum(1 for e in smc if e.get("t") and tc-48*900<=e["t"]<=tc and "BOS" in str(e.get("text","")))
        rec_={"block":k[:10],"low_t":s[i]["t"],"yr":dt.datetime.utcfromtimestamp(s[i]["t"]).year,"R":round(R,2),"win":int(R>0),"cj":cj,"low_idx":i}
        rec_.update(f); out.write(json.dumps(rec_)+"\n"); n+=1
out.close()
rows=[json.loads(l) for l in (HERE/"dataset_5atr.jsonl").read_text().splitlines()]
print(f"dataset_5atr.jsonl: {n} candidatos 5ATR (sem dedup) | WR base={100*sum(r['win'] for r in rows)/len(rows):.1f}% avgR={sum(r['R'] for r in rows)/len(rows):+.2f}")
print("  features:",len([x for x in rows[0] if x not in ('block','low_t','yr','R','win','cj','low_idx')]))
