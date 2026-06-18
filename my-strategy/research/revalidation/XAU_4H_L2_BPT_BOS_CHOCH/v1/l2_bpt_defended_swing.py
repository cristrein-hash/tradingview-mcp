#!/usr/bin/env python3
"""L2/BPT defended-swing selection. Escolhe o low ESTRUTURAL que a entrada defende,
causal (só dados<=entrada). Exit FIXO partial50@2R+6R gap-aware. No SLIM/future/prod."""
import json,csv,statistics
from datetime import datetime,timezone
D="results"
fr=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(fr);H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr];TS=[r['ts_epoch'] for r in fr]
RSIv=[r.get('rsi') for r in fr]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
def piv(k):
    pf=[False]*N
    for j in range(k,N-k):
        if L[j]<min(L[j-k:j]) and L[j]<min(L[j+1:j+k+1]): pf[j]=True
    return pf
PL5=piv(5);PL3=piv(3)
FLOOR=0.3;BUF=0.1;COST=0.10;MAXHOLD=60
# ---- candidate causal lows (all use only bars <= i, pivots confirmed) ----
def recent_pivot(i,p):
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: return L[j],i-j
    return None,None
def nearest_pl3(i,p):
    for j in range(i-3,4,-1):
        if PL3[j] and L[j]<p: return L[j],i-j
    return None,None
def retest(i,p): return min(L[max(0,i-2):i+1]),0
def microbase(i,p): return min(L[max(0,i-4):i+1]),0
def minNb(i,n): return min(L[max(0,i-n):i+1])
def capitulation_base(i,p):
    # acha a barra de maior queda/menor low em [i-20,i-5]; base = menor low APOS ela ate i
    lo_bar=min(range(max(5,i-20),i-4),key=lambda j:L[j]) if i-4>max(5,i-20) else None
    if lo_bar is None: return None,None
    base=min(L[lo_bar+1:i+1]) if lo_bar+1<=i else L[lo_bar]
    return base,i-lo_bar
def legpos(i):
    j=i;lo=min(L[max(0,i-60):i+1]);hi=max(H[max(0,i-60):i+1])
    return 100*(C[i]-lo)/(hi-lo) if hi>lo else 50
def is_capitulation(i):  # forte queda recente: min_20b muito abaixo + recuperou
    m20=minNb(i,20);atr=ATR[i]
    return (C[i]-m20)/atr>3.0  # entrada esta >3ATR acima do fundo recente => houve queda+reclaim
def sweep_risk(i,p):     # recent pivot raso E perto (prone a wick sweep)
    lo,ba=recent_pivot(i,p)
    if lo is None: return False
    return (p-lo)/ATR[i]<1.8
def stype(i,p):
    lp=legpos(i);rs=RSIv[i] or 50;atr=ATR[i]
    ext=(C[i]-minNb(i,20))/atr
    if lp>85 and ext>4.0: return 'TOP_EXHAUSTION_NO_LONG'
    if is_capitulation(i): return 'V_REVERSAL_RECLAIM'
    if sweep_risk(i,p): return 'SHALLOW_PIVOT_SWEEP'
    return 'NORMAL_BPT'
def floor_risk(p,low,atr):
    risk=p-(low-BUF*atr); return max(risk,FLOOR*atr)
# ---- RULES: return (low, risk, tag) or ('NO_TRADE'/'REVIEW',...) ----
def V1_hybrid(i):
    p=C[i];atr=ATR[i];t=stype(i,p)
    if t=='TOP_EXHAUSTION_NO_LONG': return None,None,'NO_TRADE'
    if t=='V_REVERSAL_RECLAIM':
        b,_=capitulation_base(i,p); lo=b if b is not None and b<p else microbase(i,p)[0]
    elif t=='SHALLOW_PIVOT_SWEEP':
        lo=minNb(i,30)  # swing defendido mais fundo
    else:
        rp,_=recent_pivot(i,p); lo=rp if rp is not None else retest(i,p)[0]
    risk=floor_risk(p,lo,atr)
    if risk/atr>4: return lo,risk,'REVIEW_GT4'
    return lo,risk,t
