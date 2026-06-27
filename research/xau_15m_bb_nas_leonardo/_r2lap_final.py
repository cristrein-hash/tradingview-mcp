"""Final: try to beat K5 (WR70.62/win85.6/8 blocks/streak20) on winners_kept while
robust. Then lock best. Adds contextual scorer (cut only multi-flag chop).
"""
from _r2lap_lib import load, evaluate, report

k = load()

def K5(r):
    return not ((r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0) or
                (r['absorption']==1 and r['low_vol_rel']>1.5))

# Contextual chop SCORE: count chop-symptoms; cut only when >=2 symptoms.
# symptoms (loser-dense, all WR<62 univ): one-sided(bsr4>=7), flat-flow,
# absorption, high-vol-noise(low_vol>1.5), young-regime(<25h).
def chop_score(r):
    s=0
    s+= r['buy_sell_ratio4']>=7
    s+= -2<=r['flow_accel']<=0
    s+= r['absorption']==1
    s+= r['low_vol_rel']>1.5
    s+= r['regime_age_h']<25.2
    return s

tests=[
  ("F1 K5 (lock candidate)", K5),
  ("F2 cut chop_score>=3", lambda r: chop_score(r)<3),
  ("F3 cut chop_score>=2", lambda r: chop_score(r)<2),
  # tight 3-way chop: one-sided + flat + (absorb OR highvol)
  ("F4 cut bsr4>=7 & flat & (absorb|lowvol>1.5)",
     lambda r: not (r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0 and (r['absorption']==1 or r['low_vol_rel']>1.5))),
  # K5 OR third clause one-sided&young-regime (young one-sided = unproven momentum)
  ("F5 K5 OR cut bsr4>=7&regime<25",
     lambda r: K5(r) and not (r['buy_sell_ratio4']>=7 and r['regime_age_h']<25.2)),
]
print("BASE WR=68.54 streak=24 | gates: WR>68.5, yr>=base, win>=85%, blocks>=6/8, streak<24\n")
for d,f in tests:
    report(evaluate(k,f,d)); print()
