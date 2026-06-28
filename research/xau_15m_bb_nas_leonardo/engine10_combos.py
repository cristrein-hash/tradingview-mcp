#!/usr/bin/env python3
"""ENGINE 10 (Cris 2026-06-28): o que VALE manter das 20 lentes sobre LONG BULL/RANGE knife-gated (3120),
e combos de 2/3 ajudam? (1) singles: todas as 20 (avgR TRUE vs base, por-ano). (2) combos restritos às lentes
right-signed (sem data-dredge das 20): C(k,2)+C(k,3). Reporta N/WR/sumR/avgR/DD/por-ano + concentração top5."""
import json,statistics as st,itertools
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
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    R=letrun(s,cj,s[cj]["c"],min(x["l"] for x in s[p:cj+1])-0.1*atr,atr)
    if R is None: continue
    r["R"]=R; base.append(r)
def med(k):
    v=[f(r,k) for r in base if f(r,k) is not None]; return st.median(v) if v else 0
M={k:med(k) for k in ("downleg_eff","pullback_depth","legpos90","legpos60","reclaim_atr","dist_demand_atr","clean_sky_atr")}
def preds(r):
    return {
      "downleg_grind": f(r,"downleg_eff",1)<M["downleg_eff"],
      "pullback_raso": f(r,"pullback_depth",1)<M["pullback_depth"],
      "legpos90_alto": f(r,"legpos90",0)>=M["legpos90"],
      "micro_hl": f(r,"micro_hl",0)==1,
      "rsi_low<40": f(r,"rsi_low",50)<40,
      "rsi_min8<35": f(r,"rsi_min8",50)<35,
      "reclaim_forte": f(r,"reclaim_atr",0)>=M["reclaim_atr"],
      "atr_baixo": f(r,"atr_regime",1)<1.0,
      "coiled_spring": f(r,"atr_compression_pre",0)>1.0,
      "in_demand": f(r,"in_demand",0)==1,
      "demand_reclaim": f(r,"demand_reclaim",0)==1,
      "perto_demanda": f(r,"dist_demand_atr",99)<M["dist_demand_atr"],
      "clean_sky": f(r,"clean_sky_atr",0)>=M["clean_sky_atr"],
      "sem_supply_acima": f(r,"n_supply_overhead",9)<=1,
      "sell_bubble_absorb": f(r,"sell_bub_w",0)>=2,
      "sem_buy_exaustao": f(r,"buy_bub_w",9)<4,
      "nas_long": f(r,"nas_long_16",0)>=1,
      "h4_up": f(r,"h4n_trend",0)==1,
      "h1d_up": f(r,"h1n_trend",0)==1,
      "h4_demanda": f(r,"h4n_in_demand",0)==1,
    }
for r in base: r["P"]=preds(r)
NB=len(base); baseR=[r["R"] for r in base]; base_avg=sum(baseR)/NB
def metr(sel):
    n=len(sel)
    if not n: return None
    rs=sorted([r["R"] for r in sel],reverse=True); sm=sum(rs); w=sum(1 for x in rs if x>0)
    top5=round(100*sum(rs[:5])/sm,0) if sm>0 else 0
    rt=[r["R"] for r in sorted(sel,key=lambda z:z["cj_t"])]; eq=pk=dd=0
    for x in rt: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(r["R"] for r in sel if r["yr"]==y),1) for y in (2024,2025,2026)}
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),int(top5),py
print(f"BASE 3120 — avgR {base_avg:.3f} | sumR {sum(baseR):.1f}\n")
keys=list(base[0]["P"].keys())
print("== SINGLES (todas 20) — avgR TRUE vs FALSE; + = certo ==")
print(f"{'lente':<20}{'N_T':>6}{'avgR_T':>8}{'avgR_F':>8}{'delta':>8}  yr T 24/25/26")
singE=[]
for k in keys:
    T=[r for r in base if r["P"][k]]; Fa=[r for r in base if not r["P"][k]]
    aT=sum(r["R"] for r in T)/len(T) if T else 0; aF=sum(r["R"] for r in Fa)/len(Fa) if Fa else 0
    py={y:round(sum(r["R"] for r in T if r["yr"]==y),1) for y in (2024,2025,2026)}
    singE.append((round(aT-aF,3),k,len(T),round(aT,3),round(aF,3),py))
for d,k,n,aT,aF,py in sorted(singE,reverse=True):
    print(f"{k:<20}{n:>6}{aT:>8}{aF:>8}{d:>+8}  {py[2024]}/{py[2025]}/{py[2026]}")
RIGHT=["sem_supply_acima","legpos90_alto","h4_up","pullback_raso","h1d_up","clean_sky"]
def applyc(combo): return [r for r in base if all(r["P"][k] for k in combo)]
print(f"\n== COMBOS de 2 (right-signed {RIGHT}) — N>=120 ==")
print(f"{'combo':<40}{'N':>5}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>7}{'top5%':>6}  yr24/25/26")
rows2=[]
for c in itertools.combinations(RIGHT,2):
    m=metr(applyc(c))
    if m and m[0]>=120: rows2.append((m[3],c,m))
for _,c,m in sorted(rows2,reverse=True):
    n,wr,sm,avg,dd,t5,py=m; print(f"{'+'.join(c):<40}{n:>5}{wr:>6}{sm:>8}{avg:>7}{dd:>7}{t5:>6}  {py[2024]}/{py[2025]}/{py[2026]}")
print(f"\n== COMBOS de 3 (right-signed) — N>=80 ==")
print(f"{'combo':<46}{'N':>5}{'WR':>6}{'sumR':>7}{'avgR':>7}{'DD':>7}{'top5%':>6}  yr24/25/26")
rows3=[]
for c in itertools.combinations(RIGHT,3):
    m=metr(applyc(c))
    if m and m[0]>=80: rows3.append((m[3],c,m))
for _,c,m in sorted(rows3,reverse=True):
    n,wr,sm,avg,dd,t5,py=m; print(f"{'+'.join(c):<46}{n:>5}{wr:>6}{sm:>7}{avg:>7}{dd:>7}{t5:>6}  {py[2024]}/{py[2025]}/{py[2026]}")
