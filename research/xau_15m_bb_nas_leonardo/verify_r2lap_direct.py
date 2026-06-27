#!/usr/bin/env python3
"""Re-verificação DIRETA das lapidações R_A/R_B/R_C do R2 sobre dataset_r2refine.jsonl (só r2_keep==1).
WR antes/depois total + por ANO (base-do-ano) + por BLOCO + winners mantidos + max-LOSING-streak. RAW-causal."""
import json
from pathlib import Path
HERE=Path(__file__).parent
rows=[json.loads(l) for l in (HERE/"dataset_r2refine.jsonl").read_text().splitlines() if json.loads(l)["r2_keep"]==1]
rows.sort(key=lambda r:r["low_t"])
def los_streak(rs):
    mx=cur=0
    for r in sorted(rs,key=lambda x:x["low_t"]):
        if r["win"]==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx
def R_A(r): return (r["buy_sell_ratio4"]>7 and r["low_vol_rel"]>1.37) or (r["low_vol_rel"]>1.37 and r["sell_decel"]==0) or (r["regime_age_h"]<=25.2 and r["sell_skew_mig"]>0)
def R_B(r): return (r["absorption"]==1 and r["sell_decel"]==0) or (r["buy_sell_ratio4"]>7 and r["low_vol_rel"]>1.37) or (r["regime_age_h"]<=25.2 and r["sell_skew_mig"]>0)
def R_C(r): return (r["absorption"]==1 and r["sell_decel"]==0) or (r["low_vol_rel"]>1.37 and r["sell_decel"]==0) or (r["buy_L_recent"]==1 and r["sell_skew_mig"]>0)
def wr(v): return 100*sum(r["win"] for r in v)/len(v) if v else 0
base_wr=wr(rows); base_streak=los_streak(rows)
print(f"BASE R2-kept: n={len(rows)} WR={base_wr:.1f}% max-losing-streak={base_streak}")
for name,cf in [("R_A",R_A),("R_B",R_B),("R_C",R_C)]:
    keep=[r for r in rows if not cf(r)]; cut=[r for r in rows if cf(r)]
    wkept=100*sum(r["win"] for r in keep)/max(1,sum(r["win"] for r in rows))
    lcut=100*sum(1 for r in cut if r["win"]==0)/max(1,sum(1 for r in rows if r["win"]==0))
    print(f"\n{name}: DEPOIS n={len(keep)} WR={wr(keep):.1f}% (base {base_wr:.1f}) streak={los_streak(keep)} (base {base_streak}) winners_mantidos={wkept:.0f}% losers_cortados={lcut:.0f}% cut_WR={wr(cut):.0f}%")
    nbad_y=0
    for y in (2024,2025,2026):
        ky=[r for r in keep if r["yr"]==y]; by=[r for r in rows if r["yr"]==y]
        if ky and by:
            bad=wr(ky)<wr(by); nbad_y+=bad
            print(f"   {y}: {wr(ky):.1f}% vs base-ano {wr(by):.1f}% {'PIOR' if bad else 'ok'}")
    blocks=sorted(set(r["block"] for r in rows)); nbad_b=0
    for b in blocks:
        kb=[r for r in keep if r["block"]==b]; bb=[r for r in rows if r["block"]==b]
        if kb and bb and wr(kb)<wr(bb)-0.01: nbad_b+=1
    print(f"   anos piores: {nbad_y}/3 | blocos piores: {nbad_b}/{len(blocks)}")
