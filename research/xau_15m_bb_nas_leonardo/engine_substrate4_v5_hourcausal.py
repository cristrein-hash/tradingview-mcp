#!/usr/bin/env python3
"""SUBSTRATO #4 com regime v5 HOUR-CAUSAL: para cada entrada cj_t, regime = override 1H no último bar 1H fechado
<= cj_t + camada estável do último DIA fechado (D-1). Sem look-ahead intraday. Compara v2 / v5-dia / v5-hour."""
import json,bisect,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
bars={}
for pr in PRIM.values():
    for b in pr["series"]: bars.setdefault(b["t"],b)
T15=sorted(bars)
H={}
for t in T15:
    b=bars[t]; hk=t//3600; g=H.setdefault(hk,{"c":b["c"],"h":b["h"]}); g["h"]=max(g["h"],b["h"]); g["c"]=b["c"]
HK=sorted(H); HC=[H[k]["c"] for k in HK]; HH=[H[k]["h"] for k in HK]
days={}
for t in T15:
    b=bars[t]; k=t//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]
for i in range(1,len(DK)): TR.append(max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])))
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(arr,i,n):
    c=arr[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(DC,i,50) for i in range(len(DK))]; E100=[ema_at(DC,i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw_stable(i):
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
rawS=[raw_stable(i) for i in range(len(DK))]
stable=[]; cur="RANGE"; pend=None; pn=0
for v in rawS:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    need=Kbear if pend=="BEAR" else K
    if pn>=need: cur=pend; pend=None; pn=0
    stable.append(cur)
# override 1H estado POR HORA (recovery em horas = 5 dias = 120h)
P,mom,dd_intra,Krec_h=48,24,0.06,120
ov_hour=[]; ov=False; quiet=0
for j in range(len(HK)):
    if j<max(P,mom): ov_hour.append(False); continue
    peak=max(HH[j-P:j+1]); ddp=(peak-HC[j])/peak if peak>0 else 0
    fired= ddp>=dd_intra and HC[j]<HC[j-mom]
    if fired: ov=True; quiet=0
    elif ov:
        quiet+=1
        if quiet>=Krec_h: ov=False
    ov_hour.append(ov)
HKx=[hk for hk in HK]
def regime_hourcausal(cjt):
    dk_today=cjt//86400
    # último dia fechado: maior DK < dk_today
    di=bisect.bisect_left(DK,dk_today)-1
    st="RANGE" if di<0 else stable[di]
    # último bar 1H fechado <= cjt: maior j com (HK[j]+1)*3600 <= cjt
    hi=bisect.bisect_right(HKx,(cjt//3600)-1)-1   # hora anterior à hora de cjt (fechada)
    ovr= ov_hour[hi] if hi>=0 else False
    return "BEAR" if (ovr or st=="BEAR") else st
# regime por DIA v5 (p/ comparação) e v2
DAYREG_V2={DK[i]:stable[i] for i in range(len(DK))}
trig_h=set()
for j in range(max(P,mom),len(HK)):
    peak=max(HH[j-P:j+1]); ddp=(peak-HC[j])/peak if peak>0 else 0
    if ddp>=dd_intra and HC[j]<HC[j-mom]: trig_h.add(HK[j])
dset=set(hk*3600//86400 for hk in trig_h)
v5d=[]; ov=False; quiet=0
for i in range(len(DK)):
    fired=DK[i] in dset
    if fired: ov=True; quiet=0
    elif ov:
        quiet+=1
        if quiet>=5: ov=False
    v5d.append("BEAR" if (ov or stable[i]=="BEAR") else stable[i])
DAYREG_V5={DK[i]:v5d[i] for i in range(len(DK))}
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
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
QPOS,QRSI=0.346,45.5
cand=[]
for r in ROWS:
    if f(r,"swept_prior_low",0)!=1: continue
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    if f(r,"h1_pos",0.5)<0.44: continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    lo20=min(x["l"] for x in s[max(0,cj-19):cj+1]); hi20=max(x["h"] for x in s[max(0,cj-19):cj+1])
    pos20=(entry-lo20)/((hi20-lo20) or atr); rsicj=s[cj].get("rsi") or 50
    if pos20<QPOS or rsicj<QRSI: continue
    dk=r["cj_t"]//86400
    cand.append({"cj_t":r["cj_t"],"yr":r["yr"],"R":R,"v2":DAYREG_V2.get(dk,"RANGE"),
                 "v5d":DAYREG_V5.get(dk,"RANGE"),"v5h":regime_hourcausal(r["cj_t"])})
def panel(rows,tag):
    rows=sorted(rows,key=lambda z:z["cj_t"]); R=[x["R"] for x in rows]; n=len(R)
    if not n: print(f"{tag}: vazio"); return
    sm=sum(R); w=sum(1 for x in R if x>0); eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    py={y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
    print(f"{tag:<24} N{n:>4} WR{100*w/n:>5.1f}% W{w}/L{n-w} run{sum(1 for x in R if x>=3)} | sumR{sm:>7.1f} avgR{sm/n:>6.3f} DD{dd:>6.1f} r/DD{abs(sm/dd) if dd<0 else 99:>5.2f} streak-{mL}/+{mW} | yr {py[2024]}/{py[2025]}/{py[2026]}")
print("SUBSTRATO #4 — gate de regime:\n")
panel([c for c in cand if c["v2"]!="BEAR"],"#4 v2 (dia)")
panel([c for c in cand if c["v5d"]!="BEAR"],"#4 v5 (dia)")
panel([c for c in cand if c["v5h"]!="BEAR"],"#4 v5 HOUR-CAUSAL")
base=[c for c in cand if c["v2"]!="BEAR"]
cuth=[c for c in base if c["v5h"]=="BEAR"]; cutd=[c for c in base if c["v5d"]=="BEAR"]
cuth.sort(key=lambda z:z["cj_t"])
print(f"\nv5-HOUR corta {len(cuth)} (v5-dia cortava {len(cutd)}): losers {sum(1 for c in cuth if c['R']<=0)} winners {sum(1 for c in cuth if c['R']>0)} sumR {sum(c['R'] for c in cuth):.1f}")
for c in cuth: print(f"  {dt.datetime.utcfromtimestamp(c['cj_t']).strftime('%Y-%m-%d %H:%M')}  R {c['R']:+.2f}  (v5d={c['v5d']})")
