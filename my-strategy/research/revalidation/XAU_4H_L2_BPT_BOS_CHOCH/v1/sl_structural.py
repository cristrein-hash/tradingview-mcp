#!/usr/bin/env python3
"""L2/BPT SL estrutural trade-a-trade. Exit FIXO partial50@2R+6R. SL models causais.
NO SLIM, NO future, NO production, NO 1.5ATR ceiling. research-only."""
import json,csv,statistics
from datetime import datetime,timezone
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen];O=[r['open'] for r in frozen];TS=[r['ts_epoch'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
# Williams pivots
def pivots(k):
    pf=[False]*N
    for j in range(k,N-k):
        if L[j]<min(L[j-k:j]) and L[j]<min(L[j+1:j+k+1]): pf[j]=True
    return pf
PL5=pivots(5); PL3=pivots(3)
FLOOR=0.3;BUF=0.1
def floor_sl(p,sl,atr):
    risk=p-sl
    if risk<FLOOR*atr: sl=p-FLOOR*atr;risk=FLOOR*atr
    return sl,risk
# --- SL MODELS: return (sl_price, risk, tag, conf) ; conf='ok'/'LOW_CONF' ---
def m_retest(i,p,atr):
    lo=min(L[max(0,i-2):i+1]); sl,risk=floor_sl(p,lo-BUF*atr,atr); return sl,risk,'',('ok')
def swing_origin_low(i,p):
    # causal: Williams 5/5 pivot at j is only CONFIRMED at bar j+5, so require j<=i-5
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: return L[j]
    return None
def m_swing(i,p,atr):
    lo=swing_origin_low(i,p)
    if lo is None: lo=min(L[max(0,i-6):i+1]); conf='LOW_CONF'
    else: conf='ok'
    sl,risk=floor_sl(p,lo-BUF*atr,atr); return sl,risk,'',conf
def m_demand(i,p,atr):
    # nearest defended base = lowest PL5 pivot low in last 30 bars below entry (causal: j<=i-5)
    cands=[L[j] for j in range(max(5,i-30),i-4) if PL5[j] and L[j]<p]
    if not cands:
        sl,risk,_,c=m_swing(i,p,atr); return sl,risk,'',('LOW_CONF')
    lo=min(cands); sl,risk=floor_sl(p,lo-BUF*atr,atr); return sl,risk,'',('ok')
DPOL={}
for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv")):
    try: DPOL[int(r['candidate_id'][1:])]=float(r['dist_pol_atr'])
    except: pass
def m_polarity(i,p,atr):
    dp=DPOL.get(i)
    if dp is None or dp<=0:
        sl,risk,_,_=m_swing(i,p,atr); return sl,risk,'CLOSE',('LOW_CONF')  # fallback swing, still close-based
    lvl=p-dp*atr; sl,risk=floor_sl(p,lvl-BUF*atr,atr); return sl,risk,'CLOSE',('ok')
def m_capped(i,p,atr):
    sl,risk,_,conf=m_swing(i,p,atr)
    tag='>4ATR' if risk>4*atr else ('ideal' if risk>=2*atr else 'tight')
    return sl,risk,tag,conf
def m_hybrid(i,p,atr):
    ds,dr,_,dc=m_demand(i,p,atr)
    if dc=='ok' and dr<=4*atr: return ds,dr,'demand','ok'
    ss,sr,_,sc=m_swing(i,p,atr)
    if sc=='ok' and sr<=4*atr: return ss,sr,'swing','ok'
    rs,rr,_,_=m_retest(i,p,atr); return rs,rr,'retest','LOW_CONF'
def m_base(i,p,atr):  # baseline real_outcome structural_sl
    lo=min(L[max(0,i-5):i+1]); sl=lo-BUF*atr; risk=p-sl
    if risk<FLOOR*atr: sl=p-FLOOR*atr;risk=FLOOR*atr
    return sl,risk,('R_ceiling' if risk>1.5*atr else ''),'ok'
MODELS={'BASELINE':m_base,'M1_RETEST_LOW':m_retest,'M2_SWING_ORIGIN':m_swing,'M3_DEMAND_BASE':m_demand,
        'M4_POLARITY_CLOSE':m_polarity,'M5_CAPPED_STRUCT':m_capped,'M6_HYBRID':m_hybrid}
# --- exit partial50@2R+6R ---
COST=0.10;MAXHOLD=60
def sim(i,p,risk,sl0,close_based):
    # gap-aware fills: if bar OPENS through the stop, fill at open (worse), not at stop level
    stop=sl0;pdone=False;realized=0.0;rem=1.0;end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        op=O[j];hi=H[j];lo=L[j];cl=C[j]
        if not pdone and close_based:
            if cl<stop: return rem*((cl-p)/risk)-COST,'stop'   # close-based already captures gap
        else:
            if lo<=stop:
                fill=op if op<=stop else stop   # gap-through → fill at open
                return realized+rem*((fill-p)/risk)-COST,('be' if pdone else 'stop')
        if not pdone and hi>=p+2*risk:
            realized+=0.5*2.0;rem=0.5;pdone=True;stop=p
        if pdone and hi>=p+6*risk:
            return realized+rem*6.0-COST,'runner'
    return realized+rem*((C[end]-p)/risk)-COST,'time'
# --- episodes (replicate real_outcome.py) ---
base=[r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
def lab(r): return 'BOM' if r['GT_match']=='yes' else ('NAO' if r['NAO_match']=='yes' else 'UNKNOWN')
rows_lab={int(r['candidate_id'][1:]):lab(r) for r in base}
idxs=sorted(rows_lab);episodes=[];cur=[idxs[0]]
for a,b in zip(idxs,idxs[1:]):
    if b-a<=6: cur.append(b)
    else: episodes.append(cur);cur=[b]
episodes.append(cur)
ep_reps=[]
for e in episodes:
    labs=[rows_lab[i] for i in e]
    el='BOM' if 'BOM' in labs else ('NAO' if 'NAO' in labs else 'UNKNOWN')
    rep=e[0]
    if el=='BOM': rep=[i for i in e if rows_lab[i]=='BOM'][0]
    elif el=='NAO': rep=[i for i in e if rows_lab[i]=='NAO'][0]
    ep_reps.append((rep,el))
def yr(i): return datetime.fromtimestamp(TS[i],timezone.utc).year
# --- run a model over reps -> list of dict ---
def run_model(name,fn,reps):
    out=[]
    for rep,el in reps:
        p=C[rep];atr=ATR[rep]
        if not atr: continue
        sl,risk,tag,conf=fn(rep,p,atr)
        cb = ('CLOSE' in str(tag)) or (name=='M4_POLARITY_CLOSE')
        r,how=sim(rep,p,risk,sl,cb)
        out.append({'rep':rep,'el':el,'R':r,'how':how,'risk_atr':risk/atr,'tag':tag,'conf':conf,'yr':yr(rep)})
    return out
def metrics(out):
    rs=[o['R'] for o in out];n=len(rs)
    wins=[x for x in rs if x>0];losses=[x for x in rs if x<0]
    pf=sum(wins)/abs(sum(losses)) if losses else float('inf')
    eq=0;pk=0;mdd=0;c=0;ms=0
    for x in rs:
        eq+=x;pk=max(pk,eq);mdd=max(mdd,pk-eq);c=c+1 if x<0 else 0;ms=max(ms,c)
    ratls=[o['risk_atr'] for o in out];ratls.sort()
    q=lambda a,p:a[min(len(a)-1,int(p*len(a)))]
    return {'n':n,'WR':round(100*len(wins)/n,1),'avgR':round(sum(rs)/n,3),'sumR':round(sum(rs),1),
            'medR':round(statistics.median(rs),2),'PF':round(pf,2) if pf!=float('inf') else 'inf','maxDD':round(mdd,1),
            'streak':ms,'scratch':sum(1 for x in rs if -0.11<=x<=0.11),
            'stop':sum(1 for o in out if o['how']=='stop'),'be':sum(1 for o in out if o['how']=='be'),
            'runner':sum(1 for o in out if o['how']=='runner'),'time':sum(1 for o in out if o['how']=='time'),
            'partialhit':sum(1 for o in out if o['how'] in('be','runner','time') and o['R']>0.5),
            'slATRmed':round(statistics.median(ratls),2),'slATRp90':round(q(ratls,0.9),2),'slATRmax':round(max(ratls),2),
            'sl_gt4ATR':sum(1 for o in out if o['risk_atr']>4),'lowconf':sum(1 for o in out if o['conf']=='LOW_CONF')}
print("=== FULL 276-EPISODE PERFORMANCE — exit partial50@2R+6R, cost 0.10R ===")
allres={}
for name,fn in MODELS.items():
    out=run_model(name,fn,ep_reps);allres[name]=out;m=metrics(out)
    print(f"{name:<18} n={m['n']} WR={m['WR']}% avgR={m['avgR']:+} sumR={m['sumR']:+} medR={m['medR']:+} PF={m['PF']} maxDD={m['maxDD']} streak={m['streak']} | stop={m['stop']} run={m['runner']} time={m['time']} | slATR med={m['slATRmed']} p90={m['slATRp90']} max={m['slATRmax']} >4ATR={m['sl_gt4ATR']} lowconf={m['lowconf']}")
# write performance csv
with open(f"{D}/l2_bpt_sl_structural_performance.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['model']+list(metrics(allres['BASELINE']).keys()))
    for name in MODELS: m=metrics(allres[name]);w.writerow([name]+list(m.values()))
print("\nWROTE results/l2_bpt_sl_structural_performance.csv")
print(f"episodes={len(episodes)} BOM={sum(1 for _,e in ep_reps if e=='BOM')} NAO={sum(1 for _,e in ep_reps if e=='NAO')} UNK={sum(1 for _,e in ep_reps if e=='UNKNOWN')}")

# ===== TAREFA 3: 41 episódios visuais — mapear E# -> bar idx via timestamp =====
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
swing={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
review={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_full_res_visual_episode_review.csv"))}
E2IDX={}
for eid,sr in swing.items():
    ep=parse(sr['timestamp']); E2IDX[eid]=ts2idx.get(ep)
WINNERS9=['E1','E13','E17','E27','E30','E40','E21','E23','E5']
BADSL12=['E2','E3','E4','E19','E20','E22','E28','E29','E31','E32','E38','E41']
SHOULDNOT=['E6','E7','E8','E9','E10','E11','E15','E24','E34','E36','E37','E39']
def model_R(name,fn,i):
    p=C[i];atr=ATR[i]
    if not atr: return None
    sl,risk,tag,conf=fn(i,p,atr); cb=('CLOSE' in str(tag)) or name=='M4_POLARITY_CLOSE'
    r,how=sim(i,p,risk,sl,cb); return {'R':r,'how':how,'risk_atr':risk/atr,'tag':tag,'conf':conf}
print("\n=== IMPACT on visual subsets (R>0 = saved) — exit partial50 ===")
for sub,nm in [(WINNERS9,'9 winners'),(BADSL12,'12 bad_SL'),(SHOULDNOT,'should_not_long')]:
    print(f" -- {nm} (n={len(sub)}) --")
    for name in ['BASELINE','M2_SWING_ORIGIN','M5_CAPPED_STRUCT','M6_HYBRID','M4_POLARITY_CLOSE']:
        fn=MODELS[name];rs=[];saved=0;big=0
        for eid in sub:
            i=E2IDX.get(eid)
            if i is None: continue
            mr=model_R(name,fn,i)
            if mr is None: continue
            rs.append(mr['R']); saved+= 1 if mr['R']>0 else 0; big+= 1 if mr['risk_atr']>4 else 0
        if rs: print(f"    {name:<18} saved={saved}/{len(rs)} avgR={sum(rs)/len(rs):+.2f} sumR={sum(rs):+.1f} risk>4ATR={big}")
# trade_review.csv (per E#, chosen structural model M5)
with open(f"{D}/l2_bpt_sl_structural_trade_review.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['episode_id','idx','valid_long','issue_type','suggested_SL_visual','swing_origin_dist_atr',
        'M5_risk_atr','M5_tag','M5_R','M5_how','converts_to_winner','risk_too_big_gt4ATR','subset','note'])
    for eid in sorted(swing,key=lambda x:int(x[1:])):
        i=E2IDX.get(eid); sr=swing[eid]; rv=review.get(eid,{})
        sub='winner9' if eid in WINNERS9 else ('badSL12' if eid in BADSL12 else ('should_not' if eid in SHOULDNOT else 'other'))
        if i is None: w.writerow([eid,'NA',rv.get('valid_long_yes_no_unclear',''),rv.get('issue_type',''),rv.get('suggested_SL_model',''),sr.get('sl_origin_dist_atr',''),'','','','','','',sub,'no_bar_match']);continue
        mr=model_R('M5_CAPPED_STRUCT',MODELS['M5_CAPPED_STRUCT'],i)
        w.writerow([eid,i,rv.get('valid_long_yes_no_unclear',''),rv.get('issue_type',''),rv.get('suggested_SL_model',''),
            sr.get('sl_origin_dist_atr',''),round(mr['risk_atr'],2),mr['tag'],round(mr['R'],2),mr['how'],
            'yes' if mr['R']>0 else 'no','yes' if mr['risk_atr']>4 else 'no',sub,sr.get('annot','')[:30]])
# models.csv (definitions)
defs=[('BASELINE','recent 6-bar low -0.1ATR, floor 0.3, NO real cap (flag only)','intrabar'),
 ('M1_RETEST_LOW','recent 2-bar reclaim low -0.1ATR, floor 0.3','intrabar'),
 ('M2_SWING_ORIGIN','most recent Williams 5/5 pivot low below entry -0.1ATR (=SL_STRUCTURE_LOW visual)','intrabar'),
 ('M3_DEMAND_BASE','lowest Williams5/5 pivot low in last 30 bars below entry -0.1ATR (proxy demand; no OB-zone data offline)','intrabar'),
 ('M4_POLARITY_CLOSE','polarity level entry-dist_pol_atr*ATR; exit on CLOSE below -0.1ATR (close-based invalidation)','close'),
 ('M5_CAPPED_STRUCT','=M2 swing origin; floor 0.3; NO hard ceiling; TAG >4ATR/ideal2-4/tight','intrabar'),
 ('M6_HYBRID','hierarchy: demand(<=4ATR)->swing(<=4ATR)->retest(LOW_CONF); bounds SL operationally','intrabar')]
with open(f"{D}/l2_bpt_sl_structural_models.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['model','definition','stop_type','full_sumR','full_WR','full_streak','full_maxDD','full_slATRmed','full_gt4ATR'])
    for nm,d,st in defs:
        m=metrics(allres[nm]);w.writerow([nm,d,st,m['sumR'],m['WR'],m['streak'],m['maxDD'],m['slATRmed'],m['sl_gt4ATR']])
# ===== TAREFA 6: split temporal =====
print("\n=== TEMPORAL SPLIT (sanity check, NOT clean OOS — rule used 41 visuals) ===")
with open(f"{D}/l2_bpt_sl_structural_temporal_split.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['model','window','n','WR','avgR','sumR','streak','maxDD'])
    for name in ['BASELINE','M2_SWING_ORIGIN','M5_CAPPED_STRUCT','M6_HYBRID','M4_POLARITY_CLOSE']:
        out=allres[name]
        for win,lo,hi in [('2020-2022',2020,2022),('2023-2026',2023,2026)]:
            sub=[o for o in out if lo<=o['yr']<=hi]
            if not sub: continue
            m=metrics(sub);w.writerow([name,win,m['n'],m['WR'],m['avgR'],m['sumR'],m['streak'],m['maxDD']])
            print(f"  {name:<18} {win} n={m['n']} WR={m['WR']}% avgR={m['avgR']:+} sumR={m['sumR']:+} streak={m['streak']} maxDD={m['maxDD']}")
        yrs={}
        for o in out: yrs.setdefault(o['yr'],[]).append(o)
        ann=" ".join(f"{y}:{round(sum(x['R'] for x in yrs[y]),0):+.0f}R/n{len(yrs[y])}" for y in sorted(yrs))
        print(f"      annual sumR: {ann}")
print("\nWROTE trade_review, models, temporal_split CSVs")
