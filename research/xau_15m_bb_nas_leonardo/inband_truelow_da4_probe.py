#!/usr/bin/env python3
"""DA4 probe — verifica 3 follow-ups dos negativos de inband_truelow_waves_20260705.py.
(1) % da banda com F0_flush_pos<=0,2 (universo já entra no low verdadeiro por construção?)
(2) W7 dryup<=1,0 sozinho na banda: hit% vs banda, por ano, null seed 113
(4) onde moram os círculos GT que a banda retr[0,5-1,3] perde (retr<0,5 / retr>1,3 / sem pernada / sem candidato)
Replica byte-a-byte a construção da banda do script original. Read-only; não altera ficheiros existentes."""
import json, bisect, random, hashlib
import statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT_60 = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]
VOL = [float(b.get("v") or 0) for b in S]

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

UNIV = [u for u in U if u["cj_t"] in R3]
US = sorted(UNIV, key=lambda u: u["cj_t"]); UT = [u["cj_t"] for u in US]
for u in UNIV: u["_circ"] = set()
for gi, g in enumerate(GT_60):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UT) and UT[j] <= g["flush_t"] + 8 * 3600:
        v = US[j]
        if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - g["flush_low"]) <= (v.get("g_atr") or 5.0):
            v["_circ"].add(gi)
        j += 1
for u in UNIV: u["_gt"] = int(bool(u["_circ"]))

for u in UNIV:
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    u["_t"] = None; u["_reason"] = None; u["_retr"] = None
    j = bisect.bisect_right(KLOW, ci) - 1
    if j < 0:
        u["_reason"] = "sem_pernada"; continue
    ki, l0i = LOWS[j]
    L0 = LO[l0i]
    h1i = max(range(l0i, ci + 1), key=lambda k: HI[k])
    H1 = HI[h1i]
    if H1 - L0 < 1e-9 or h1i >= ci:
        u["_reason"] = "pernada_invalida"; continue
    retr = (H1 - flo) / (H1 - L0)
    u["_retr"] = retr
    if retr < 0.5:
        u["_reason"] = "retr<0.5"; continue
    if retr > 1.3:
        u["_reason"] = "retr>1.3"; continue
    fi_true = min(range(h1i, ci + 1), key=lambda k: LO[k])
    true_low = LO[fi_true]
    flush_pos = (flo - true_low) / a
    bars_after = ci - fi_true
    is_low = int(abs(flo - true_low) <= 0.2 * a)
    pb = fi_true - h1i
    vdry = None
    if pb >= 32:
        vfirst = sum(VOL[k] for k in range(h1i, h1i + 16)) / 16
        vlast = sum(VOL[k] for k in range(fi_true - 16, fi_true)) / 16
        vdry = vlast / max(1e-9, vfirst)
    u["_t"] = {"F0_flush_pos": flush_pos, "F0b_bars_after": bars_after, "F0c_is_low": is_low,
               "W7_vol_dryup": vdry}
    u["_reason"] = "in_band"

BAND = [u for u in UNIV if u.get("_t")]
Bgt = [u for u in BAND if u["_gt"]]; Bng = [u for u in BAND if not u["_gt"]]
circ_band = set().union(*(u["_circ"] for u in BAND)) if BAND else set()
print(f"banda: N{len(BAND)} · GT-cand {len(Bgt)} · círculos banda {len(circ_band)}/60 · sósias {len(Bng)}")
assert len(BAND) == 1447 and len(Bgt) == 65 and len(circ_band) == 34, "banda diverge do run original!"

# ---------- (1) F0_flush_pos distribuição ----------
fp_all = [u["_t"]["F0_flush_pos"] for u in BAND]
fp_gt = [u["_t"]["F0_flush_pos"] for u in Bgt]
fp_ng = [u["_t"]["F0_flush_pos"] for u in Bng]
def pct_le(v, x): return 100 * sum(1 for y in v if y <= x) / len(v)
print("\n(1) F0_flush_pos:")
print(f"  medianas: GT {st.median(fp_gt):.3f} · sósia {st.median(fp_ng):.3f} · banda toda {st.median(fp_all):.3f}")
for thr in (0.0, 0.2, 0.3, 0.5, 1.0):
    print(f"  flush_pos<={thr:>3}: banda {pct_le(fp_all,thr):5.1f}% · GT {pct_le(fp_gt,thr):5.1f}% · sósia {pct_le(fp_ng,thr):5.1f}%")
