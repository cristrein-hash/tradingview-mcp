#!/usr/bin/env python3
"""DA: the +4.9 sumR of (h1_eff & macro_bear==0) vs (h1_eff) decomposes into +0.31R from BEAR
removal and +4.44R from 17 NEW trades surfaced by re-dedup. Probe whether those new trades are a
legitimate consequence of removing BEAR rows (a BEAR trade occupied a slot; removing it frees a
later overlapping non-BEAR trade) or an artifact. Each new trade must be: (a) non-BEAR, (b) pass
h1_eff>=0.15, (c) have been blocked in the 211 by an overlapping earlier trade that is BEAR (or
chain thereof). Report their regime and whether the slot-freer was BEAR. 2026-06-27."""
import json
from pathlib import Path
import filter_harness as H

def regime(r):
    if r['macro_bear']==1: return 'BEAR'
    if r['macro_bull']==1: return 'BULL'
    return 'NEUTRAL'

s211,t211=H.run(lambda r: r['h1_eff']>=0.15)
scand,tcand=H.run(lambda r: r['h1_eff']>=0.15 and r['macro_bear']==0)
ids211={(c['block'],c['low_t']) for c in t211}
new=[c for c in tcand if (c['block'],c['low_t']) not in ids211]
print(f"NEW trades (in cand, not in 211): {len(new)}  sumR={sum(c['R'] for c in new):+.2f}")

# all h1_eff candidates pre-dedup, by block, sorted by cj
ROWS=H.ROWS
def cands(keepfn):
    return [c for c in ROWS if keepfn(c)]
pool211=cands(lambda r: r['h1_eff']>=0.15)
# For each new trade, find what overlapping earlier trade occupied its slot in the 211 dedup
byblk={}
for c in pool211: byblk.setdefault(c['block'],[]).append(c)
for b in byblk: byblk[b].sort(key=lambda x:x['cj'])

freed_by_bear=0; freed_by_nonbear=0
for nt in new:
    blk=nt['block']; cs=byblk[blk]
    # simulate 211 dedup and find which trade was 'busy' at nt['cj']
    busy=-10**9; blocker=None
    for c in cs:
        if c['cj']>nt['cj']: break
        if c['cj']<=busy: continue
        busy=c['exi'];
        if c['cj']<=nt['cj']<=c['exi'] or c['cj']<nt['cj']:
            blocker=c
    # blocker = last taken trade before/overlapping nt in the 211 chain
    bl_reg = regime(blocker) if blocker else None
    print(f"  new {nt['block']} cj={nt['cj']} R={nt['R']:+.2f} reg={regime(nt)} | blocked-by reg={bl_reg} R={blocker['R'] if blocker else None}")
    if bl_reg=='BEAR': freed_by_bear+=1
    elif bl_reg is not None: freed_by_nonbear+=1
print(f"\nnew trades freed because a BEAR trade vacated the slot: {freed_by_bear}")
print(f"new trades whose slot-freer was NON-bear (pure reshuffle, not caused by BEAR removal): {freed_by_nonbear}")
