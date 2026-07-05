#!/usr/bin/env python3
"""GATE DE RETRAÇÃO MACRO — do diagnóstico 2 à entry (2026-07-05).
Diagnóstico: fundos GT = retração PROFUNDA da última perna macro (retr med 0,56-0,74 vs null
0,26) + pullback envelhecido + volta à origem (d_L0 2 ATR vs 6,7 em r=6).
LEDGER (declarado, 8 looks, r em {6,8}):
  G1 retr in [0.5, 1.3]
  G2 G1 & pb_age_h >= 8
  G3 G1 & d_L0 <= 4
  G4 G3 & h1_trend==1
Painel completo + recall estrito 60 + null 4000× vs universo. Nota de método: retr medida com
flush_low do candidato e H1 até cj (reclaim curto vs perna macro — viés pequeno, declarado).
SANITY_PROBE: P1 pivô confirmado antes de cj (assert) · P2 null mesmo universo · P3 GT nunca é
feature (banda veio do diag, universo avaliado por outcome apenas agora)."""
import json, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
GT_60 = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
GT_ALL = [(g["flush_t"], g["flush_low"]) for g in GT_60]
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]

def zigzag_low_pivots(r):
    lows = []
    d = 0; ehi = elo = 0
    for i in range(1, N):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= r * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= r * atr and elo < i:
            lows.append((i, elo)); d = 1  # known_i, pivot_i
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    return lows

UNIV = [u for u in U if u["cj_t"] in R3]
def annotate(r):
    lows = zigzag_low_pivots(r)
    K = [x[0] for x in lows]
    for u in UNIV:
        fi = bisect.bisect_right(TS, u["cj_t"]) - 1
        a = u.get("g_atr") or 5.0
        flo = u["g_sl"] + 0.1 * a
        j = bisect.bisect_right(K, fi) - 1
        if j < 0:
            u["_m"] = None; continue
        known_i, l0i = lows[j]
        assert known_i <= fi  # P1
        L0 = LO[l0i]
        h1i = max(range(l0i, fi + 1), key=lambda k: HI[k])
        H1 = HI[h1i]
        if H1 - L0 < 1e-9:
            u["_m"] = None; continue
        u["_m"] = {"retr": (H1 - flo) / (H1 - L0), "travel": (H1 - L0) / a,
                   "age": (fi - h1i) * 0.25, "dL0": (flo - L0) / a}

def null_p(rows):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in UNIV]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(31)
    ge = sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs)
    return ge / 4000

panel(UNIV, "UNIVERSO", GT_ALL)
out = {}
for r in (6, 8):
    annotate(r)
    OKm = [u for u in UNIV if u.get("_m")]
    G1 = [u for u in OKm if 0.5 <= u["_m"]["retr"] <= 1.3]
    G2 = [u for u in G1 if u["_m"]["age"] >= 8]
    G3 = [u for u in G1 if u["_m"]["dL0"] <= 4]
    G4 = [u for u in G3 if fv(u, "h1_trend", 0) == 1]
    print(f"\n--- r={r} ---")
    for nm, rows in ((f"G1 retr.5-1.3", G1), (f"G2 +age>=8h", G2), (f"G3 +dL0<=4", G3), (f"G4 +h1up", G4)):
        if not rows:
            print(f"  {nm:<26} vazio"); continue
        p = panel(rows, nm, GT_ALL)
        pn = null_p(rows)
        print(f"      P(null>=obs)={pn:.4f}")
        out[f"r{r} {nm}"] = {**(p or {}), "p_null": pn}
json.dump(out, open(HERE / "results" / "macro_retrace_gate_20260705.json", "w"), indent=1)
print("OK → results/macro_retrace_gate_20260705.json")
