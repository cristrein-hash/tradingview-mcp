#!/usr/bin/env python3
"""ESTUDO sweep-reject 4H (o gate que bloqueou facas) — RAW 4H multi-ano. READ_OB_ZONES.
Enumera candidatos (sweep de high + upper-wick), rotula por RESULTADO forward (breakdown=CAPTURA vs
continua-up=FALSO), mede que critérios/limiares discriminam, valida em sub-janela. Depois estuda a
RETOMADA de longs (quebra de estrutura HH+HL) por TF (1H/4H multi-ano; 15M só recente — flag).
Sem inventar: pavio/close/sweep = geometria da vela; estrutura = swings do próprio preço. py3."""
import json, datetime as dt, statistics as st
from pathlib import Path
ROOT = Path("/Users/cristrein/tradingview-mcp")
def utc(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
def load(f):
    r=[json.loads(l) for l in open(f) if l.strip()]
    return sorted([(int(x['t']),float(x['o']),float(x['h']),float(x['l']),float(x['c'])) for x in r])
B4=load(ROOT/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl")
def atr(bars,i,n=14):
    if i<n: return None
    return sum(max(bars[k][2]-bars[k][3],abs(bars[k][2]-bars[k-1][4]),abs(bars[k][3]-bars[k-1][4])) for k in range(i-n+1,i+1))/n

K=6  # horizonte forward (6x4H = 24h)
cands=[]
for i in range(20,len(B4)-K):
    t,o,h,l,c=B4[i]; a=atr(B4,i)
    if not a: continue
    prior_high=max(x[2] for x in B4[i-3:i])
    if h<=prior_high: continue           # tem de VARRER um high anterior
    rng=h-l
    if rng<=0: continue
    uw=(h-max(o,c))/rng
    if uw<0.30: continue                 # candidato frouxo: pavio superior >=30%
    fut=B4[i+1:i+1+K]
    down=(c-min(x[3] for x in fut))/a; up=(max(x[2] for x in fut)-c)/a
    cands.append(dict(t=t,uw=uw,depth=(h-prior_high)/a,close_pos=(c-l)/rng,body=abs(c-o)/rng,
                      down=round(down,2),up=round(up,2),label='CAPTURE' if down>up else 'FALSE'))
cap=[x for x in cands if x['label']=='CAPTURE']; fal=[x for x in cands if x['label']=='FALSE']
print("="*70)
print("ESTUDO SWEEP-REJECT 4H — RAW %d barras (%s → %s)"%(len(B4),utc(B4[0][0])[:10],utc(B4[-1][0])[:10]))
print("="*70)
print("candidatos (sweep+upper-wick>=0.30): %d | CAPTURE %d (%.0f%%) · FALSE %d"%(
    len(cands),len(cap),100*len(cap)/len(cands),len(fal)))
def auc(k):
    n=w=0
    for a_ in cap:
        for b_ in fal:
            n+=1; w+=1 if a_[k]>b_[k] else (0.5 if a_[k]==b_[k] else 0)
    return w/n if n else .5
print("\ncritério              AUC(cap>false)   média CAPTURE   média FALSE")
for k in ('uw','depth','close_pos','body'):
    print("  %-12s        %.2f            %.2f            %.2f"%(k,auc(k),st.mean(x[k] for x in cap),st.mean(x[k] for x in fal)))
print("\nTaxa de CAPTURE por limiar (procura threshold funcional):")
for k,ths in (('uw',[0.4,0.5,0.6]),('close_pos',[0.5,0.4,0.33]),('depth',[0.3,0.6,1.0])):
    for th in ths:
        sub=[x for x in cands if (x[k]>=th if k!='close_pos' else x[k]<=th)]
        if sub:
            cr=100*sum(1 for x in sub if x['label']=='CAPTURE')/len(sub)
            op='>=' if k!='close_pos' else '<='
            print("  %s%s%-4s : N=%3d  CAPTURE=%.0f%%"%(k,op,th,len(sub),cr))
# sub-janela: metade/metade
mid=B4[len(B4)//2][0]
for half,lab in ((lambda x:x['t']<mid,'1ª metade'),(lambda x:x['t']>=mid,'2ª metade')):
    sub=[x for x in cands if half(x)]
    if sub:
        cr=100*sum(1 for x in sub if x['label']=='CAPTURE')/len(sub)
        print("  [sub-janela %s] N=%d CAPTURE=%.0f%%"%(lab,len(sub),cr))
print("\n(baseline: qualquer vela 4H aleatória tem ~50%% chance de 'down>up' forward — comparar contra isto)")
