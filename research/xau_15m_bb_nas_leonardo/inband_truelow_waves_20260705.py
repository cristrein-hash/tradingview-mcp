#!/usr/bin/env python3
"""ONDAS v2 COM LOW VERDADEIRO — correção de cálculo declarada (2026-07-06, ordem Cris "FAÇA").
Correções sobre a rodada 1 (todas as lições DA3 embutidas):
  FIX-1 fi_true = ARGMIN low em [h1i..ci] (a barra do low REAL da janela; antes pegava retest)
  FIX-2 feature nova F0 flush_pos = (flush_low_candidato − low_verdadeiro)/ATR
        candidato entra ACIMA do low real = sósia estrutural (hipótese do Cris: o discriminador)
        + F0b bars_after_low = ci − fi_true (quanto tempo depois do low real o candidato confirma)
        + F0c is_the_low = flush do candidato É o low da janela (|d|<=0,2ATR)
  FIX-3 seeds FIXAS explícitas em todos os nulls (zero hash salted)
  FIX-4 GT-precisão por CÍRCULO DISTINTO (nunca por candidato); recall = círculos/60
  FIX-5 sub-janela ANUAL obrigatória em qualquer look com P<0,05 antes de headline
  FIX-6 painel por EPISÓDIO (candidatos <=8h e <=1ATR agrupados; 1º por episódio) além do painel cru
W-features re-ancoradas em fi_true: W1 n_waves (h1i→fi_true) · W5 bottom_time · W6 vol_climax@fi_true
· W7 vol_dryup · W8 wave_decel.
FASE A (mapa GT vs sósia, sem outcome): F0/F0b/F0c + W re-ancoradas.
FASE B (4 looks declarados): T1 is_the_low==1 · T2 flush_pos<=0,3 & bars_after_low<=16 ·
T3 T2 & W1 in q25-75-GT · T4 T2 & W5 & W7 in q25-75-GT.
SANITY_PROBE: P1 tudo <= ci (asserts) · P2 fi_true por argmin (zero busca por preço) · P3 GT só
métrica/calibração · P4 null = banda, seeds 101/103/107/109 · P5 episódio-painel reportado."""
import json, bisect, random, hashlib
import statistics as st
import datetime as dt
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

def micro_waves(h1i, fi):
    waves = []; d = 0; ehi = elo = h1i
    for i in range(h1i + 1, fi + 1):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= 2 * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= 2 * atr and elo < i:
            srcw = max(range(max(h1i, elo - 96), elo + 1), key=lambda k: HI[k])
            waves.append({"hi_i": srcw, "lo_i": elo, "travel": HI[srcw] - LO[elo], "bars": max(1, elo - srcw)})
            d = 1; ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    if not waves or waves[-1]["lo_i"] < fi - 4:
        srcw = max(range(max(h1i, fi - 96), fi + 1), key=lambda k: HI[k])
        if HI[srcw] - LO[fi] > 1.0 * ATR[fi] and srcw < fi:
            waves.append({"hi_i": srcw, "lo_i": fi, "travel": HI[srcw] - LO[fi], "bars": max(1, fi - srcw)})
    return waves

for u in UNIV:
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    u["_t"] = None
    j = bisect.bisect_right(KLOW, ci) - 1
    if j < 0: continue
    ki, l0i = LOWS[j]
    assert ki <= ci  # P1
    L0 = LO[l0i]
    h1i = max(range(l0i, ci + 1), key=lambda k: HI[k])
    H1 = HI[h1i]
    if H1 - L0 < 1e-9 or h1i >= ci: continue
    retr = (H1 - flo) / (H1 - L0)
    if not (0.5 <= retr <= 1.3): continue
    fi_true = min(range(h1i, ci + 1), key=lambda k: LO[k])      # FIX-1
    true_low = LO[fi_true]
    assert h1i <= fi_true <= ci  # P1/P2
    flush_pos = (flo - true_low) / a                             # F0
    bars_after = ci - fi_true                                    # F0b
    is_low = int(abs(flo - true_low) <= 0.2 * a)                 # F0c
    wv = micro_waves(h1i, fi_true)
    n_waves = len(wv)
    wdecel = None
    if wv:
        v_first = wv[0]["travel"] / a / wv[0]["bars"]
        v_last = wv[-1]["travel"] / a / wv[-1]["bars"]
        wdecel = v_last / max(0.01, v_first)
    q1 = true_low + 0.25 * (H1 - true_low)
    win48 = list(range(max(h1i, fi_true - 48), fi_true + 1))
    bottom_time = sum(1 for k in win48 if CL[k] <= q1) / max(1, len(win48))
    v48 = [VOL[k] for k in range(max(0, fi_true - 48), fi_true)]
    vclimax = VOL[fi_true] / max(1e-9, sum(v48) / len(v48)) if v48 and VOL[fi_true] else None
    pb = fi_true - h1i
    vdry = None
    if pb >= 32:
        vfirst = sum(VOL[k] for k in range(h1i, h1i + 16)) / 16
        vlast = sum(VOL[k] for k in range(fi_true - 16, fi_true)) / 16
        vdry = vlast / max(1e-9, vfirst)
    u["_t"] = {"F0_flush_pos": flush_pos, "F0b_bars_after": bars_after, "F0c_is_low": is_low,
               "W1_n_waves": n_waves, "W5_bottom_time": bottom_time, "W6_vol_climax": vclimax,
               "W7_vol_dryup": vdry, "W8_wave_decel": wdecel}

