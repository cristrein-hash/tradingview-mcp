#!/usr/bin/env python3
"""L2/BPT ENTRY SELECTION/TIMING. Regra dura: bater LONG-RANDOM-CASADO-POR-LEGPOS.
SL=demand-anchored (as-of-bar, causal), exit partial50@2R+6R. Classifica por TIPO DE SAÍDA.
H1 demand-backed, H2 reclaim-timing (causal), H3 no-trade/top filter. Bootstrap+Bonferroni x3. No plot."""
import json,csv,gzip,random,statistics,re
from bisect import bisect_right
random.seed(20260618)
D="results"
fr=[json.loads(l) for l in open("/tmp/raw_features_2020_2026.jsonl")]
H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr];TS=[r['ts_epoch'] for r in fr];RS=[r.get('rsi') for r in fr];N=len(fr)
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
PL5=[False]*N
for j in range(5,N-5):
    if L[j]<min(L[j-5:j]) and L[j]<min(L[j+1:j+6]): PL5[j]=True
def swing_origin(i):
    p=C[i];a=ATR[i];lo=None
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: lo=L[j];break
    if lo is None: lo=min(L[max(0,i-6):i+1])
    return max(p-(lo-0.1*a),0.3*a)
def legpos(i):
    p=C[i];hi=max(H[max(0,i-90):i+1]);lo=min(L[max(0,i-90):i+1]);return 100*(p-lo)/(hi-lo) if hi>lo else 50
