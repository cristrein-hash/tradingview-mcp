#!/usr/bin/env python3
"""Extended-family filter probe (reproducible). Agent: extended family.
Loads filter_dataset.jsonl, dedups like harness, scans tail buckets to find
where LOSERS concentrate. KEEP=block danger. Metrics ONLY via filter_harness for final.
This script is exploratory diagnostic; final numbers come from filter_harness.py.
"""
import json, operator as o
from pathlib import Path
import statistics as st
HERE = Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines()]
byblk={}
for c in ROWS: byblk.setdefault(c["block"],[]).append(c)
taken=[]
for blk,cs in byblk.items():
    cs.sort(key=lambda x:x["cj"]); busy=-10**9
    for c in cs:
        if c["cj"]<=busy: continue
        busy=c["exi"]; taken.append(c)

def wr_at(f, op, thr):
    sub=[c for c in taken if c.get(f) is not None and op(c[f],thr)]
    if not sub: return None
    w=sum(c["win"] for c in sub); r=sum(c["R"] for c in sub)
    return (len(sub),round(100*w/len(sub),1),round(r,1))

# The danger (low-WR) tails: path_eff high, macro_retr high, low momentum-extension.
# Also probe DANGER = NOT extended (the trades that AREN'T stretched up = chasing into nothing).
tests=[
 ('path_eff',o.ge,0.7),('path_eff',o.ge,0.75),('path_eff',o.ge,0.85),
 ('macro_retr',o.ge,0.85),('macro_retr',o.ge,0.9),
 ('disp4_atr',o.ge,2.8),('disp4_atr',o.ge,3.0),('disp4_atr',o.ge,3.3),
 ('h4_eff',o.ge,0.55),('h4_eff',o.ge,0.6),
 ('vpnode_dist_atr',o.le,0.5),('vpnode_dist_atr',o.le,1.0),
 ('room_above_atr',o.le,0.05),('room_above_atr',o.le,0.15),('room_above_atr',o.ge,2.0),
 ('rsi',o.le,50),('rsi',o.le,55),
 ('h1_pos',o.le,0.7),('h1_pos',o.le,0.8),
 ('dist_ema_atr',o.le,1.5),('dist_ema_atr',o.le,1.8),
 ('leg_ext_atr',o.le,4.0),('leg_ext_atr',o.le,4.5),
]
print('FEAT op thr -> (n, WR, sumR)  base WR 58.4 / sumR 70.7')
for f,op,thr in tests:
    print(f'{f:16s} {op.__name__} {thr:6}  {wr_at(f,op,thr)}')

# ---- FINAL CANDIDATES (metrics via filter_harness.py, not here) ----
FINAL_KEEP_EXPRS = [
  # C12 best: block on-VP-node (wall) + block rsi<=50 (chasing weakness)
  "((r.get('vpnode_dist_atr') is None) or abs(r['vpnode_dist_atr'])>0.6) and r['rsi']>50",
  # C11 simplest single rule: block sitting on a VP node
  "(r.get('vpnode_dist_atr') is None) or abs(r['vpnode_dist_atr'])>0.6",
  # C1 best DD: block within 1.0 ATR above a node
  "(r.get('vpnode_dist_atr') is None) or r['vpnode_dist_atr']>1.0",
  # C2 clean rsi floor only
  "r['rsi']>50",
  # C8 rsi>55 (slightly more WR, sumR up)
  "r['rsi']>55",
]
