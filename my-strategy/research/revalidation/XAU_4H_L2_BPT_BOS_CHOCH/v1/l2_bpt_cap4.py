#!/usr/bin/env python3
"""L2/BPT CAP4 operacional sobre SL estrutural swing-origin (M2/M5). Exit FIXO partial50@2R+6R
gap-aware. CAP = filtro de viabilidade operacional, NÃO otimização de PnL. No SLIM/future/prod/1.5cap."""
import json,csv,statistics
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
def struct_risk(i):   # M2/M5 swing-origin (causal j<=i-5)
    p=C[i];atr=ATR[i]
    if not atr: return None,None
    lo=None
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: lo=L[j];break
    if lo is None: lo=min(L[max(0,i-6):i+1])
    sl=lo-BUF*atr;risk=p-sl
    if risk<FLOOR*atr: risk=FLOOR*atr
    return risk,risk/atr
def base_risk(i):     # baseline tight 6-bar
    p=C[i];atr=ATR[i]
    lo=min(L[max(0,i-5):i+1]);risk=p-(lo-BUF*atr)
    if risk<FLOOR*atr: risk=FLOOR*atr
    return risk
def sim(i,risk):      # partial50@2R+6R gap-aware
    p=C[i];stop=p-risk;pdone=False;realized=0.0;rem=1.0;end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        if L[j]<=stop:
            fill=O[j] if O[j]<=stop else stop
            return realized+rem*((fill-p)/risk)-COST,('be' if pdone else 'stop')
        if not pdone and H[j]>=p+2*risk: realized+=0.5*2.0;rem=0.5;pdone=True;stop=p
        if pdone and H[j]>=p+6*risk: return realized+rem*6.0-COST,'runner'
    return realized+rem*((C[end]-p)/risk)-COST,'time'
def yr(i): return datetime.fromtimestamp(TS[i],timezone.utc).year
# episodes (same as sl_structural)
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
# build per-episode structural record
EP=[]
for rep,el in reps:
    risk,ratl=struct_risk(rep)
    if risk is None: continue
    r,how=sim(rep,risk)
    EP.append({'i':rep,'el':el,'risk':risk,'ratl':ratl,'R':r,'how':how,'yr':yr(rep)})
def metr(rows):
    rs=[x['R'] for x in rows];n=len(rs)
    if n==0: return {'n':0}
    w=[x for x in rs if x>0];lo=[x for x in rs if x<0]
    eq=pk=mdd=c=ms=0
    for x in rs: eq+=x;pk=max(pk,eq);mdd=max(mdd,pk-eq);c=c+1 if x<0 else 0;ms=max(ms,c)
    rat=sorted(x['ratl'] for x in rows);q=lambda a,p:a[min(len(a)-1,int(p*len(a)))]
    return {'n':n,'WR':round(100*len(w)/n,1),'avgR':round(sum(rs)/n,3),'sumR':round(sum(rs),1),
            'medR':round(statistics.median(rs),2),'PF':round(sum(w)/abs(sum(lo)),2) if lo else 'inf','maxDD':round(mdd,1),'streak':ms,
            'stop':sum(1 for x in rows if x['how']=='stop'),'be':sum(1 for x in rows if x['how']=='be'),
            'runner':sum(1 for x in rows if x['how']=='runner'),'time':sum(1 for x in rows if x['how']=='time'),
            'slATRmed':round(statistics.median(rat),2),'slATRp90':round(q(rat,.9),2),'slATRmax':round(max(rat),2),
            'gt4':sum(1 for x in rows if x['ratl']>4)}
# ---- POLICIES ----
def reject(thr): return [x for x in EP if x['ratl']<=thr]
def clamp4():
    out=[]
    for x in EP:
        if x['ratl']>4:
            risk=4*ATR[x['i']];r,how=sim(x['i'],risk);out.append({**x,'risk':risk,'ratl':4.0,'R':r,'how':how})
        else: out.append(x)
    return out
