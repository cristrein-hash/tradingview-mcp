#!/usr/bin/env python3
"""DIAGNÓSTICO 2 — POSIÇÃO DO FUNDO NA PERNA MACRO (2026-07-05).
O erro visual apontado pelo Cris: entries em pontos altos, descontextualizados das legs macro.
legpos60 (15h) é míope — a perna dele tem DIAS/SEMANAS. Medir nos 60 GT vs null:
  perna macro causal (zigzag r·ATR, r em {6,8,12}): L0 = último pivô LOW confirmado antes de fi
  (known<=fi), H1 = max high de L0 até fi.
  retrace   = (H1 − flush_low)/(H1 − L0)     (0 = topo, 1 = voltou ao pivô, >1 = varreu abaixo)
  travel    = (H1 − L0)/ATR@fi               (tamanho da perna)
  pb_age_h  = horas desde a barra do H1      (duração do pullback)
  d_L0      = (flush_low − L0)/ATR@fi        (distância à origem da perna)
Null: 300 barras aleatórias (mesmo matcher). Distribuições → banda dimensional.
SANITY_PROBE: P1 pivô só usado após confirmação (known_i<=fi assert) · P2 H1 só com barras <=fi ·
P3 null idêntico · P4 amostra impressa."""
import json, bisect, hashlib, random
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

def zigzag_pivots(r):
    piv = []
    d = 0; ehi = elo = 0
    for i in range(1, N):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= r * atr and ehi < i:
            piv.append(("H", ehi, i)); d = -1
            elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= r * atr and elo < i:
            piv.append(("L", elo, i)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    return piv

def measure(rows, piv):
    lows = [(p[2], p[1]) for p in piv if p[0] == "L"]   # (known_i, pivot_i)
    K = [x[0] for x in lows]
    out = []
    for fi, flo in rows:
        j = bisect.bisect_right(K, fi) - 1
        if j < 0:
            out.append(None); continue
        known_i, l0i = lows[j]
        assert known_i <= fi  # P1
        L0 = LO[l0i]
        h1i = max(range(l0i, fi + 1), key=lambda k: HI[k])  # P2
        H1 = HI[h1i]
        if H1 - L0 < 1e-9:
            out.append(None); continue
        a = ATR[fi]
        out.append({"retr": (H1 - flo) / (H1 - L0), "travel": (H1 - L0) / a,
                    "pb_age_h": (fi - h1i) * 0.25, "d_L0": (flo - L0) / a})
    return out

GT_rows = []
for g in GT:
    fi = bisect.bisect_right(TS, g["flush_t"]) - 1
    GT_rows.append((fi, g["flush_low"]))
random.seed(7)
NULL_rows = [(i, LO[i]) for i in random.sample(list(range(3000, N - 100)), 300)]

for r in (6, 8, 12):
    piv = zigzag_pivots(r)
    mg = [x for x in measure(GT_rows, piv) if x]
    mn = [x for x in measure(NULL_rows, piv) if x]
    print(f"\n=== r={r} (pivôs {len(piv)}) · GT {len(mg)} · null {len(mn)} ===")
    for f in ("retr", "travel", "pb_age_h", "d_L0"):
        a = sorted(x[f] for x in mg); b = sorted(x[f] for x in mn)
        qa = lambda v, q: v[int(q * (len(v) - 1))]
        print(f"  {f:<9} GT q25/med/q75 {qa(a,.25):>6.2f}/{qa(a,.5):>6.2f}/{qa(a,.75):>6.2f}"
              f"   null {qa(b,.25):>6.2f}/{qa(b,.5):>6.2f}/{qa(b,.75):>6.2f}")
    # bandas candidatas: retr em [0.35,1.1] & travel>=10 — fração GT vs null (mapa, não teste)
    for rlo, rhi, tmin in ((0.35, 1.10, 10), (0.5, 1.2, 8), (0.35, 1.10, 0)):
        fg = sum(1 for x in mg if rlo <= x["retr"] <= rhi and x["travel"] >= tmin) / len(mg)
        fn = sum(1 for x in mn if rlo <= x["retr"] <= rhi and x["travel"] >= tmin) / len(mn)
        print(f"  banda retr[{rlo},{rhi}] travel>={tmin}: GT {100*fg:.0f}% null {100*fn:.0f}% lift {fg/fn if fn else 0:.2f}")
print("\nP4 amostra 6 GT (r=8):")
piv = zigzag_pivots(8)
for (fi, flo), x in list(zip(GT_rows, measure(GT_rows, piv)))[:6]:
    if x:
        print(f"  {dt.datetime.utcfromtimestamp(TS[fi]).strftime('%Y-%m-%d %H:%M')} retr {x['retr']:.2f} "
              f"travel {x['travel']:.1f} pb_age {x['pb_age_h']:.0f}h d_L0 {x['d_L0']:+.1f}")
