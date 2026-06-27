"""
_reopt5_harness.py — RAW-causal re-optimization harness for 5ATR candidates.

Base = 5ATR-confirm candidates (fractal min, entry at 5ATR bar, SL=flush-0.1ATR, EXIT=let-run),
NO dedup. n=3047, WR base=60.49%, avgR +0.298. win = R>0.

Goal: STACK of 1-3 filters (may be CUT-when-loser-dense) raising WR above 60.49% with STABILITY:
  - wr_keep > 60.49
  - wr_keep_per_year >= base_year for EACH of 2024/2025/2026
  - winners_kept_pct >= 85%
  - >= 6/8 blocks non-worse (block WR after >= block WR base)
  - lower max-losing-streak

FORBIDDEN as feature: R, win, cj, low_idx.

Streak = max consecutive losers ordered by low_t.
"""
import json, statistics

PATH = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_5atr.jsonl'

def load():
    return [json.loads(l) for l in open(PATH)]

ROWS = load()
BASE_N = len(ROWS)
BASE_WINS = sum(r['win'] for r in ROWS)
BASE_WR = 100*BASE_WINS/BASE_N

# base year WR
BASE_YR = {}
for y in (2024,2025,2026):
    sub=[r for r in ROWS if r['yr']==y]
    BASE_YR[y]=100*sum(x['win'] for x in sub)/len(sub)

BLOCKS = sorted(set(r['block'] for r in ROWS))
BASE_BLOCK = {}
for b in BLOCKS:
    sub=[r for r in ROWS if r['block']==b]
    BASE_BLOCK[b]=100*sum(x['win'] for x in sub)/len(sub)

def max_losing_streak(rows):
    s=sorted(rows, key=lambda r:r['low_t'])
    mx=cur=0
    for r in s:
        if r['win']==0:
            cur+=1; mx=max(mx,cur)
        else:
            cur=0
    return mx

BASE_STREAK = max_losing_streak(ROWS)

def evaluate(keep_fn, name=''):
    """keep_fn(row)->bool : True = KEEP the candidate (passes filter)."""
    kept=[r for r in ROWS if keep_fn(r)]
    cut =[r for r in ROWS if not keep_fn(r)]
    n_keep=len(kept)
    if n_keep==0:
        return None
    wins_keep=sum(r['win'] for r in kept)
    wr_keep=100*wins_keep/n_keep
    total_winners=BASE_WINS
    winners_kept=wins_keep
    winners_kept_pct=100*winners_kept/total_winners
    total_losers=BASE_N-BASE_WINS
    losers_cut=sum(1 for r in cut if r['win']==0)
    losers_cut_pct=100*losers_cut/total_losers if total_losers else 0
    streak=max_losing_streak(kept)
    # per year
    yr={}
    for y in (2024,2025,2026):
        sy=[r for r in kept if r['yr']==y]
        yr[y]=100*sum(x['win'] for x in sy)/len(sy) if sy else 0.0
    # per block non-worse
    nonworse=0; block_detail={}
    for b in BLOCKS:
        sb=[r for r in kept if r['block']==b]
        wrb=100*sum(x['win'] for x in sb)/len(sb) if sb else 0.0
        block_detail[b]=(round(wrb,1), len(sb))
        if sb and wrb>=BASE_BLOCK[b]-1e-9:
            nonworse+=1
        elif not sb:
            pass  # empty block does not count as non-worse
    avgR=statistics.mean(r['R'] for r in kept)
    robust = (wr_keep>BASE_WR and
              all(yr[y]>=BASE_YR[y]-1e-9 for y in (2024,2025,2026)) and
              winners_kept_pct>=85.0 and
              nonworse>=6)
    return dict(name=name, n_keep=n_keep, wr_keep=round(wr_keep,2), avgR=round(avgR,3),
                streak_keep=streak, streak_base=BASE_STREAK,
                winners_kept_pct=round(winners_kept_pct,2),
                losers_cut_pct=round(losers_cut_pct,2),
                yr={y:round(yr[y],2) for y in (2024,2025,2026)},
                nonworse=nonworse, blocks=block_detail, robust=robust)

def report(res):
    if res is None:
        print('  EMPTY'); return
    print(f"  {res['name']}")
    print(f"    n_keep={res['n_keep']} wr_keep={res['wr_keep']} (base {round(BASE_WR,2)}) avgR={res['avgR']}")
    print(f"    streak {res['streak_base']}->{res['streak_keep']}  winners_kept%={res['winners_kept_pct']}  losers_cut%={res['losers_cut_pct']}")
    print(f"    yr {res['yr']} | base {{2024:{round(BASE_YR[2024],2)},2025:{round(BASE_YR[2025],2)},2026:{round(BASE_YR[2026],2)}}}")
    print(f"    blocks nonworse={res['nonworse']}/8  {res['blocks']}")
    print(f"    ROBUST={res['robust']}")

if __name__=='__main__':
    print('BASE n=',BASE_N,'WR=',round(BASE_WR,2),'streak=',BASE_STREAK)
    print('BASE_YR',{y:round(v,2) for y,v in BASE_YR.items()})
    print('BASE_BLOCK',{b:round(v,1) for b,v in BASE_BLOCK.items()})
