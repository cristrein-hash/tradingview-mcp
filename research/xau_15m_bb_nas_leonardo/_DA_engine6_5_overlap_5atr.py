#!/usr/bin/env python3
"""DA ENGINE6 ATTACK #5 — OVERLAP with PRE-APPROVED 5ATR (strategy_5atr_regime170_trades.csv).
reclaim>=4 confirmation family vs the 5ATR-confirm strategy. Match by entry timestamp proximity.
5ATR strategy entry_t is the confirm-bar time. reclaim_atr cand cj_t is the confirm-bar time.
Count overlap (same/near entry). Novel vs redundant?"""
import json,csv
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
# 5atr trades
A5=[]
with open(HERE/"strategy_5atr_regime170_trades.csv") as fh:
    for row in csv.DictReader(fh): A5.append(int(row["entry_t"]))
A5set=set(A5)
print("="*78); print("ATTACK #5 — OVERLAP vs PRE-APPROVED 5ATR (N=170)"); print("="*78)
BAR=900
for thr in (4.0,3.5):
    sel=[r for r in ROWS if f(r,"reclaim_atr",0)>=thr]
    cjs=[int(r["cj_t"]) for r in sel]
    exact=sum(1 for t in cjs if t in A5set)
    near=sum(1 for t in cjs if any(abs(t-a)<=3*BAR for a in A5set))
    print(f"--- reclaim>={thr} (N={len(sel)}) vs 5ATR(170) ---")
    print(f"   exact entry-t overlap: {exact}/{len(sel)} = {100*exact/len(sel):.0f}%")
    print(f"   within +-3 bars overlap: {near}/{len(sel)} = {100*near/len(sel):.0f}%")
    # reverse: how many of the 170 5atr trades are captured by reclaim>=thr cands?
    rev=sum(1 for a in A5 if any(abs(a-t)<=3*BAR for t in cjs))
    print(f"   of 170 5ATR trades, captured by this cand set (+-3bar): {rev}/170 = {100*rev/170:.0f}%")
    print()
# what is the 5atr strategy mechanically? note from build_5atr / build_symmetric_5atr
print("NOTE: pre-approved 5ATR = 5-ATR-confirm bottom entry + regime gate (N=170, WR64%, +66R, DD-3).")
print("      reclaim>=4 = same N-ATR-confirm family (4 ATR reclaim threshold) WITHOUT the regime gate")
print("      and with let-run exit. Overlap quantifies redundancy.")
