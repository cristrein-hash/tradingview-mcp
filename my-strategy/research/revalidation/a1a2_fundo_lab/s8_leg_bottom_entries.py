#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · Stage 6 — entradas A1/A2 nos BOTTOMS das legs regime v3 (hipótese Cris 2026-07-17).
Para cada fractal swing-low (Set/2025+), acha a leg v3 corrente (causal: última leg do 4H FECHADO ≤ t),
o seu limite inferior CAUSAL (min low 15M da abertura da leg até t), e a proximidade do fundo a esse limite.
Gate = fundo perto do limite inferior (grelha declarada de limiares em ATR). Entry A1/A2 (MB3 após p+3,
SL low-real, 3R). Painel completo por limiar e por tipo de leg. GT overlap. Causal, RAW-first. py3.9 stdlib.
"""
import sys, csv, bisect, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from a1_causal_entry import load_series, _is_swinglow, M_FRAC, causal_entry
from s2b_seq_features import blocks
import leg_v3 as LV

WIN_START = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())
BAR4 = 14400
GRID = [0.25, 0.5, 1.0, 2.0]   # limiares de proximidade (fundo a ≤ X·ATR do limite inferior da leg)
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")

# leg v3 (4H) causal
_v3 = LV.build_leg_v3()
_LT = [r["t"] for r in _v3]; _LEG = [r.get("leg", "?") for r in _v3]
_LKN = [t + BAR4 for t in _LT]   # known-at = fecho da barra 4H


def leg_idx_at(t):
    return bisect.bisect_right(_LKN, t) - 1   # última leg 4H FECHADA <= t


def leg_start_time(i):
    j = i
    while j > 0 and _LEG[j - 1] == _LEG[i]:
        j -= 1
    return _LT[j]


def panel(rs):
    if not rs:
        return "N 0"
    wr = 100 * sum(1 for r in rs if r > 0) / len(rs); sm = sum(rs); avg = sm / len(rs)
    cum = pk = dd = cs = mst = 0
    for r in rs:
        cum += r; pk = max(pk, cum); dd = min(dd, cum - pk); cs = cs + 1 if r < 0 else 0; mst = max(mst, cs)
    return f"N {len(rs)} · WR {wr:.0f}% · sumR {sm:+.1f} · avgR {avg:+.2f} · DD {dd:.1f} · streak {mst}"


def main():
    S = load_series(blocks()); T, L, ATR, N = S["T"], S["L"], S["ATR"], S["N"]
    tab = {}
    for r in csv.DictReader(open(HERE / "results" / "a1a2_bucket_table.csv")):
        tab[int(r["t"])] = r["kind"]
    # recolher todos os fractais Set/2025+ com leg, proximidade causal, entry A1/A2
    rows = []
    for p in range(M_FRAC, N - M_FRAC):
        if T[p] < WIN_START or not _is_swinglow(L, p, M_FRAC) or ATR[p] is None or ATR[p] <= 0:
            continue
        li = leg_idx_at(int(T[p]))
        if li < 0:
            continue
        leg = _LEG[li]
        if leg == "IMPULSO_DOWN":                          # CORTE (ordem Cris 2026-07-17)
            continue
        lst = leg_start_time(li)
        k0 = bisect.bisect_left(T, lst)
        e = causal_entry(S, p + M_FRAC, "MB3")
        if not e:
            continue
        ei = e["ei"]
        leg_lo = min(L[k0:ei + 1]) if ei >= k0 else L[p]   # limite inferior CAUSAL da leg (até à ENTRADA)
        prox = (e["ent"] - leg_lo) / ATR[p]                # proximidade da ENTRADA ao limite inferior da leg
        R = 3.0 if e["o"] == "WIN" else (-1.0 if e["o"] == "LOSS" else 0.0)
        rows.append({"t": T[p], "leg": leg, "prox": prox, "kind": tab.get(T[p], "CAND"),
                     "o": e["o"], "R": R, "ratr": e["RATR"], "ent_above_low": e["ent"] - L[p]})
    print(f"fractais Set/2025+ com entry: {len(rows)}\n")
    resolved = lambda rs: [r["R"] for r in rs if r["o"] in ("WIN", "LOSS")]

    print("=== PAINEL por limiar de proximidade da ENTRADA ao limite inferior da leg (IMPULSO_DOWN cortado) ===")
    for thr in [99] + GRID:
        sub = [r for r in rows if r["prox"] <= thr]
        gt = sum(1 for r in sub if r["kind"] in ("GT_A1", "GT_A2"))
        tag = "TODOS" if thr == 99 else f"≤{thr}ATR"
        rr = st.median([r['ratr'] for r in sub]) if sub else 0
        print(f"  {tag:8}: {panel(resolved(sub))} | med RATR {rr:.2f} | GT {gt}")

    print("\n=== entrada ≤0.5·ATR do limite inferior, por TIPO de leg ===")
    near = [r for r in rows if r["prox"] <= 0.5]
    from collections import Counter
    for lg in [x for x, _ in Counter(r["leg"] for r in near).most_common()]:
        s = [r for r in near if r["leg"] == lg]
        print(f"  {lg:14}: {panel(resolved(s))}")


if __name__ == "__main__":
    main()