# ---- demand cache as-of-bar (gz) : ts -> nearest demand low BELOW close ----
RAW="/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
GZ=[f"{RAW}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",f"{RAW}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
COB="OB Detector"
demlow_by_ts={}
for gz in GZ:
    with gzip.open(gz,'rt') as f:
        for line in f:
            try: d=json.loads(line)
            except: continue
            ov=d.get('ohlcv') or []
            if not ov: continue
            t=ov[-1]['time']
            cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
            if not cob: continue
            lows=[b.get('low') for b in (cob.get('all_boxes') or []) if (b.get('text') or '').upper()=='DEMAND' and b.get('low') is not None]
            demlow_by_ts[t]=lows
print("demand snapshots:",len(demlow_by_ts))
def demand_sl(i):  # SL ancorado na demanda 4H mais próxima abaixo; fallback swing
    p=C[i];a=ATR[i];lows=demlow_by_ts.get(TS[i])
    if lows:
        below=[lo for lo in lows if lo<p]
        if below:
            nd=max(below)  # demanda mais próxima abaixo
            if (p-nd)<=5*a: return max(p-(nd-0.1*a),0.3*a)
    return swing_origin(i)
def realR(i,risk):
    p=C[i];stop=p-risk;pd=False;rz=0.0;rem=1.0;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if L[j]<=stop:
            f=O[j] if O[j]<=stop else stop;return rz+rem*((f-p)/risk)-0.10
        if not pd and H[j]>=p+2*risk: rz+=1.0;rem=0.5;pd=True;stop=p
        if pd and H[j]>=p+6*risk: return rz+rem*6.0-0.10
    return rz+rem*((C[e]-p)/risk)-0.10
def exitype(i,risk):
    p=C[i];stop=p-risk;pd=False;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if not pd and L[j]<=stop: return 'STOP'
        if not pd and H[j]>=p+2*risk: pd=True
        if pd and H[j]>=p+6*risk: return 'WIN'
        if pd and L[j]<=p: return 'WIN'
    return 'WIN' if pd else 'SCRATCH'
def lpbucket(lp):
    return 0 if lp<30 else 1 if lp<55 else 2 if lp<75 else 3
# ---- universe p/ baseline legpos-random: barras com snapshot+demanda+ATR ----
universe=[i for i in range(95,N-61) if ATR[i] and demlow_by_ts.get(TS[i]) and any(lo<C[i] for lo in demlow_by_ts[TS[i]])]
uni_by_b={0:[],1:[],2:[],3:[]}
for i in universe: uni_by_b[lpbucket(legpos(i))].append(i)
print("universe (demand-backed bars):",len(universe),"| por bucket:",{b:len(v) for b,v in uni_by_b.items()})
# ---- episodes ----
base=[int(r['candidate_id'][1:]) for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2.csv"))]
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
idxs=sorted(base);eps=[];cur=[idxs[0]]
for a,b in zip(idxs,idxs[1:]):
    if b-a<=6: cur.append(b)
    else: eps.append(cur);cur=[b]
eps.append(cur)
reps=[(e[0],e) for e in eps if ATR[e[0]]]  # (rep_idx, full cluster idx list)
def dnum(r,k):
    try:return float(r[k])
    except:return None
def metrics(idxlist):
    Rs=[realR(i,demand_sl(i)) for i in idxlist]
    ex=[exitype(i,demand_sl(i)) for i in idxlist]
    from collections import Counter
    c=Counter(ex);n=len(Rs)
    return dict(n=n,avgR=round(sum(Rs)/n,3),sumR=round(sum(Rs),1),WIN=c['WIN'],STOP=c['STOP'],SCR=c['SCRATCH'])
def baseline_match(idxlist,B=2000):
    # avgR esperado de random long casado pela distribuição de legpos do subset
    from collections import Counter
    bc=Counter(lpbucket(legpos(i)) for i in idxlist);ntot=len(idxlist)
    means=[]
    for _ in range(B):
        samp=[]
        for b,cnt in bc.items():
            pool=uni_by_b[b]
            if not pool: continue
            samp+=[pool[random.randrange(len(pool))] for _ in range(cnt)]
        if samp: means.append(sum(realR(i,demand_sl(i)) for i in samp)/len(samp))
    means.sort();q=lambda p:means[int(p*len(means))]
    return q(.05),q(.5),q(.95),means
def test(name,idxlist):
    m=metrics(idxlist);b5,b50,b95,bdist=baseline_match(idxlist)
    delta=m['avgR']-b50
    p=sum(1 for x in bdist if m['avgR']>x)/len(bdist)  # P(subset avgR > random draw)
    print(f"  {name:<26} n={m['n']:<4} avgR={m['avgR']:+.3f} (WIN{m['WIN']}/STOP{m['STOP']}/SCR{m['SCR']}) | baseline legpos-random avgR[5/50/95]=[{b5:.3f}/{b50:.3f}/{b95:.3f}] | delta={delta:+.3f} P(>rand)={p:.2f}")
    return dict(name=name,n=m['n'],avgR=m['avgR'],sumR=m['sumR'],WIN=m['WIN'],STOP=m['STOP'],SCR=m['SCR'],base50=round(b50,3),delta=round(delta,3),p_gt_rand=round(p,2))
print("\n=== ENTRY SELECTION — cada hipótese vs LONG-RANDOM-CASADO-POR-LEGPOS (SL demand, exit partial50) ===")
res=[]
# ALL episodes (referência)
allidx=[r for r,_ in reps]
res.append(test("ALL_L2BPT(BOS)",allidx))
# H1 demand-backed: dist_4h_demand_low_atr<=2.5 & touched
def F(i): return legpos(i)>=85 and (RS[i] or 0)>=70
h1=[r for r,_ in reps if dsq.get(r) and (dnum(dsq[r],'dist_4h_demand_low_atr') or 9)<=2.5 and dsq[r].get('demand_4h_touched_on_retest')=='1']
res.append(test("H1_demand_backed(<=2.5)",h1))
# H2 reclaim-timing CAUSAL: dentro do cluster, escolher o 1º candidato (cronológico) que JÁ
# retestou a demanda (touched_on_retest=1, janela [i-WIN,i] = causal). Evita prematuro pré-retest.
# NÃO usar min-low do cluster (seria look-ahead: depende de candidatos futuros).
h2=[]
for r,cl in reps:
    touched=[j for j in sorted(cl) if dsq.get(j) and dsq[j].get('demand_4h_touched_on_retest')=='1']
    h2.append(touched[0] if touched else r)   # 1º reclaim retest-confirmado, senão o rep
res.append(test("H2_reclaim_timing_causal",h2))
# H3 no-trade/top filter: KEPT = remove F_STRICT
h3=[r for r,_ in reps if not F(r)]
res.append(test("H3_filter_kept(noF)",h3))
# Bonferroni nota
print("\n  Bonferroni x3: delta significativo exige P(>rand) >= 0.983 (one-sided 0.05/3).")
with open(f"{D}/l2_bpt_entry_sel_results.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(res[0].keys()));w.writeheader();w.writerows(res)
print("WROTE l2_bpt_entry_sel_results.csv")