def V2_nearest_valid(i):
    p=C[i];atr=ATR[i]
    # menor distancia entre candidatos validos (pivot/pl3/microbase/cap_base) abaixo da entrada, 0.3-4ATR
    cands=[]
    for fn in [recent_pivot,nearest_pl3]:
        lo,_=fn(i,p)
        if lo is not None and lo<p: cands.append(lo)
    mb=microbase(i,p)[0]; cb,_=capitulation_base(i,p)
    if mb<p: cands.append(mb)
    if cb is not None and cb<p: cands.append(cb)
    # nearest within band; prefer >=0.5ATR to avoid wick, <=4ATR
    valid=[c for c in cands if 0.5*atr<=(p-c)<=4*atr]
    pick=max(valid) if valid else (max([c for c in cands if c<p],default=None))
    if pick is None: return retest(i,p)[0],floor_risk(p,retest(i,p)[0],atr),'fallback'
    risk=floor_risk(p,pick,atr)
    return pick,risk,'nearest_valid' if risk/atr<=4 else 'REVIEW_GT4'
def V3_deeper_if_sweep(i):
    p=C[i];atr=ATR[i]
    rp,_=recent_pivot(i,p)
    if sweep_risk(i,p):
        lo=minNb(i,30)  # vai mais fundo se risco de sweep
    else:
        lo=rp if rp is not None else retest(i,p)[0]
    risk=floor_risk(p,lo,atr)
    return lo,risk,'deeper_sweep' if sweep_risk(i,p) else 'recent'
def sim(i,risk):
    p=C[i];stop=p-risk;pdone=False;realized=0.0;rem=1.0;end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        if L[j]<=stop:
            fill=O[j] if O[j]<=stop else stop
            return realized+rem*((fill-p)/risk)-COST,('be' if pdone else 'stop')
        if not pdone and H[j]>=p+2*risk: realized+=0.5*2.0;rem=0.5;pdone=True;stop=p
        if pdone and H[j]>=p+6*risk: return realized+rem*6.0-COST,'runner'
    return realized+rem*((C[end]-p)/risk)-COST,'time'
