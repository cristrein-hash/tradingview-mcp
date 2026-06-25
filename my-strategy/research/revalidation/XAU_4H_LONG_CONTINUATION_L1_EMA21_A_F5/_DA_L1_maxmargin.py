#!/usr/bin/env python3
"""SANITY_PROBE — busca MAX-MARGEM: p/ cada feature RAW, acha o bolso (cauda) que contém SÓ losers e mede a folga até o
winner mais próximo, normalizada por desvio-padrão da feature (gap_std) p/ comparar entre features. Também testa
2-combos (AND) que ALARGAM a folga. Objetivo: cortar >=1 loser com a MAIOR distância robusta de qualquer winner,
0 winners. n=34 calibração. Multi-fatorial. Verified 2026-06-25."""
import json, itertools, statistics as st
from pathlib import Path
T = json.load(open(Path(__file__).parent / "l1_contrastive_features.json"))
for t in T:
    t["win"] = t["win"] in (True, "True"); t["runner"] = t["runner"] in (True, "True")
NUM = ["vol_ratio", "vol_spike", "buy10", "sell10", "sell_l10", "buy_l10", "sell_now", "dist_poc", "weekly", "cascade",
       "rng10", "rng20", "rng40", "consec_up", "consec_dn", "ext_atr", "dist_sup", "dist_dem", "n_sup", "n_dem",
       "ret5", "ext_ema", "rsi_vs_ma", "atr_ratio", "rsi"]
def val(t, f):
    v = t.get(f)
    try: return float(v)
    except Exception: return None
W = [t for t in T if t["win"]]; Lo = [t for t in T if not t["win"]]
def margin_tail(f, side):
    """maior cauda pura-loser do lado 'low'/'high'; retorna (n_losers, gap_ate_winner, thr_midpoint)."""
    pts = [(val(t, f), t["win"]) for t in T if val(t, f) is not None]
    if len(pts) < 4: return None
    pts.sort(key=lambda x: x[0], reverse=(side == "high"))
    n = 0; last_loser = None
    for v, w in pts:
        if w: break       # parou no 1o winner
        n += 1; last_loser = v
    if n == 0: return None
    first_winner = next((v for v, w in pts if w), None)
    if first_winner is None: return None
    sd = st.pstdev([p[0] for p in pts]) or 1e-9
    gap = abs(first_winner - last_loser); thr = (first_winner + last_loser) / 2
    return dict(f=f, side=side, n=n, gap=gap, gap_std=gap / sd, thr=thr, last_loser=last_loser, first_winner=first_winner)
res = []
for f in NUM:
    for side in ("low", "high"):
        m = margin_tail(f, side)
        if m and m["n"] >= 1: res.append(m)
res.sort(key=lambda m: -m["gap_std"])
print("=== SINGLE-feature max-margem (bolso só-loser, folga ao winner em unidades de std) ===")
print(f"{'feature':>10} {'lado':>4} {'nL':>3} {'gap':>8} {'gap_std':>8} {'thr_mid':>9}")
for m in res[:12]:
    print(f"{m['f']:>10} {m['side']:>4} {m['n']:>3} {m['gap']:>8.3f} {m['gap_std']:>8.2f} {m['thr']:>9.3f}")
# dist_poc otimizado ao midpoint
dp = next((m for m in res if m["f"] == "dist_poc" and m["side"] == "low"), None)
if dp:
    print(f"\n  dist_poc midpoint: thr={dp['thr']:.3f} corta {dp['n']} losers, folga ao winner +{dp['first_winner']-dp['thr']:.3f} ATR (vs +0.019 no thr antigo 0.354)")
# 2-combos que ALARGAM: para cada par, o bolso (ambos no lado pure-loser) — mede menor gap_std entre as 2 dims
print("\n=== 2-COMBOS que aumentam a folga (AND de duas caudas só-loser) ===")
combos = []
singles = {(m["f"], m["side"]): m for m in res}
for (f1, s1), m1 in singles.items():
    for (f2, s2), m2 in singles.items():
        if f1 >= f2: continue
        def inside(t, m):
            v = val(t, m["f"]);
            return v is not None and (v <= m["thr"] if m["side"] == "low" else v >= m["thr"])
        cut = [t for t in T if inside(t, m1) and inside(t, m2)]
        lc = sum(1 for t in cut if not t["win"]); wc = sum(1 for t in cut if t["win"])
        if wc == 0 and lc >= 2:
            # folga combinada = min das duas gap_std individuais (aprox conservadora)
            combos.append((f"{m1['f']}{'<=' if s1=='low' else '>='}{m1['thr']:.3g} AND {m2['f']}{'<=' if s2=='low' else '>='}{m2['thr']:.3g}", lc, min(m1["gap_std"], m2["gap_std"]), max(m1["gap_std"], m2["gap_std"])))
combos = sorted({c[0]: c for c in combos}.values(), key=lambda c: (-c[2], -c[1]))
for d, lc, gmin, gmax in combos[:8]:
    print(f"  corta {lc}L 0W | folga_min={gmin:.2f}std folga_max={gmax:.2f}std : {d}")
if not combos: print("  (nenhum 2-combo 0-winner com >=2 losers)")
print("\nn=34 calibração — folga em std compara robustez; gap_std alto = bolso mais separado dos winners.")
