#!/usr/bin/env python3
"""SANITY_PROBE — valida corte loser h1_pos sobre swept-sempre: sensibilidade thr + null (corte aleatório mesmo N)."""
import json,statistics as st,random
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
N,ef,slp,Rt,K,Kb=15,0.30,0.20,2.0,5,5
def raw(i):
    if i<max(2*N,40): return "RANGE"
    a=atrd(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; pa=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); e=abs(net)/pa if pa>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; s100=(E100[i]-E100[i-10])/a
    tu=e>=ef and slope>slp; td=e>=ef and slope<-slp; sb=E50[i]>E100[i] and s100>0; se=E50[i]<E100[i] and s100<0
    cont=e<ef and 0.15<=pos<=0.85 and abs(slope)<slp
    pk=max(DH[i-30:i+1]); rt=(pk-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (rt>=Rt and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rl=[raw(i) for i in range(len(DK))]; reg=[]; cur="RANGE"; pend=None; pn=0
for v in rl:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    if pn>=(Kb if pend=="BEAR" else K): cur=pend; pend=None; pn=0
    reg.append(cur)
DR={DK[i]:reg[i] for i in range(len(DK))}
HMAX=480; RCAP=20.0
def cfl(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def lr(s,cj,e,sl,a):
    risk=e-sl
    if risk<=0: return None
    tr=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=tr: ex=tr; break
        if (s[k]["h"]-e)/risk>=1: r1=True
        if r1:
            sw=cfl(s,k)
            if sw: tr=max(tr,sw-0.1*a)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-e)/risk))
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
def knife(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
base=[]
for r in ROWS:
    if f(r,"swept_prior_low",0)!=1: continue
    pr=PRIMK.get(r["block"]); s=pr["series"]; tm={b["t"]:i for i,b in enumerate(s)}
    p=tm.get(r["t"]); cj=tm.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife(r): continue
    if DR.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    a=s[p]["atr"] or s[cj]["atr"]
    if not a: continue
    e=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*a; R=lr(s,cj,e,sl,a)
    if R is None: continue
    r["_R"]=R; r["_h1"]=f(r,"h1_pos",0.5); base.append(r)
base.sort(key=lambda z:z["cj_t"])
def metr(rows):
    R=[x["_R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; n=len(R); sm=sum(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1)
nb,wb,smb,avb,ddb=metr(base)
print(f"BASE swept-sempre: N{nb} WR{wb} sumR{smb} avgR{avb} DD{ddb}")
print("\nSENSIBILIDADE h1_pos>=thr (corta abaixo):")
for thr in (0.40,0.44,0.50):
    kept=[t for t in base if t["_h1"]>=thr]; n,w,sm,av,dd=metr(kept)
    py={y:round(sum(t["_R"] for t in kept if t["yr"]==y),1) for y in (2024,2025,2026)}
    print(f"  h1_pos>={thr}: N{n} WR{w} sumR{sm} avgR{av} DD{dd} (cortou {nb-n}) yr {py[2024]}/{py[2025]}/{py[2026]}")
thr=0.44; kept=[t for t in base if t["_h1"]>=thr]; ncut=nb-len(kept)
_,_,sm_o,av_o,dd_o=metr(kept)
rng=random.Random(20260628); avs=[]; sms=[]; dds=[]
for _ in range(500):
    idx=set(rng.sample(range(nb),ncut)); k=[base[i] for i in range(nb) if i not in idx]
    _,_,sm,av,dd=metr(k); avs.append(av); sms.append(sm); dds.append(dd)
def pct(a,v): return 100*sum(1 for x in a if x>=v)/len(a)
print(f"\nNULL corte aleatório de {ncut} (500 reps) vs h1_pos<0.44:")
print(f"  avgR: null mean {st.mean(avs):.3f} [p95 {sorted(avs)[475]:.3f}] | h1 {av_o:.3f} | random>=h1 {pct(avs,av_o):.0f}% (p={pct(avs,av_o)/100:.3f})")
print(f"  sumR: null mean {st.mean(sms):.1f} | h1 {sm_o:.1f} | random>=h1 {pct(sms,sm_o):.0f}%")
print(f"  DD:   null mean {st.mean(dds):.1f} | h1 {dd_o:.1f}")
