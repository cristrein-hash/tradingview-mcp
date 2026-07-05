#!/usr/bin/env python3
"""DA VETOR A — null correto p/ achados 1 e 2 (2026-07-05).
Ataque: os GT rows usam flush_low (mínimo local profundo); o null original usa low de barra
ALEATÓRIA. Refazer o lift com null = candidatos flush-reclaim do universo (lab_g_candidates com
outcome em r3_target_universe, flush = g_sl + 0,1·g_atr) que NÃO são GT.
Também: null aleatório TIME-MATCHED (GT são todos >= 2025-08; null original começa em 2024).
Métricas: (a) retr zigzag r=6/r=8 (mediana + banda [0.5,1.3] e bandas do diag) ·
          (b) família A: swing-high w32 rompido, |d|<=1 e <=0.5 ATR (construção do diag).
Nada é modificado; só leitura."""
import json, bisect, random
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GT = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

# ---------- zigzag (byte-idêntico aos scripts atacados) ----------
def zigzag_low_pivots(r):
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
ZZ = {r: zigzag_low_pivots(r) for r in (6, 8)}
ZK = {r: [x[0] for x in ZZ[r]] for r in ZZ}

def retr_at(fi, flo, r):
    lows = ZZ[r]; K = ZK[r]
    j = bisect.bisect_right(K, fi) - 1
    if j < 0:
        return None
    _, l0i = lows[j]
    L0 = LO[l0i]
    H1 = max(HI[k] for k in range(l0i, fi + 1))
    if H1 - L0 < 1e-9:
        return None
    return (H1 - flo) / (H1 - L0)

# ---------- família A do diag: swing-high w32 rompido, morte sustentada 16 (ATR[br], corte fi-96) ----------
def swings(w, kind):
    out = []; arr = HI if kind == "H" else LO
    for k in range(w, N - w):
        v = arr[k]
        seg = arr[k - w:k + w + 1]
        if (v == max(seg) if kind == "H" else v == min(seg)) and arr[k - w:k].count(v) == 0:
            out.append((k, v))
    return out
LEV = []
for k, H in swings(32, "H"):
    br = None
    for j in range(k + 32, N):
        if CL[j] > H + 0.1 * ATR[j]:
            br = j; break
    if br is None:
        continue
    c = 0; kd = None
    for j in range(br, N):
        if CL[j] < H - 0.25 * ATR[br]:
            c += 1
            if c >= 16:
                kd = j; break
        else:
            c = 0
    LEV.append((k, H, br, kd))
LOOK_D = 30 * 96

def famA_mind(fi, flo):
    best = None
    a = ATR[fi]
    for k, H, br, kd in LEV:
        if br >= fi or fi - k > LOOK_D:
            continue
        if kd is not None and kd < fi - 96:     # morta ANTES de fi-96 (regra do diag)
            continue
        d = (flo - H) / a
        if best is None or abs(d) < abs(best):
            best = d
    return best

# ---------- linhas ----------
GT_rows = []
for g in GT:
    fi = bisect.bisect_right(TS, g["flush_t"]) - 1
    if fi > 96:
        GT_rows.append((fi, g["flush_low"]))
gt_t = [g["flush_t"] for g in GT]
gt_lo_t, gt_hi_t = min(gt_t), max(gt_t)

random.seed(7)
NULL_full = [(i, LO[i]) for i in random.sample(list(range(3000, N - 100)), 300)]
win_pool = [i for i in range(3000, N - 100) if gt_lo_t <= TS[i] <= gt_hi_t]
random.seed(7)
NULL_win = [(i, LO[i]) for i in random.sample(win_pool, 300)]

UNIV = [u for u in U if u["cj_t"] in R3]
US = sorted(UNIV, key=lambda u: u["cj_t"]); UT = [u["cj_t"] for u in US]
for u in UNIV:
    u["_gt"] = 0
for g in GT:
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UT) and UT[j] <= g["flush_t"] + 8 * 3600:
        v = US[j]
        if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - g["flush_low"]) <= (v.get("g_atr") or 5.0):
            v["_gt"] = 1
        j += 1

def cand_row(u):
    fi = bisect.bisect_right(TS, u["cj_t"]) - 1
    return (fi, u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0))

