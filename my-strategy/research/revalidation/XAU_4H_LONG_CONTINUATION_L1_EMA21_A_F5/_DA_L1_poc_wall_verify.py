#!/usr/bin/env python3
"""SANITY_PROBE — verifica o candidato com lastro causal (Auction value-area): dist_poc<=0.35 ATR = compra colada no
POC sem aceitação acima do valor (WALL). Reporta contraste above_poc winner vs loser, e WR/sumR do set mantido após
cortes estruturais. Lê l1_contrastive_features.json (gerado pelo extrator). Verified 2026-06-25."""
import json, statistics as st
from pathlib import Path
T = json.load(open(Path(__file__).parent / "l1_contrastive_features.json"))
for t in T:
    for k in ("dist_poc", "R", "mfe", "rng40", "vol_ratio"):
        t[k] = float(t[k]) if t[k] not in (None, "None", "") else None
    t["win"] = (t["win"] in (True, "True")); t["runner"] = (t["runner"] in (True, "True"))
    t["above_poc"] = int(t["above_poc"]); t["below_val"] = int(t["below_val"]); t["above_vah"] = int(t["above_vah"])
nW = sum(1 for t in T if t["win"]); nL = sum(1 for t in T if not t["win"])
print(f"base 34: W={nW} L={nL} WR={100*nW/34:.0f}% sumR={sum(t['R'] for t in T):+.1f}\n")
# contraste value-area
print("=== contraste value-area (volume) winner vs loser ===")
for f in ("above_poc", "above_vah", "below_val"):
    w = sum(1 for t in T if t["win"] and t[f]); wl = sum(1 for t in T if not t["win"] and t[f])
    print(f"  {f:>10}=1 : winners {w}/{nW} ({100*w/nW:.0f}%) | losers {wl}/{nL} ({100*wl/nL:.0f}%)")
dp = [t["dist_poc"] for t in T if t["dist_poc"] is not None]
print(f"\n  dist_poc med winner={st.median([t['dist_poc'] for t in T if t['win'] and t['dist_poc'] is not None]):.2f}"
      f" | loser={st.median([t['dist_poc'] for t in T if not t['win'] and t['dist_poc'] is not None]):.2f}")
# aplicar cortes estruturais e medir set mantido
def apply(cond, name):
    cut = [t for t in T if cond(t)]; kept = [t for t in T if not cond(t)]
    lc = sum(1 for t in cut if not t["win"]); wc = sum(1 for t in cut if t["win"]); rc = sum(1 for t in cut if t["runner"])
    wr = 100 * sum(1 for t in kept if t["win"]) / len(kept) if kept else 0; sr = sum(t["R"] for t in kept)
    print(f"  {name:>34} | corta {len(cut):>2} ({lc}L/{wc}W/{rc}run) | mantém {len(kept)}: WR {wr:.0f}% sumR {sr:+.1f}")
print("\n=== cortes estruturais (corta = remove) — RESTRIÇÃO: 0 winner ===")
apply(lambda t: t["dist_poc"] is not None and t["dist_poc"] <= 0.354, "dist_poc<=0.35 (compra no POC=WALL)")
apply(lambda t: t["above_poc"] == 0, "NÃO acima do POC")
apply(lambda t: t["below_val"] == 1, "abaixo do VAL (fora do valor)")
apply(lambda t: t["dist_poc"] is not None and t["dist_poc"] <= 0.354 and t["vol_ratio"] is not None and t["vol_ratio"] >= 0.141, "dist_poc<=0.35 AND vol_ratio>=0.14")
print("\nIn-sample n=34. Null de permutação (extrator) P≈0.05 — carregar status.")
