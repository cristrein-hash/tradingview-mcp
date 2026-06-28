#!/usr/bin/env python3
"""DA audit of T1/T2 backfire claim. Reuses engine13 base construction verbatim, then computes
removed-set stats, DD episode location, per-year avgR, and cluster-R distribution."""
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
LDON=96
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
    lo=max(0,cj-LDON); hi=max(x["h"] for x in s[lo:cj+1]); low=min(x["l"] for x in s[lo:cj+1])
    rpos=(entry-low)/(hi-low) if hi>low else 0.5
    base.append({"cj_t":r["cj_t"],"yr":r["yr"],"reg":DAYREG.get(r["cj_t"]//86400,"RANGE"),
                 "entry":entry,"R":R,"atr":atr,"rpos":rpos})
base.sort(key=lambda z:z["cj_t"])

def T2(rows,thr): return [r for r in rows if not (r["reg"]=="RANGE" and r["rpos"]>thr)]
def T1(rows,G,D):
    taken=[]; out=[]
    for r in rows:
        dup=any((r["cj_t"]-t0)/900<=G and abs(r["entry"]-p0)<=D*a0 for t0,p0,a0 in taken)
        if not dup: out.append(r); taken.append((r["cj_t"],r["entry"],r["atr"]))
    return out
def setstats(rows,tag):
    n=len(rows)
    if not n: print(f"  {tag}: empty"); return
    R=[x["R"] for x in rows]; sm=sum(R); w=sum(1 for x in R if x>0)
    big3=sum(1 for x in R if x>=3); big5=sum(1 for x in R if x>=5)
    print(f"  {tag}: N{n} WR{100*w/n:.1f}% sumR{sm:.1f} avgR{sm/n:.3f} R>=3:{big3} R>=5:{big5} maxR{max(R):.1f}")
def dd_episode(rows,tag):
    eq=pk=0; dd=0; ddt=None; pkt=None
    for x in rows:
        eq+=x["R"]
        if eq>pk: pk=eq; pkt=x["cj_t"]
        if eq-pk<dd: dd=eq-pk; ddt=x["cj_t"]
    fmt=lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d") if t else "?"
    print(f"  {tag}: maxDD {dd:.1f}  trough@{fmt(ddt)}  (peak before@{fmt(pkt)})")

# build sets
G,D,THR=12,0.6,0.5
b_t1=T1(base,G,D)
b_t2=T2(base,THR)
b_t1t2=T1(T2(base,THR),G,D)
keep_t1=set(id(r) for r in b_t1)
keep_t2=set(id(r) for r in b_t2)
rem_t1=[r for r in base if id(r) not in keep_t1]
rem_t2=[r for r in base if id(r) not in keep_t2]

print("="*70)
print("ITEM 1 — T1 removed set (de-cluster drops)")
setstats(base,"BASE full")
setstats(b_t1,"KEPT (+T1)")
setstats(rem_t1,"REMOVED by T1")
print("="*70)
print("ITEM 2 — T2 removed set (range-top drops)")
setstats(b_t2,"KEPT (+T2)")
setstats(rem_t2,"REMOVED by T2")
print("="*70)
print("ITEM 3 — DD episode location")
dd_episode(base,"BASE")
b_g16=T1(T2(base,0.5),16,D)
dd_episode(b_g16,"G=16 thr=0.5 (T1+T2)")
dd_episode(b_t1t2,"G=12 thr=0.5 (T1+T2)")
# DD by year for base
print("  --- base equity trajectory: DD within each year ---")
for y in (2024,2025,2026):
    yr=[r for r in base if r["yr"]==y]
    if yr: dd_episode(yr,f"BASE {y}-only")
print("="*70)
print("ITEM 4 — per-year avgR BASE vs +T1+T2")
for y in (2024,2025,2026):
    by=[r for r in base if r["yr"]==y]
    ty=[r for r in b_t1t2 if r["yr"]==y]
    bm=f"N{len(by)} sumR{sum(x['R'] for x in by):.1f} avgR{sum(x['R'] for x in by)/len(by):.3f} WR{100*sum(1 for x in by if x['R']>0)/len(by):.1f}%" if by else "empty"
    tm=f"N{len(ty)} sumR{sum(x['R'] for x in ty):.1f} avgR{sum(x['R'] for x in ty)/len(ty):.3f} WR{100*sum(1 for x in ty if x['R']>0)/len(ty):.1f}%" if ty else "empty"
    print(f"  {y}: BASE {bm}")
    print(f"        +T1+T2 {tm}")
print("="*70)
print("ITEM 5 — cluster R distribution (keep-FIRST vs alternatives)")
# Reconstruct clusters the way T1 sees them: a cluster = entries that would be collapsed
# into a single kept entry. Walk base in time order, assign each entry to the FIRST kept
# anchor it duplicates (within G bars & D*ATR). This mirrors T1's taken[] logic.
G,D=12,0.6
clusters=[]  # list of lists of rows
anchors=[]   # (cj_t,entry,atr, cluster_index)
for r in base:
    hit=None
    for (t0,p0,a0,ci) in anchors:
        if (r["cj_t"]-t0)/900<=G and abs(r["entry"]-p0)<=D*a0:
            hit=ci; break
    if hit is None:
        ci=len(clusters); clusters.append([r]); anchors.append((r["cj_t"],r["entry"],r["atr"],ci))
    else:
        clusters[hit].append(r)
sizes=[len(c) for c in clusters]
print(f"  clusters total={len(clusters)} singletons={sum(1 for c in clusters if len(c)==1)} multi={sum(1 for c in clusters if len(c)>1)}")
print(f"  cluster size hist: max={max(sizes)} mean={sum(sizes)/len(sizes):.2f}")
from collections import Counter
print(f"  cluster size dist: {dict(sorted(Counter(sizes).items()))}")
def cluster_R_split(thresh,label):
    big=[c for c in clusters if len(c)>=thresh]
    if not big: print(f"  [{label}] clusters>= {thresh}: NONE"); return
    first_frac=[]; first_is_best=0; tot_R_big=0; first_R_big=0; best_R_big=0
    runner_nonfirst=0; runner_total=0
    for c in big:
        Rs=[x["R"] for x in c]; tot=sum(Rs)
        if tot!=0:
            first_frac.append(Rs[0]/tot)
            if Rs[0]==max(Rs): first_is_best+=1
            tot_R_big+=tot; first_R_big+=Rs[0]; best_R_big+=max(Rs)
        for j,v in enumerate(Rs):
            if v>=3:
                runner_total+=1
                if j!=0: runner_nonfirst+=1
    print(f"  [{label}] clusters>= {thresh}: count={len(big)} totalR={tot_R_big:.1f} firstR={first_R_big:.1f}({100*first_R_big/tot_R_big:.0f}%) bestR={best_R_big:.1f}")
    print(f"     first==best in {first_is_best}/{len(big)}  meanFirstFrac={sum(first_frac)/len(first_frac):.2f}" if first_frac else "")
    if runner_total: print(f"     runners(R>=3) inside: total={runner_total} non-first={runner_nonfirst}({100*runner_nonfirst/runner_total:.0f}% non-first)")
cluster_R_split(2,"size>=2")
cluster_R_split(3,"size>=3")

# Counterfactual: keep-FIRST vs keep-BEST vs keep-ALL (=base) at the cluster level only
def cluster_metrics(pick):
    # pick: function(cluster_rows)->list of kept rows
    kept=[]
    for c in clusters: kept+=pick(c)
    kept.sort(key=lambda z:z["cj_t"])
    R=[x["R"] for x in kept]; sm=sum(R); n=len(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    rd=abs(sm/dd) if dd<0 else 99.9
    return n,100*w/n,sm,sm/n,dd,rd
print("  --- cluster-level counterfactuals (T1 collapse rule G=12/D=0.6, no T2) ---")
for tag,pick in (("keep-ALL (=base)",lambda c:c),
                 ("keep-FIRST (T1)",lambda c:[c[0]]),
                 ("keep-BEST-R (hindsight)",lambda c:[max(c,key=lambda z:z['R'])]),
                 ("keep-LAST",lambda c:[c[-1]])):
    n,wr,sm,avg,dd,rd=cluster_metrics(pick)
    print(f"    {tag:<26} N{n} WR{wr:.1f}% sumR{sm:.1f} avgR{avg:.3f} DD{dd:.1f} r/DD{rd:.2f}")

print("  --- do big clusters EVER exist? rebuild with wide G/D ---")
for Gw,Dw in ((24,1.0),(48,1.5),(96,2.0)):
    cl=[]; anc=[]
    for r in base:
        hit=None
        for (t0,p0,a0,ci) in anc:
            if (r["cj_t"]-t0)/900<=Gw and abs(r["entry"]-p0)<=Dw*a0: hit=ci; break
        if hit is None: ci=len(cl); cl.append([r]); anc.append((r["cj_t"],r["entry"],r["atr"],ci))
        else: cl[hit].append(r)
    sz=[len(c) for c in cl]
    big=[c for c in cl if len(c)>=4]
    print(f"    G={Gw} D={Dw}: clusters={len(cl)} maxsize={max(sz)} big(>=4)={len(big)}")
