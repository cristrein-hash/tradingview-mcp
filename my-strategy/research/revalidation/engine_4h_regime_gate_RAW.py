#!/usr/bin/env python3
"""Detector REGIME 4H-nativo 100% RAW (raw_4h_ohlc.jsonl + raw_1h_ohlc.jsonl). Lógica v5: estável diário (RAW 4H
resample) + override drawdown% no RAW 1H (2024+) com fallback RAW 4H (2020-2023). Params espelhados do v5 (não
fitados). Gate !=BEAR sobre L1 (34/26) e L2/BPT (276). Mede delta DD/streak/sumR. Causal."""
import json,csv,bisect,datetime as dt
from pathlib import Path
BASE=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
L2DIR=BASE/"XAU_4H_L2_BPT_BOS_CHOCH/v1"; L1DIR=BASE/"XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5"
B4=[json.loads(l) for l in (BASE/"raw_4h_ohlc.jsonl").read_text().splitlines()]
B1=[json.loads(l) for l in (BASE/"raw_1h_ohlc.jsonl").read_text().splitlines()]
TS4=[b["t"] for b in B4]; C4=[b["c"] for b in B4]; H4=[b["h"] for b in B4]
TS1=[b["t"] for b in B1]; C1=[b["c"] for b in B1]; H1=[b["h"] for b in B1]
# daily resample do RAW 4H
days={}
for b in B4:
    k=b["t"]//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
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
def override(TS,C,Hh,P,mom,dd_thr,Krec):
    out=[]; ov=False; quiet=0
    for j in range(len(TS)):
        if j<max(P,mom): out.append(False); continue
        peak=max(Hh[j-P:j+1]); ddp=(peak-C[j])/peak if peak>0 else 0
        fired= ddp>=dd_thr and C[j]<C[j-mom]
        if fired: ov=True; quiet=0
        elif ov:
            quiet+=1
            if quiet>=Krec: ov=False
        out.append(ov)
    return out
OV4=override(TS4,C4,H4,12,6,0.06,30)      # 4H: 2d peak, 1d mom, 5d rec
OV1=override(TS1,C1,H1,48,24,0.06,120)    # 1H: idem v5 15M
T1MIN=TS1[0]
def stable_prevday(ts):
    di=bisect.bisect_left(DK,ts//86400)-1
    return "RANGE" if di<0 else stable[di]
def ovr_at(ts):
    # CAUSAL FIX 2026-07-12 (ordem Cris): t do RAW = ABERTURA da barra; usar a última barra
    # FECHADA <= ts (open+dur <= ts), não a barra em formação que contém ts (close futuro = leak).
    if ts>=T1MIN:
        j=bisect.bisect_right(TS1,ts-3600)-1; return OV1[j] if j>=0 else False
    j=bisect.bisect_right(TS4,ts-14400)-1; return OV4[j] if j>=0 else False
def regime_at(ts):
    st=stable_prevday(ts); return "BEAR" if (ovr_at(ts) or st=="BEAR") else st
def regime_prevday_close(date_ep):
    di=bisect.bisect_left(DK,date_ep//86400)-1
    if di<0: return "RANGE"
    dayend=(DK[di]+1)*86400-1
    return "BEAR" if (ovr_at(dayend) or stable[di]=="BEAR") else stable[di]
from collections import Counter
rc=Counter(regime_at(t) for t in TS4[::6]); tot=sum(rc.values())
print(f"RAW 4H regime distrib (amostra diária): {dict(rc)} (BEAR {rc['BEAR']/tot:.2f}) | 1H override desde {dt.datetime.utcfromtimestamp(T1MIN).strftime('%Y-%m-%d')}")
def panel(R):
    n=len(R);
    if not n: return None
    sm=sum(R); w=sum(1 for x in R if x>0); eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    return n,round(100*w/n,1),round(sm,1),round(dd,1),f"-{mL}/+{mW}"
def show(tag,trades):
    p=panel([r for _,r in trades])
    if not p: print(f"{tag}: vazio"); return
    n,wr,sm,dd,sk=p; print(f"{tag:<32} N{n:>4} WR{wr:>5}% sumR{sm:>7} DD{dd:>6} streak{sk}")
def isoep(s): return int(dt.datetime.strptime(s,"%Y-%m-%dT%H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
def dep(s): return int(dt.datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
L1=json.loads((L1DIR/"l1_approved34.json").read_text()); cut8=set(json.loads((L1DIR/"l1_poc_cut8_ts.json").read_text()))
l1=sorted((isoep(t["ts"]),float(t["R"]),t["ts"]) for t in L1)
print("\n=== L1 EMA21 Continuation (RAW regime) ===")
show("L1-34 base",[(ts,r) for ts,r,_ in l1])
show("L1-34 +regime!=BEAR",[(ts,r) for ts,r,_ in l1 if regime_at(ts)!="BEAR"])
l1c=[(ts,r,s) for ts,r,s in l1 if s not in cut8]
show("L1-26 (poc-cut) base",[(ts,r) for ts,r,_ in l1c])
show("L1-26 +regime!=BEAR",[(ts,r) for ts,r,_ in l1c if regime_at(ts)!="BEAR"])
print("L1 cortados:", ", ".join(f"{s}({r:+.1f},{regime_at(ts)})" for ts,r,s in l1 if regime_at(ts)=="BEAR"))
# ---- L1 FINAL APROVADA: poc-cut + regime v5 !=BEAR ----
final=[{"ts":s,"R":r,"regime":regime_at(ts)} for ts,r,s in l1c if regime_at(ts)!="BEAR"]
json.dump({"strategy":"XAU_4H_LONG_L1_EMA21_pocCut_regimeV5","n":len(final),
           "regime_detector":"v5 4H-native RAW (stable daily + 1H/4H drawdown override)","trades":final},
          open(L1DIR/"l1_FINAL_regime_gated.json","w"),indent=1)
print(f"\nSALVO l1_FINAL_regime_gated.json: {len(final)} trades (L1 EMA21 + poc-cut + regime v5 !=BEAR)")
rows=list(csv.DictReader(open(L2DIR/"results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
def L2set(col):
    o=[]
    for r in rows:
        try: R=float(r[col])
        except: continue
        o.append((dep(r["datetime"]),R))
    return sorted(o)
print("\n=== L2/BPT 276 (RAW regime) ===")
for col in ("capped_realR","realized_letrun_120"):
    l2=L2set(col)
    show(f"L2-276 [{col}] base",l2)
    show(f"L2-276 [{col}] +regime!=BEAR",[(t,r) for t,r in l2 if regime_prevday_close(t)!="BEAR"])
l2=L2set("capped_realR"); ncut=sum(1 for t,_ in l2 if regime_prevday_close(t)=="BEAR")
print(f"\nL2 regime corta {ncut}/276 trades")
