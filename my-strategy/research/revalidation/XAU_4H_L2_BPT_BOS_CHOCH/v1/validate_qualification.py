#!/usr/bin/env python3
"""VALIDAÇÃO do Trade Qualification Engine. Junta decisões (cegas ao resultado) aos outcomes
(demand-SL + partial50, por TIPO DE SAÍDA). Mede TAKE vs REVIEW vs SKIP + 3 baselines + bootstrap +
recall gate + subset NON-GT (held-out dos priors) + correlação confidence->R. Episódio é a unidade."""
import json,csv,gzip,random,glob
import os
from collections import Counter,defaultdict
random.seed(20260618)
D="results"
fr=[json.loads(l) for l in open(os.environ.get("L2_RAW_FEATURES","/tmp/raw_features_2020_2026.jsonl"))]
H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr]
TS=[r['ts_epoch'] for r in fr];N=len(fr)
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
RAW="/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD";COB="OB Detector"
GZ=[f"{RAW}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",f"{RAW}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
demlow={}
for gz in GZ:
    with gzip.open(gz,'rt') as f:
        for line in f:
            try:d=json.loads(line)
            except:continue
            ov=d.get('ohlcv') or []
            if not ov: continue
            cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
            if cob: demlow[ov[-1]['time']]=[b['low'] for b in (cob.get('all_boxes') or []) if (b.get('text') or '').upper()=='DEMAND' and b.get('low') is not None]
def demand_sl(i):
    p=C[i];a=ATR[i];lows=demlow.get(TS[i])
    if lows:
        below=[lo for lo in lows if lo<p]
        if below:
            nd=max(below)
            if (p-nd)<=5*a: return max(p-(nd-0.1*a),0.3*a)
    return swing_origin(i)
def realR(i,risk=None):
    risk=risk or demand_sl(i)
    p=C[i];stop=p-risk;pd=False;rz=0.0;rem=1.0;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if L[j]<=stop:
            f=O[j] if O[j]<=stop else stop;return rz+rem*((f-p)/risk)-0.10
        if not pd and H[j]>=p+2*risk: rz+=1.0;rem=0.5;pd=True;stop=p
        if pd and H[j]>=p+6*risk: return rz+rem*6.0-0.10
    return rz+rem*((C[e]-p)/risk)-0.10
def lpb(lp): return 0 if lp<30 else 1 if lp<55 else 2 if lp<75 else 3
# universe p/ baselines
universe=[i for i in range(95,N-61) if ATR[i] and demlow.get(TS[i]) and any(lo<C[i] for lo in demlow[TS[i]])]
uni_by_b=defaultdict(list)
for i in universe: uni_by_b[lpb(legpos(i))].append(i)
def drop20(i): return (max(C[max(0,i-20):i+1])-C[i])/ATR[i] if ATR[i] else 0
def db(i): return 0 if drop20(i)<2 else 1 if drop20(i)<4 else 2  # bucket capitulação
uni_by_sb=defaultdict(list)  # state bucket = (legpos_b, drop_b)
for i in universe: uni_by_sb[(lpb(legpos(i)),db(i))].append(i)

# ---- load decisions + outcomes ----
dec={}
for fp in glob.glob(os.environ.get('L2_QUAL_DEC_GLOB','/tmp/qual_dec_*.jsonl')):
    for l in open(fp):
        if l.strip():
            r=json.loads(l);dec[r['bar_idx']]=r
out={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
missing=[i for i in out if i not in dec]
print(f"decisões={len(dec)} outcomes={len(out)} | FALTANTE(s): {missing}")
for i in missing: dec[i]={'bar_idx':i,'decision':'SKIP','direction':'NONE','confidence':0,'episode_id':out[i]['episode_id'],'_imputed':True}

def stats(idxs):
    Rs=[float(out[i]['realR']) for i in idxs];ex=Counter(out[i]['exitype'] for i in idxs)
    n=len(Rs);wins=ex['WIN_RUNNER']+ex['WIN_HELD']+ex['WIN_BE']
    # DD e streak por ordem cronológica
    eq=0;peak=0;dd=0;cur=0;mx=0
    for i in sorted(idxs):
        r=float(out[i]['realR']);eq+=r;peak=max(peak,eq);dd=max(dd,peak-eq)
        if r<0: cur+=1;mx=max(mx,cur)
        else: cur=0
    return dict(n=n,WR=round(100*wins/n,1) if n else 0,avgR=round(sum(Rs)/n,3) if n else 0,sumR=round(sum(Rs),1),
                maxDD=round(dd,1),maxLossStreak=mx,
                exit=dict(ex))
def boot_mean(idxs,B=5000):
    Rs=[float(out[i]['realR']) for i in idxs];n=len(Rs);ms=[]
    for _ in range(B): ms.append(sum(Rs[random.randrange(n)] for _ in range(n))/n)
    ms.sort();return ms
def base_legpos(idxs,B=5000):
    bc=Counter(lpb(legpos(i)) for i in idxs);ms=[]
    for _ in range(B):
        s=[]
        for b,cnt in bc.items():
            pool=uni_by_b[b]
            if pool: s+=[pool[random.randrange(len(pool))] for _ in range(cnt)]
        if s: ms.append(sum(realR(i) for i in s)/len(s))
    ms.sort();return ms
def base_state(idxs,B=3000):
    bc=Counter((lpb(legpos(i)),db(i)) for i in idxs);ms=[]
    for _ in range(B):
        s=[]
        for b,cnt in bc.items():
            pool=uni_by_sb.get(b) or uni_by_b[b[0]]
            if pool: s+=[pool[random.randrange(len(pool))] for _ in range(cnt)]
        if s: ms.append(sum(realR(i) for i in s)/len(s))
    ms.sort();return ms

allids=list(out.keys())
buckets={k:[i for i in out if dec[i]['decision']==k] for k in ['TAKE','REVIEW','SKIP']}
take_long=[i for i in buckets['TAKE'] if dec[i]['direction']=='LONG']
print("\n===== POR DECISÃO (demand-SL + partial50, unidade=episódio) =====")
for k in ['TAKE','REVIEW','SKIP']:
    print(f"  {k:<7}",stats(buckets[k]))
print(f"  ALL_276",stats(allids))

print("\n===== TESTES DE HIPÓTESE (bootstrap 5000) =====")
takeR=[float(out[i]['realR']) for i in buckets['TAKE']]
skipR=[float(out[i]['realR']) for i in buckets['SKIP']]
allR=[float(out[i]['realR']) for i in allids]
mtake=sum(takeR)/len(takeR);mskip=sum(skipR)/len(skipR);mall=sum(allR)/len(allR)
# TAKE vs SKIP (two-sample bootstrap)
diffs=[]
for _ in range(5000):
    a=sum(takeR[random.randrange(len(takeR))] for _ in range(len(takeR)))/len(takeR)
    b=sum(skipR[random.randrange(len(skipR))] for _ in range(len(skipR)))/len(skipR)
    diffs.append(a-b)
diffs.sort();p_ts=sum(1 for d in diffs if d>0)/len(diffs)
print(f"  TAKE avgR={mtake:+.3f} vs SKIP avgR={mskip:+.3f} | delta={mtake-mskip:+.3f} P(TAKE>SKIP)={p_ts:.3f} CI95=[{diffs[125]:+.2f},{diffs[4875]:+.2f}]")
# TAKE vs ALL base rate
bm=boot_mean(buckets['TAKE']);p_all=sum(1 for x in bm if x>mall)/len(bm)
print(f"  TAKE vs ALL_276 base rate {mall:+.3f}: P(TAKE>base)={p_all:.3f} TAKE_CI95=[{bm[125]:+.2f},{bm[4875]:+.2f}]")
# TAKE vs legpos-random
bl=base_legpos(buckets['TAKE']);p_lp=sum(1 for x in bl if mtake>x)/len(bl)
print(f"  TAKE vs legpos-random: rand avgR[5/50/95]=[{bl[250]:.3f}/{bl[2500]:.3f}/{bl[4750]:.3f}] delta={mtake-bl[2500]:+.3f} P={p_lp:.3f}")
# TAKE vs state-matched
bs=base_state(buckets['TAKE']);p_st=sum(1 for x in bs if mtake>x)/len(bs)
print(f"  TAKE vs state-matched (legpos+capit): rand avgR[5/50/95]=[{bs[150]:.3f}/{bs[1500]:.3f}/{bs[2850]:.3f}] delta={mtake-bs[1500]:+.3f} P={p_st:.3f}")

print("\n===== RECALL GATE (winners devem cair em TAKE/REVIEW, não SKIP) =====")
for i in allids:
    if out[i]['is_winner_gt']=='1': print(f"  WINNER {out[i]['episode_id']:<4} -> {dec[i]['decision']:<7} {dec[i]['direction']} R={out[i]['realR']}")
for i in allids:
    if out[i]['is_loser_gt']=='1': print(f"  LOSER  {out[i]['episode_id']:<4} -> {dec[i]['decision']:<7} {dec[i]['direction']} R={out[i]['realR']}")

print("\n===== SUBSET NON-GT (exclui os 10 curados — held-out dos priors) =====")
nongt=[i for i in allids if out[i]['is_winner_gt']=='0' and out[i]['is_loser_gt']=='0']
for k in ['TAKE','REVIEW','SKIP']:
    ids=[i for i in nongt if dec[i]['decision']==k];print(f"  {k:<7}",stats(ids))

print("\n===== CONFIDENCE -> R (TAKE+REVIEW longs) =====")
conf=[(int(dec[i].get('confidence') or 0),float(out[i]['realR'])) for i in allids if dec[i]['decision'] in('TAKE','REVIEW')]
for lo,hi in [(0,40),(40,55),(55,70),(70,101)]:
    g=[r for c,r in conf if lo<=c<hi]
    if g: print(f"  conf[{lo}-{hi}): n={len(g)} avgR={sum(g)/len(g):+.3f} WR_pos={100*sum(1 for r in g if r>0)/len(g):.0f}%")

# write outcomes-merged matrix
with open(f"{D}/l2_bpt_trade_qualification_outcomes.csv") as f: pass
import csv as _c
rows=[]
for i in sorted(allids):
    d=dec[i];rows.append({'bar_idx':i,'episode_id':d.get('episode_id',''),'decision':d['decision'],'direction':d['direction'],
        'confidence':d.get('confidence'),'setup_type':d.get('expected_setup_type',''),'realR':out[i]['realR'],'exitype':out[i]['exitype'],
        'decisive_reason':d.get('decisive_reason','')})
with open(f"{D}/l2_bpt_trade_qualification_decisions_merged.csv","w",newline="") as f:
    w=_c.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
print("\nWROTE results/l2_bpt_trade_qualification_decisions_merged.csv")
