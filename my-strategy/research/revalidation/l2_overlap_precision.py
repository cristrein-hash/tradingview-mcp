#!/usr/bin/env python3
"""L2/BPT [letrun_120] no OVERLAP 2024-05+ (1H RAW = precisão extrema). Pergunta: o gate regime v5 !=BEAR PRESERVA
os big winners de fundo da L2, ou mesmo com precisão máxima os corta? Lista cada big winner (letrun) c/ regime.
Detector 4H-nativo RAW (estável diário RAW4H + override RAW1H 2024+). RAW only, causal."""
import json,csv,bisect,datetime as dt
from pathlib import Path
BASE=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
L2DIR=BASE/"XAU_4H_L2_BPT_BOS_CHOCH/v1"
B4=[json.loads(l) for l in (BASE/"raw_4h_ohlc.jsonl").read_text().splitlines()]
B1=[json.loads(l) for l in (BASE/"raw_1h_ohlc.jsonl").read_text().splitlines()]
TS4=[b["t"] for b in B4]; C4=[b["c"] for b in B4]; H4=[b["h"] for b in B4]
TS1=[b["t"] for b in B1]; C1=[b["c"] for b in B1]; H1=[b["h"] for b in B1]
days={}
for b in B4:
    k=b["t"]//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]}); g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
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
def override(TS,C,Hh,P,mom,dd,Krec):
    out=[]; ov=False; q=0
    for j in range(len(TS)):
        if j<max(P,mom): out.append(False); continue
        peak=max(Hh[j-P:j+1]); ddp=(peak-C[j])/peak if peak>0 else 0
        fired= ddp>=dd and C[j]<C[j-mom]
        if fired: ov=True; q=0
        elif ov:
            q+=1
            if q>=Krec: ov=False
        out.append(ov)
    return out
OV4=override(TS4,C4,H4,12,6,0.06,30); OV1=override(TS1,C1,H1,48,24,0.06,120); T1MIN=TS1[0]
def ovr_at(ts):
    if ts>=T1MIN:
        j=bisect.bisect_right(TS1,ts)-1; return OV1[j] if j>=0 else False
    j=bisect.bisect_right(TS4,ts)-1; return OV4[j] if j>=0 else False
def regime_prevday_close(date_ep):
    di=bisect.bisect_left(DK,date_ep//86400)-1
    if di<0: return "RANGE"
    dayend=(DK[di]+1)*86400-1
    return "BEAR" if (ovr_at(dayend) or stable[di]=="BEAR") else stable[di]
def dep(s): return int(dt.datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rows=list(csv.DictReader(open(L2DIR/"results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
OVL=dep("2024-05-24")
l2=[]
for r in rows:
    t=dep(r["datetime"])
    if t<OVL: continue
    try: R=float(r["realized_letrun_120"])
    except: continue
    l2.append((t,R,r["datetime"]))
l2.sort()
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
def show(tag,trades):
    p=panel([r for _,r,_ in trades])
    if not p: print(f"{tag}: vazio"); return
    n,wr,sm,dd,sk=p; print(f"{tag:<34} N{n:>3} WR{wr:>5}% sumR{sm:>7} DD{dd:>6} streak{sk}")
print(f"L2/BPT OVERLAP (>=2024-05-24), régua letrun_120, detector RAW 1H-preciso:\n")
show("L2 overlap base",l2)
show("L2 overlap +regime!=BEAR",[(t,r,d) for t,r,d in l2 if regime_prevday_close(t)!="BEAR"])
print(f"\nBIG WINNERS de fundo (letrun R>=5) — preservados ou cortados pelo gate?:")
bw=[(t,r,d) for t,r,d in l2 if r>=5]
keptR=cutR=0
for t,r,d in sorted(bw,key=lambda z:-z[1]):
    reg=regime_prevday_close(t); status="KEPT" if reg!="BEAR" else "CORTADO"
    if reg!="BEAR": keptR+=r
    else: cutR+=r
    print(f"  {d}  letrun {r:+.1f}  regime={reg:<5} {status}")
print(f"\nbig-winners (R>=5): {len(bw)} | R preservado {keptR:.1f} | R cortado {cutR:.1f}")
allcut=[(t,r,d) for t,r,d in l2 if regime_prevday_close(t)=="BEAR"]
print(f"total cortado: {len(allcut)} trades | R cortado {sum(r for _,r,_ in allcut):.1f} (losers {sum(1 for _,r,_ in allcut if r<=0)} / winners {sum(1 for _,r,_ in allcut if r>0)})")
