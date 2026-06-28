#!/usr/bin/env python3
"""ENGINE 11 (Cris 2026-06-28): FIXA a base LONG BULL/RANGE knife-gated (3120) com h4_up & h1d_up.
Painel completo de métricas + por-ano + salva fixed_base_h4h1.csv. h4_up+h1d_up já auditado (DA engine10 item6=beta risk-shaper)."""
import json,csv,statistics as st,datetime as dt
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
    trail=sl; r1=False; ex=None; cap=False; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    R=(ex-entry)/risk
    return max(-1.0,min(RCAP,R)),(R>=RCAP)
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
def knife_v2(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
sel=[]
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")=="BEAR": continue
    if not (f(r,"h4n_trend",0)==1 and f(r,"h1n_trend",0)==1): continue   # FIX: h4_up & h1d_up
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; entry=s[cj]["c"]
    out=letrun(s,cj,entry,sl,atr)
    if out is None: continue
    R,capped=out
    sel.append({"cj_t":r["cj_t"],"date":dt.datetime.utcfromtimestamp(r["cj_t"]).strftime("%Y-%m-%d %H:%M"),
        "yr":r["yr"],"entry":round(entry,2),"sl":round(sl,2),"R":round(R,3),"capped":int(capped),
        "reg":DAYREG.get(r["cj_t"]//86400,"RANGE")})
sel.sort(key=lambda z:z["cj_t"])
def panel(rows,tag):
    n=len(rows)
    if not n: print(f"{tag}: vazio"); return
    rs=[x["R"] for x in rows]; sm=sum(rs); w=sum(1 for x in rs if x>0)
    eq=pk=dd=0; curv=0
    for x in rs: curv+=x; pk=max(pk,curv); dd=min(dd,curv-pk)
    rd=abs(sm/dd) if dd<0 else float('inf')
    top=sorted(rs,reverse=True)
    print(f"\n== {tag} ==")
    print(f"N {n} | WR {100*w/n:.1f}% | sumR {sm:.1f} | avgR {sm/n:.3f} | medR {st.median(rs):.3f}")
    print(f"DD {dd:.1f} | return/DD {rd:.2f} | maxR {max(rs):.1f} | capped(20R) {sum(x['capped'] for x in rows)} | top5 {sum(top[:5]):.1f}R ({100*sum(top[:5])/sm:.0f}%)")
    print(f"{'ano':<6}{'N':>5}{'WR':>7}{'sumR':>8}{'avgR':>7}{'DD':>7}")
    for y in (2024,2025,2026):
        yr=[x for x in rows if x["yr"]==y]
        if not yr: continue
        yrs=[x["R"] for x in yr]; ysm=sum(yrs); yw=sum(1 for x in yrs if x>0)
        e=pk2=d2=0
        for x in yrs: e+=x; pk2=max(pk2,e); d2=min(d2,e-pk2)
        print(f"{y:<6}{len(yr):>5}{100*yw/len(yr):>6.1f}%{ysm:>8.1f}{ysm/len(yr):>7.3f}{d2:>7.1f}")
    rg={}
    for x in rows: rg.setdefault(x["reg"],[]).append(x["R"])
    print("por regime:",{k:f"N{len(v)} avgR{sum(v)/len(v):.3f}" for k,v in rg.items()})
panel(sel,"BASE FIXA 3120 + h4_up & h1d_up")
with open(HERE/"fixed_base_h4h1.csv","w",newline="") as fh:
    wcsv=csv.DictWriter(fh,fieldnames=["cj_t","date","yr","reg","entry","sl","R","capped"]); wcsv.writeheader(); wcsv.writerows(sel)
print(f"\nsalvo: fixed_base_h4h1.csv (N={len(sel)})")
