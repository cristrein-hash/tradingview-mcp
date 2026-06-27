#!/usr/bin/env python3
"""Diagnostico do CAMINHO dos 25 runners do Cris (Rpot>3): por que nenhum trail os cavalga? Cris 2026-06-27.
Por runner: o preco alcanca cris_exit dentro de HMAX? em quantas barras? pico MFE_R? e o RECUO MAIS FUNDO
(em R, retracao do pico) ANTES de alcancar cris_exit -> esse recuo e' o que tira qualquer trail.
RAW-causal. So mede."""
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170={int(r["num"]):r for r in csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv"))}
def fnum(x): return float(x) if x not in (None,"","None") else None

rows=[]
for num,gt in GT.items():
    rp=fnum(gt["cris_Rpot"])
    if not rp or rp<=3: continue
    tr=T170[num]; t=int(tr["entry_t"]); fd=FD[t]
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=fd["cj"]
    entry=fnum(gt["entry"]); sl=float(tr["sl"]); risk=entry-sl; ce=fnum(gt["cris_exit"])
    end=min(cj+HMAX,len(s)-1)
    reach=None; runhi=entry; maxR=0; deepest=0; bars_reach=None
    for k in range(cj+1,end+1):
        b=s[k]
        runhi=max(runhi,b["h"]); maxR=max(maxR,(runhi-entry)/risk)
        # recuo do pico (giveback) em R, antes de alcancar cris_exit
        if reach is None and runhi>entry+risk:    # so conta apos +1R
            gb=(runhi-b["l"])/risk
            deepest=max(deepest,gb)
        if reach is None and b["h"]>=ce:
            reach=True; bars_reach=k-cj
    rows.append({"num":num,"rp":round(rp,1),"reached":bool(reach),"bars":bars_reach,
                 "maxR":round(maxR,1),"deepest_giveback_R":round(deepest,1)})

rows.sort(key=lambda x:-x["rp"])
print(f"=== 25 runners do Cris: caminho ===")
print(f"{'#':>4}{'Rpot':>6}{'reach':>6}{'bars':>6}{'maxR':>6}{'maxGiveback_R':>14}")
for r in rows:
    print(f"{r['num']:>4}{r['rp']:>6}{('Y' if r['reached'] else 'N'):>6}{str(r['bars']):>6}{r['maxR']:>6}{r['deepest_giveback_R']:>14}")
reached=[r for r in rows if r["reached"]]
print(f"\nalcancaram cris_exit dentro de HMAX: {len(reached)}/{len(rows)}")
print(f"mediana barras ate alcancar: {st.median([r['bars'] for r in reached if r['bars']]):.0f}")
print(f"mediana do RECUO MAIS FUNDO (do pico, em R) antes de alcancar: {st.median([r['deepest_giveback_R'] for r in rows]):.1f}R")
print(f"runners com recuo >1.5R (qualquer trail razoavel sai): {sum(1 for r in rows if r['deepest_giveback_R']>1.5)}/{len(rows)}")
print(f"runners com recuo >3R: {sum(1 for r in rows if r['deepest_giveback_R']>3)}/{len(rows)}")
