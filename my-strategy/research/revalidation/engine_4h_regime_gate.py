#!/usr/bin/env python3
"""Detector REGIME 4H-NATIVO (lógica v5 do 15M, escalada p/ 4H): camada estável diária (resample 4H->dia) +
OVERRIDE drawdown% no 4H (peak 12 bars~2d, mom 6 bars~1d, dd>=6%, Krec 30 bars~5d). Params ESPELHADOS do v5 15M,
NÃO fitados às estratégias (anti-circular). Aplica gate !=BEAR sobre L1 (34/26) e L2/BPT (276) aprovadas e mede
delta DD/streak/sumR. Causal (bar-causal). Era 2020-2025."""
import json,csv,bisect,datetime as dt
from pathlib import Path
BASE=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
L2DIR=BASE/"XAU_4H_L2_BPT_BOS_CHOCH/v1"
L1DIR=BASE/"XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
# ---- 4H bars ----
B4=[]
for l in (L2DIR/"repro_recovery/raw_features_2020_2026.jsonl").read_text().splitlines():
    o=json.loads(l); B4.append((o["ts_epoch"],o["open"],o["high"],o["low"],o["close"]))
B4.sort(); TS=[b[0] for b in B4]; O=[b[1] for b in B4]; HH=[b[2] for b in B4]; LL=[b[3] for b in B4]; C=[b[4] for b in B4]
# ---- daily resample ----
days={}
for ts,o,h,l,c in B4:
    k=ts//86400; g=days.setdefault(k,{"h":h,"l":l,"c":c}); g["h"]=max(g["h"],h); g["l"]=min(g["l"],l); g["c"]=c
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]
for i in range(1,len(DK)): TR.append(max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])))
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(arr,i,n):
    c=arr[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(DC,i,50) for i in range(len(DK))]; E100=[ema_at(DC,i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw_stable(i):
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
rawS=[raw_stable(i) for i in range(len(DK))]
stable=[]; cur="RANGE"; pend=None; pn=0
for v in rawS:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    need=Kbear if pend=="BEAR" else K
    if pn>=need: cur=pend; pend=None; pn=0
    stable.append(cur)
DSTAB={DK[i]:stable[i] for i in range(len(DK))}
# ---- override 4H (bar-causal) ----
P,mom,dd_thr,Krec=12,6,0.06,30
ov4=[]; ov=False; quiet=0
for j in range(len(B4)):
    if j<max(P,mom): ov4.append(False); continue
    peak=max(HH[j-P:j+1]); ddp=(peak-C[j])/peak if peak>0 else 0
    fired= ddp>=dd_thr and C[j]<C[j-mom]
    if fired: ov=True; quiet=0
    elif ov:
        quiet+=1
        if quiet>=Krec: ov=False
    ov4.append(ov)
def stable_prevday(ts):
    di=bisect.bisect_left(DK,ts//86400)-1
    return "RANGE" if di<0 else stable[di]
def regime_at_ts(ts):
    j=bisect.bisect_right(TS,ts)-1            # último bar 4H <= ts
    ovr= ov4[j] if j>=0 else False
    st=stable_prevday(ts)
    return "BEAR" if (ovr or st=="BEAR") else st
def regime_prevday_close(date_epoch):
    # p/ L2 date-only: regime no fechamento do dia ANTERIOR (causal)
    di=bisect.bisect_left(DK, date_epoch//86400)-1
    if di<0: return "RANGE"
    # último bar 4H do dia DK[di]
    dayend=(DK[di]+1)*86400
    j=bisect.bisect_right(TS,dayend-1)-1
    ovr= ov4[j] if j>=0 else False
    return "BEAR" if (ovr or stable[di]=="BEAR") else stable[di]
# sanity: distribuição de regime nos bars 4H
from collections import Counter
rc=Counter(regime_at_ts(ts) for ts in TS[::6])
print(f"4H regime distrib (amostra diária): {dict(rc)}  (BEAR frac {rc['BEAR']/sum(rc.values()):.2f})")
def panel(R):
    n=len(R)
    if not n: return None
    sm=sum(R); w=sum(1 for x in R if x>0); eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    return n,round(100*w/n,1),round(sm,1),round(dd,1),f"-{mL}/+{mW}"
def show(tag,trades):  # trades=[(ts,R)] já ordenado
    p=panel([r for _,r in trades])
    if not p: print(f"{tag}: vazio"); return
    n,wr,sm,dd,sk=p
    print(f"{tag:<30} N{n:>4} WR{wr:>5}% sumR{sm:>7} DD{dd:>6} streak{sk}")
# ===== L1 EMA21 =====
L1=json.loads((L1DIR/"l1_approved34.json").read_text())
cut8=set(json.loads((L1DIR/"l1_poc_cut8_ts.json").read_text()))
def isoep(s):
    return int(dt.datetime.strptime(s,"%Y-%m-%dT%H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
l1=[(isoep(t["ts"]),float(t["R"]),t["ts"]) for t in L1]; l1.sort()
print("\n=== L1 EMA21 Continuation ===")
show("L1-34 base",[(ts,r) for ts,r,_ in l1])
show("L1-34 +regime!=BEAR",[(ts,r) for ts,r,_ in l1 if regime_at_ts(ts)!="BEAR"])
l1c=[(ts,r,s) for ts,r,s in l1 if s not in cut8]
show("L1-26 (poc-cut)",[(ts,r) for ts,r,_ in l1c])
show("L1-26 +regime!=BEAR",[(ts,r) for ts,r,_ in l1c if regime_at_ts(ts)!="BEAR"])
cutL1=[(s,r,regime_at_ts(ts)) for ts,r,s in l1 if regime_at_ts(ts)=="BEAR"]
print(f"L1 regime corta {len(cutL1)}: "+", ".join(f"{s}({r:+.1f})" for s,r,_ in cutL1))
# ===== L2/BPT 276 =====
rows=list(csv.DictReader(open(L2DIR/"results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
def dep(s): return int(dt.datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
def L2set(rcol):
    out=[]
    for r in rows:
        try: R=float(r[rcol])
        except: continue
        out.append((dep(r["datetime"]),R))
    out.sort(); return out
print("\n=== L2/BPT 276 base (R=capped_realR) ===")
l2=L2set("capped_realR")
show("L2-276 base",l2)
show("L2-276 +regime!=BEAR",[(t,r) for t,r in l2 if regime_prevday_close(t)!="BEAR"])
print("\n=== L2/BPT 276 (R=realized_letrun_120, régua oficial let-run) ===")
l2lr=L2set("realized_letrun_120")
show("L2-276 letrun base",l2lr)
show("L2-276 letrun +regime!=BEAR",[(t,r) for t,r in l2lr if regime_prevday_close(t)!="BEAR"])
ncutL2=sum(1 for t,_ in l2 if regime_prevday_close(t)=="BEAR")
cutR=sum(r for t,r in l2 if regime_prevday_close(t)=="BEAR")
print(f"\nL2 regime corta {ncutL2} trades (capped sumR cortado {cutR:.1f})")
