import json,csv
from datetime import datetime,timezone
D="results"
fr=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(fr);H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr];TS=[r['ts_epoch'] for r in fr]
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
    risk=p-(lo-BUF*atr)
    return max(risk,FLOOR*atr)
def tight_risk(i):
    p=C[i];atr=ATR[i];risk=p-(min(L[max(0,i-5):i+1])-BUF*atr)
    return max(risk,FLOOR*atr)
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
swing={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
labels={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_episode_labels.csv"))}
svp={r['time']:r for r in (json.loads(l) for l in open('/tmp/svp_bars.jsonl'))}

# generic exit sim. takeoffs=[(frac,R)], runner_target, be_after_R (move to BE once price>=be_after_R*risk; None=never)
def sim(i,risk,takeoffs,runner_tgt,be_after):
    p=C[i];stop=p-risk;realized=0.0;rem=1.0;done=[False]*len(takeoffs);armed=False;end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        if L[j]<=stop:
            fill=O[j] if O[j]<=stop else stop
            return realized+rem*((fill-p)/risk)-COST
        for k,(frac,Rk) in enumerate(takeoffs):
            if not done[k] and rem>0 and H[j]>=p+Rk*risk:
                realized+=frac*Rk;rem=max(0,rem-frac);done[k]=True
        if be_after is not None and not armed and H[j]>=p+be_after*risk: armed=True;stop=max(stop,p)
        if rem>0 and runner_tgt and H[j]>=p+runner_tgt*risk:
            return realized+rem*runner_tgt-COST
        if rem<=0: return realized-COST
    return realized+rem*((C[end]-p)/risk)-COST
def path(i,risk):
    p=C[i];end=min(i+MAXHOLD,N-1);mfe=0;mae=0;t1=t2=tstop=None;sl=p-risk
    for j in range(i+1,end+1):
        mfe=max(mfe,(H[j]-p)/risk);mae=min(mae,(L[j]-p)/risk)
        if t1 is None and H[j]>=p+1*risk: t1=j-i
        if t2 is None and H[j]>=p+2*risk: t2=j-i
        if tstop is None and L[j]<=sl: tstop=j-i
    return mfe,mae,t1,t2,tstop
VAR={
 'A partial50@2R+6R (atual)':(lambda i,r:sim(i,r,[(0.5,2.0)],6.0,2.0)),
 'B no-partial +3R':(lambda i,r:sim(i,r,[],3.0,None)),
 'C no-partial +6R':(lambda i,r:sim(i,r,[],6.0,None)),
 'D partial25@2R runner75 +6R':(lambda i,r:sim(i,r,[(0.25,2.0)],6.0,2.0)),
 'E partial50@3R +6R':(lambda i,r:sim(i,r,[(0.5,3.0)],6.0,3.0)),
 'F partial50@2R BE-only-after+3R':(lambda i,r:sim(i,r,[(0.5,2.0)],6.0,3.0)),
}
out=[]
for eid in ['E1','E17']:
    i=ts2idx[parse(swing[eid]['timestamp'])];p=C[i];atr=ATR[i]
    sr=struct_risk(i);tr=tight_risk(i)
    mfe,mae,t1,t2,tstop=path(i,sr); mfeT,maeT,_,_,_=path(i,tr)
    lr=labels.get(eid,{});b=svp.get(TS[i],{})
    print(f"\n===== {eid} ({swing[eid]['timestamp']}) idx={i} =====")
    print(f"  entry={p:.1f} ATR={atr:.2f} | SL_estrut risk={sr:.1f} ({sr/atr:.2f}ATR) | SL_tight risk={tr:.1f} ({tr/atr:.2f}ATR)")
    print(f"  PATH (SL estrut): MFE={mfe:.2f}R MAE={mae:.2f}R | +1R@bar{t1} +2R@bar{t2} stop@bar{tstop}")
    print(f"  PATH (SL tight):  MFE={mfeT:.2f}R (move igual, risk menor => mais R-múltiplos)")
    print(f"  causal: legpos≈? rsi={lr.get('rsi')} bear_leg={lr.get('bear_leg_context')} demand={lr.get('demand_below_cat')}/{lr.get('dist_demand_atr')}ATR sweep?={swing[eid]['sweep']} bos_down={swing[eid]['bos_down_recent']} reclaim={lr.get('reclaim_candle')} nas={lr.get('recent_nas')} VPvol={b.get('volume')}")
    print(f"  --- exit variants ---")
    for vn,fn in VAR.items():
        rs=fn(i,sr);rt=fn(i,tr)
        print(f"    {vn:<34} SLestrut R={rs:+.2f} | SLtight R={rt:+.2f}")
        out.append({'episode':eid,'variant':vn,'SL_estrut_ATR':round(sr/atr,2),'R_SLestrut':round(rs,2),'R_SLtight':round(rt,2),'MFE_R':round(mfe,2),'MAE_R':round(mae,2)})
with open(f"{D}/l2_bpt_e1_e17_exit_sl_audit.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
print("\nWROTE results/l2_bpt_e1_e17_exit_sl_audit.csv")
