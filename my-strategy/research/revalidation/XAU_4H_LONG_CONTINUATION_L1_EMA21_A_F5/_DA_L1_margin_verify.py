#!/usr/bin/env python3
"""SANITY_PROBE — detalha as 3 rules candidatas p/ aumentar margem: lista trades cortados + folga ao winner mais próximo.
(A) dist_poc<=0.334 midpoint (8L, fina); (B) atr_ratio>=thr (2L, robusta); (C) sell10>=thr (1L, mais robusta).
Confirma 0 winners e mostra o trade-off losers↔margem. n=34 calibração."""
import json, statistics as st
from pathlib import Path
T = json.load(open(Path(__file__).parent / "l1_contrastive_features.json"))
for t in T:
    t["win"] = t["win"] in (True, "True"); t["runner"] = t["runner"] in (True, "True")
def fv(t, f):
    try: return float(t.get(f))
    except Exception: return None
def report(f, op, thr, name):
    cut = [t for t in T if fv(t, f) is not None and (fv(t, f) <= thr if op == "<=" else fv(t, f) >= thr)]
    lc = [t for t in cut if not t["win"]]; wc = [t for t in cut if t["win"]]
    others_w = [fv(t, f) for t in T if t["win"] and fv(t, f) is not None]
    # winner mais próximo do limite
    if op == "<=": nearest = min((w for w in others_w if w > thr), default=None)
    else: nearest = max((w for w in others_w if w < thr), default=None)
    sd = st.pstdev([fv(t, f) for t in T if fv(t, f) is not None]) or 1e-9
    gap = abs(nearest - thr) if nearest is not None else None
    print(f"\n[{name}] {f} {op} {thr:.4g}")
    print(f"  corta {len(lc)} losers, {len(wc)} winners | runners cortados: {sum(1 for t in lc if t['runner'])}")
    print(f"  datas losers: {[t['ts'][:10] for t in sorted(lc, key=lambda x: x['ts'])]}")
    if nearest is not None:
        print(f"  winner mais próximo: {f}={nearest:.4g} | folga={gap:.4g} ({gap/sd:.2f} std)")
report("dist_poc", "<=", 0.334, "A  midpoint 8-cut (fino)")
report("atr_ratio", ">=", 0.009, "B  vol-alta 2-cut (robusto)")
report("sell10", ">=", 5, "C  cluster SELL 1-cut (mais robusto)")
# UNIÃO A∪B∪C (cada um 0-winner => união 0-winner) — total losers cortados
def hit(t):
    return (fv(t,"dist_poc") is not None and fv(t,"dist_poc")<=0.334) or (fv(t,"atr_ratio") is not None and fv(t,"atr_ratio")>=0.009) or (fv(t,"sell10") is not None and fv(t,"sell10")>=5)
U = [t for t in T if hit(t)]; ul=[t for t in U if not t["win"]]; uw=[t for t in U if t["win"]]
kept=[t for t in T if not hit(t)]
wr=100*sum(1 for t in kept if t["win"])/len(kept) if kept else 0
print(f"\n[UNIÃO A∪B∪C] corta {len(ul)} losers {len(uw)} winners | mantém {len(kept)}: WR {wr:.0f}%")
print("  (união de cortes 0-winner continua 0-winner; soma losers de pockets distintos)")
print("\nTRADE-OFF: + losers = - margem. n=34 calibração; pocket 1-2 trades com std alto = isolamento de outlier, não regra certificada.")
