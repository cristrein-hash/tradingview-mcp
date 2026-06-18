#!/usr/bin/env python3
"""L2/BPT SL ESTRUTURAL POR CONTEXTO. SL ancorado na zona de DEMANDA 4H defendida (causal,
as-of-bar) -> tight quando demanda perto, largo quando é a base funda. Exit FIXO partial50@2R+6R.
Classifica por TIPO DE SAÍDA (nunca R-sign). No SLIM/teto1.5/CAP4/outcome-future."""
import json, csv, statistics
from datetime import datetime, timezone
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
def swing_origin(i):  # mecânico antigo (p/ comparar)
    p=C[i];a=ATR[i];lo=None
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: lo=L[j];break
    if lo is None: lo=min(L[max(0,i-6):i+1])
    return max(p-(lo-0.1*a),0.3*a)
def legpos(i):
    p=C[i];hi=max(H[max(0,i-90):i+1]);lo=min(L[max(0,i-90):i+1]);return 100*(p-lo)/(hi-lo) if hi>lo else 50
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
def dnum(r,k):
    try: return float(r[k])
    except: return None
BUF=0.1;FLOOR=0.3
# ---- SL POR CONTEXTO ----
def context_sl(i):
    p=C[i];a=ATR[i];r=dsq.get(i,{})
    lp=legpos(i);rsi=RS[i] or 0
    # TOP_EXHAUSTION -> no_trade
    if lp>=85 and rsi>=70: return None,None,'TOP_EXHAUSTION_NO_LONG',None
    dem_low=dnum(r,'nearest_4h_demand_low');dist=dnum(r,'dist_4h_demand_low_atr')
    touched=r.get('demand_4h_touched_on_retest')=='1'
    # demanda defendida e razoável -> SL ancorado nela (tight quando perto, largo quando funda)
    if dem_low is not None and dist is not None and dist<=5.0:
        sl=dem_low-BUF*a; risk=max(p-sl,FLOOR*a)
        typ='V_REVERSAL_DEMAND' if dist<=2.0 else 'NORMAL_DEMAND_BASE'
        return sl,risk,typ,dist
    # demanda longe/ausente -> estrutura funda (swing origin) com flag review (entrada provavelmente tardia)
    risk=swing_origin(i)
    return p-risk,risk,'LATE_WIDE_REVIEW',(dist if dist else 99)
def classify(i,risk):  # tipo de saída (partial50@2R+6R)
    p=C[i];stop=p-risk;pd=False;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if not pd and L[j]<=stop: return 'STOP_LOSS'
        if not pd and H[j]>=p+2*risk: pd=True
        if pd and H[j]>=p+6*risk: return 'WIN_RUNNER'
        if pd and L[j]<=p: return 'WIN_partialBE'
    return 'WIN_partial_held' if pd else 'SCRATCH_timeout'
def realR(i,risk):
    p=C[i];stop=p-risk;pd=False;rz=0.0;rem=1.0;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if L[j]<=stop:
            f=O[j] if O[j]<=stop else stop;return rz+rem*((f-p)/risk)-0.10
        if not pd and H[j]>=p+2*risk: rz+=1.0;rem=0.5;pd=True;stop=p
        if pd and H[j]>=p+6*risk: return rz+rem*6.0-0.10
    return rz+rem*((C[e]-p)/risk)-0.10
# ---- casos-chave ----
sw={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_swing_anatomy.csv"))}
def idxof(eid):
    t=int(datetime.strptime(sw[eid]['timestamp'],'%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc).timestamp())
    return TS.index(t) if t in TS else None
KEEP=['E1','E17','E13','E5','E21','E27','E30','E40'];NOTRADE=['E23','E15','E24','E34']
print("=== CASOS-CHAVE: SL por contexto (demanda 4H) vs swing-origin mecânico ===")
rows=[]
for eid in KEEP+NOTRADE:
    i=idxof(eid);
    if i is None or not ATR[i]: continue
    sl,risk,typ,dist=context_sl(i)
    sw_atr=swing_origin(i)/ATR[i]
    if sl is None:
        print(f"  {eid:<4} {typ:<22} NO_TRADE | swing-origin seria {sw_atr:.1f}ATR")
        rows.append({'eid':eid,'type':typ,'sl_atr':'','exit':'NO_TRADE','R':'','swing_atr':round(sw_atr,2)});continue
    ratl=risk/ATR[i];ex=classify(i,risk);R=realR(i,risk)
    flag='SHALLOW_SWEEP?' if ex=='STOP_LOSS' and dist and dist<3 else ''
    print(f"  {eid:<4} {typ:<22} SL={ratl:.2f}ATR (demanda dist {dist}) exit={ex:<16} R={R:+.2f} | swing-orig {sw_atr:.1f}ATR {flag}")
    rows.append({'eid':eid,'type':typ,'sl_atr':round(ratl,2),'dem_dist':dist,'exit':ex,'R':round(R,2),'swing_atr':round(sw_atr,2)})
with open(f"{D}/l2_bpt_sl_context_key_cases.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['eid','type','sl_atr','dem_dist','exit','R','swing_atr']);w.writeheader()
    for r in rows: w.writerow({k:r.get(k,'') for k in ['eid','type','sl_atr','dem_dist','exit','R','swing_atr']})
print("\nHARD-STOP: E1/E17 tight+hold? E13 resolve ou scratch? E23/E15/E24/E34 no_trade?")
