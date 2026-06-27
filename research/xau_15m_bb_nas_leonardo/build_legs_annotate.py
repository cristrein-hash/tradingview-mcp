#!/usr/bin/env python3
"""CAMADA B (leg map 15M) + REANOTAÇÃO dos candidatos. Fonte: primitives/*.json + macro_regime_4h.json +
candidates_stageB.csv (tudo RAW-derivado, exclusivo). Para cada candidato adiciona:
  macro (último 4H FECHADO as-of nas_t), macro_swing_dir, macro_ema_pos;
  leg_dir (direção da perna 15M corrente = oposto do último pivô confirmado, fractal k=2, causal até j);
  setup_vs_macro ∈ {with_macro, counter_macro, neutral_macro}; is_pullback (entra contra a perna, a favor do macro).
Causal/SHIFT1: leg e macro usam só info até o close do bar de confirmação (nas_t). Saída candidates_annotated.csv.
Verified 2026-06-26."""
import json, csv, bisect
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
M = json.loads((HERE / "macro_regime_4h.json").read_text())["bars_4h"]
mend = [b["t_end"] for b in M]
def macro_at(t):  # último 4H FECHADO (t_end <= t) → causal
    k = bisect.bisect_right(mend, t) - 1
    return (M[k]["macro"], M[k]["swing_dir"], M[k]["ema_pos"]) if k >= 0 else ("WARMUP", 0, 0)
SER = {}; TID = {}
for blk, pr in PRIM.items():
    s = pr["series"]; SER[blk] = s; TID[blk] = {b["t"]: i for i, b in enumerate(s)}
K = 2
def leg_dir(s, j, W=80):
    """direção da perna corrente: +1 se último pivô confirmado é um swing LOW (subindo), -1 se HIGH (caindo)."""
    H = [b["h"] for b in s]; L = [b["l"] for b in s]; last_t = None; last = 0
    lo = max(K, j - W)
    # loop ASCENDENTE → o pivô mais recente sempre vence (recência garantida pela ordem; sem guard necessário).
    # Em empate high+low na mesma barra (raro, ~0.4%), low vence por vir depois — arbitrário e imaterial (DA 2026-06-26).
    for i in range(lo, j - K + 1):
        if H[i] == max(H[i - K:i + K + 1]): last = -1   # pivô de topo → perna desce
        if L[i] == min(L[i - K:i + K + 1]): last = 1    # pivô de fundo → perna sobe
    return last
rows = list(csv.DictReader(open(HERE / "candidates_stageB.csv")))
out = []
for r in rows:
    blk = r["block"]; s = SER.get(blk); tid = TID.get(blk)
    if s is None: continue
    nt = int(r["nas_t"]); j = tid.get(nt)
    if j is None: continue
    macro, msd, mep = macro_at(nt); ld = leg_dir(s, j); D = r["dir"]
    if macro == "NEUTRAL" or macro == "WARMUP": svm = "neutral_macro"
    elif (D == "LONG" and macro == "BULL") or (D == "SHORT" and macro == "BEAR"): svm = "with_macro"
    else: svm = "counter_macro"
    # is_pullback: a favor do macro E entrando contra a perna 15M corrente (compra na queda / vende na alta)
    is_pb = (svm == "with_macro") and ((D == "LONG" and ld == -1) or (D == "SHORT" and ld == 1))
    out.append({**r, "macro": macro, "macro_swing_dir": msd, "macro_ema_pos": mep,
                "leg_dir": ld, "setup_vs_macro": svm, "is_pullback": is_pb})
cols = list(out[0].keys())
with open(HERE / "candidates_annotated.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
# ---- sumário ----
from collections import Counter
import datetime as dt
n = len(out); svmc = Counter(r["setup_vs_macro"] for r in out)
wm = [r for r in out if r["setup_vs_macro"] == "with_macro"]
wm_pb = [r for r in out if r["is_pullback"]]
ts = sorted(int(r["entry_t"]) for r in out); weeks = (ts[-1] - ts[0]) / (7 * 86400)
print(f"candidatos anotados = {n}")
print(f"setup_vs_macro: {dict(svmc)}")
print(f"  with_macro: {len(svmc and wm)} ({100*len(wm)/n:.0f}%) | counter_macro: {svmc['counter_macro']} ({100*svmc['counter_macro']/n:.0f}%) | neutral: {svmc['neutral_macro']} ({100*svmc['neutral_macro']/n:.0f}%)")
wl = sum(1 for r in wm if r["dir"] == "LONG")
print(f"with_macro dir: LONG {wl} / SHORT {len(wm)-wl} | freq with_macro: {len(wm)/weeks:.1f}/sem")
print(f"with_macro & is_pullback (continuação ideal): {len(wm_pb)} ({len(wm_pb)/weeks:.2f}/sem)")
# faixa Set/2025+ (que dá p/ plotar)
cut = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())
wm_recent = [r for r in wm if int(r["entry_t"]) >= cut]
print(f"with_macro >= 2025-09-01: {len(wm_recent)} (LONG {sum(1 for r in wm_recent if r['dir']=='LONG')} / SHORT {sum(1 for r in wm_recent if r['dir']=='SHORT')})")