POL={'STRUCT_PURE (no cap)':EP,'CAP3_REJECT':reject(3),'CAP4_REJECT':reject(4),'CAP5_REJECT':reject(5),'CAP4_CLAMP_DIAG':clamp4()}
print("=== CAP POLICIES (SL estrutural swing-origin; exit partial50; base 276) ===")
res={}
for nm,rows in POL.items():
    m=metr(rows);res[nm]=(rows,m);rej=276-m['n'] if 'REJECT' in nm else 0;cl=m['gt4'] if 'CLAMP' in nm else 0
    print(f"{nm:<22} n={m['n']} rej={rej} clamp={cl} | WR={m['WR']}% avgR={m['avgR']:+} sumR={m['sumR']:+} medR={m['medR']:+} PF={m['PF']} maxDD={m['maxDD']} streak={m['streak']} | run={m['runner']} stop={m['stop']} | slATR med={m['slATRmed']} p90={m['slATRp90']} max={m['slATRmax']} >4ATR={m['gt4']}")
# CAP4_REVIEW buckets
le4=[x for x in EP if x['ratl']<=4];gt4=[x for x in EP if x['ratl']>4]
print("\n=== CAP4_REVIEW (mede os 2 buckets separados) ===")
for nm,rows in [('SL_LE_4ATR',le4),('SL_GT_4ATR_REVIEW',gt4)]:
    m=metr(rows);print(f"  {nm:<18} n={m['n']} ({100*m['n']/276:.0f}%) WR={m['WR']}% avgR={m['avgR']:+} sumR={m['sumR']:+} medR={m['medR']:+} PF={m['PF']} maxDD={m['maxDD']} streak={m['streak']} BOM={sum(1 for x in rows if x['el']=='BOM')}")
# yearly + split for key policies
print("\n=== SPLIT TEMPORAL + yearly (STRUCT_PURE, CAP4_REJECT, CAP4_CLAMP) ===")
for nm in ['STRUCT_PURE (no cap)','CAP4_REJECT','CAP4_CLAMP_DIAG']:
    rows=res[nm][0]
    for w,a,b in [('2020-2022',2020,2022),('2023-2026',2023,2026)]:
        m=metr([x for x in rows if a<=x['yr']<=b]);print(f"  {nm:<22} {w} n={m['n']} avgR={m['avgR']:+} sumR={m['sumR']:+} streak={m['streak']} maxDD={m['maxDD']}")
    ys={}
    for x in rows: ys.setdefault(x['yr'],[]).append(x)
    print(f"      yearly: "+" ".join(f"{y}:{round(sum(z['R'] for z in ys[y]),0):+.0f}/n{len(ys[y])}" for y in sorted(ys)))
# write policy results csv
with open(f"{D}/l2_bpt_sl_cap4_policy_results.csv","w",newline="") as f:
    w=csv.writer(f);hdr=['policy','n','rejected','clamped']+[k for k in metr(EP) if k!='n']
    w.writerow(hdr)
    for nm,rows in POL.items():
        m=metr(rows);rej=276-m['n'] if 'REJECT' in nm else 0;cl=m['gt4'] if 'CLAMP' in nm else 0
        w.writerow([nm,m['n'],rej,cl]+[m[k] for k in metr(EP) if k!='n'])
    for nm,rows in [('CAP4_REVIEW:LE4',le4),('CAP4_REVIEW:GT4',gt4)]:
        m=metr(rows);w.writerow([nm,m['n'],0,0]+[m[k] for k in metr(EP) if k!='n'])
print("\nWROTE l2_bpt_sl_cap4_policy_results.csv")