C_gt = [cand_row(u) for u in UNIV if u["_gt"]]
C_ng = [cand_row(u) for u in UNIV if not u["_gt"]]
C_ng_win = [cand_row(u) for u in UNIV if not u["_gt"] and gt_lo_t <= u["cj_t"] <= gt_hi_t]

def stats(rows):
    r6 = [retr_at(fi, flo, 6) for fi, flo in rows]
    r6 = [x for x in r6 if x is not None]
    r8 = [retr_at(fi, flo, 8) for fi, flo in rows]
    r8 = [x for x in r8 if x is not None]
    dA = [famA_mind(fi, flo) for fi, flo in rows]
    dA = [x for x in dA if x is not None]
    nA = len([famA_mind(fi, flo) for fi, flo in rows])  # denominador = todas as linhas
    def frac(v, lo, hi):
        return sum(1 for x in v if lo <= x <= hi) / len(v) if v else 0
    return {
        "n": len(rows),
        "retr6_med": st.median(r6) if r6 else None,
        "band6_50_130": frac(r6, 0.5, 1.3),
        "band6_35_110": frac(r6, 0.35, 1.10),
        "retr8_med": st.median(r8) if r8 else None,
        "band8_50_130": frac(r8, 0.5, 1.3),
        "A_le1": sum(1 for x in dA if abs(x) <= 1.0) / len(rows),
        "A_le05": sum(1 for x in dA if abs(x) <= 0.5) / len(rows),
    }

SETS = [("GT rows (60, flush_low)", GT_rows),
        ("NULL barras aleatórias FULL (orig)", NULL_full),
        ("NULL barras aleatórias TIME-MATCHED", NULL_win),
        ("CAND GT-matched (flush-reclaim)", C_gt),
        ("CAND não-GT (null honesto)", C_ng),
        ("CAND não-GT TIME-MATCHED", C_ng_win)]
R = {}
print(f"{'conjunto':<38}{'N':>6} {'retr6med':>9} {'bd6[.5,1.3]':>12} {'bd6[.35,1.1]':>13} {'retr8med':>9} {'A<=1':>7} {'A<=.5':>7}")
for nm, rows in SETS:
    s = stats(rows); R[nm] = s
    print(f"{nm:<38}{s['n']:>6} {s['retr6_med']:>9.2f} {100*s['band6_50_130']:>11.1f}% {100*s['band6_35_110']:>12.1f}% "
          f"{s['retr8_med']:>9.2f} {100*s['A_le1']:>6.1f}% {100*s['A_le05']:>6.1f}%")

def lift(a, b, k):
    return R[a][k] / R[b][k] if R[b][k] else float("inf")

print("\nLIFTS (achado morto se < ~1,3):")
pairs = [("GT rows (60, flush_low)", "NULL barras aleatórias FULL (orig)", "GT vs null-aleatório ORIGINAL"),
         ("GT rows (60, flush_low)", "NULL barras aleatórias TIME-MATCHED", "GT vs null-aleatório time-matched"),
         ("CAND GT-matched (flush-reclaim)", "CAND não-GT (null honesto)", "cand-GT vs cand-nãoGT (HONESTO)"),
         ("CAND GT-matched (flush-reclaim)", "CAND não-GT TIME-MATCHED", "cand-GT vs cand-nãoGT time-matched")]
for a, b, tag in pairs:
    print(f"  {tag:<40} banda6[.5,1.3] {lift(a,b,'band6_50_130'):>5.2f} · famA<=1 {lift(a,b,'A_le1'):>5.2f} · "
          f"famA<=.5 {lift(a,b,'A_le05'):>5.2f} · Δretr6med {R[a]['retr6_med']-R[b]['retr6_med']:+.2f}")

# quantos GT foram matched por candidato (cobertura do proxy)
n_gtm = sum(u["_gt"] for u in UNIV)
gts_cov = 0
tsr = sorted((u["cj_t"], u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0), u.get("g_atr") or 5.0) for u in UNIV if u["_gt"])
T = [x[0] for x in tsr]
for g in GT:
    j = bisect.bisect_left(T, g["flush_t"] - 8 * 3600); ok = False
    while j < len(T) and T[j] <= g["flush_t"] + 8 * 3600:
        if abs(tsr[j][1] - g["flush_low"]) <= tsr[j][2]:
            ok = True; break
        j += 1
    gts_cov += ok
print(f"\ncobertura: {n_gtm} candidatos GT-matched · {gts_cov}/60 GT cobertos por >=1 candidato")
