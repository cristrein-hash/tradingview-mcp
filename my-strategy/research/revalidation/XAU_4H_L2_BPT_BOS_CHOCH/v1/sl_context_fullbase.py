import json,csv,statistics,random
from datetime import datetime,timezone
random.seed(20260618)
exec(open('sl_context.py').read().split('# ---- casos-chave')[0])  # engine: context_sl, classify, realR, swing_origin, legpos
# episodes
base=[int(r['candidate_id'][1:]) for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
idxs=sorted(base);eps=[];cur=[idxs[0]]
for a,b in zip(idxs,idxs[1:]):
    if b-a<=6: cur.append(b)
    else: eps.append(cur);cur=[b]
eps.append(cur)
reps=[e[0] for e in eps if ATR[e[0]]]
def yr(i): return datetime.fromtimestamp(TS[i],timezone.utc).year
def tight6(i):
    p=C[i];a=ATR[i];lo=min(L[max(0,i-5):i+1]);return max(p-(lo-0.1*a),0.3*a)
# build outcomes per policy
def run(slf,allow_notrade):
    out=[]
    for i in reps:
        if allow_notrade:
            sl,risk,typ,dist=context_sl(i)
            if sl is None: continue  # no_trade
        else:
            risk=slf(i)
        R=realR(i,risk);ex=classify(i,risk)
        out.append({'i':i,'R':R,'ex':ex,'ratl':risk/ATR[i],'yr':yr(i)})
    return out
def metr(o):
    rs=[x['R'] for x in o];n=len(rs)
    from collections import Counter
    ex=Counter(x['ex'] for x in o)
    win=ex['WIN_RUNNER']+ex['WIN_partialBE']+ex['WIN_partial_held'];stop=ex['STOP_LOSS'];scr=ex['SCRATCH_timeout']
    eq=pk=dd=c=ms=0
    for x in rs: eq+=x;pk=max(pk,eq);dd=max(dd,pk-eq);c=c+1 if x<0 else 0;ms=max(ms,c)
    rat=sorted(x['ratl'] for x in o);q=lambda p:rat[min(len(rat)-1,int(p*len(rat)))]
    return dict(n=n,sumR=round(sum(rs),1),avgR=round(sum(rs)/n,3),medR=round(statistics.median(rs),2),
        WIN=win,STOP=stop,SCRATCH=scr,maxDD=round(dd,1),streak=ms,
        slmed=round(statistics.median(rat),2),slp90=round(q(.9),2),slmax=round(max(rat),2),
        lt1=sum(1 for x in rat if x<1),a12=sum(1 for x in rat if 1<=x<2),a24=sum(1 for x in rat if 2<=x<4),gt4=sum(1 for x in rat if x>=4))
ctx=run(None,True);sw=run(swing_origin,False);t6=run(tight6,False)
notrade=len(reps)-len(ctx)
print("=== FULL BASE — exit partial50@2R+6R ===")
for nm,o in [('CONTEXT_DEMAND_SL',ctx),('SWING_ORIGIN(mec)',sw),('TIGHT_6BAR',t6)]:
    m=metr(o)
    print(f"  {nm:<20} n={m['n']} sumR={m['sumR']:+} avgR={m['avgR']:+} medR={m['medR']:+} | WIN={m['WIN']} STOP={m['STOP']} SCR={m['SCRATCH']} | DD={m['maxDD']} strk={m['streak']} | SLmed={m['slmed']} p90={m['slp90']} max={m['slmax']} | <1ATR={m['lt1']} 1-2={m['a12']} 2-4={m['a24']} >4={m['gt4']}")
print(f"  (CONTEXT: {notrade} no_trade excluídos por TOP_EXHAUSTION)")
# improvement register
mc=metr(ctx);ms=metr(sw)
with open(f"{D}/l2_bpt_sl_context_improvement_register.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['policy','n','sumR','avgR','WIN','STOP','SCRATCH','maxDD','streak','SLmed','SLp90','SL_lt1','SL_1_2','SL_2_4','SL_gt4','verdict'])
    for nm,o in [('CONTEXT_DEMAND_SL',ctx),('SWING_ORIGIN_mec',sw),('TIGHT_6BAR',t6)]:
        m=metr(o);w.writerow([nm,m['n'],m['sumR'],m['avgR'],m['WIN'],m['STOP'],m['SCRATCH'],m['maxDD'],m['streak'],m['slmed'],m['slp90'],m['lt1'],m['a12'],m['a24'],m['gt4'],''])
# policy_results
with open(f"{D}/l2_bpt_sl_context_policy_results.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['i','entry_ts','sl_atr','exit_type','R','year'])
    for x in ctx: w.writerow([x['i'],datetime.fromtimestamp(TS[x['i']],timezone.utc).strftime('%Y-%m-%d %H:%M'),round(x['ratl'],2),x['ex'],round(x['R'],2),x['yr']])
# bootstrap CONTEXT vs SWING (paired on common traded reps)
common=[i for i in reps if context_sl(i)[0] is not None]
Rc={};Rs={}
for i in common:
    sl,risk,typ,dist=context_sl(i);Rc[i]=realR(i,risk);Rs[i]=realR(i,swing_origin(i))
ids=list(common);n=len(ids);B=5000
def md(seq):
    eq=pk=m=0
    for x in seq:eq+=x;pk=max(pk,eq);m=max(m,pk-eq)
    return m
da=[];ds=[];dd=[]
for _ in range(B):
    bi=[ids[random.randrange(n)] for _ in range(n)]
    ca=[Rc[i] for i in bi];sa=[Rs[i] for i in bi]
    da.append(sum(ca)/n-sum(sa)/n);ds.append(sum(ca)-sum(sa))
    # block for dd
    seqc=[];seqs=[];k=0
    while len(seqc)<n:
        s=random.randrange(0,n-10)
        for j in range(s,s+10): seqc.append(Rc[ids[j]]);seqs.append(Rs[ids[j]])
    dd.append(md(seqc[:n])-md(seqs[:n]))
def pc(a,p):a=sorted(a);return round(a[int(p*len(a))],3)
with open(f"{D}/l2_bpt_sl_context_bootstrap.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['metric','ci5','ci50','ci95','P_better_than_swing'])
    w.writerow(['delta_avgR',pc(da,.05),pc(da,.5),pc(da,.95),round(sum(1 for x in da if x>0)/B,2)])
    w.writerow(['delta_sumR',pc(ds,.05),pc(ds,.5),pc(ds,.95),round(sum(1 for x in ds if x>0)/B,2)])
    w.writerow(['delta_maxDD',pc(dd,.05),pc(dd,.5),pc(dd,.95),round(sum(1 for x in dd if x<0)/B,2)])
print(f"\n=== BOOTSTRAP CONTEXT vs SWING-ORIGIN (paired, n={n} common, {B}x) ===")
print(f"  delta_avgR  CI[{pc(da,.05)},{pc(da,.5)},{pc(da,.95)}] P(ctx>swing)={sum(1 for x in da if x>0)/B:.2f}")
print(f"  delta_sumR  CI[{pc(ds,.05)},{pc(ds,.5)},{pc(ds,.95)}] P>0={sum(1 for x in ds if x>0)/B:.2f}")
print(f"  delta_maxDD CI[{pc(dd,.05)},{pc(dd,.5)},{pc(dd,.95)}] P(ctx<swing)={sum(1 for x in dd if x<0)/B:.2f}")
# temporal
print("\n=== split temporal (CONTEXT) ===")
for w_,lo,hi in [('2020-2022',2020,2022),('2023-2026',2023,2026)]:
    sub=[x for x in ctx if lo<=x['yr']<=hi];m=metr(sub)
    print(f"  {w_} n={m['n']} sumR={m['sumR']:+} avgR={m['avgR']:+} WIN={m['WIN']} STOP={m['STOP']} SCR={m['SCRATCH']} DD={m['maxDD']}")
