#!/usr/bin/env python3
"""ENGINE 21 (Cris 2026-06-28): MAPA DE LOSERS sobre a base APROVADA swept-sempre (N896, 2024-26).
(1) std-diff causal LOSER(R<=0) vs WIN(R>0). (2) teste de corte single-feature: cortar o lado-loser e medir
painel completo + quantos LOSER/WIN/RUNNER remove. Objetivo: filtrar losers sem matar runner. Causal, inline."""
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
    if not (f(r,"swept_prior_low",0)==1): continue   # SWEPT-SEMPRE
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    r["_R"]=R; base.append(r)
base.sort(key=lambda z:z["cj_t"])
NB=len(base); loser=[t for t in base if t["_R"]<=0]; win=[t for t in base if t["_R"]>0]; run=[t for t in base if t["_R"]>=3]
print(f"SWEPT-SEMPRE base N={NB} | LOSER(R<=0) {len(loser)} ({100*len(loser)/NB:.0f}%) | WIN {len(win)} | RUNNER(R>=3) {len(run)}")
FEATS=["reclaim_atr","reclaim_ema_bars","downleg_eff","downleg_decel","pullback_depth","legpos60","legpos90",
"rsi_low","rsi_min8","atr_regime","atr_compression_pre","dist_demand_atr","clean_sky_atr","n_supply_overhead",
"n_demand_near","sell_bub_w","buy_bub_w","nas_long_16","confirm_body_atr","low_wick","up_closes_pc","micro_hl",
"in_demand","demand_reclaim","h4n_rsi","h1n_rsi","h4n_clean_sky_atr","h4n_dist_demand_atr","h1_pos","h4_pos"]
def m(g,k): v=[f(t,k) for t in g if f(t,k) is not None]; return (st.mean(v),st.pstdev(v) if len(v)>1 else 0) if v else (0,0)
print("\n=== std-diff WIN vs LOSER (sinal + => maior em WIN; alvo de corte = lado LOSER) ===")
rows=[]
for k in FEATS:
    mw,sw=m(win,k); ml,sl_=m(loser,k); sp=((sw**2+sl_**2)/2)**0.5 or 1
    rows.append(((mw-ml)/sp,k,round(mw,2),round(ml,2)))
for d,k,mw,ml in sorted(rows,key=lambda z:-abs(z[0])):
    if abs(d)>=0.12: print(f"  {k:<20} win {mw:>8} | loser {ml:>8} | std-diff {d:>+6.2f}")
def med(k): v=[f(t,k) for t in base if f(t,k) is not None]; return st.median(v) if v else 0
def panel(rows,tag):
    n=len(rows)
    if not n: print(f"{tag:<30} vazio"); return
    R=[x["_R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; sm=sum(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    py={y:round(sum(t["_R"] for t in rows if t["yr"]==y),1) for y in (2024,2025,2026)}
    nl=sum(1 for x in R if x<=0); nr=sum(1 for x in R if x>=3)
    print(f"{tag:<30} N{n:>4} WR{100*w/n:>5.1f}% sumR{sm:>7.1f} avgR{sm/n:>6.3f} DD{dd:>6.1f} streak-{mL}/+{mW} | loser{nl} run{nr} | yr {py[2024]}/{py[2025]}/{py[2026]}")
print("\n=== CORTE single-feature (mantém quem NÃO é lado-loser); compara com BASE ===")
panel(base,"BASE swept-sempre")
# para top separadores, cortar o lado loser por quartil
top=[k for d,k,_,_ in sorted(rows,key=lambda z:-abs(z[0])) if abs(d)>=0.15][:8]
for k in top:
    d=[x for x in rows if x[1]==k][0][0]; mv=med(k)
    # se win>loser (d>0): losers têm valor BAIXO -> cortar abaixo do 1º quartil; senão cortar acima do 3º quartil
    vals=sorted(f(t,k) for t in base if f(t,k) is not None)
    q1=vals[len(vals)//4]; q3=vals[3*len(vals)//4]
    if d>0: kept=[t for t in base if (f(t,k) is None) or f(t,k)>=q1]; cut=f"corta {k}<{q1}"
    else: kept=[t for t in base if (f(t,k) is None) or f(t,k)<=q3]; cut=f"corta {k}>{q3}"
    panel(kept,cut)
