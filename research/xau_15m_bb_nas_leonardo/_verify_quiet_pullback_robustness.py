"""DA robustness probe for rule: disp4_atr<-0.5 & atr_regime<1.0.
Threshold sensitivity, baseline/complement lift, R-cap inspection, WR-flat check."""
import json, collections

rows=[json.loads(l) for l in open('entry_dataset.jsonl')]

def st(s):
    if not s: return (0,None,None)
    wr=100*sum(1 for r in s if r['R_reclaim']>0)/len(s)
    a=sum(r['R_reclaim'] for r in s)/len(s)
    return (len(s),round(wr,1),round(a,3))

print('=== disp4 threshold sweep (atr_regime<1.0) ===')
for d in [-0.3,-0.4,-0.5,-0.6,-0.7,-0.8]:
    print('disp4<',d, st([r for r in rows if r['disp4_atr']<d and r['atr_regime']<1.0]))

print('=== atr_regime threshold sweep (disp4<-0.5) ===')
for a in [0.8,0.9,1.0,1.1,1.2]:
    print('atr_reg<',a, st([r for r in rows if r['disp4_atr']<-0.5 and r['atr_regime']<a]))

print('=== baseline all ===', st(rows))
print('=== complement (rule FALSE) ===',
      st([r for r in rows if not(r['disp4_atr']<-0.5 and r['atr_regime']<1.0)]))

Rs=collections.Counter(round(r['R_reclaim'],1) for r in rows
                       if r['disp4_atr']<-0.5 and r['atr_regime']<1.0)
print('R value freq:', Rs.most_common(8))
