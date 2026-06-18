#!/usr/bin/env python3
"""L2/BPT entry/exhaustion filters. Causal (<=entrada). SL FIXO STRUCT_PURE swing-origin,
exit FIXO partial50@2R+6R gap-aware. No SLIM/tick-vol-authority/outcome-proxy/future/prod."""
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
# ---- causal entry features ----
def legpos90(i):
    p=C[i];hi=max(H[max(0,i-90):i+1]);lo=min(L[max(0,i-90):i+1]);return 100*(p-lo)/(hi-lo) if hi>lo else 50
def body_frac(i):  # corpo do candle de entrada / range
    rng=H[i]-L[i];return abs(C[i]-O[i])/rng if rng>0 else 0
def dist_hi90(i): return (max(H[max(0,i-90):i+1])-C[i])/ATR[i]
def ext_lo20(i): return (C[i]-min(L[max(0,i-20):i+1]))/ATR[i]
# ---- FILTERS: return True if BLOCK/FLAG ----
def F_TOP_OB_RSI(i):   # blow-off top: legpos alto + overbought
    return legpos90(i)>=85 and (RS[i] or 0)>=68
def F_TOP_OB_RSI_strict(i):
    return legpos90(i)>=85 and (RS[i] or 0)>=70
def F_WEAK_RECLAIM_NEAR_HIGH(i):  # review: reclaim fraco perto do high
    return dist_hi90(i)<2.0 and body_frac(i)<0.15
def F_LATE_LEG_EXT(i):  # legpos alto + muito extendido do low (alternativa ao RSI)
    return legpos90(i)>=85 and ext_lo20(i)>=4.5
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
# baseline outcomes
EP=[]
for rep,el in reps:
    if not ATR[rep]: continue
    r,how=sim(rep,struct_risk(rep))
    EP.append({'i':rep,'el':el,'R':r,'yr':yr(rep)})
def metr(rows):
    rs=[x['R'] for x in rows];n=len(rs)
    if n==0: return {'n':0,'WR':0,'avgR':0,'sumR':0,'PF':0,'maxDD':0,'streak':0}
    w=[x for x in rs if x>0];lo=[x for x in rs if x<0]
    eq=pk=mdd=c=ms=0
    for x in rs: eq+=x;pk=max(pk,eq);mdd=max(mdd,pk-eq);c=c+1 if x<0 else 0;ms=max(ms,c)
    return {'n':n,'WR':round(100*len(w)/n,1),'avgR':round(sum(rs)/n,3),'sumR':round(sum(rs),1),
            'PF':round(sum(w)/abs(sum(lo)),2) if lo else 'inf','maxDD':round(mdd,1),'streak':ms}
base_m=metr(EP)
print("=== BASELINE (STRUCT_PURE + partial50, sem filtro) ===")
print(f"  {base_m}")
FILT={'F_TOP_OB_RSI':F_TOP_OB_RSI,'F_TOP_OB_RSI_strict':F_TOP_OB_RSI_strict,'F_LATE_LEG_EXT':F_LATE_LEG_EXT,'F_WEAK_RECLAIM_NEAR_HIGH':F_WEAK_RECLAIM_NEAR_HIGH}
print("\n=== FILTROS na base completa (block = remove o trade) ===")
pol=[]
for nm,fn in FILT.items():
    blocked=[x for x in EP if fn(x['i'])];kept=[x for x in EP if not fn(x['i'])]
    bm=metr(kept);bd_bom=sum(1 for x in blocked if x['el']=='BOM');bd_sumR=round(sum(x['R'] for x in blocked),1)
    print(f"  {nm:<24} block={len(blocked)} (BOM={bd_bom} sumR_blocked={bd_sumR:+}) -> KEPT n={bm['n']} WR={bm['WR']}% sumR={bm['sumR']:+} PF={bm['PF']} maxDD={bm['maxDD']} streak={bm['streak']}")
    pol.append({'filter':nm,'blocked':len(blocked),'BOM_blocked':bd_bom,'sumR_blocked':bd_sumR,**{f'kept_{k}':v for k,v in bm.items()}})
with open(f"{D}/l2_bpt_entry_exhaustion_policy_results.csv","w",newline="") as f:
    f.write("baseline,"+",".join(f"{k}={v}" for k,v in base_m.items())+"\n")
    w=csv.DictWriter(f,fieldnames=list(pol[0].keys()));w.writeheader();w.writerows(pol)
# recall-gate on case episodes
swing={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
CUT=['E23','E15','E24','E34','E39'];KEEP=['E1','E5','E13','E17','E21','E27','E30','E40']
print("\n=== RECALL-GATE nos casos (block? por filtro principal) ===")
rg=[]
for eid in CUT+KEEP:
    if eid not in swing: continue
    i=ts2idx[parse(swing[eid]['timestamp'])]
    row={'eid':eid,'set':'CUT' if eid in CUT else 'KEEP','legpos':round(legpos90(i)),'rsi':RS[i],
         'F_TOP_OB_RSI':'BLOCK' if F_TOP_OB_RSI(i) else '-','F_WEAK_RECLAIM':'FLAG' if F_WEAK_RECLAIM_NEAR_HIGH(i) else '-'}
    rg.append(row)
    print(f"  {eid:<5}{row['set']:<6} legpos={row['legpos']:<4} rsi={str(row['rsi']):<6} TOP_OB_RSI={row['F_TOP_OB_RSI']:<6} WEAK_RECLAIM={row['F_WEAK_RECLAIM']}")
with open(f"{D}/l2_bpt_entry_exhaustion_recall_gate.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rg[0].keys()));w.writeheader();w.writerows(rg)
# filter candidates registry
cand=[
 ['F_TOP_OB_RSI','legpos90>=85 & RSI>=68','blow-off top','AUTO_BLOCK_CANDIDATE','causal; pega E23/E24, poupa must-preserve'],
 ['F_TOP_OB_RSI_strict','legpos90>=85 & RSI>=70','blow-off top','TAG_ONLY','mais restrito; só E23'],
 ['F_LATE_LEG_EXT','legpos90>=85 & ext_lo20>=4.5','late/extended','REVIEW_ONLY','alternativa ao RSI; risco cortar V-reversal'],
 ['F_WEAK_RECLAIM_NEAR_HIGH','dist_hi90<2 & body<0.15','reclaim fraco','REVIEW_ONLY','n=1 (E15); overfit risk'],
 ['F_BEAR_BOUNCE','bearleg context','bear-leg bounce','REVIEW_ONLY','E39 indistinguível de E17 — NUNCA auto-block'],
 ['F_SUPPLY_REJECTION','supply prox + rejeição pós-entrada','supply reject','REJECTED_AS_ENTRY','usa candle pós-entrada = não causal p/ entry'],
]
with open(f"{D}/l2_bpt_entry_exhaustion_filter_candidates.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['filter','definition','hypothesis','classification','note']);w.writerows(cand)
print("\nWROTE case_study, filter_candidates, policy_results, recall_gate CSVs")
