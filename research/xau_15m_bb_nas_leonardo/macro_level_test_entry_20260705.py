#!/usr/bin/env python3
"""MACRO LEVEL-TEST — do diagnóstico à entry (2026-07-05).
Diagnóstico (gt_structural_distance_diag): fundos GT sentam em swing-high ROMPIDO (A: 45% <=1ATR
vs null 17%) e swing-low vivo (C: 30% vs 12%). Morte de nível = violação SUSTENTADA (16 closes).

FASE A (calibração GT, outcome-blind): varrer escala w em {16,32,48,64} p/ A e C, banda |d|<=1
→ escolher w* por lift GT. FASE B (teste, 4 looks declarados):
  E1 universo & testa-A(w*)   E2 universo & testa-C(w*)
  E3 testa A∪C                E4 E3 & h1_trend==1
Painel completo + recall estrito + null 4000× vs universo. flush do candidato = g_sl + 0,1·g_atr.
SANITY_PROBE: P1 nível ativo só em [break/confirm, morte) com known<cj (assert) · P2 null usa o
mesmo universo/matcher · P3 GT-lift escolhe w* SEM olhar outcome · P4 taxa-base candidatos-em-nível
reportada."""
import json, bisect, hashlib, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
GT_60 = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
GT_ALL = [(g["flush_t"], g["flush_low"]) for g in GT_60]
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

def swings(w, kind):
    arr = HI if kind == "H" else LO
    out = []
    for k in range(w, N - w):
        v = arr[k]
        seg = arr[k - w:k + w + 1]
        if (v == max(seg) if kind == "H" else v == min(seg)) and arr[k - w:k].count(v) == 0:
            out.append((k, v))
    return out

def sustained_death(level, start_i, run=16):
    c = 0
    for k in range(start_i, N):
        if CL[k] < level - 0.25 * ATR[k]:
            c += 1
            if c >= run:
                return k - run + 1
        else:
            c = 0
    return None

def build_levels(w):
    """A: highs rompidos (ativo [break_i, death)) · C: lows vivos (ativo [k+w, death))."""
    A, C = [], []
    for k, H in swings(w, "H"):
        br = None
        for j in range(k + w, min(k + w + 2880, N)):
            if CL[j] > H + 0.1 * ATR[j]:
                br = j
                break
            if CL[j] < H - 6 * ATR[j]:
                break
        if br is None:
            continue
        d = sustained_death(H, br)
        assert br > k  # P1
        A.append({"lv": H, "s": br, "e": d if d is not None else N, "src": k})
    for k, L in swings(w, "L"):
        d = sustained_death(L, k + w)
        C.append({"lv": L, "s": k + w, "e": d if d is not None else N, "src": k})
    return A, C

LOOK = 30 * 96
def tests_level(levels, fi, flo, atr, band=1.0):
    for z in levels:
        if z["s"] < fi <= z["e"] and fi - z["src"] <= LOOK:
            if abs(flo - z["lv"]) <= band * atr:
                return True
    return False

# ---- FASE A: escala por GT-lift (outcome-blind) ----
random.seed(7)
pool = list(range(3000, N - 100))
NULLB = random.sample(pool, 300)
print("FASE A — escala (GT 60 vs null 300 barras):")
print(f"{'w':>4} {'famA GT%':>9} {'famA null%':>10} {'liftA':>6} {'famC GT%':>9} {'famC null%':>10} {'liftC':>6}")
LV = {}
best = (None, 0)
for w in (16, 32, 48, 64):
    A, C = build_levels(w)
    LV[w] = (A, C)
    def rate(rows, levels):
        ok = 0
        for fi, flo in rows:
            if tests_level(levels, fi, flo, ATR[fi]):
                ok += 1
        return ok / len(rows)
    gtr = [(bisect.bisect_right(TS, t) - 1, lo) for t, lo in GT_ALL]
    nrows = [(i, LO[i]) for i in NULLB]
    ga, na = rate(gtr, A), rate(nrows, A)
    gc, nc = rate(gtr, C), rate(nrows, C)
    la = ga / na if na else 0; lc = gc / nc if nc else 0
    print(f"{w:>4} {100*ga:>8.0f}% {100*na:>9.0f}% {la:>6.2f} {100*gc:>8.0f}% {100*nc:>9.0f}% {lc:>6.2f}")
    score = ga * la
    if score > best[1]:
        best = (w, score)
W = best[0]
print(f"\nw* = {W} (maior GT%×lift famA)")
A_LV, C_LV = LV[W]

# ---- FASE B: entry no universo (4 looks) ----
UNIV = [u for u in U if u["cj_t"] in R3]
for u in UNIV:
    fi = bisect.bisect_right(TS, u["cj_t"]) - 1
    flo = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0)
    a = u.get("g_atr") or 5.0
    u["_tA"] = tests_level(A_LV, fi, flo, a)
    u["_tC"] = tests_level(C_LV, fi, flo, a)
base_rateA = sum(u["_tA"] for u in UNIV) / len(UNIV)
print(f"P4 taxa-base candidatos: testa-A {100*base_rateA:.0f}% · testa-C {100*sum(u['_tC'] for u in UNIV)/len(UNIV):.0f}%")

def null_p(rows, ref):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in ref]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(21)
    ge = sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs)
    return ge / 4000

print("\nFASE B — painéis (universo c/ R3):")
panel(UNIV, "UNIVERSO", GT_ALL)
E1 = [u for u in UNIV if u["_tA"]]
E2 = [u for u in UNIV if u["_tC"]]
E3 = [u for u in UNIV if u["_tA"] or u["_tC"]]
E4 = [u for u in E3 if fv(u, "h1_trend", 0) == 1]
out = {}
for nm, rows in (("E1 testa-A", E1), ("E2 testa-C", E2), ("E3 A∪C", E3), ("E4 A∪C & h1up", E4)):
    p = panel(rows, nm, GT_ALL)
    if rows:
        pn = null_p(rows, UNIV)
        print(f"      P(null>=obs)={pn:.4f}")
        out[nm] = {**(p or {}), "p_null": pn}
json.dump({"w_star": W, "panels": out},
          open(HERE / "results" / "macro_level_test_entry_20260705.json", "w"), indent=1)
print("OK → results/macro_level_test_entry_20260705.json")