BAND = [u for u in UNIV if u.get("_t")]
Bgt = [u for u in BAND if u["_gt"]]; Bng = [u for u in BAND if not u["_gt"]]
circ_band = set().union(*(u["_circ"] for u in BAND)) if BAND else set()
print(f"banda: N{len(BAND)} · GT-candidatos {len(Bgt)} · círculos alcançáveis {len(circ_band)}/60 · sósias {len(Bng)}")
FEATS = ["F0_flush_pos", "F0b_bars_after", "F0c_is_low", "W1_n_waves", "W5_bottom_time",
         "W6_vol_climax", "W7_vol_dryup", "W8_wave_decel"]
print("\nFASE A — medianas GT [q25,q75] vs sósia:")
sep = {}
for f in FEATS:
    A = sorted(u["_t"][f] for u in Bgt if u["_t"][f] is not None)
    B = sorted(u["_t"][f] for u in Bng if u["_t"][f] is not None)
    if not A or not B: continue
    ma, mb = st.median(A), st.median(B)
    iqr = max(0.01, (sorted(A + B)[3 * len(A + B) // 4] - sorted(A + B)[len(A + B) // 4]))
    sep[f] = abs(ma - mb) / iqr
    print(f"  {f:<16} GT {ma:>6.2f} [{A[len(A)//4]:.2f},{A[3*len(A)//4]:.2f}] · sósia {mb:>6.2f} · sep {sep[f]:.2f}")

def qgt(f, p):
    v = sorted(u["_t"][f] for u in Bgt if u["_t"][f] is not None)
    return v[int(p * (len(v) - 1))]
def episodes(rows):
    eps = []; cur = []
    for u in sorted(rows, key=lambda x: x["cj_t"]):
        flo = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0)
        if cur and u["cj_t"] - cur[-1]["cj_t"] <= 8 * 3600 and abs(flo - (cur[-1]["g_sl"] + 0.1 * (cur[-1].get("g_atr") or 5.0))) <= (u.get("g_atr") or 5.0):
            cur.append(u)
        else:
            if cur: eps.append(cur)
            cur = [u]
    if cur: eps.append(cur)
    return [e[0] for e in eps]
def null_p(rows, ref, seed):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in ref]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
def panel4(rows, tag, ref=None):
    n = len(rows)
    if not n: print(f"  {tag:<28} vazio"); return None
    rs = sorted(rows, key=lambda u: u["cj_t"]); nets = [R3[u["cj_t"]]["net3"] for u in rs]
    h = sum(1 for u in rs if R3[u["cj_t"]]["R3"] >= 3)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for u2, x in zip(rs, nets): yr[u2["yr"]] = round(yr.get(u2["yr"], 0) + x, 1)
    circ = set().union(*(u2["_circ"] for u2 in rs))
    wk = len({u2["g_week"] for u2 in U})
    ne = len(episodes(rs))
    print(f"  {tag:<28} N{n:>4} (ep {ne}) hit3R {100*h/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} stk-{mL} "
          f"| {n/wk:.2f}/sem | círculos {len(circ)}/60 | {yr}")
    return {"n": n, "ep": ne, "hit": round(h/n, 3), "net": round(sum(nets), 1), "stk": mL,
            "circles": len(circ), "yr": yr}
panel4(BAND, "BANDA (base)")
W15 = (qgt("W1_n_waves", 0.25), qgt("W1_n_waves", 0.75))
W55 = (qgt("W5_bottom_time", 0.25), qgt("W5_bottom_time", 0.75))
W75 = (qgt("W7_vol_dryup", 0.25), qgt("W7_vol_dryup", 0.75))
def okb(u, f, lo, hi):
    v = u["_t"][f]
    return v is not None and lo <= v <= hi
looks = {
    "T1 is_the_low": (lambda u: u["_t"]["F0c_is_low"] == 1, 101),
    "T2 pos<=0,3&after<=16": (lambda u: u["_t"]["F0_flush_pos"] <= 0.3 and u["_t"]["F0b_bars_after"] <= 16, 103),
    "T3 T2&W1": (lambda u: u["_t"]["F0_flush_pos"] <= 0.3 and u["_t"]["F0b_bars_after"] <= 16
                 and okb(u, "W1_n_waves", *W15), 107),
    "T4 T2&W5&W7": (lambda u: u["_t"]["F0_flush_pos"] <= 0.3 and u["_t"]["F0b_bars_after"] <= 16
                    and okb(u, "W5_bottom_time", *W55) and okb(u, "W7_vol_dryup", *W75), 109),
}
out = {}
print("\nFASE B — 4 looks (seeds fixas):")
for nm, (fn, sd) in looks.items():
    rows = [u for u in BAND if fn(u)]
    p = panel4(rows, nm)
    if rows and p:
        pn = null_p(rows, BAND, sd)
        ep_rows = episodes(rows)
        pe = null_p(ep_rows, episodes(BAND), sd + 1) if len(ep_rows) >= 10 else None
        line = f"      P(null cand)={pn:.4f}" + (f" · P(null episódio)={pe:.4f}" if pe is not None else "")
        print(line)
        out[nm] = {**p, "p": pn, "p_ep": pe}
        if pn < 0.05:
            print("      SUB-JANELA ANUAL (FIX-5):")
            for yy in (2024, 2025, 2026):
                ry = [u for u in rows if u["yr"] == yy]; by = [u for u in BAND if u["yr"] == yy]
                if ry and by:
                    hy = sum(1 for u in ry if R3[u["cj_t"]]["R3"] >= 3) / len(ry)
                    hb = sum(1 for u in by if R3[u["cj_t"]]["R3"] >= 3) / len(by)
                    print(f"        {yy}: look {100*hy:.1f}% (N{len(ry)}) vs banda {100*hb:.1f}%")
json.dump({"sep": sep, "looks": out},
          open(HERE / "results" / "inband_truelow_waves_20260705.json", "w"), indent=1, default=float)
print("OK → results/inband_truelow_waves_20260705.json")
