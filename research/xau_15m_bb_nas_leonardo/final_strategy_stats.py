#!/usr/bin/env python3
"""Estatísticas completas do stack PRÉ-APROVADO: 8ATR confirm + R2 + R_B lapidado (LONG nos fundos).
N, WR, avgR, sumR, maxDD(R), max-losing-streak, freq/sem, por ano. Sobre dataset_r2refine.jsonl (R=let-run do 8ATR)."""
import json,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
rows=[json.loads(l) for l in (HERE/"dataset_r2refine.jsonl").read_text().splitlines()]
def R_B(r): return (r["absorption"]==1 and r["sell_decel"]==0) or (r["buy_sell_ratio4"]>7 and r["low_vol_rel"]>1.37) or (r["regime_age_h"]<=25.2 and r["sell_skew_mig"]>0)
final=[r for r in rows if r["r2_keep"]==1 and not R_B(r)]
final.sort(key=lambda r:r["low_t"])
def stats(v,lab):
    n=len(v); w=sum(1 for r in v if r["win"]); sm=sum(r["R"] for r in v)
    eq=pk=dd=0; stk=mstk=0
    for r in v:
        eq+=r["R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
        if r["R"]<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    span=(v[-1]["low_t"]-v[0]["low_t"])/(7*86400) if len(v)>1 else 1
    run=sum(1 for r in v if r["R"]>=5)
    print(f"{lab}: N={n} WR={100*w/n:.1f}% avgR={sm/n:+.2f} sumR={sm:+.0f} maxDD={dd:.0f}R streakL={mstk} runners(>=5R)={run} freq={n/span:.1f}/sem")
stats(final,"STACK FINAL (8ATR+R2+R_B)")
for y in (2024,2025,2026):
    yv=[r for r in final if r["yr"]==y]
    if yv: stats(yv,f"  {y}")
# comparativo
print("\ncomparativo de N por estágio:")
print(f"  8ATR confirm (todos): N={len(rows)}")
print(f"  +R2: N={sum(1 for r in rows if r['r2_keep']==1)}")
print(f"  +R_B (final): N={len(final)}")
