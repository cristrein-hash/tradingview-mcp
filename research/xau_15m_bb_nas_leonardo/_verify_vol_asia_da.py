"""Devil's Advocate verification for rule:
   vol_low_vs_med <= 0.9 AND hour in 0..6 (Asia, dry exhaustion).
Checks: look-ahead, ex-caps per-year, robustness. Outcome = R_reclaim."""
import json
from collections import Counter

rows=[json.loads(l) for l in open('entry_dataset.jsonl')]
def sel(r): return (r['vol_low_vs_med']<=0.9) and (0<=r['hour']<=6)
S=[r for r in rows if sel(r)]

# Rule uses ONLY vol_low_vs_med + hour -> neither near_M8 nor R_8atr/outcome used as feature. PASS veto.
print('rule hour dist', Counter(r['hour'] for r in S))
print('rule vol range', round(min(r['vol_low_vs_med'] for r in S),3), round(max(r['vol_low_vs_med'] for r in S),3))

caps=[r for r in S if r['R_reclaim']>=20]
print('capped(>=20) trades:', len(caps), 'years', Counter(r['yr'] for r in caps))

def avgyr(sub):
    d={}
    for yr in (2024,2025,2026):
        s=[r['R_reclaim'] for r in sub if r['yr']==yr]
        if s: d[yr]=(round(sum(s)/len(s),3),len(s))
    return d
print('per-year FULL:', avgyr(S))
print('per-year ex 20R caps:', avgyr([r for r in S if r['R_reclaim']<20]))

# ex-top2 per year (remove 2 global biggest)
Ssort=sorted(S,key=lambda r:r['R_reclaim'],reverse=True)
ex2=Ssort[2:]
print('per-year ex-top2 global:', avgyr(ex2))
