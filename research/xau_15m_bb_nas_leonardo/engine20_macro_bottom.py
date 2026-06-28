#!/usr/bin/env python3
"""ENGINE 20 (Cris 2026-06-28): testa entrada de FUNDO-MACRO de range em 2 frames — (2) episódio do detector v2
(running hi/lo) e (3) Donchian longo (N dias). Em cada: candidatos fractais em RANGE, macro_rpos<=thr (fundo),
COM e SEM gate HTF-up. let-run, painel completo (incl streak)+por-ano. Vê se capturar a golden zone é produtivo."""
import json,statistics as st,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
allbars={}
for pr in PRIM.values():
    for b in pr["series"]: allbars.setdefault(b["t"],b)
T=sorted(allbars)
days={}
for t in T:
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
# (2) episódio RANGE: running hi/lo desde início do episódio
macro_ep={}; ml=mh=None; last="X"
for t in T:
    dr=DAYREG.get(t//86400,"X"); x=allbars[t]
    if dr=="RANGE":
        if last!="RANGE": ml=mh=None
        ml=x["l"] if ml is None else min(ml,x["l"]); mh=x["h"] if mh is None else max(mh,x["h"])
        macro_ep[t]=(ml,mh)
    last=dr
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
DON=480  # Donchian longo (~5 dias 15m)
cand=[]
for r in ROWS:
    tc=r["cj_t"]
    if DAYREG.get(tc//86400,"RANGE")!="RANGE": continue   # só RANGE (fundo de range)
    if knife_v2(r): continue
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(tc)
    if p is None or cj is None or cj+2>=len(s): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    # frame 2: episódio
    ep=macro_ep.get(tc); rpe=(entry-ep[0])/(ep[1]-ep[0]) if ep and ep[1]>ep[0] else None
    # frame 3: Donchian longo
    lo=max(0,cj-DON); dlo=min(x["l"] for x in s[lo:cj+1]); dhi=max(x["h"] for x in s[lo:cj+1])
    rpd=(entry-dlo)/(dhi-dlo) if dhi>dlo else None
    cand.append({"cj_t":tc,"yr":r["yr"],"R":R,"htf":(f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1),
                 "rpe":rpe,"rpd":rpd})
def panel(rows,tag):
    n=len(rows)
    if not n: print(f"{tag:<40} vazio"); return
    R=[x["R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; sm=sum(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    py={y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
    print(f"{tag:<40} N{n:>4} WR{100*w/n:>5.1f}% sumR{sm:>7.1f} avgR{sm/n:>6.3f} DD{dd:>6.1f} r/DD{abs(sm/dd) if dd<0 else 99:>5.2f} streak-{mL}/+{mW}  yr {py[2024]}/{py[2025]}/{py[2026]}")
print(f"Candidatos fractais em RANGE (knife-ok): {len(cand)} | com HTF-up: {sum(1 for c in cand if c['htf'])}\n")
print("=== FRAME 2 (episódio detector) — fundo macro ===")
for thr in (0.25,0.34,0.5):
    base=[c for c in cand if c["rpe"] is not None and c["rpe"]<=thr]
    panel([c for c in base],f"rpe<={thr} TODOS")
    panel([c for c in base if c["htf"]],f"rpe<={thr} +HTF-up")
    panel([c for c in base if not c["htf"]],f"rpe<={thr} SEM HTF (fundo puro)")
print("\n=== FRAME 3 (Donchian longo ~5d) — fundo macro ===")
for thr in (0.25,0.34,0.5):
    base=[c for c in cand if c["rpd"] is not None and c["rpd"]<=thr]
    panel([c for c in base],f"rpd<={thr} TODOS")
    panel([c for c in base if c["htf"]],f"rpd<={thr} +HTF-up")
    panel([c for c in base if not c["htf"]],f"rpd<={thr} SEM HTF (fundo puro)")
