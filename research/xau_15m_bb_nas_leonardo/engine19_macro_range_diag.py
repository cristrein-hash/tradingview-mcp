#!/usr/bin/env python3
"""ENGINE 19 (Cris 2026-06-28): DIAGNÓSTICO do erro de leitura de fundo-de-range. Recalcula posição da entrada
contra o RANGE MACRO (running hi/lo desde o início do episódio RANGE), não o Donchian micro de 1 dia. Reconciliação
de preço (min/max do meu dado no episódio ago/2025). Lista entradas base com macro_rpos + R, destaca fundo macro."""
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
# episódio RANGE contendo 2025-08-15
target=int(dt.datetime(2025,8,15).timestamp())//86400
i0=DK.index(min(DK,key=lambda k:abs(k-target)))
a=i0
while a>0 and reg[a-1]=="RANGE": a-=1
b=i0
while b<len(DK)-1 and reg[b+1]=="RANGE": b+=1
ep_start=DK[a]*86400; ep_end=(DK[b]+1)*86400
print(f"Episódio RANGE detectado: {dt.datetime.utcfromtimestamp(ep_start).strftime('%Y-%m-%d')} -> {dt.datetime.utcfromtimestamp(DK[b]*86400).strftime('%Y-%m-%d')}")
# preço do MEU dado no episódio (reconciliação offset)
epbars=[allbars[t] for t in T if ep_start<=t<ep_end]
lows=[x["l"] for x in epbars]; highs=[x["h"] for x in epbars]
print(f"MEU DADO no episódio: low {min(lows):.2f}  high {max(highs):.2f}  (range macro {max(highs)-min(lows):.1f})")
print(f"  (seu chart marca a caixa ~3431-3477; se diferente = offset de feed)")
# running macro hi/lo (causal) ao longo do episódio
macro={}
mh=ml=None
for t in T:
    if not (ep_start<=t<ep_end): continue
    x=allbars[t]; ml=x["l"] if ml is None else min(ml,x["l"]); mh=x["h"] if mh is None else max(mh,x["h"])
    macro[t]=(ml,mh)
# base entries (mesma pipeline) no episódio
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
def knife_v2(r):
    aa=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    bb=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return aa or bb
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[bb["l"] for bb in s]; lo=max(2,i-120); bst=None
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
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
ent=[]
for r in ROWS:
    tc=r["cj_t"]
    if not (ep_start<=tc<ep_end): continue
    if DAYREG.get(tc//86400,"RANGE")!="RANGE": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={bb["t"]:i for i,bb in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(tc)
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    ml_,mh_=macro.get(tc,(None,None))
    if ml_ is None or mh_<=ml_: continue
    mrpos=(entry-ml_)/(mh_-ml_)
    # micro rpos (96b) p/ comparar
    lo=max(0,cj-96); milo=min(x["l"] for x in s[lo:cj+1]); mihi=max(x["h"] for x in s[lo:cj+1])
    micro=(entry-milo)/(mihi-milo) if mihi>milo else .5
    ent.append({"date":dt.datetime.utcfromtimestamp(tc).strftime("%m-%d %H:%M"),"entry":round(entry,1),
        "macro_rpos":round(mrpos,2),"micro_rpos":round(micro,2),"R":round(R,2)})
ent.sort(key=lambda z:z["macro_rpos"])
print(f"\nEntradas base no episódio (N={len(ent)}), ordenadas por MACRO_rpos (0=fundo macro):")
print(f"{'data':<14}{'entry':>8}{'macro_rpos':>11}{'micro_rpos':>11}{'R':>7}")
for x in ent:
    flag=" <== fundo macro" if x["macro_rpos"]<=0.25 else (" (micro disse fundo)" if x["micro_rpos"]<=0.34 and x["macro_rpos"]>0.5 else "")
    print(f"{x['date']:<14}{x['entry']:>8}{x['macro_rpos']:>11}{x['micro_rpos']:>11}{x['R']:>7}{flag}")
# resumo: quantos micro-fundo são macro-topo
mis=[x for x in ent if x["micro_rpos"]<=0.34 and x["macro_rpos"]>0.5]
print(f"\nDISCREPÂNCIA: {len(mis)} entradas que o micro chamou de FUNDO (<=0.34) estão na METADE SUPERIOR do range MACRO (>0.5)")
mb=[x for x in ent if x["macro_rpos"]<=0.25]
print(f"Entradas REALMENTE no fundo macro (macro_rpos<=0.25): N={len(mb)} | avgR {st.mean([x['R'] for x in mb]) if mb else 0:.2f}")
