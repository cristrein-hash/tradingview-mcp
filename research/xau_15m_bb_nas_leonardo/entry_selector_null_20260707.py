#!/usr/bin/env python3
"""NULL / winner's-curse do seletor de entry (2026-07-07). O seletor (reclaim_lag<=4 & cascade>=5 ->
hit-3R 66,7%) é vencedor de uma grelha in-sample dentro do markup. Testo se um hit-3R desse nível a
N~33 é batível por acaso: permuto os OUTCOMES do markup, re-corro a MESMA grelha de gates, e vejo a
distribuição do melhor hit-3R (N>=25, todos-anos>=45%). Se o observado > q95 do null -> sinal real.
Também: ablação (cada gate sozinho) + causalidade (reclaim_lag e cascade são known_at).
SANITY_PROBE: null de multiplicidade sobre a MESMA grelha (não single-axis); markup master; outcome
permutado; ablação; causal; validação-não-calibração."""
import json, itertools, bisect
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=json.load(open(HERE/"results"/"entry_engine_master_20260707.json"))
MK=[r for r in rows if r["kind"]=="MARKUP"]
def year(d): return d[:4]
gates={
 "recl_str>=0.3":lambda r:r["recl_str"]>=0.3, "recl_str>=0.6":lambda r:r["recl_str"]>=0.6,
 "reclaim_lag<=4":lambda r:r["reclaim_lag"]<=4, "reclaim_lag<=6":lambda r:r["reclaim_lag"]<=6,
 "choch>=1":lambda r:r["choch_since_lo"]>=1, "cascade>=3":lambda r:r["cascade"]>=3, "cascade>=5":lambda r:r["cascade"]>=5,
 "sweep<=0.1":lambda r:r["sweep"]<=0.1, "drop>=6":lambda r:r["drop"]>=6, "drop<=9":lambda r:r["drop"]<=9,
 "box96<=0.3":lambda r:r["box96"]<=0.3, "rsi_lo<=40":lambda r:(r["rsi_lo"] or 50)<=40, "rsi_above":lambda r:r["rsi_above_ma"]==1,
 "demand_near":lambda r:r["demand_d"]<=0.5,
}
combos=[("solo",n,f) for n,f in gates.items()]+[("pair",f"{a[0]} & {b[0]}",lambda r,a=a,b=b:a[1](r) and b[1](r)) for a,b in itertools.combinations(gates.items(),2)]
def best_hit(universe):
    best=0
    for _,name,fn in combos:
        sel=[r for r in universe if fn(r)]
        if len(sel)<25: continue
        # todos-anos>=45%
        ok=True
        for y in ("2025","2026"):
            sy=[r for r in sel if year(r["d"])==y]
            if len(sy)<8 or sum(r["out"] for r in sy)/len(sy)<0.45: ok=False;break
        if not ok: continue
        h=sum(r["out"] for r in sel)/len(sel); best=max(best,h)
    return best
obs=best_hit(MK)
outs=[r["out"] for r in MK]
# permutação determinística (sem random): rotações do vetor de outcomes
import collections
null=[]
for shift in range(1,len(MK)):
    perm=outs[shift:]+outs[:shift]
    MKp=[{**r,"out":perm[k]} for k,r in enumerate(MK)]
    null.append(best_hit(MKp))
null=[x for x in null if x>0]
null.sort()
q95=null[int(len(null)*0.95)] if null else 0; q50=null[len(null)//2] if null else 0
pval=sum(1 for x in null if x>=obs)/len(null) if null else 1
print(f"markup N{len(MK)} base {sum(outs)/len(outs):.1%}")
print(f"OBSERVADO melhor-da-grelha hit-3R: {obs:.1%}")
print(f"NULL (rotações de outcome, mesma grelha): mediana {q50:.1%} · q95 {q95:.1%} · P(null>=obs) {pval:.3f}  (n_null={len(null)})")
# ablação do vencedor
print("\n=== ablação do vencedor (reclaim_lag<=4 & cascade>=5) ===")
for name,fn in [("vencedor",lambda r:r["reclaim_lag"]<=4 and r["cascade"]>=5),
                ("só reclaim_lag<=4",lambda r:r["reclaim_lag"]<=4),
                ("só cascade>=5",lambda r:r["cascade"]>=5),
                ("markup base",lambda r:True)]:
    sel=[r for r in MK if fn(r)]; h=sum(r["out"] for r in sel)/len(sel)
    print(f"  {name:<22} N{len(sel):<4} hit-3R {h:.1%}")
print("OK")
