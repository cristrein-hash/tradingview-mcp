#!/usr/bin/env python3
"""Independent DA verification of E5_demand sell_w==0 loser-cut.
Target: macro_drop_atr<=3.6 AND in_demand==1, outcome=R_reclaim.
Filter: KEEP sell_w==0 (cut bars with a weak SELL bubble at reclaim).
Checks: WR before/after, maxstreak before/after, winners_kept_pct, losers_cut_pct,
per-year and per-block stability, look-ahead audit, threshold-neighborhood collapse.
"""
import json, collections

ROWS=[json.loads(l) for l in open('entry_dataset.jsonl')]
MEM=[r for r in ROWS if r.get('macro_drop_atr',1e9)<=3.6 and r.get('in_demand')==1]
MEM.sort(key=lambda r:r['low_t'])

def is_w(r): return r['R_reclaim']>0
def is_l(r): return r['R_reclaim']<=0
def maxstreak(rows):
    m=c=0
    for r in rows:
        if is_l(r): c+=1; m=max(m,c)
        else: c=0
    return m
def stats(rows):
    n=len(rows); w=sum(is_w(r) for r in rows)
    return n,w,n-w,(w/n if n else 0),maxstreak(rows)

n0,w0,l0,wr0,ms0=stats(MEM)
print('BEFORE: n=%d W=%d L=%d WR=%.4f maxstreak=%d'%(n0,w0,l0,wr0,ms0))

KEEP=lambda r: r.get('sell_w',0)==0
KEPT=[r for r in MEM if KEEP(r)]
CUT=[r for r in MEM if not KEEP(r)]
n1,w1,l1,wr1,ms1=stats(KEPT)
print('AFTER sell_w==0: n=%d W=%d L=%d WR=%.4f maxstreak=%d'%(n1,w1,l1,wr1,ms1))
print('winners_kept_pct=%.2f'%(w1/w0*100))
print('losers_cut_pct=%.2f'%((l0-l1)/l0*100))
print('cut: n=%d W=%d L=%d'%(len(CUT),sum(is_w(r) for r in CUT),sum(is_l(r) for r in CUT)))

# Look-ahead audit: sell_w is a bubble-polarity flag read AT reclaim bar.
# Confirm it is NOT one of the forbidden outcome/future fields.
FORBID={'R_reclaim','R_8atr','near_M8','held8','runner','reclaim_idx','low_idx'}
print('look-ahead check: filter field = sell_w; in FORBID?', 'sell_w' in FORBID)

print('--- per year ---')
for y in (2024,2025,2026):
    by=[r for r in MEM if r['yr']==y]; ay=[r for r in KEPT if r['yr']==y]
    _,_,_,wrb,_=stats(by); _,_,_,wra,_=stats(ay)
    print('y%d: BEFORE n=%d WR=%.4f | AFTER n=%d WR=%.4f delta=%+.4f'%(y,len(by),wrb,len(ay),wra,wra-wrb))

print('--- per block ---')
for b in sorted(set(r['block'] for r in MEM)):
    bb=[r for r in MEM if r['block']==b]; ab=[r for r in KEPT if r['block']==b]
    _,_,_,wrb,_=stats(bb); _,_,_,wra,_=stats(ab)
    flag=' WORSE' if (ab and wra<wrb) else ''
    print('%-12s BEFORE n=%3d WR=%.3f | AFTER n=%3d WR=%.3f delta=%+.3f%s'%(b,len(bb),wrb,len(ab),wra,wra-wrb,flag))

# Threshold-neighborhood: sell_w is binary, so no threshold to perturb.
# Robustness instead = is the cut subset (sell_w==1) genuinely loser-skewed?
print('--- cut-subset purity (sell_w==1) ---')
nc,wc,lc,wrc,_=stats(CUT)
print('cut subset WR=%.4f (n=%d) vs kept WR=%.4f vs base WR=%.4f'%(wrc,nc,wr1,wr0))
