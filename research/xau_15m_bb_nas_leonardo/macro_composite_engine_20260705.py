#!/usr/bin/env python3
"""COMPOSIÇÃO MACRO-ESTRUTURAL (2026-07-05): retração-profunda ∩ nível-rompido ∩ flush.
Leitura dos prints do Cris em 3 camadas que TÊM de coexistir:
  (a) CONTEXTO: pullback profundo da última perna macro (G1 r=6: retr 0,5-1,3 · recall 36/60)
  (b) LOCAL: em cima de demanda verdadeira = swing-high w32 JÁ ROMPIDO vivo (|d|<=1 ATR; diag:
      GT 45% vs null 17%)
  (c) GATILHO: flush violento + reclaim (g_atr_spike, reclaim_atr — perfil GT 1,92 / 2,35)
LEDGER (declarado, 6 looks):
  C1 G1r6 & testa-A(w32)          C2 C1 & spike>=1.3       C3 C1 & reclaim>=1.5
  C4 C1 & spike>=1.3 & recl>=1.5  C5 G1r6&dL0<=4 & testa-A C6 C4 | (C5 & spike>=1.3)
Painel + null 4000× + GT-PRECISÃO (membros que são GT-estritos) — a métrica do Cris.
SANITY_PROBE: P1 causalidade herdada (pivô/nível confirmados antes de cj, asserts nos builders) ·
P2 GT nunca é feature de seleção · P3 null mesmo universo · P4 membros impressos p/ visual."""
import json, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
GT_60 = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
GT_ALL = [(g["flush_t"], g["flush_low"]) for g in GT_60]
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

# ---- (a) perna macro r=6 ----
def zigzag_low_pivots(r=6):
    lows = []; d = 0; ehi = elo = 0
    for i in range(1, N):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= r * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= r * atr and elo < i:
            lows.append((i, elo)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    return lows
LOWS = zigzag_low_pivots(6); KLOW = [x[0] for x in LOWS]

# ---- (b) níveis A: swing-high w32 rompidos, morte sustentada ----
def build_A(w=32):
    A = []
    for k in range(w, N - w):
        v = HI[k]
        seg = HI[k - w:k + w + 1]
        if v != max(seg) or HI[k - w:k].count(v) > 0:
            continue
        br = None
        for j in range(k + w, min(k + w + 2880, N)):
            if CL[j] > v + 0.1 * ATR[j]:
                br = j; break
            if CL[j] < v - 6 * ATR[j]:
                break
        if br is None:
            continue
        c = 0; death = N
        for k2 in range(br, N):
            if CL[k2] < v - 0.25 * ATR[k2]:
                c += 1
                if c >= 16:
                    death = k2 - 15; break
            else:
                c = 0
        assert br > k  # P1
        A.append({"lv": v, "s": br, "e": death, "src": k})
    return A
A_LV = build_A()
LOOK = 30 * 96

UNIV = [u for u in U if u["cj_t"] in R3]
# GT-estrito por candidato (métrica, NUNCA seleção)
BSs = sorted(UNIV, key=lambda u: u["cj_t"]); BT = [u["cj_t"] for u in BSs]
for u in UNIV:
    u["_gt"] = 0
for g in GT_60:
    j = bisect.bisect_left(BT, g["flush_t"] - 8 * 3600)
    while j < len(BT) and BT[j] <= g["flush_t"] + 8 * 3600:
        u = BSs[j]
        if abs((u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0)) - g["flush_low"]) <= (u.get("g_atr") or 5.0):
            u["_gt"] = 1
        j += 1

for u in UNIV:
    fi = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    j = bisect.bisect_right(KLOW, fi) - 1
    u["_retr"] = None; u["_dL0"] = None; u["_tA"] = False
    if j >= 0:
        _, l0i = LOWS[j]
        L0 = LO[l0i]
        H1 = max(HI[k] for k in range(l0i, fi + 1))
        if H1 - L0 > 1e-9:
            u["_retr"] = (H1 - flo) / (H1 - L0)
            u["_dL0"] = (flo - L0) / a
    for z in A_LV:
        if z["s"] < fi <= z["e"] and fi - z["src"] <= LOOK and abs(flo - z["lv"]) <= 1.0 * a:
            u["_tA"] = True; break

def null_p(rows, seed=41):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in UNIV]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000

G1 = [u for u in UNIV if u["_retr"] is not None and 0.5 <= u["_retr"] <= 1.3]
C1 = [u for u in G1 if u["_tA"]]
C2 = [u for u in C1 if fv(u, "g_atr_spike", 0) >= 1.3]
C3 = [u for u in C1 if fv(u, "reclaim_atr", 0) >= 1.5]
C4 = [u for u in C1 if fv(u, "g_atr_spike", 0) >= 1.3 and fv(u, "reclaim_atr", 0) >= 1.5]
C5 = [u for u in G1 if u["_dL0"] is not None and u["_dL0"] <= 4 and u["_tA"]]
C6k = {u["cj_t"] for u in C4} | {u["cj_t"] for u in C5 if fv(u, "g_atr_spike", 0) >= 1.3}
C6 = [u for u in UNIV if u["cj_t"] in C6k]
panel(UNIV, "UNIVERSO", GT_ALL)
out = {}
for nm, rows in (("C1 G1&nivelA", C1), ("C2 C1&spike", C2), ("C3 C1&reclaim", C3),
                 ("C4 C1&spike&recl", C4), ("C5 G1&dL0&nivelA", C5), ("C6 C4|C5spk", C6)):
    if not rows:
        print(f"  {nm:<26} vazio"); continue
    p = panel(rows, nm, GT_ALL)
    pn = null_p(rows)
    gtp = sum(u["_gt"] for u in rows)
    print(f"      P(null>=obs)={pn:.4f} · GT-precisão {gtp}/{len(rows)} = {100*gtp/len(rows):.0f}%")
    out[nm] = {**(p or {}), "p_null": pn, "gt_members": gtp}
best = min((k for k in out), key=lambda k: out[k]["p_null"])
print(f"\nP4 membros de C4 (p/ visual):")
for u in sorted(C4, key=lambda x: x["cj_t"]):
    r3 = R3[u["cj_t"]]
    print(f"  {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} "
          f"{'WIN ' if r3['R3']>=3 else 'loss'} net {r3['net3']:+.1f} GT={u['_gt']} retr {u['_retr']:.2f}")
json.dump(out, open(HERE / "results" / "macro_composite_engine_20260705.json", "w"), indent=1)
print("OK → results/macro_composite_engine_20260705.json")
