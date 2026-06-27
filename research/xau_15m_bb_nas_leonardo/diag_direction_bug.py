#!/usr/bin/env python3
"""Diagnostico do BUG DIRECIONAL (Cris 2026-06-27 via prints):
estrategia atual = LONG-only de fractal-low; alguns disparam em TOPO/BEAR (deveriam ser SHORT).
Para cada um dos 256 trades A2: regime macro 4H as-of entry + reversao M8 mais proxima (kind BOT/TOP) + dist.
Quantifica: quantos longs estao em BEAR e quantos ancoram perto de um TOPO M8 (mal-direcionados). RAW-causal."""
import json, csv, bisect
from pathlib import Path
HERE = Path(__file__).parent

# trades
TR = []
with open(HERE/"strategy_5atr_a2_trades.csv") as f:
    for r in csv.DictReader(f):
        TR.append(dict(num=int(r["num"]), t=int(r["entry_t"]), entry=float(r["entry"]),
                       R=float(r["R"]), win=int(r["win"])))

# M8 reversals
M8 = []
with open(HERE/"true_reversals_M8.csv") as f:
    for r in csv.DictReader(f):
        M8.append(dict(t=int(r["t"]), kind=r["kind"], price=float(r["price"])))
M8.sort(key=lambda x: x["t"])
M8T = [x["t"] for x in M8]

# macro regime 4h (as-of: usa barra 4H cujo t_end <= entry, ie ja fechada)
MR = json.load(open(HERE/"macro_regime_4h.json"))["bars_4h"]
MR.sort(key=lambda x: x["t_end"])
MRend = [x["t_end"] for x in MR]
def regime_asof(t):
    k = bisect.bisect_right(MRend, t) - 1
    return MR[k]["macro"] if k >= 0 else "NA"

BAR = 900
def nearest_m8(t):
    """reversao M8 mais proxima em tempo; retorna (kind, dist_bars_signed, price)."""
    k = bisect.bisect_left(M8T, t)
    cands = []
    for j in (k-1, k):
        if 0 <= j < len(M8):
            cands.append(M8[j])
    if not cands: return None, None, None
    best = min(cands, key=lambda x: abs(x["t"]-t))
    return best["kind"], (t-best["t"])//BAR, best["price"]

rows = []
for tr in TR:
    reg = regime_asof(tr["t"])
    kind, db, mp = nearest_m8(tr["t"])
    rows.append({**tr, "reg": reg, "m8kind": kind, "m8db": db})

n = len(rows)
def grp(pred):
    g = [r for r in rows if pred(r)]
    if not g: return (0,0,0.0)
    w = sum(1 for r in g if r["win"])
    return (len(g), w, sum(r["R"] for r in g))

print(f"TOTAL trades (todos LONG): {n}")
print()
print("--- por REGIME macro 4H as-of entry ---")
for reg in ("BULL","NEUTRAL","BEAR"):
    cnt,w,sm = grp(lambda r,reg=reg: r["reg"]==reg)
    if cnt: print(f"  {reg:<8} n={cnt:>3}  WR={100*w/cnt:4.1f}%  sumR={sm:+6.1f}  avgR={sm/cnt:+.2f}")
print()
print("--- reversao M8 mais proxima do entry (qualquer dist) ---")
for k in ("BOT","TOP"):
    cnt,w,sm = grp(lambda r,k=k: r["m8kind"]==k)
    if cnt: print(f"  perto de {k}: n={cnt:>3}  WR={100*w/cnt:4.1f}%  sumR={sm:+6.1f}  avgR={sm/cnt:+.2f}")
print()
print("--- reversao M8 proxima E dentro de +-8 barras (ancoragem real) ---")
for k in ("BOT","TOP"):
    cnt,w,sm = grp(lambda r,k=k: r["m8kind"]==k and r["m8db"] is not None and abs(r["m8db"])<=8)
    if cnt: print(f"  ancora {k} (<=8b): n={cnt:>3}  WR={100*w/cnt:4.1f}%  sumR={sm:+6.1f}  avgR={sm/cnt:+.2f}")
print()
print("--- INTERSECAO: LONG em BEAR (candidatos a estar errados / deveriam ser SHORT) ---")
cnt,w,sm = grp(lambda r: r["reg"]=="BEAR")
print(f"  LONG em BEAR: n={cnt}  WR={100*w/cnt:.1f}%  sumR={sm:+.1f}" if cnt else "  nenhum")
cnt,w,sm = grp(lambda r: r["reg"]=="BEAR" and r["m8kind"]=="TOP" and r["m8db"] is not None and abs(r["m8db"])<=8)
print(f"  LONG em BEAR ancorado a TOPO M8(<=8b): n={cnt}  WR={100*w/cnt if cnt else 0:.1f}%  sumR={sm:+.1f}")
