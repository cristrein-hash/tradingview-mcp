#!/usr/bin/env python3
"""
_disc8_audit_best.py — Self-audit of the best candidate rules from parts 2-3.
Check per-BLOCK (8 blocks) stability, streak reduction reality, and that the WR
lift is not carried by a few trades. Honest reporting before presenting.

Candidates (acceptance-time / vol-contextual exhaustion cut):
 R1 CUT(bars_to_8atr<31 & path_eff>0.6)         -- robust, gentle
 R2 CUT(bars_to_8atr<40 & macro_retr<1.0)       -- robust, more cut
 R3 CUT(bars_to_8atr<50)                         -- stronger WR, NOT robust on 85% gate
 R4 CUT(bars_to_8atr<60)                         -- WR 0.684, ~64% winners kept
RULES: win=R>0, chronological streak, no R/win feature.
"""
import json
ROWS=[json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r:r['low_t'])
N=len(ROWS); BASE_WR=sum(r['win'] for r in ROWS)/N
TOT_WIN=sum(r['win'] for r in ROWS); TOT_LOSS=N-TOT_WIN
def streak(rows):
    mx=cur=0
    for r in rows:
        if r['win']==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx

CANDS={
 "R1 CUT(bars<31 & path_eff>0.6)": lambda r: not (r['bars_to_8atr']<31 and r['path_eff']>0.6),
 "R2 CUT(bars<40 & macro_retr<1.0)": lambda r: not (r['bars_to_8atr']<40 and r['macro_retr']<1.0),
 "R3 CUT(bars<50)": lambda r: r['bars_to_8atr']>=50,
 "R4 CUT(bars<60)": lambda r: r['bars_to_8atr']>=60,
}
BLOCKS=sorted(set(r['block'] for r in ROWS))
print(f"BASE_WR={BASE_WR:.4f} BASE_STREAK={streak(ROWS)} N={N}")
# per-block base WR
print("\nPer-block BASE WR:")
for b in BLOCKS:
    sub=[r for r in ROWS if r['block']==b]
    print(f"  {b} n={len(sub):3d} wr={sum(x['win'] for x in sub)/len(sub):.3f}")

for name,pred in CANDS.items():
    keep=[r for r in ROWS if pred(r)]
    nk=len(keep); wk=sum(r['win'] for r in keep)
    print(f"\n=== {name} ===")
    print(f"  n_keep={nk} wr_keep={wk/nk:.4f} streak={streak(keep)} "
          f"winners_kept={wk/TOT_WIN:.3f} losers_cut={(TOT_LOSS-(nk-wk))/TOT_LOSS:.3f}")
    print("  per-block keep WR (vs base block WR):")
    n_up=0; n_blk=0
    for b in BLOCKS:
        sub=[r for r in keep if r['block']==b]
        base=[r for r in ROWS if r['block']==b]
        bw=sum(x['win'] for x in base)/len(base)
        if sub:
            kw=sum(x['win'] for x in sub)/len(sub)
            up = kw>=bw
            n_blk+=1; n_up+= 1 if up else 0
            print(f"    {b} n={len(sub):3d} wr={kw:.3f} base={bw:.3f} {'+' if up else '-'}")
    print(f"  blocks improved/equal: {n_up}/{n_blk}")
    # leave-one-block-out: does WR lift survive removing best block?
    lifts=[]
    for b in BLOCKS:
        kk=[r for r in keep if r['block']!=b]
        if kk: lifts.append((b, sum(x['win'] for x in kk)/len(kk)))
    worst=min(lifts,key=lambda x:x[1])
    print(f"  leave-one-block-out worst WR: {worst[1]:.4f} (removing {worst[0]}) vs base {BASE_WR:.4f}")