# ===== TAREFA 3: recall-gate (8 must_preserve + E13 + E23) =====
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
swing={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
review={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_full_res_visual_episode_review.csv"))}
MUST=['E1','E5','E13','E17','E21','E27','E30','E40']
print("\n=== RECALL-GATE: must_preserve (8) + E23 sob CAP4 ===")
rg=[]
for eid in MUST+['E23']:
    if eid not in swing: continue
    i=ts2idx[parse(swing[eid]['timestamp'])]
    risk,ratl=struct_risk(i)
    r,how=sim(i,risk)
    cap4='REJECTED' if ratl>4 else 'kept'
    rg.append({'eid':eid,'idx':i,'ratl':round(ratl,2),'R':round(r,2),'how':how,'cap4':cap4,
               'must':eid in MUST,'status':review.get(eid,{}).get('issue_type','')})
    print(f"  {eid:<4} SL={ratl:.2f}ATR R={r:+.2f} ({how}) CAP4={cap4} {'[MUST_PRESERVE]' if eid in MUST else '[should_not_long]'}")
cut=[x['eid'] for x in rg if x['must'] and x['cap4']=='REJECTED']
muted=[x['eid'] for x in rg if x['must'] and 0<x['R']<1.0]
print(f"  >> CAP4_REJECT corta {len(cut)}/8 must_preserve: {cut}")
print(f"  >> mutados (0<R<1): {muted}  | E23 (should_not_long): {'CORTADO (positivo)' if [x for x in rg if x['eid']=='E23'][0]['cap4']=='REJECTED' else 'mantido'}")
with open(f"{D}/l2_bpt_sl_cap4_recall_gate.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['eid','idx','ratl','R','how','cap4','must','status']);w.writeheader();w.writerows(rg)

# ===== TAREFA 4: trade review dos >4ATR =====
# map idx->visual eid
idx2eid={ts2idx[parse(s['timestamp'])]:eid for eid,s in swing.items() if parse(s['timestamp']) in ts2idx}
def reason(x,eid):
    st=review.get(eid,{}).get('issue_type','') if eid else ''
    if 'top' in st or 'macro_bear' in st or 'exhaust' in st: return 'top/exhaustion'
    if x['el']=='BOM': return 'big V-reversal / estrutura larga válida (monumental)'
    if eid and 'bad_entry' in st: return 'precisa entrada melhor / defended swing distante'
    if eid and 'premature' in st: return 'entrada tarde/precipitada'
    return 'unknown — needs visual/better entry'
gt4rows=[]
for x in gt4:
    eid=idx2eid.get(x['i'])
    br=base_risk(x['i']);bR,bhow=sim(x['i'],br)
    crisk=4*ATR[x['i']];cR,chow=sim(x['i'],crisk)
    gt4rows.append({'episode_id':eid or f"idx{x['i']}",'entry_ts':datetime.fromtimestamp(TS[x['i']],timezone.utc).strftime('%Y-%m-%d %H:%M'),
        'SL_ATR':round(x['ratl'],2),'model':'M5_SWING_ORIGIN','visual_label':review.get(eid,{}).get('corrected_visual_label','') if eid else '',
        'BOM_NAO_UNK':x['el'],'baseline_R':round(bR,2),'structural_R':round(x['R'],2),'cap4_reject':'REJECTED',
        'cap4_clamp_R':round(cR,2),'reason':reason(x,eid)})
gt4rows.sort(key=lambda r:-r['SL_ATR'])
with open(f"{D}/l2_bpt_sl_gt4atr_review.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(gt4rows[0].keys()));w.writeheader();w.writerows(gt4rows)
from collections import Counter
print(f"\n=== >4ATR REVIEW (n={len(gt4)}): por label e razão ===")
print("  BOM/NAO/UNK:",dict(Counter(x['el'] for x in gt4)))
print("  razões:",dict(Counter(r['reason'] for r in gt4rows)))
print("  structural sumR do bucket:",round(sum(x['R'] for x in gt4),1),"| clamp sumR:",round(sum(r['cap4_clamp_R'] for r in gt4rows),1),"| baseline sumR:",round(sum(r['baseline_R'] for r in gt4rows),1))
print("  top-10 maiores SL:")
for r in gt4rows[:10]:
    print(f"    {r['episode_id']:<8} {r['entry_ts']} SL={r['SL_ATR']}ATR {r['BOM_NAO_UNK']:<8} structR={r['structural_R']:+} clampR={r['cap4_clamp_R']:+} | {r['reason']}")
# cap4 trade review (all 276 with bucket)
with open(f"{D}/l2_bpt_sl_cap4_trade_review.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['idx','entry_ts','year','label','SL_ATR','bucket','structural_R','how','cap4_reject_kept','cap4_clamp_R'])
    for x in EP:
        crisk=4*ATR[x['i']] if x['ratl']>4 else x['risk'];cR,_=sim(x['i'],crisk)
        w.writerow([x['i'],datetime.fromtimestamp(TS[x['i']],timezone.utc).strftime('%Y-%m-%d %H:%M'),x['yr'],x['el'],
            round(x['ratl'],2),'GT4' if x['ratl']>4 else 'LE4',round(x['R'],2),x['how'],'kept' if x['ratl']<=4 else 'REJECTED',round(cR,2)])
print("\nWROTE recall_gate, gt4atr_review, cap4_trade_review CSVs")
