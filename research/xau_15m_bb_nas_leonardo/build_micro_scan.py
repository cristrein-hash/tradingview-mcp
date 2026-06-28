#!/usr/bin/env python3
"""ENGINE MICRO (Cris 2026-06-28): substrato do engine multi-agente. Sobre a base APROVADA swept-sempre (N896),
computa ~30 lentes MICRO-ESTRUTURAIS causais (candle/swing/momentum/compressão/localização/fluxo) a partir das
barras 15M até cj. Para cada lente: std-diff W/L + STACK sobre h1_pos>=0,44 (losers cortados vs runners cortados,
avgR/sumR/DD). Também exporta sweptsempre_micro.jsonl (janela+features) p/ os agentes. Determinístico."""
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
def micro(s,p,cj,atr):
    o=lambda i:s[i]["o"]; h=lambda i:s[i]["h"]; l=lambda i:s[i]["l"]; c=lambda i:s[i]["c"]
    rsi=lambda i:s[i].get("rsi") or 50; vol=lambda i:s[i].get("v") or 0; e21=lambda i:s[i].get("ema21") or c(i)
    a=atr or 1.0; M={}
    M["body_cj"]=(c(cj)-o(cj))/a
    M["close_pos_cj"]=(c(cj)-l(cj))/((h(cj)-l(cj)) or a)
    M["low_wick_p"]=(min(o(p),c(p))-l(p))/a
    M["low_wick_cj"]=(min(o(cj),c(cj))-l(cj))/a
    av5=sum(s[i].get("v") or 0 for i in range(max(0,cj-4),cj+1))/5; av20=sum(s[i].get("v") or 0 for i in range(max(0,cj-19),cj+1))/20 or 1
    M["vol_p_spike"]=(vol(p))/av20; M["vol_cj"]=(vol(cj))/av20
    a5=sum(s[i].get("atr") or a for i in range(max(0,cj-4),cj+1))/5; a20=sum(s[i].get("atr") or a for i in range(max(0,cj-19),cj+1))/20 or a
    M["atr_contraction"]=a5/a20
    M["rsi_cj"]=rsi(cj); M["rsi_slope3"]=rsi(cj)-rsi(cj-3); M["rsi_min8"]=min(rsi(i) for i in range(max(0,cj-7),cj+1))
    M["dist_ema21"]=(c(cj)-e21(cj))/a; M["ema21_slope"]=(e21(cj)-e21(max(0,cj-5)))/a
    M["reclaim_speed"]=(c(cj)-l(p))/a
    hl=0
    for i in range(max(2,cj-8),cj+1):
        if l(i)>l(i-1): hl+=1
    M["higher_lows8"]=hl
    M["micro_bos_up"]=1 if c(cj)>max(h(i) for i in range(max(0,cj-5),cj)) else 0
    M["up_closes5"]=sum(1 for i in range(max(1,cj-4),cj+1) if c(i)>c(i-1))
    lo20=min(l(i) for i in range(max(0,cj-19),cj+1)); hi20=max(h(i) for i in range(max(0,cj-19),cj+1))
    M["pos_recent20"]=(c(cj)-lo20)/((hi20-lo20) or a)
    M["room_recent20"]=(hi20-c(cj))/a
    dd=0
    for i in range(max(1,p-5),p+1):
        if c(i)<c(i-1): dd+=1
    M["downcloses_pre"]=dd
    M["dip_depth"]=(max(h(i) for i in range(max(0,p-10),p+1))-l(p))/a
    acc=sum(1 for i in range(p,cj+1) if c(i)>l(p)+0.5*a)
    M["acceptance"]=acc
    M["up_velocity"]=(c(cj)-l(p))/a/max(1,cj-p)
    M["range_cj"]=(h(cj)-l(cj))/a
    return M
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
base=[]; export=[]
for r in ROWS:
    if f(r,"swept_prior_low",0)!=1: continue
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    M=micro(s,p,cj,atr)
    rec={"cj_t":r["cj_t"],"yr":r["yr"],"R":round(R,3),"h1_pos":f(r,"h1_pos",0.5),"micro":{k:round(v,3) for k,v in M.items()},
         "feat":{k:f(r,k) for k in ("reclaim_atr","clean_sky_atr","sell_bub_w","nas_long_16","legpos90","pullback_depth","in_demand","dist_demand_atr","n_supply_overhead","atr_regime","up_closes_pc")}}
    r["_R"]=R; r["_M"]=M; r["_h1"]=f(r,"h1_pos",0.5); base.append(r); export.append(rec)
