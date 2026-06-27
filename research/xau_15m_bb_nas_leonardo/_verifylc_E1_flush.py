#!/usr/bin/env python3
"""Independent DA verification of low_closepos<=0.7922 loser-cut on E1_flush.
Recompute BEFORE/AFTER WR, maxstreak, winners_kept, losers_cut, WR-by-year, WR-by-block,
threshold neighborhood. No look-ahead check on the filter feature."""
import json

rows = [json.loads(l) for l in open('entry_dataset.jsonl')]
# E1_flush membership (rule axes)
mem = [r for r in rows if r['rsi_low'] >= 48.5 and r['disp4_atr'] < -0.898]
mem.sort(key=lambda r: r['low_t'])

def is_win(r): return r['R_reclaim'] > 0

def stats(sub):
    n=len(sub); w=sum(1 for r in sub if is_win(r))
    wr=w/n if n else 0
    streak=mx=0
    for r in sub:
        if is_win(r): streak=0
        else: streak+=1; mx=max(mx,streak)
    return n,w,wr,mx

N0,W0,WR0,MX0 = stats(mem); L0=N0-W0
print(f"BEFORE n={N0} winners={W0} losers={L0} WR={WR0:.4f} maxstreak={MX0}")

# Confirm filter feature is not look-ahead: low_closepos = close pos within reclaim bar's range.
# Is it correlated 1:1 with outcome? check it's not a disguised outcome.
filt = lambda r: r['low_closepos'] <= 0.7922
after = [r for r in mem if filt(r)]
N1,W1,WR1,MX1 = stats(after); L1=N1-W1
wk = W1/W0; lc = (L0-L1)/L0
print(f"AFTER  n={N1} winners={W1} losers={L1} WR={WR1:.4f} maxstreak={MX1}")
print(f"winners_kept_pct={wk*100:.1f}  losers_cut_pct={lc*100:.1f}")
print(f"WR delta={WR1-WR0:+.4f}  streak delta={MX1-MX0:+d}")

# Per-year WR before/after
print("\n=== WR by YEAR (before -> after) ===")
yrs=sorted(set(r['yr'] for r in mem))
worse_year=False
for y in yrs:
    b=[r for r in mem if r['yr']==y]
    a=[r for r in b if filt(r)]
    bn,bw,bwr,_=stats(b); an,aw,awr,amx=stats(a)
    flag = "  <-- WORSE" if (an>0 and awr < bwr-1e-9) else ""
    if an>0 and awr < bwr-1e-9: worse_year=True
    print(f"  {y}: before n={bn} WR={bwr:.3f} | after n={an} WR={awr:.3f} streak={amx}{flag}")

# Per-block WR before/after (block field)
print("\n=== WR by BLOCK (before -> after) ===")
blocks=sorted(set(r['block'] for r in mem))
worse_block=False
for blk in blocks:
    b=[r for r in mem if r['block']==blk]
    a=[r for r in b if filt(r)]
    bn,bw,bwr,_=stats(b); an,aw,awr,amx=stats(a)
    flag=""
    if an>=5 and awr < bwr-1e-9:
        flag="  <-- WORSE"; worse_block=True
    print(f"  {blk}: before n={bn:3d} WR={bwr:.3f} | after n={an:3d} WR={awr:.3f} streak={amx}{flag}")

# Threshold neighborhood collapse check
print("\n=== threshold neighborhood ===")
for t in [0.72,0.74,0.76,0.7922,0.81,0.83,0.85]:
    s=[r for r in mem if r['low_closepos']<=t]
    nn,ww,wwr,mmx=stats(s)
    print(f"  t={t}: n={nn} WR={wwr:.3f} streak={mmx} winkept={ww/W0:.3f} loscut={(L0-(nn-ww))/L0:.3f}")

# Sanity: does low_closepos perfectly predict outcome (look-ahead smell)?
print("\n=== look-ahead smell: low_closepos vs outcome separation ===")
win_lcp=[r['low_closepos'] for r in mem if is_win(r)]
los_lcp=[r['low_closepos'] for r in mem if not is_win(r)]
import statistics as st
print(f"  winners low_closepos mean={st.mean(win_lcp):.3f} median={st.median(win_lcp):.3f}")
print(f"  losers  low_closepos mean={st.mean(los_lcp):.3f} median={st.median(los_lcp):.3f}")
# fraction of winners above 0.7922 (would be cut) and losers above (correctly cut)
w_cut=sum(1 for x in win_lcp if x>0.7922); l_cut=sum(1 for x in los_lcp if x>0.7922)
print(f"  winners cut={w_cut}/{len(win_lcp)}  losers cut={l_cut}/{len(los_lcp)}")

print("\n=== VERDICT INPUTS ===")
print(f"cuts_loser={lc>0}  winners_kept>=90%={wk>=0.90}  WR_up={WR1>WR0}  streak_ok={MX1<=MX0}")
print(f"any_year_worse={worse_year}  any_block_worse(n>=5)={worse_block}")
