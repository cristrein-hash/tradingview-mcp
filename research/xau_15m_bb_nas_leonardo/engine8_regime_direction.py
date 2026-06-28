#!/usr/bin/env python3
"""ENGINE 8 (Cris 2026-06-28): teste direção-por-regime. LONG só em BULL/RANGE (universo knife-gated), SHORT só em BEAR
(espelho: fractais de topo + let-run short). Régua let-run, detector regime v2 (causal). Reporta cada perna + combinado."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
# ---- regime diário v2 ----
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
def regime_at(t): return DAYREG.get(t//86400,"RANGE")
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def cf_high(s,i):
    Hh=[b["h"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if Hh[p]==max(Hh[p-2:p+3]): bst=Hh[p]
    return bst
def letrun_long(s,cj,entry,sl,atr):
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
def letrun_short(s,cj,entry,sl,atr):
    risk=sl-entry
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["h"]>=trail: ex=trail; break
        if (entry-s[k]["l"])/risk>=1: r1=True
        if r1:
            sw=cf_high(s,k)
            if sw: trail=min(trail,sw+0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(entry-ex)/risk))
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
# ---- LONG: universo knife-gated + regime ----
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
def knife_v2(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
longs=[]
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    R=letrun_long(s,cj,s[cj]["c"],min(x["l"] for x in s[p:cj+1])-0.1*atr,atr)
    if R is None: continue
    longs.append({"t":r["cj_t"],"R":R,"reg":regime_at(r["cj_t"]),"yr":r["yr"],"dir":"L"})
# ---- SHORT: fractais de topo (k=3) + let-run short ----
shorts=[]
for bkey,pr in PRIMK.items():
    s=pr["series"]; nn=len(s); Hh=[b["h"] for b in s]
    last=-99
    for p in range(96,nn-4):
        if Hh[p]!=max(Hh[p-3:p+4]): continue
        cj=p+3
        if cj>=nn-2 or cj-last<3: continue
        atr=s[p]["atr"]
        if not atr: continue
        last=cj; entry=s[cj]["c"]; sl=max(x["h"] for x in s[p:cj+1])+0.1*atr
        R=letrun_short(s,cj,entry,sl,atr)
        if R is None: continue
        import datetime as dt
        shorts.append({"t":s[cj]["t"],"R":R,"reg":regime_at(s[cj]["t"]),"yr":dt.datetime.utcfromtimestamp(s[cj]["t"]).year,"dir":"S"})
def metr(rows):
    n=len(rows)
    if not n: return None
    rs=[x["R"] for x in sorted(rows,key=lambda z:z["t"])]; sm=sum(rs); w=sum(1 for x in rs if x>0)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),py
def show(tag,rows):
    m=metr(rows)
    if not m: print(f"{tag:<34} (vazio)"); return
    n,wr,sm,avg,dd,py=m
    print(f"{tag:<34}{n:>5}{wr:>6}{sm:>8}{avg:>7}{dd:>8}  {py[2024]}/{py[2025]}/{py[2026]}")
print(f"LONG univ (knife-gated)={len(longs)} | SHORT univ (topos)={len(shorts)}")
print(f"\n{'cenário':<34}{'N':>5}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>8}  yr24/25/26")
show("LONG todos (knife-gated)",longs)
show("LONG só BULL+RANGE",[x for x in longs if x["reg"] in ("BULL","RANGE")])
show("  (LONG em BEAR — excluído)",[x for x in longs if x["reg"]=="BEAR"])
show("SHORT todos (topos)",shorts)
show("SHORT só BEAR",[x for x in shorts if x["reg"]=="BEAR"])
show("  (SHORT fora de BEAR — excluído)",[x for x in shorts if x["reg"]!="BEAR"])
combo=[x for x in longs if x["reg"] in ("BULL","RANGE")]+[x for x in shorts if x["reg"]=="BEAR"]
show("COMBO LONG(BULL/RANGE)+SHORT(BEAR)",combo)
