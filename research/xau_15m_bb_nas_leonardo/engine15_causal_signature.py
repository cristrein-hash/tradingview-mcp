#!/usr/bin/env python3
"""ENGINE 15 (Cris 2026-06-28): aprofunda o mapa SÓ com features causais (cj-known, sem look-ahead, sem posição
relativa-ao-cluster). Mede cada sinal e composições: N, RUNNER%(R>=3), WIN%, avgR, por-ano, top5% concentração.
+ keep-test: usar assinatura como regra de MANTER dentro do cluster (vs keep-all) — ver se seleciona sem capar runner.
Anti-ilusão inline (por-ano+concentração+N). Base fixa 3120+h4_up&h1d_up."""
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
    r["_R"]=R; r["_entry"]=entry; r["_atr"]=atr
    base.append(r)
base.sort(key=lambda z:z["cj_t"])
NB=len(base); baseAvg=sum(t["_R"] for t in base)/NB
def med(k): v=[f(t,k) for t in base if f(t,k) is not None]; return st.median(v) if v else 0
M={k:med(k) for k in ("clean_sky_atr","h4n_clean_sky_atr","rsi_low","pullback_depth","reclaim_atr","legpos90","h4n_dist_demand_atr")}
# sinais causais (per-entry, cj-known)
def sig(t):
    return {
      "swept": f(t,"swept_prior_low",0)==1,
      "cleansky4h": f(t,"h4n_clean_sky_atr",0)>=M["h4n_clean_sky_atr"],
      "cleansky15": f(t,"clean_sky_atr",0)>=M["clean_sky_atr"],
      "oversold": f(t,"rsi_low",50)<=M["rsi_low"],
      "deeppull": f(t,"pullback_depth",0)>=M["pullback_depth"],
      "reclaim": f(t,"reclaim_atr",0)>=M["reclaim_atr"],
      "h4demanda_perto": f(t,"h4n_dist_demand_atr",99)<=M["h4n_dist_demand_atr"],
      "naslong": f(t,"nas_long_16",0)>=1,
    }
for t in base: t["_s"]=sig(t)
def stats(g):
    n=len(g)
    if not n: return None
    R=[t["_R"] for t in g]; sm=sum(R); run=sum(1 for x in R if x>=3); win=sum(1 for x in R if x>0)
    top=sorted(R,reverse=True); t5=100*sum(top[:5])/sm if sm>0 else 0
    py={y:round(sum(t["_R"] for t in g if t["yr"]==y),1) for y in (2024,2025,2026)}
    eq=pk=dd=0
    for x in sorted([(t["cj_t"],t["_R"]) for t in g]):
        eq+=x[1]; pk=max(pk,eq); dd=min(dd,eq-pk)
    return n,100*run/n,100*win/n,sm/n,sm,round(t5),round(dd,1),py
def line(tag,g):
    s=stats(g)
    if not s: print(f"  {tag:<28} vazio"); return
    n,rp,wp,av,sm,t5,dd,py=s
    print(f"  {tag:<28} N{n:>4} RUN%{rp:>5.1f} WIN%{wp:>5.1f} avgR{av:>6.3f} sumR{sm:>7.1f} DD{dd:>6} top5{t5:>3}%  yr {py[2024]}/{py[2025]}/{py[2026]}")
print(f"BASE N{NB} avgR{baseAvg:.3f} | RUN%{100*sum(1 for t in base if t['_R']>=3)/NB:.1f} WIN%{100*sum(1 for t in base if t['_R']>0)/NB:.1f}\n")
print("=== SINAIS CAUSAIS ISOLADOS (grupo TRUE) ===")
for k in base[0]["_s"]:
    line(k,[t for t in base if t["_s"][k]])
print("\n=== COMPOSIÇÕES (backbone swept + clean_sky) ===")
combos=[("swept+cleansky4h",lambda t:t["_s"]["swept"] and t["_s"]["cleansky4h"]),
        ("swept+cleansky15",lambda t:t["_s"]["swept"] and t["_s"]["cleansky15"]),
        ("swept+reclaim",lambda t:t["_s"]["swept"] and t["_s"]["reclaim"]),
        ("swept+cleansky4h+reclaim",lambda t:t["_s"]["swept"] and t["_s"]["cleansky4h"] and t["_s"]["reclaim"]),
        ("swept+cleansky4h+deeppull",lambda t:t["_s"]["swept"] and t["_s"]["cleansky4h"] and t["_s"]["deeppull"]),
        ("NÃO-swept (resto)",lambda t:not t["_s"]["swept"])]
for tag,pr in combos: line(tag,[t for t in base if pr(t)])
# keep-test: dentro do cluster, manter só assinatura SWEPT (fallback keep-all se nenhum no cluster); isolados mantidos
G,D=24,1.0; clusters=[]; cur=[base[0]]
for a,b in zip(base,base[1:]):
    if (b["cj_t"]-a["cj_t"])/900<=G and abs(b["_entry"]-a["_entry"])<=D*b["_atr"]: cur.append(b)
    else: clusters.append(cur); cur=[b]
clusters.append(cur)
def panel(rows,tag):
    n=len(rows)
    if not n: print(f"{tag}: vazio"); return
    R=[x["_R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; sm=sum(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    py={y:round(sum(t["_R"] for t in rows if t["yr"]==y),1) for y in (2024,2025,2026)}
    print(f"{tag:<34} N{n:>4} WR{100*w/n:>5.1f}% sumR{sm:>7.1f} avgR{sm/n:>6.3f} DD{dd:>6.1f} r/DD{abs(sm/dd) if dd<0 else 99:>5.2f} streak-{mL}/+{mW}  yr {py[2024]}/{py[2025]}/{py[2026]}")
print("\n=== KEEP-TEST: manter assinatura SWEPT dentro do cluster (fallback keep-all) vs base ===")
kept=[]
for c in clusters:
    if len(c)==1: kept+=c; continue
    sw=[t for t in c if t["_s"]["swept"]]
    kept += (sw if sw else c)
panel(base,"BASE (keep-all)")
panel(kept,"KEEP swept-em-cluster")
# keep-test variante: manter swept+cleansky4h
kept2=[]
for c in clusters:
    if len(c)==1: kept2+=c; continue
    sw=[t for t in c if t["_s"]["swept"] and t["_s"]["cleansky4h"]]
    kept2 += (sw if sw else c)
panel(kept2,"KEEP swept+cleansky4h-em-cluster")
