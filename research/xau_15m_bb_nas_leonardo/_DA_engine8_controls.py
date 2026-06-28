#!/usr/bin/env python3
"""DA ENGINE 8 — controls. Reproduces engine8 universe, then runs:
 (A) return/DD before vs after regime-direction filter (Q1, Q5)
 (B) SHORT-in-BEAR per-block + strip-2026 + per-year (Q2)
 (C) COMBO 2026 decomposition: remove-bear-longs vs add-bear-shorts (Q6)
 (D) naive baselines: LONG-all-take, regime-blind, random-direction-of-trades
 (E) regime label coverage / dependency
All in-sample, RAW-causal, NO OOS. Régua = let-run (identical to engine8)."""
import json,statistics as st,random,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
BLOCKS=sorted(PRIMK)
# ---- regime v2 (verbatim copy from engine8) ----
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
    longs.append({"t":r["cj_t"],"R":R,"reg":regime_at(r["cj_t"]),"yr":r["yr"],"dir":"L","block":r["block"]})
shorts=[]
for bkey,pr in PRIMK.items():
    s=pr["series"]; nn=len(s); Hh=[b["h"] for b in s]; last=-99
    for p in range(96,nn-4):
        if Hh[p]!=max(Hh[p-3:p+4]): continue
        cj=p+3
        if cj>=nn-2 or cj-last<3: continue
        atr=s[p]["atr"]
        if not atr: continue
        last=cj; entry=s[cj]["c"]; sl=max(x["h"] for x in s[p:cj+1])+0.1*atr
        R=letrun_short(s,cj,entry,sl,atr)
        if R is None: continue
        shorts.append({"t":s[cj]["t"],"R":R,"reg":regime_at(s[cj]["t"]),"yr":dt.datetime.utcfromtimestamp(s[cj]["t"]).year,"dir":"S","block":bkey})

def block_of(t):
    # assign each trade to its source block by date range
    for b in BLOCKS:
        s=PRIMK[b]["series"]
        if s[0]["t"]<=t<=s[-1]["t"]: return b
    return None
for x in longs+shorts:
    if "block" not in x or x["block"] not in BLOCKS:
        x["block"]=block_of(x["t"])

def M(rows):
    rows=sorted(rows,key=lambda z:z["t"]); n=len(rows)
    if not n: return dict(n=0,wr=0,sum=0,avg=0,dd=0,py={})
    rs=[x["R"] for x in rows]; sm=sum(rs); w=sum(1 for x in rs if x>0)
    eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
    return dict(n=n,wr=round(100*w/n,1),sum=round(sm,1),avg=round(sm/n,3),dd=round(dd,1),py=py)
def line(tag,m):
    if m["n"]==0: print(f"{tag:<40} (vazio)"); return
    rd = m['sum']/abs(m['dd']) if m['dd']!=0 else float('inf')
    print(f"{tag:<40}{m['n']:>5}{m['wr']:>6}{m['sum']:>8}{m['avg']:>7}{m['dd']:>8} rd={rd:>5.2f}  {m['py'].get(2024)}/{m['py'].get(2025)}/{m['py'].get(2026)}")

L_all=longs
L_br=[x for x in longs if x["reg"] in ("BULL","RANGE")]
L_bear=[x for x in longs if x["reg"]=="BEAR"]
S_bear=[x for x in shorts if x["reg"]=="BEAR"]
combo=L_br+S_bear

print("="*120)
print("Q1/Q5 — RETURN/DD before vs after regime-direction filter")
print(f"{'scenario':<40}{'N':>5}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>8}{' rd':>9}  yr24/25/26")
line("LONG-all (take all knife-gated)",M(L_all))
line("LONG bull/range (regime-filtered)",M(L_br))
line("  delta (removed bear-longs)",M(L_bear))
line("COMBO long(b/r)+short(bear)",M(combo))
ma,mb=M(L_all),M(L_br)
print(f"  -> return/DD  LONG-all={ma['sum']/abs(ma['dd']):.2f}  LONG-b/r={mb['sum']/abs(mb['dd']):.2f}  (Δ {mb['sum']/abs(mb['dd'])-ma['sum']/abs(ma['dd']):+.2f})")
print(f"  -> sumR Δ {mb['sum']-ma['sum']:+.1f}R for cutting {len(L_bear)} bear-longs (which were {M(L_bear)['sum']:+.1f}R, avg {M(L_bear)['avg']:+.3f})")

