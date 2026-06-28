#!/usr/bin/env python3
"""Exporta a base SUBSTRATO #4 (swept-sempre + h1_pos>=0.44 + pos_recent20>=q0.25 + rsi_cj>=q0.2) com TODAS as
features causais de NAS / Bubbles / OB Detector / SMC-CHoCH (15m + nativo 4H/1D) -> substrate4_flow.jsonl.
Para o engine multi-agente de fluxo. Determinístico, causal."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
allbars={}
for pr in PRIM.values():
    for b in pr["series"]: allbars.setdefault(b["t"],b)
days={}
for t in sorted(allbars):
    b=allbars[t]; k=t//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw(i):
    if i<max(2*N,40): return "RANGE"
    a=atrd(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; s100=(E100[i]-E100[i-10])/a
    tu=eff>=eff_thr and slope>slope_thr; td=eff>=eff_thr and slope<-slope_thr
    sb=E50[i]>E100[i] and s100>0; se=E50[i]<E100[i] and s100<0
    cont=eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rl=[raw(i) for i in range(len(DK))]; reg=[]; cur="RANGE"; pend=None; pn=0
for v in rl:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    if pn>=(Kbear if pend=="BEAR" else K): cur=pend; pend=None; pn=0
    reg.append(cur)
DAYREG={DK[i]:reg[i] for i in range(len(DK))}
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
def knife_v2(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
FLOW=["buy_bub_w","sell_bub_w","nas_long_16","in_demand","demand_reclaim","dist_demand_atr","clean_sky_atr",
"n_supply_overhead","n_demand_near","htf_demand_any","htf_demand_confluence","h4n_in_demand","h4n_dist_demand_atr",
"h1n_in_demand","h1n_dist_demand_atr","h4n_nas_long_rec","h1n_nas_long_rec","h4n_choch_up_rec","h1n_choch_up_rec",
"h4n_clean_sky_atr","h1n_clean_sky_atr"]
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
B=[]
for r in ROWS:
    if f(r,"swept_prior_low",0)!=1: continue
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    if f(r,"h1_pos",0.5)<0.44: continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    lo20=min(x["l"] for x in s[max(0,cj-19):cj+1]); hi20=max(x["h"] for x in s[max(0,cj-19):cj+1])
    pos20=(entry-lo20)/((hi20-lo20) or atr); rsicj=s[cj].get("rsi") or 50
    r["_R"]=R; r["_pos20"]=pos20; r["_rsi"]=rsicj; B.append(r)
def quant(vals,q): vs=sorted(vals); return vs[min(len(vs)-1,max(0,int(q*len(vs))))]
qpos=quant([x["_pos20"] for x in B],0.25); qrsi=quant([x["_rsi"] for x in B],0.2)
S4=[x for x in B if x["_pos20"]>=qpos and x["_rsi"]>=qrsi]
out=[]
for r in S4:
    flow={k:f(r,k) for k in FLOW}
    flow["sell_minus_buy"]=(f(r,"sell_bub_w",0) or 0)-(f(r,"buy_bub_w",0) or 0)
    flow["nas_any_rec"]=1 if (f(r,"nas_long_16",0)>=1 or f(r,"h4n_nas_long_rec",0)>=1 or f(r,"h1n_nas_long_rec",0)>=1) else 0
    flow["choch_any_rec"]=1 if (f(r,"h4n_choch_up_rec",0)>=1 or f(r,"h1n_choch_up_rec",0)>=1) else 0
    out.append({"cj_t":r["cj_t"],"yr":r["yr"],"R":round(r["_R"],3),"flow":{k:(round(v,3) if isinstance(v,float) else v) for k,v in flow.items()}})
with open(HERE/"substrate4_flow.jsonl","w") as fh:
    for rec in out: fh.write(json.dumps(rec)+"\n")
NB=len(out); ls=sum(1 for x in out if x["R"]<=0); rn=sum(1 for x in out if x["R"]>=3)
print(f"SUBSTRATO#4 N={NB} (qpos={qpos:.3f} qrsi={qrsi:.1f}) losers {ls} runners {rn} | export substrate4_flow.jsonl OK")
print("features fluxo:", list(out[0]["flow"].keys()))
