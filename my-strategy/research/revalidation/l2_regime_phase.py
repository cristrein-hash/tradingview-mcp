#!/usr/bin/env python3
"""TRILHA A — fase de transição de regime na L2/BPT (overlap 2024-05+, 1H-preciso). Classifica cada trade L2 pela
FASE do ciclo de regime no momento (não gate): bear_onset / capitulacao_flip(recuperação recente) / bull_maduro /
range / range_recov. Mede WR/streak/sumR/big-winners por fase. Régua letrun_120. RAW, causal."""
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
# regime diário (com override) p/ a sequência de fases
dreg=[]
for i in range(len(DK)):
    dayend=(DK[i]+1)*86400-1
    dreg.append("BEAR" if (ovr_at(dayend) or stable[i]=="BEAR") else stable[i])
def phase_at(date_ep):
    di=bisect.bisect_left(DK,date_ep//86400)-1
    if di<0: return "n/a"
    cur=dreg[di]
    # dias desde última BEAR (fim do bear -> recuperação)
    days_since_bear=99
    for j in range(di,max(-1,di-30),-1):
        if dreg[j]=="BEAR": days_since_bear=di-j; break
    if cur=="BEAR": return "bear"
    if days_since_bear<=5: return "capit_flip"   # <=5d após sair do BEAR = reversão de capitulação
    if cur=="RANGE": return "range"
    # BULL: maduro vs jovem
    bull_age=0
    for j in range(di,-1,-1):
        if dreg[j]=="BULL": bull_age+=1
        else: break
    return "bull_jovem" if bull_age<=10 else "bull_maduro"
def dep(s): return int(dt.datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rows=list(csv.DictReader(open(L2DIR/"results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
OVL=dep("2024-05-24")
l2=[]
for r in rows:
    t=dep(r["datetime"])
    if t<OVL: continue
    try: R=float(r["realized_letrun_120"])
    except: continue
    l2.append((t,R,phase_at(t)))
def panel(R):
    n=len(R)
    if not n: return None
    sm=sum(R); w=sum(1 for x in R if x>0); eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=cl=0
    for x in R:
        if x<0: cl+=1
        else: cl=0
        mL=max(mL,cl)
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),mL,sum(1 for x in R if x>=5)
from collections import defaultdict
byp=defaultdict(list)
for t,R,ph in l2: byp[ph].append(R)
print(f"L2/BPT overlap (N={len(l2)}, régua letrun_120) por FASE de regime:\n")
print(f"{'fase':<14}{'N':>4}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>7}{'maxLoss':>8}{'bigW':>5}")
for ph in ("capit_flip","bull_jovem","bull_maduro","range","bear"):
    p=panel(byp.get(ph,[]))
    if not p: print(f"{ph:<14} (vazio)"); continue
    n,wr,sm,av,dd,mL,bw=p
    print(f"{ph:<14}{n:>4}{wr:>5}%{sm:>8}{av:>7}{dd:>7}{mL:>8}{bw:>5}")
allp=panel([R for _,R,_ in l2]); print(f"\n{'TODOS':<14}{allp[0]:>4}{allp[1]:>5}%{allp[2]:>8}{allp[3]:>7}{allp[4]:>7}{allp[5]:>8}{allp[6]:>5}")
