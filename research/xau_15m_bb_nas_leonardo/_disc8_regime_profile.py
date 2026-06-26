"""Profile WR across regime/localization features (single + binned) to find
directional signal before building combos. Lens: macro_drop, macro_retr,
macro_bull/bear, hd_pos, h4_pos, h4_trend, hd_trend, dist_supply/demand.
RAW-causal. Reports WR for low/high tertiles + per-year stability of split.
"""
import sys
sys.path.insert(0, '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo')
from _disc8_lib import load
import statistics as st

rows = load()
n = len(rows)
base = sum(r['win'] for r in rows) / n
print(f"BASE WR={base:.4f} n={n}\n")

NUM = ['macro_drop_atr','macro_retr','hd_pos','h4_pos','h1_pos',
       'dist_supply_atr','dist_demand_atr','vpnode_dist_atr','h4_dist','hd_dist',
       'h1_dist','atr_regime','atr_expand','path_eff','bars_to_8atr','rsi','rsi_low',
       'disp4_atr','h4_eff','hd_eff','h1_eff','vol_low_vs_med','n_demand_near','macro_drop_atr']
CAT = ['macro_bull','macro_bear','h1_trend','h4_trend','hd_trend','in_demand',
       'demand_fresh','vol_climax','killzone']

def wr(sub):
    return (sum(r['win'] for r in sub)/len(sub), len(sub)) if sub else (None,0)

print("=== CATEGORICAL splits ===")
for k in CAT:
    vals = sorted(set(r.get(k) for r in rows if r.get(k) is not None))
    line = f"{k}: "
    for v in vals:
        sub = [r for r in rows if r.get(k)==v]
        w,c = wr(sub)
        line += f"  {v}->WR{w:.3f}(n{c})"
    print(line)

print("\n=== NUMERIC tertile splits (WR low / mid / high tertile) ===")
for k in NUM:
    vals = [r.get(k) for r in rows if r.get(k) is not None]
    if len(vals) < 100:
        continue
    q1 = sorted(vals)[len(vals)//3]
    q2 = sorted(vals)[2*len(vals)//3]
    lo = [r for r in rows if r.get(k) is not None and r[k] <= q1]
    mid= [r for r in rows if r.get(k) is not None and q1 < r[k] <= q2]
    hi = [r for r in rows if r.get(k) is not None and r[k] > q2]
    wl,nl = wr(lo); wm,nm = wr(mid); wh,nh = wr(hi)
    spread = max(wl,wm,wh) - min(wl,wm,wh)
    flag = " <<<" if spread >= 0.05 else ""
    print(f"{k:18s} cut[{q1:.2f},{q2:.2f}] lo{wl:.3f}(n{nl}) mid{wm:.3f}(n{nm}) hi{wh:.3f}(n{nh}) spread{spread:.3f}{flag}")