print(f"  q75/q90 banda: {sorted(fp_all)[int(0.75*(len(fp_all)-1))]:.2f} / {sorted(fp_all)[int(0.90*(len(fp_all)-1))]:.2f}")

# ---------- (2) W7 dryup<=1.0 sozinho ----------
def hitpct(rows):
    return 100 * sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows) if rows else float("nan")
def null_p(rows, ref, seed):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in ref]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
W7def = [u for u in BAND if u["_t"]["W7_vol_dryup"] is not None]
W7cut = [u for u in W7def if u["_t"]["W7_vol_dryup"] <= 1.0]
print(f"\n(2) W7 dryup<=1,0 sozinho (definido só quando pullback>=32b):")
print(f"  W7 definido: {len(W7def)}/{len(BAND)} ({100*len(W7def)/len(BAND):.0f}% da banda) · GT-cand c/ W7: {sum(1 for u in W7def if u['_gt'])}/{len(Bgt)}")
print(f"  banda-total     N{len(BAND):>5} hit {hitpct(BAND):5.1f}%")
print(f"  W7-definido     N{len(W7def):>5} hit {hitpct(W7def):5.1f}%")
print(f"  dryup<=1,0      N{len(W7cut):>5} hit {hitpct(W7cut):5.1f}%  · P(null vs W7-definido, seed113)={null_p(W7cut, W7def, 113):.4f} · P(null vs banda, seed113)={null_p(W7cut, BAND, 113):.4f}")
nets = lambda rows: round(sum(R3[u["cj_t"]]["net3"] for u in rows), 1)
print(f"  NET dryup<=1,0: {nets(W7cut):+.1f} · círculos {len(set().union(*(u['_circ'] for u in W7cut)) if W7cut else set())}/60")
print("  por ano (hit look vs hit banda | NET look):")
for yy in (2024, 2025, 2026):
    ry = [u for u in W7cut if u["yr"] == yy]; by = [u for u in BAND if u["yr"] == yy]
    if ry:
        print(f"    {yy}: N{len(ry):>4} hit {hitpct(ry):5.1f}% vs banda {hitpct(by):5.1f}% | NET {nets(ry):+.1f}")

# ---------- (4) círculos perdidos ----------
covered_univ = set()
per_circ = {}
for u in UNIV:
    for gi in u["_circ"]:
        covered_univ.add(gi)
        per_circ.setdefault(gi, []).append(u)
lost = sorted(covered_univ - circ_band)
no_cand = sorted(set(range(60)) - covered_univ)
print(f"\n(4) círculos: universo alcança {len(covered_univ)}/60 · banda {len(circ_band)}/60 · perdidos pela banda {len(lost)} · sem candidato no universo {len(no_cand)}")
cats = {}
for gi in lost:
    rs = [u["_reason"] for u in per_circ[gi]]
    retrs = [u["_retr"] for u in per_circ[gi] if u["_retr"] is not None]
    kinds = set(rs)
    if kinds == {"retr<0.5"}: c = "só retr<0.5"
    elif kinds == {"retr>1.3"}: c = "só retr>1.3"
    elif kinds <= {"retr<0.5", "retr>1.3"}: c = "mix retr fora (ambos lados)"
    elif "sem_pernada" in kinds or "pernada_invalida" in kinds:
        c = "sem pernada válida" if kinds <= {"sem_pernada", "pernada_invalida"} else "mix c/ sem-pernada"
    else: c = "outro:" + ",".join(sorted(kinds))
    cats[c] = cats.get(c, 0) + 1
    rr = f"retr med {st.median(retrs):.2f}" if retrs else "sem retr"
    print(f"  círculo #{gi:>2} · cand {len(per_circ[gi])} · razões {sorted(kinds)} · {rr}")
print("  RESUMO perdidos:", cats)
print(f"  sem candidato no universo (nenhum match ±8h/±1ATR): círculos {no_cand}")
