#!/usr/bin/env python3
"""CRUZAMENTO GTQ/DF × RETRAÇÃO MACRO (2026-07-05) — teste da hipótese do feedback visual:
os membros plotados que o Cris rejeitou ("pontos altos, descontextualizados das legs macro")
são os que FALHAM a banda de retração macro (retr r6 in [0.5,1.3]); os 5-6 válidos passam.
Se sim: o gate macro é o corretor do defeito visual, e a agulha vira GTQ∩banda.
+ PERFIL GT vs sósias DENTRO da banda G1 (retr/travel/age/dL0/nivelA + features antigas) —
onde mora a discriminação que falta.
SANITY_PROBE: P1 mesmas construções causais dos scripts anteriores (exec) · P2 GT só métrica ·
P3 membros GTQ impressos 1-a-1 com retr p/ reconciliar com os prints do Cris."""
import json, bisect, random
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
GT_60 = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
GT_ALL = [(g["flush_t"], g["flush_low"]) for g in GT_60]
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

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

def annotate(u):
    fi = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    j = bisect.bisect_right(KLOW, fi) - 1
    u["_retr"] = None; u["_travel"] = None; u["_age"] = None; u["_dL0"] = None
    if j >= 0:
        _, l0i = LOWS[j]
        L0 = LO[l0i]
        h1i = max(range(l0i, fi + 1), key=lambda k: HI[k])
        H1 = HI[h1i]
        if H1 - L0 > 1e-9:
            u["_retr"] = (H1 - flo) / (H1 - L0)
            u["_travel"] = (H1 - L0) / a
            u["_age"] = (fi - h1i) * 0.25
            u["_dL0"] = (flo - L0) / a

# reconstruir GTQ e DF exatamente como no plot
H1F = [u for u in BASE if fv(u, "h1_trend", 0) == 1]
BSs = sorted(BASE, key=lambda u: u["cj_t"]); BT = [u["cj_t"] for u in BSs]
for u in BASE:
    u["_gt"] = 0
for g in GT_60:
    j = bisect.bisect_left(BT, g["flush_t"] - 8 * 3600)
    while j < len(BT) and BT[j] <= g["flush_t"] + 8 * 3600:
        v = BSs[j]
        if abs((v["g_sl"] + 0.1 * v["g_atr"]) - g["flush_low"]) <= (v.get("g_atr") or 5.0):
            v["_gt"] = 1
        j += 1
GTm = [u for u in H1F if u["_gt"]]
FE = ["legpos60", "g_atr_spike", "g_ema21_dist", "g_sweep_depth", "n_supply_overhead"]
def qs(f, lo, hi):
    v = sorted(fv(u, f) for u in GTm if fv(u, f) is not None)
    return v[int(lo * (len(v) - 1))], v[int(hi * (len(v) - 1))]
bands = {f: qs(f, 0.25, 0.75) for f in FE}
GTQ = [u for u in H1F
       if fv(u, "legpos60", 9) <= bands["legpos60"][1]
       and fv(u, "g_atr_spike", 0) >= bands["g_atr_spike"][0]
       and fv(u, "g_ema21_dist", 9) <= bands["g_ema21_dist"][1]
       and fv(u, "g_sweep_depth", -9) >= bands["g_sweep_depth"][0]
       and fv(u, "n_supply_overhead", 99) <= bands["n_supply_overhead"][1]]
DF = [u for u in BASE if fv(u, "h1_trend", 0) == 1 and fv(u, "legpos60", 9) <= 0.20
      and fv(u, "g_atr_spike", 0) >= 1.3 and fv(u, "g_ema21_dist", 9) < 0]
seen_ann = set()
for u in GTQ + DF:
    if id(u) not in seen_ann:
        annotate(u); seen_ann.add(id(u))
IN = lambda u: u["_retr"] is not None and 0.5 <= u["_retr"] <= 1.3
print("GTQ-18 membro a membro (WIN/loss · GT · retr — reconciliar com prints):")
for i, u in enumerate(sorted(GTQ, key=lambda x: x["cj_t"]), 1):
    r3 = R3[u["cj_t"]]
    print(f"  #G{i:<2} {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} "
          f"{'WIN ' if r3['R3']>=3 else 'loss'} GT={u['_gt']} retr {u['_retr'] if u['_retr'] is None else round(u['_retr'],2)}"
          f" {'<<< BANDA' if IN(u) else '(fora: ponto alto)'}")
gq_in = [u for u in GTQ if IN(u)]
df_in = [u for u in DF if IN(u)]
print()
panel(GTQ, "GTQ-18 original", GT_ALL)
panel(gq_in, "GTQ ∩ banda-macro", GT_ALL)
panel(DF, "DF-40 original", GT_ALL)
panel(df_in, "DF ∩ banda-macro", GT_ALL)

# perfil GT vs sósias dentro da banda (universo)
UNIV = [u for u in U if u["cj_t"] in R3]
US = sorted(UNIV, key=lambda u: u["cj_t"]); UT = [u["cj_t"] for u in US]
for u in UNIV:
    u["_gt"] = 0
for g in GT_60:
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UT) and UT[j] <= g["flush_t"] + 8 * 3600:
        v = US[j]
        if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - g["flush_low"]) <= (v.get("g_atr") or 5.0):
            v["_gt"] = 1
        j += 1
for u in UNIV:
    annotate(u)
B = [u for u in UNIV if IN(u)]
Bgt = [u for u in B if u["_gt"]]; Bng = [u for u in B if not u["_gt"]]
print(f"\nPERFIL dentro da banda G1: GT {len(Bgt)} vs sósias {len(Bng)} (medianas)")
DIMS = [("retr", "_retr"), ("travel", "_travel"), ("age_h", "_age"), ("dL0", "_dL0")]
for nm, k in DIMS:
    a = [u[k] for u in Bgt if u[k] is not None]; b = [u[k] for u in Bng if u[k] is not None]
    print(f"  {nm:<10} GT {st.median(a):>7.2f} · sósia {st.median(b):>7.2f}")
for f in ("g_atr_spike", "g_sweep_depth", "reclaim_atr", "legpos60", "g_ema21_dist", "rsi_low",
          "h1_rsi", "h1_pos", "n_supply_overhead", "g_box96", "pullback_depth", "low_wick"):
    a = [fv(u, f) for u in Bgt if fv(u, f) is not None]
    b = [fv(u, f) for u in Bng if fv(u, f) is not None]
    if a and b:
        print(f"  {f:<18} GT {st.median(a):>7.2f} · sósia {st.median(b):>7.2f}")
