#!/usr/bin/env python3
"""L2/BPT entry/exhaustion — RAW audit + bootstrap completo (5000). SL STRUCT_PURE, exit partial50.
No SLIM/tick-vol/retracted/future. Paired delta-vs-baseline bootstrap."""
import json, csv, statistics, random
from datetime import datetime, timezone
random.seed(20260618)
D="results"
fr=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(fr);H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr];TS=[r['ts_epoch'] for r in fr];RS=[r.get('rsi') for r in fr]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
PL5=[False]*N
for j in range(5,N-5):
    if L[j]<min(L[j-5:j]) and L[j]<min(L[j+1:j+6]): PL5[j]=True
FLOOR=0.3;BUF=0.1;COST=0.10;MAXHOLD=60
def struct_risk(i):
    p=C[i];atr=ATR[i];lo=None
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: lo=L[j];break
    if lo is None: lo=min(L[max(0,i-6):i+1])
    return max(p-(lo-BUF*atr),FLOOR*atr)
def sim(i,risk):
    p=C[i];stop=p-risk;pdone=False;realized=0.0;rem=1.0;end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        if L[j]<=stop:
            fill=O[j] if O[j]<=stop else stop
            return realized+rem*((fill-p)/risk)-COST
        if not pdone and H[j]>=p+2*risk: realized+=0.5*2.0;rem=0.5;pdone=True;stop=p
        if pdone and H[j]>=p+6*risk: return realized+rem*6.0-COST
    return realized+rem*((C[end]-p)/risk)-COST
def legpos90(i):
    p=C[i];hi=max(H[max(0,i-90):i+1]);lo=min(L[max(0,i-90):i+1]);return 100*(p-lo)/(hi-lo) if hi>lo else 50
def body_frac(i):
    rng=H[i]-L[i];return abs(C[i]-O[i])/rng if rng>0 else 0