print("="*120)
print("Q2 — SHORT-in-BEAR: per-block, strip-2026, leave-block")
print(f"{'short-in-bear by year':<40}{S_bear and ''}")
line("SHORT-in-BEAR all",M(S_bear))
line("SHORT-in-BEAR strip-2026",M([x for x in S_bear if x["yr"]!=2026]))
line("SHORT-in-BEAR only-2024",M([x for x in S_bear if x["yr"]==2024]))
line("SHORT-in-BEAR only-2026",M([x for x in S_bear if x["yr"]==2026]))
print("\n  per-block (8 leave-out units):")
pos_blocks=0
for b in BLOCKS:
    sb=[x for x in S_bear if x["block"]==b]
    m=M(sb)
    if m["n"]>0:
        flag="POS" if m["sum"]>0 else "neg"
        if m["sum"]>0: pos_blocks+=1
        print(f"    {b}  n={m['n']:<4} sumR={m['sum']:+7.1f}  avgR={m['avg']:+.3f}  [{flag}]")
    else:
        print(f"    {b}  n=0 (no bear-regime short trades)")
nb=sum(1 for b in BLOCKS if any(x["block"]==b for x in S_bear))
print(f"  -> blocks with ANY short-in-bear trade: {nb}/8 ; blocks POSITIVE: {pos_blocks}/{nb}")
print("  leave-one-block-out sumR (short-in-bear):")
for b in BLOCKS:
    rest=[x for x in S_bear if x["block"]!=b]
    print(f"    drop {b}: sumR={M(rest)['sum']:+.1f}  (n={M(rest)['n']})")

print("="*120)
print("Q6 — COMBO 2026 decomposition")
y=2026
la_26=sum(x["R"] for x in L_all if x["yr"]==y)
lbr_26=sum(x["R"] for x in L_br if x["yr"]==y)
lbear_26=sum(x["R"] for x in L_bear if x["yr"]==y)
sbear_26=sum(x["R"] for x in S_bear if x["yr"]==y)
combo_26=sum(x["R"] for x in combo if x["yr"]==y)
print(f"  LONG-all 2026          = {la_26:+.1f}R  (n={sum(1 for x in L_all if x['yr']==y)})")
print(f"  remove bear-longs 2026 = {-lbear_26:+.1f}R  (bear-longs were {lbear_26:+.1f}R, n={sum(1 for x in L_bear if x['yr']==y)})")
print(f"  = LONG b/r 2026        = {lbr_26:+.1f}R")
print(f"  add short-in-bear 2026 = {sbear_26:+.1f}R  (n={sum(1 for x in S_bear if x['yr']==y)})")
print(f"  = COMBO 2026           = {combo_26:+.1f}R")
print(f"  -> headline 2026 gain over LONG-all = {combo_26-la_26:+.1f}R ; from-cut-bear-longs={-lbear_26:+.1f}, from-add-shorts={sbear_26:+.1f}")

print("="*120)
print("Q5 — naive baselines (is it beta direction-overlay vs selective?)")
line("LONG-all-take (no regime)",M(L_all))
# random direction: take same long universe but randomly flip half to short outcome? not meaningful. Instead:
# baseline = trade entire long+short universe blind (regime-blind both directions)
line("ALL long+short universe blind",M(longs+shorts))
# regime-blind long-only universe is L_all already. selectivity = count
print(f"  -> COMBO trades {len(combo)} / long universe {len(longs)} = {100*len(combo)/len(longs):.0f}% of long universe (overlay, not slim base)")
print(f"  -> avgR combo {M(combo)['avg']:+.3f} ; avgR long-all {M(L_all)['avg']:+.3f}  (selective edge would lift avgR materially)")

print("="*120)
print("Q4/E — regime label coverage (calibration vs application period)")
from collections import Counter
cc=Counter(reg)
print(f"  regime-day distribution (full 2024-2026): {dict(cc)}")
# per-year regime days
yr_reg=Counter()
for i,k in enumerate(DK):
    yy=dt.datetime.utcfromtimestamp(k*86400).year
    yr_reg[(yy,reg[i])]+=1
for yy in (2024,2025,2026):
    row={r:yr_reg[(yy,r)] for r in ("BULL","RANGE","BEAR")}
    print(f"    {yy}: {row}")
# bear-regime days that produced short trades
bear_days=set(k for i,k in enumerate(DK) if reg[i]=="BEAR")
print(f"  total BEAR days in detector: {len(bear_days)}")
sbd=set(x['t']//86400 for x in S_bear)
print(f"  distinct BEAR days that have a short-trade: {len(sbd & bear_days)}")
