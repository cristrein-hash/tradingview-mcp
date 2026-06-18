#!/usr/bin/env python3
"""F_TOP_OB_RSI_strict = legpos90>=85 AND RSI>=70 (CONGELADO). Janela extra 2021-2022 +
lista completa dos trades filtrados. SL STRUCT_PURE, exit partial50. No tuning, no SLIM."""
import json, csv, statistics
from datetime import datetime, timezone
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
            return realized+rem*((fill-p)/risk)-COST,('be' if pdone else 'stop')
        if not pdone and H[j]>=p+2*risk: realized+=0.5*2.0;rem=0.5;pdone=True;stop=p
        if pdone and H[j]>=p+6*risk: return realized+rem*6.0-COST,'runner'
    return realized+rem*((C[end]-p)/risk)-COST,'time'
def legpos90(i):
    p=C[i];hi=max(H[max(0,i-90):i+1]);lo=min(L[max(0,i-90):i+1]);return 100*(p-lo)/(hi-lo) if hi>lo else 50
def dist_hi90(i): return (max(H[max(0,i-90):i+1])-C[i])/ATR[i]
def ext_lo20(i): return (C[i]-min(L[max(0,i-20):i+1]))/ATR[i]
# FROZEN FILTER
def FSTRICT(i): return legpos90(i)>=85 and (RS[i] or 0)>=70
# episodes
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
def dts(i): return datetime.fromtimestamp(TS[i],timezone.utc).strftime('%Y-%m-%d %H:%M')
EP=[]
for rep,el in reps:
    if not ATR[rep]: continue
    r,how=sim(rep,struct_risk(rep))
    EP.append({'i':rep,'el':el,'R':r,'how':how,'yr':yr(rep),'lp':legpos90(rep),'rsi':RS[rep]})
# must-preserve / should-cut maps via swing timestamps
swing={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
rev={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_full_res_visual_episode_review.csv"))}
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
MUST=['E1','E5','E13','E17','E21','E27','E30','E40'];CUT=['E23','E15','E24','E34','E39']
idx2eid={}
for eid,s in swing.items():
    k=parse(s['timestamp'])
    if k in ts2idx: idx2eid[ts2idx[k]]=eid
def metr(rows):
    rs=[x['R'] for x in rows];n=len(rs)
    if not n: return dict(n=0,WR=0,avgR=0,sumR=0,DD=0,streak=0)
    w=sum(1 for x in rs if x>0);eq=pk=mdd=c=ms=0
    for x in rs: eq+=x;pk=max(pk,eq);mdd=max(mdd,pk-eq);c=c+1 if x<0 else 0;ms=max(ms,c)
    return dict(n=n,WR=round(100*w/n,1),avgR=round(sum(rs)/n,3),sumR=round(sum(rs),1),DD=round(mdd,1),streak=ms)
# ---- PART 1: extra window 2021-2022 + all annual ----
print("=== PART 1: janela extra 2021-2022 (NÃO usada p/ tuning; calib=2020, OOS=2023-26) ===")
out_w=[]
for win,lo,hi in [('2021-2022',2021,2022),('2020',2020,2020),('2021',2021,2021),('2022',2022,2022),('2023',2023,2023),('2024',2024,2024),('2025',2025,2025),('2026',2026,2026)]:
    sub=[x for x in EP if lo<=x['yr']<=hi]
    if not sub: continue
    blk=[x for x in sub if FSTRICT(x['i'])];kept=[x for x in sub if not FSTRICT(x['i'])]
    mb=metr(sub);mk=metr(kept);bom=sum(1 for x in blk if x['el']=='BOM')
    must=sum(1 for x in blk if idx2eid.get(x['i']) in MUST)
    fr_rs=[x['R'] for x in blk]
    row=dict(window=win,n_total=mb['n'],n_filtered=len(blk),filt_netR=round(sum(fr_rs),1) if fr_rs else 0,
        filt_avgR=round(statistics.mean(fr_rs),3) if fr_rs else 0,filt_WR=round(100*sum(1 for x in fr_rs if x>0)/len(fr_rs),1) if fr_rs else 0,
        kept_avgR_before=mb['avgR'],kept_avgR_after=mk['avgR'],kept_sumR_before=mb['sumR'],kept_sumR_after=mk['sumR'],
        DD_before=mb['DD'],DD_after=mk['DD'],streak_before=mb['streak'],streak_after=mk['streak'],
        BOM_cut=bom,must_cut=must,UNK_cut=sum(1 for x in blk if x['el']=='UNKNOWN'),NAO_cut=sum(1 for x in blk if x['el']=='NAO'))
    out_w.append(row)
    tag='<<< JANELA EXTRA' if win=='2021-2022' else ''
    print(f"  {win:<10} n={row['n_total']:<4} filt={row['n_filtered']:<3} filt_netR={row['filt_netR']:+6} filt_avgR={row['filt_avgR']:+.3f} | kept avgR {row['kept_avgR_before']}->{row['kept_avgR_after']} sumR {row['kept_sumR_before']}->{row['kept_sumR_after']} DD {row['DD_before']}->{row['DD_after']} | BOMcut={row['BOM_cut']} mustcut={row['must_cut']} {tag}")
with open(f"{D}/l2_bpt_f_top_ob_rsi_strict_extra_window.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(out_w[0].keys()));w.writeheader();w.writerows(out_w)
# ---- PART 2: full filtered-trade list ----
def top_likelihood(x):
    i=x['i'];lp=x['lp'];rs=x['rsi'] or 0;dh=dist_hi90(i);ext=ext_lo20(i)
    if lp>=90 and rs>=72 and dh<1.5: return 'HIGH'
    if lp>=88 and rs>=70 and ext>=4: return 'MEDIUM'
    if lp>=85 and rs>=70: return 'LOW'
    return 'UNKNOWN'
filt=[x for x in EP if FSTRICT(x['i'])]
rows2=[]
for x in sorted(filt,key=lambda z:z['i']):
    eid=idx2eid.get(x['i'],'')
    rows2.append(dict(episode_id=eid or f"idx{x['i']}",entry_ts=dts(x['i']),entry_price=round(C[x['i']],1),
        legpos90=round(x['lp']),RSI=round(x['rsi'],1) if x['rsi'] else '',outcomeR=round(x['R'],2),outcome_bucket=x['how'],
        year=x['yr'],label=x['el'],visual_label=rev.get(eid,{}).get('corrected_visual_label','') if eid else '',
        must_preserve='yes' if eid in MUST else 'no',should_cut='yes' if eid in CUT else 'no',
        top_exhaustion_likelihood=top_likelihood(x),notes=''))
with open(f"{D}/l2_bpt_f_top_ob_rsi_strict_filtered_trades_full.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows2[0].keys()));w.writeheader();w.writerows(rows2)
from collections import Counter
print(f"\n=== PART 2: {len(filt)} trades filtrados (lista completa) ===")
print("  por ano:",dict(Counter(x['yr'] for x in filt)))
print("  top_likelihood:",dict(Counter(top_likelihood(x) for x in filt)))
print("  BOM filtrados:",sum(1 for x in filt if x['el']=='BOM'),"| must-preserve filtrados:",sum(1 for x in filt if idx2eid.get(x['i']) in MUST))
print("  trades filtrados que mapeiam a E#:",[idx2eid[x['i']] for x in filt if x['i'] in idx2eid])
print("WROTE extra_window.csv + filtered_trades_full.csv")
