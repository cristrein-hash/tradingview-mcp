#!/usr/bin/env python3
"""ENGINE 14 (Cris 2026-06-28): MAPEAMENTO trade-a-trade dos clusters de pequenos ranges (base fixa 3120+h4_up&h1d_up).
Objetivo: o que diferencia a ENTRADA-RUNNER das irmãs no cluster + assinatura dos redundantes-corretos (que ganham).
SEM supressão, SEM refutação — só caracterização causal (features no cj) vs outcome. Posicional + por-feature
(pooled runner-vs-loser e RELATIVO dentro do cluster runner-vs-irmãs)."""
import json,statistics as st,datetime as dt
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
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
base=[]
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr
    R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    r["_R"]=R; r["_entry"]=entry; r["_atr"]=atr; r["_reg"]=DAYREG.get(r["cj_t"]//86400,"RANGE")
    base.append(r)
base.sort(key=lambda z:z["cj_t"])
# clusters: G barras + D ATR mesmo nivel (captura pequenos ranges)
G,D=24,1.0
clusters=[]; cur=[base[0]]
for a,b in zip(base,base[1:]):
    gap=(b["cj_t"]-a["cj_t"])/900
    near=abs(b["_entry"]-a["_entry"])<=D*b["_atr"]
    if gap<=G and near: cur.append(b)
    else: clusters.append(cur); cur=[b]
clusters.append(cur)
multi=[c for c in clusters if len(c)>=2]
allc=[t for c in multi for t in c]
print(f"BASE={len(base)} | clusters(>=2)={len(multi)} | trades em cluster={len(allc)} | tam medio {st.mean(len(c) for c in multi):.1f} | (G={G}b D={D}ATR)")
def cls(R): return "RUN" if R>=3 else ("WIN" if R>0 else "LOSS")
# posicional dentro do cluster
for c in multi:
    n=len(c); rs=[t["_R"] for t in c]; lo=min(t["_entry"] for t in c); hi=max(t["_entry"] for t in c)
    for i,t in enumerate(c):
        t["_pos_t"]=i/(n-1) if n>1 else 0          # 0=primeira 1=ultima (tempo)
        t["_is_first"]=(i==0); t["_is_last"]=(i==n-1)
        t["_pos_p"]=(t["_entry"]-lo)/(hi-lo) if hi>lo else 0.5  # 0=mais baixa 1=mais alta
        t["_is_lowest"]=(t["_entry"]==lo); t["_csize"]=n
print("\n=== POSICIONAL: taxa de RUNNER (R>=3) e avgR por posição no cluster ===")
def grp(pred,tag):
    g=[t for t in allc if pred(t)]
    if not g: print(f"  {tag:<26} vazio"); return
    R=[t["_R"] for t in g]; run=sum(1 for x in R if x>=3); win=sum(1 for x in R if x>0)
    print(f"  {tag:<26} N{len(g):>4} | RUNNER% {100*run/len(g):>4.1f} | WIN% {100*win/len(g):>4.1f} | avgR {sum(R)/len(R):>6.3f}")
grp(lambda t:t["_is_first"],"1ª do cluster (tempo)")
grp(lambda t:t["_is_last"],"última do cluster (tempo)")
grp(lambda t:not t["_is_first"] and not t["_is_last"],"meio do cluster")
grp(lambda t:t["_is_lowest"],"mais BAIXA (preço) do cluster")
grp(lambda t:not t["_is_lowest"],"não-mais-baixa")
grp(lambda t:t["_pos_p"]<=0.34,"terço inferior do cluster")
grp(lambda t:t["_pos_p"]>=0.66,"terço superior do cluster")
# por-feature: pooled RUNNER vs LOSS (dentro de clusters)
FEATS=["reclaim_atr","reclaim_ema_bars","downleg_eff","downleg_decel","pullback_depth","legpos60","legpos90",
"rsi_low","rsi_min8","atr_regime","atr_compression_pre","dist_demand_atr","clean_sky_atr","n_supply_overhead",
"n_demand_near","sell_bub_w","buy_bub_w","nas_long_16","confirm_body_atr","low_wick","up_closes_pc","micro_hl",
"swept_prior_low","in_demand","demand_reclaim","h4n_rsi","h1n_rsi","h4n_clean_sky_atr","h1_pos","h4_pos","_pos_t","_pos_p"]
run=[t for t in allc if t["_R"]>=3]; loss=[t for t in allc if t["_R"]<=0]
def m(g,k): v=[f(t,k) for t in g if f(t,k) is not None]; return (st.mean(v),st.pstdev(v) if len(v)>1 else 0,len(v)) if v else (0,0,0)
print(f"\n=== POOLED em clusters: RUNNER(R>=3,N{len(run)}) vs LOSS(R<=0,N{len(loss)}) — std-diff (Cohen-like) ===")
rows=[]
for k in FEATS:
    mr,sr,nr=m(run,k); ml,sl_,nl=m(loss,k); sp=((sr**2+sl_**2)/2)**0.5 or 1
    rows.append(((mr-ml)/sp,k,round(mr,3),round(ml,3)))
for d,k,mr,ml in sorted(rows,key=lambda z:-abs(z[0])):
    if abs(d)>=0.12: print(f"  {k:<20} run {mr:>8} | loss {ml:>8} | std-diff {d:>+6.2f}")
# RELATIVO dentro do cluster: runner (maxR) vs irmãs, clusters size>=3
big=[c for c in multi if len(c)>=3]
print(f"\n=== RELATIVO: dentro de cada cluster (>=3, N={len(big)}), RUNNER=maxR vs média das IRMÃS — Δ e consistência sinal ===")
rel={k:[] for k in FEATS}
for c in big:
    win=max(c,key=lambda t:t["_R"]); sib=[t for t in c if t is not win]
    for k in FEATS:
        wv=f(win,k); sv=[f(t,k) for t in sib if f(t,k) is not None]
        if wv is not None and sv: rel[k].append(wv-st.mean(sv))
out=[]
for k,vals in rel.items():
    if len(vals)<8: continue
    md=st.mean(vals); cons=sum(1 for x in vals if x>0)/len(vals); sd=st.pstdev(vals) or 1
    out.append((md/sd,k,round(md,3),round(100*cons),len(vals)))
for z,k,md,cons,n in sorted(out,key=lambda z:-abs(z[0])):
    if abs(z)>=0.12: print(f"  {k:<20} Δ(run-irmãs) {md:>8} | mesmo-sinal {cons:>3}% | norm {z:>+6.2f} (n{n})")