def dist_hi90(i): return (max(H[max(0,i-90):i+1])-C[i])/ATR[i]
def ext_lo20(i): return (C[i]-min(L[max(0,i-20):i+1]))/ATR[i]
FILT={
 'F_TOP_OB_RSI_strict': lambda i: legpos90(i)>=85 and (RS[i] or 0)>=70,
 'F_TOP_OB_RSI':        lambda i: legpos90(i)>=85 and (RS[i] or 0)>=68,
 'F_LATE_LEG_EXT':      lambda i: legpos90(i)>=85 and ext_lo20(i)>=4.5,
 'F_WEAK_RECLAIM':      lambda i: dist_hi90(i)<2.0 and body_frac(i)<0.15,
}
# ---- episodes ----
base=[r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
def lab(r): return 'BOM' if r['GT_match']=='yes' else ('NAO' if r['NAO_match']=='yes' else 'UNKNOWN')
rl={int(r['candidate_id'][1:]):lab(r) for r in base}
idxs=sorted(rl);eps=[];cur=[idxs[0]]
for a,b in zip(idxs,idxs[1:]):
    if b-a<=6: cur.append(b)
    else: eps.append(cur);cur=[b]
eps.append(cur)
reps=[]
for e in eps:
    labs=[rl[i] for i in e];el='BOM' if 'BOM' in labs else('NAO' if 'NAO' in labs else 'UNKNOWN')
    rep=e[0]
    if el=='BOM': rep=[i for i in e if rl[i]=='BOM'][0]
    elif el=='NAO': rep=[i for i in e if rl[i]=='NAO'][0]
    reps.append((rep,el))
def yr(i): return datetime.fromtimestamp(TS[i],timezone.utc).year
EP=[]
for rep,el in reps:
    if not ATR[rep]: continue
    EP.append({'i':rep,'el':el,'R':sim(rep,struct_risk(rep)),'yr':yr(rep)})
# ---- metrics ----
def avgR(rs): return sum(rs)/len(rs) if rs else 0
def wr(rs): return 100*sum(1 for x in rs if x>0)/len(rs) if rs else 0
def maxdd(seq):
    eq=pk=mdd=0
    for x in seq: eq+=x;pk=max(pk,eq);mdd=max(mdd,pk-eq)
    return mdd
def lstreak(seq):
    c=ms=0
    for x in seq: c=c+1 if x<0 else 0;ms=max(ms,c)
    return ms
def pct(a,p): a=sorted(a);return a[min(len(a)-1,int(p*len(a)))]
# ---- BOOTSTRAP (paired) ----
B=5000;BLK=10
def bootstrap(fn):
    n=len(EP);Rall=[e['R'] for e in EP];blk=[fn(e['i']) for e in EP]
    d_avg=[];d_sum=[];d_wr=[];d_dd=[];d_str=[]
    f_avg=[];f_sum=[];f_wr=[];f_dd=[];f_str=[]
    for _ in range(B):
        # simple resample for avg/sum/wr
        idx=[random.randrange(n) for _ in range(n)]
        ball=[Rall[k] for k in idx]; fk=[Rall[k] for k in idx if not blk[k]]
        if not fk: fk=[0]
        d_avg.append(avgR(fk)-avgR(ball)); d_sum.append(sum(fk)-sum(ball)); d_wr.append(wr(fk)-wr(ball))
        f_avg.append(avgR(fk)); f_sum.append(sum(fk)); f_wr.append(wr(fk))
        # block resample (ordered) for dd/streak
        seq=[];kept=[]
        while len(seq)<n:
            s=random.randrange(0,n-BLK)
            for k in range(s,s+BLK):
                seq.append(Rall[k])
                if not blk[k]: kept.append(Rall[k])
        seq=seq[:n]
        d_dd.append(maxdd(kept)-maxdd(seq)); d_str.append(lstreak(kept)-lstreak(seq))
        f_dd.append(maxdd(kept)); f_str.append(lstreak(kept))
    return {
     'f_avgR':(round(pct(f_avg,.05),3),round(pct(f_avg,.5),3),round(pct(f_avg,.95),3)),
     'f_sumR':(round(pct(f_sum,.05),1),round(pct(f_sum,.5),1),round(pct(f_sum,.95),1)),
     'f_WR':(round(pct(f_wr,.05),1),round(pct(f_wr,.5),1),round(pct(f_wr,.95),1)),
     'd_avgR':(round(pct(d_avg,.05),3),round(pct(d_avg,.5),3),round(pct(d_avg,.95),3)),
     'd_sumR':(round(pct(d_sum,.05),1),round(pct(d_sum,.5),1),round(pct(d_sum,.95),1)),
     'd_maxDD':(round(pct(d_dd,.05),1),round(pct(d_dd,.5),1),round(pct(d_dd,.95),1)),
     'd_streak':(round(pct(d_str,.05),0),round(pct(d_str,.5),0),round(pct(d_str,.95),0)),
     'P_dAvg>0':round(sum(1 for x in d_avg if x>0)/B,2),
     'P_dSum>0':round(sum(1 for x in d_sum if x>0)/B,2),
     'P_dDD<0':round(sum(1 for x in d_dd if x<0)/B,2),
     'P_dStreak<0':round(sum(1 for x in d_str if x<0)/B,2),
    }
# baseline point
Rall=[e['R'] for e in EP]
print(f"BASELINE: n={len(EP)} avgR={avgR(Rall):+.3f} sumR={sum(Rall):+.1f} WR={wr(Rall):.1f}% maxDD={maxdd(Rall):.1f} streak={lstreak(Rall)}")
boot={}
print(f"\n=== BOOTSTRAP {B} (paired delta vs baseline) ===")
for nm,fn in FILT.items():
    b=bootstrap(fn);boot[nm]=b
    print(f"  {nm}")
    print(f"    delta_avgR CI[5/50/95]={b['d_avgR']}  P(>0)={b['P_dAvg>0']}")
    print(f"    delta_sumR CI={b['d_sumR']}  P(>0)={b['P_dSum>0']}")
    print(f"    delta_maxDD CI={b['d_maxDD']}  P(<0)={b['P_dDD<0']}")
    print(f"    delta_streak CI={b['d_streak']}  P(<0)={b['P_dStreak<0']}")
with open(f"{D}/l2_bpt_entry_exhaustion_bootstrap.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['filter','metric','ci5','ci50','ci95','P_improve'])
    w.writerow(['BASELINE','avgR','','%.3f'%avgR(Rall),'','']);w.writerow(['BASELINE','sumR','','%.1f'%sum(Rall),'',''])
    for nm,b in boot.items():
        for met,key,pk in [('delta_avgR','d_avgR','P_dAvg>0'),('delta_sumR','d_sumR','P_dSum>0'),('delta_maxDD','d_maxDD','P_dDD<0'),('delta_streak','d_streak','P_dStreak<0')]:
            w.writerow([nm,met,b[key][0],b[key][1],b[key][2],b[pk]])
# ---- improvement register ----
swing={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
MUST=['E1','E5','E13','E17','E21','E27','E30','E40']
must_idx={ts2idx[parse(swing[e]['timestamp'])] for e in MUST if e in swing}
def verdict(b,bomcut):
    if bomcut>0: return 'REJECTED_RECALL_FAIL'
    pa,pd=b['P_dAvg>0'],b['P_dDD<0']
    if pa>=0.9 and pd>=0.9: return 'ROBUST_IMPROVEMENT'
    if (pa>=0.6 or pd>=0.6) and b['d_avgR'][0]>-0.05: return 'SMALL_BUT_STABLE'
    if pa<0.5 and pd<0.5: return 'HARMFUL'
    return 'POINT_ESTIMATE_ONLY'
reg=[]
for nm,fn in FILT.items():
    blocked=[e for e in EP if fn(e['i'])];kept=[e for e in EP if not fn(e['i'])]
    rk=[e['R'] for e in kept];bomcut=sum(1 for e in blocked if e['el']=='BOM')
    mustcut=sum(1 for e in blocked if e['i'] in must_idx)
    b=boot[nm]
    reg.append({'filter':nm,'n_removed':len(blocked),'removed_winners_must':mustcut,'removed_BOM':bomcut,
        'removed_NAO':sum(1 for e in blocked if e['el']=='NAO'),'removed_UNKNOWN':sum(1 for e in blocked if e['el']=='UNKNOWN'),
        'avgR_before':round(avgR(Rall),3),'avgR_after':round(avgR(rk),3),'delta_avgR_ci':str(b['d_avgR']),
        'sumR_before':round(sum(Rall),1),'sumR_after':round(sum(rk),1),'delta_sumR_ci':str(b['d_sumR']),
        'WR_before':round(wr(Rall),1),'WR_after':round(wr(rk),1),
        'DD_before':round(maxdd(Rall),1),'DD_after':round(maxdd([e['R'] for e in kept]),1),'delta_maxDD_ci':str(b['d_maxDD']),
        'streak_before':lstreak(Rall),'streak_after':lstreak([e['R'] for e in kept]),
        'P_dAvg>0':b['P_dAvg>0'],'P_dDD<0':b['P_dDD<0'],'verdict':verdict(b,bomcut)})
with open(f"{D}/l2_bpt_entry_exhaustion_improvement_register.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(reg[0].keys()));w.writeheader();w.writerows(reg)
print("\n=== IMPROVEMENT REGISTER (verdict) ===")
for r in reg: print(f"  {r['filter']:<22} rm={r['n_removed']} BOMcut={r['removed_BOM']} mustcut={r['removed_winners_must']} | avgR {r['avgR_before']}->{r['avgR_after']} sumR {r['sumR_before']}->{r['sumR_after']} DD {r['DD_before']}->{r['DD_after']} | {r['verdict']}")
print("\nWROTE bootstrap.csv + improvement_register.csv")
