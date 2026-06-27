"""Devil's Advocate checks for A1 5ATR filter (look-ahead / sentinel / power).
disp4_atr>=0.78 AND dist_supply_atr>=-0.28."""
import json
rows=[json.loads(l) for l in open('dataset_5atr.jsonl')]

# 1. dist_supply_atr=99 sentinel = no supply overhead within window. >=50 detects it.
sent=[r for r in rows if r['dist_supply_atr']>=50]
print('sentinel(dist_supply>=50) n=%d WR=%.1f'%(len(sent),100*sum(r['win'] for r in sent)/len(sent)))

# 2. sentinel rows are ALL kept (99 >= -0.28). Are they carrying the filter?
kept=[r for r in rows if r['disp4_atr']>=0.78 and r['dist_supply_atr']>=-0.28]
ks=[r for r in kept if r['dist_supply_atr']>=50]
print('kept n=%d, sentinel_in_kept=%d (%.1f%%)'%(len(kept),len(ks),100*len(ks)/len(kept)))

# 3. Test filter EXCLUDING sentinels (is edge real among rows that DO have supply data?)
real=[r for r in rows if r['dist_supply_atr']<50]
rkept=[r for r in real if r['disp4_atr']>=0.78 and r['dist_supply_atr']>=-0.28]
rcut=[r for r in real if not(r['disp4_atr']>=0.78 and r['dist_supply_atr']>=-0.28)]
print('REAL-supply subset: base n=%d WR=%.2f'%(len(real),100*sum(r['win'] for r in real)/len(real)))
print('  keep n=%d WR=%.2f | cut n=%d WR=%.2f'%(len(rkept),100*sum(r['win'] for r in rkept)/len(rkept),len(rcut),100*sum(r['win'] for r in rcut)/len(rcut)))

# 4. disp4 negative (displacement is structural, not outcome)
neg=[r for r in rows if r['disp4_atr']<0]
print('disp4<0 n=%d'%len(neg))

# 5. power: cut group
cut=[r for r in rows if not(r['disp4_atr']>=0.78 and r['dist_supply_atr']>=-0.28)]
print('cut n=%d WR=%.1f'%(len(cut),100*sum(r['win'] for r in cut)/len(cut)))
