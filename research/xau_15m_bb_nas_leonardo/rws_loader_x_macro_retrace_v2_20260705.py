#!/usr/bin/env python3
"""CRUZAMENTO loader × retração — v2 no DOMÍNIO SELADO do RWS (2026-07-05).
Correção da v1: a config selada N54 = rws15m sobre NB (g_v5h != BEAR & g_knife == 0); a v1 rodou
no universo inteiro. Mesmo ledger, domínio certo:
  D0' retr dos 54 selados · X1' split 54 dentro/fora banda[0,5-1,3]
  X2' NB & loader>=2 & banda · X3' X2'+A6+A7 · X4' X3'&reclaim>=1,5
SANITY_PROBE: P1 mesmo zigzag causal · P2 banda fixa do DA (não recalibrada) · P3 GT só métrica."""
import json, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "rws_loader_x_macro_retrace_20260705.py").read_text().split("# D0: onde os 54")[0])
def null_p_ref(rows, ref, seed):
    H0 = [1 if R3[r["cj_t"]]["R3"] >= 3 else 0 for r in ref]
    obs = sum(1 for r in rows if R3[r["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
NB = [r for r in UNIV if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
RWS54 = [r for r in NB if rws15m(r)]
rv = sorted(r["_retr"] for r in RWS54 if r["_retr"] is not None)
print(f"D0': RWS-{len(RWS54)} selado · retr q25/med/q75 = {rv[len(rv)//4]:.2f}/{rv[len(rv)//2]:.2f}/{rv[3*len(rv)//4]:.2f}"
      f" · na banda: {sum(1 for r in RWS54 if IN(r))}/{len(RWS54)}")
panel2(NB, "NB (domínio selado)")
panel2([r for r in RWS54 if IN(r)], "X1' RWS54 ∩ banda")
panel2([r for r in RWS54 if not IN(r)], "X1' RWS54 fora banda")
X2 = [r for r in NB if FT.get(r["cj_t"], {}).get("buy_recent", 0) >= 2 and IN(r)]
p2 = panel2(X2, "X2' NB loader>=2 & banda")
if X2:
    print(f"      P(null vs NB)={null_p_ref(X2, NB, 71):.4f}")
def deep_ok(r):
    f = FT.get(r["cj_t"], {})
    if not f or f.get("buy_recent", 0) < 2 or not IN(r):
        return False
    if f.get("burst_recent_vs_older", 0) >= 3 and f.get("large_buy_win8") == 0 and f.get("nas_last_short_recent") == 0:
        return False
    if f.get("rsi_bear_div_20", 0) >= 2:
        return False
    return True
X3 = [r for r in NB if deep_ok(r)]
p3 = panel2(X3, "X3' RWS-DEEP em NB")
if X3:
    print(f"      P(null vs NB)={null_p_ref(X3, NB, 72):.4f}")
X4 = [r for r in X3 if fv(r, "reclaim_atr") >= 1.5]
p4 = panel2(X4, "X4' X3' & reclaim>=1,5")
if X4:
    q50, q95, pgt5 = streak_dist(X4, 75)
    print(f"      P(null vs NB)={null_p_ref(X4, NB, 74):.4f} · streak q50 {q50} q95 {q95} P(>5) {pgt5:.2f}")
json.dump({"X2p": p2, "X3p": p3, "X4p": p4},
          open(HERE / "results" / "rws_loader_x_macro_retrace_v2_20260705.json", "w"), indent=1)
print("OK → results/rws_loader_x_macro_retrace_v2_20260705.json")
