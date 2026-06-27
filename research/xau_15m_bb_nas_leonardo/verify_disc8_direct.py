#!/usr/bin/env python3
"""Re-verificação DIRETA dos discriminadores 8ATR R1/R2/R4 (o workflow deu 0 survivors mas synth disse 3 — resolvo aqui).
Para cada regra (cut-quando): WR antes/depois total + por ANO + por BLOCO + max-losing-streak + winners mantidos. RAW-causal."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
rows=[json.loads(l) for l in (HERE/"dataset_8atr.jsonl").read_text().splitlines()]
rows.sort(key=lambda r:r["low_t"])
base_wr=100*sum(r["win"] for r in rows)/len(rows)
def streak(rs):
    mx=cur=0
    for r in sorted(rs,key=lambda x:x["low_t"]):
        if r["win"]==0: cur+=1; mx=max(mx,cur)
        else: cur=0
    return mx
def g(r,k):
    v=r.get(k); return v
def cut_R1(r): return (g(r,"h1_trend") is not None and g(r,"h1_trend")<1) and (g(r,"h4_eff") is not None and g(r,"h4_eff")<0.25)
def cut_R2(r): return (g(r,"h1_eff") is not None and g(r,"h1_eff")<0.20) and (g(r,"h4_pos") is not None and g(r,"h4_pos")<1.02)
def cut_R4(r): return (g(r,"h1_pos") is not None and g(r,"h1_pos")<1.01) and (g(r,"macro_retr") is not None and g(r,"macro_retr")<1.17)
def rep(cutf,name):
    keep=[r for r in rows if not cutf(r)]; cut=[r for r in rows if cutf(r)]
    if not keep: print(f"{name}: keep vazio"); return
    wr=100*sum(r["win"] for r in keep)/len(keep)
    wkept=100*sum(r["win"] for r in keep)/max(1,sum(r["win"] for r in rows))
    lcut=100*sum(1 for r in cut if r["win"]==0)/max(1,sum(1 for r in rows if r["win"]==0))
    print(f"\n{name}: cut quando condição. base WR={base_wr:.1f}% streak={streak(rows)} n={len(rows)}")
    print(f"  DEPOIS: n={len(keep)} WR={wr:.1f}% streak={streak(keep)} winners_mantidos={wkept:.0f}% losers_cortados={lcut:.0f}%")
    print("  por ANO (WR depois | base do ano):")
    for y in (2024,2025,2026):
        ky=[r for r in keep if r["yr"]==y]; by=[r for r in rows if r["yr"]==y]
        if ky and by: print(f"    {y}: {100*sum(r['win'] for r in ky)/len(ky):.1f}% | base {100*sum(r['win'] for r in by)/len(by):.1f}%  {'PIOR' if 100*sum(r['win'] for r in ky)/len(ky) < 100*sum(r['win'] for r in by)/len(by) else 'ok'}")
    print("  por BLOCO (WR depois vs base do bloco):")
    blocks=sorted(set(r["block"] for r in rows)); nbad=0
    for b in blocks:
        kb=[r for r in keep if r["block"]==b]; bb=[r for r in rows if r["block"]==b]
        if kb and bb:
            wd=100*sum(r['win'] for r in kb)/len(kb); wb=100*sum(r['win'] for r in bb)/len(bb)
            bad=wd<wb-0.01; nbad+=bad
            print(f"    {b}: {wd:.0f}% vs {wb:.0f}% {'PIOR' if bad else ''}")
    print(f"  blocos que PIORAM: {nbad}/{len(blocks)}")
for cf,nm in [(cut_R1,"R1 (h1_trend<1 & h4_eff<0.25)"),(cut_R2,"R2 (h1_eff<0.20 & h4_pos<1.02)"),(cut_R4,"R4 (h1_pos<1.01 & macro_retr<1.17)")]:
    rep(cf,nm)