with open(HERE/"sweptsempre_micro.jsonl","w") as fh:
    for rec in export: fh.write(json.dumps(rec)+"\n")
NB=len(base); loser=lambda t:t["_R"]<=0; runner=lambda t:t["_R"]>=3
print(f"BASE swept-sempre N={NB} | export sweptsempre_micro.jsonl OK | losers {sum(1 for t in base if loser(t))} runners {sum(1 for t in base if runner(t))}")
FE=list(base[0]["_M"].keys())
def val(t,k): return t["_M"].get(k)
W=[t for t in base if t["_R"]>0]; L=[t for t in base if t["_R"]<=0]
def m(g,k):
    v=[val(t,k) for t in g if val(t,k) is not None]; return (st.mean(v),st.pstdev(v) if len(v)>1 else 0) if v else (0,0)
print("\n=== std-diff WIN vs LOSER (lentes micro) — |>=0.12| ===")
sep=[]
for k in FE:
    mw,sw=m(W,k); ml,sl_=m(L,k); sp=((sw**2+sl_**2)/2)**0.5 or 1
    sep.append(((mw-ml)/sp,k,round(mw,2),round(ml,2)))
for d,k,mw,ml in sorted(sep,key=lambda z:-abs(z[0])):
    if abs(d)>=0.12: print(f"  {k:<18} win {mw:>8} | loser {ml:>8} | std-diff {d:>+6.2f}")
# STACK sobre h1_pos>=0.44
H=[t for t in base if t["_h1"]>=0.44]
def panel(rows):
    R=[x["_R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; n=len(R); sm=sum(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    nl=sum(1 for x in R if x<=0); nr=sum(1 for x in R if x>=3)
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),nl,nr
nH,wH,smH,avH,ddH,nlH,nrH=panel(H)
print(f"\n=== STACK sobre h1_pos>=0.44 (base do stack: N{nH} avgR{avH} losers{nlH} runners{nrH}) ===")
print("(corta lado-loser de cada lente; mantém runners ao máximo)")
res=[]
for d,k,_,_ in sorted(sep,key=lambda z:-abs(z[0])):
    if abs(d)<0.12: continue
    vals=sorted(val(t,k) for t in H if val(t,k) is not None)
    if len(vals)<20: continue
    q1=vals[len(vals)//4]; q3=vals[3*len(vals)//4]
    if d>0: kept=[t for t in H if val(t,k) is None or val(t,k)>=q1]; cut=f"{k}>=~q1"
    else: kept=[t for t in H if val(t,k) is None or val(t,k)<=q3]; cut=f"{k}<=~q3"
    n,w,sm,av,dd,nl,nr=panel(kept)
    res.append((av,cut,n,w,sm,av,dd,nl,nr,nlH-nl,nrH-nr))
print(f"{'corte (sobre h1)':<22}{'N':>5}{'WR':>6}{'sumR':>7}{'avgR':>7}{'DD':>7}{'losL':>6}{'runL':>6}{'efic':>6}")
for av,cut,n,w,sm,a,dd,nl,nr,dl,dr in sorted(res,reverse=True):
    efic=round(dl/dr,1) if dr>0 else 99.9
    print(f"{cut:<22}{n:>5}{w:>6}{sm:>7}{a:>7}{dd:>7}{dl:>6}{dr:>6}{efic:>6}")
print("\n(losL=losers cortados, runL=runners cortados, efic=losL/runL — alto=corta loser preservando runner)")