# ---- KEY CASES ----
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
swing={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
KEY=['E1','E17','E13','E23','E5','E21','E27','E30','E40']
print("=== KEY CASES: tipo + regras defended-swing (exit partial50) ===")
rows=[]
for eid in KEY:
    i=ts2idx[parse(swing[eid]['timestamp'])];p=C[i];atr=ATR[i]
    t=stype(i,p)
    out={'eid':eid,'type':t,'legpos':round(legpos(i)),'rsi':RSIv[i]}
    line=f"  {eid:<4} {t:<22} legpos={out['legpos']:<3}"
    for rn,fn in [('V1',V1_hybrid),('V2',V2_nearest_valid),('V3',V3_deeper_if_sweep)]:
        lo,risk,tag=fn(i)
        if lo is None:
            out[rn+'_R']='NO_TRADE';out[rn+'_ATR']='';line+=f" | {rn}=NO_TRADE";continue
        r,how=sim(i,risk);out[rn+'_R']=round(r,2);out[rn+'_ATR']=round(risk/atr,2)
        line+=f" | {rn} {risk/atr:.1f}ATR R={r:+.2f}"
    print(line);rows.append(out)
with open(f"{D}/l2_bpt_defended_swing_key_cases.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

# ---- Tarefa 3: candidatos causais de SL por caso-chave ----
labels={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_episode_labels.csv"))}
crows=[]
for eid in KEY:
    i=ts2idx[parse(swing[eid]['timestamp'])];p=C[i];atr=ATR[i]
    cands={'recent_pivot':recent_pivot(i,p)[0],'nearest_pl3':nearest_pl3(i,p)[0],'retest_low':retest(i,p)[0],
           'microbase_low':microbase(i,p)[0],'cap_base_low':capitulation_base(i,p)[0],
           'min_10b':minNb(i,10),'min_20b':minNb(i,20),'min_30b':minNb(i,30)}
    dd=labels.get(eid,{}).get('dist_demand_atr','')
    for nm,lo in cands.items():
        if lo is None: continue
        d=(p-lo)/atr
        crows.append({'eid':eid,'candidate':nm,'price':round(lo,1),'dist_atr':round(d,2),
            'in_band_0.5_4':'yes' if 0.5<=d<=4 else 'no','too_shallow':'yes' if d<0.5 else 'no','too_deep':'yes' if d>4 else 'no',
            'demand_dist_atr':dd})
with open(f"{D}/l2_bpt_defended_swing_candidates.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(crows[0].keys()));w.writeheader();w.writerows(crows)

# ---- DIAGNOSTIC full base (gate NOT fully passed -> NOT promoted) ----
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
def runpol(fn,name):
    out=[]
    for rep,el in reps:
        if not ATR[rep]: continue
        lo,risk,tag=fn(rep)
        if lo is None: out.append({'el':el,'R':None,'no_trade':True,'ratl':None});continue
        r,how=sim(rep,risk);out.append({'el':el,'R':r,'how':how,'ratl':risk/ATR[rep],'no_trade':False})
    tr=[o for o in out if not o['no_trade']];rs=[o['R'] for o in tr]
    nt=sum(1 for o in out if o['no_trade'])
    w=[x for x in rs if x>0];lo=[x for x in rs if x<0]
    eq=pk=mdd=c=ms=0
    for x in rs: eq+=x;pk=max(pk,eq);mdd=max(mdd,pk-eq);c=c+1 if x<0 else 0;ms=max(ms,c)
    rat=sorted(o['ratl'] for o in tr)
    return {'policy':name,'n':len(tr),'no_trade':nt,'WR':round(100*len(w)/len(rs),1),'avgR':round(sum(rs)/len(rs),3),
            'sumR':round(sum(rs),1),'PF':round(sum(w)/abs(sum(lo)),2) if lo else 'inf','maxDD':round(mdd,1),'streak':ms,
            'slATRmed':round(statistics.median(rat),2),'slATRp90':round(rat[int(.9*len(rat))],2),'slATRmax':round(max(rat),2),
            'gt4':sum(1 for o in tr if o['ratl']>4)}
print("\n=== DIAGNOSTIC full base (gate NÃO passou -> NÃO promovido) ===")
pr=[runpol(V1_hybrid,'V1_HYBRID'),runpol(V2_nearest_valid,'V2_NEAREST_VALID')]
for m in pr: print(f"  {m['policy']:<18} n={m['n']} no_trade={m['no_trade']} WR={m['WR']}% avgR={m['avgR']:+} sumR={m['sumR']:+} PF={m['PF']} maxDD={m['maxDD']} streak={m['streak']} | slATR med={m['slATRmed']} max={m['slATRmax']} >4ATR={m['gt4']}")
print("  (baselines do bloco anterior p/ referência: STRUCT_PURE sumR+62.5 maxDD24 >4ATR97 | CAP4_REJECT sumR+56.2 maxDD17)")
with open(f"{D}/l2_bpt_defended_swing_policy_results.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(pr[0].keys()));w.writeheader();w.writerows(pr)
# recall-gate
with open(f"{D}/l2_bpt_defended_swing_recall_gate.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['eid','must_preserve','V1_R','V1_ATR','V2_R','V2_ATR','resolved'])
    for r in rows:
        must=r['eid'] in ['E1','E5','E13','E17','E21','E27','E30','E40']
        w.writerow([r['eid'],must,r.get('V1_R'),r.get('V1_ATR'),r.get('V2_R'),r.get('V2_ATR'),''])
print("\nWROTE key_cases, candidates, policy_results, recall_gate CSVs")
print("HARD-STOP: nenhuma regra única resolve E1+E17+E13+E23 -> NÃO promover; full base = diagnostic only")
