#!/usr/bin/env python3
"""Diagnóstico factual dos 26 trades Cp (Set/2025->07-04): separa LOSSES em GRAB (SL varrido mas alcança 3R
depois = região certa/entrada precoce) vs FACA-VERDADEIRA (nunca alcança 3R, continua a cair). Mede a
profundidade da faca (quão abaixo do SL o preço vai). RAW-only 15M, causal. Reusa a série do cp_plot_window."""
import sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cp_plot_window as CP   # reusa loading + run_trades + série

T, H, L, C, N, ATR = CP.T, CP.H, CP.L, CP.C, CP.N, CP.ATR
import bisect
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")


def classify(etime, ent, sl, tgt):
    k = bisect.bisect_left(T, etime)
    r = ent - sl
    hit_sl = None; hit_tgt = None; minlow = ent
    for m in range(k + 1, min(N, k + 481)):
        minlow = min(minlow, L[m])
        if hit_sl is None and L[m] <= sl: hit_sl = m
        if hit_tgt is None and H[m] >= tgt: hit_tgt = m
        if hit_tgt and hit_tgt <= (hit_sl or 10**9): break
    if hit_tgt is not None and (hit_sl is None or hit_tgt < hit_sl):
        return "WIN", 0.0
    if hit_sl is not None:
        knife_depth = (sl - minlow) / r   # 0 = tocou SL e parou; >0 = furou o SL (faca)
        if hit_tgt is not None:
            return "GRAB", knife_depth      # varreu SL mas alcançou 3R depois
        return "KNIFE", knife_depth         # nunca alcançou 3R = faca verdadeira
    return "OPEN", (sl - minlow) / r


def main():
    tr = CP.run_trades()
    print(f"N={len(tr)} trades Cp\n")
    from collections import Counter
    cc = Counter(); knives = []
    for i, s in enumerate(tr, 1):
        cls, depth = classify(s["etime"], s["ent"], s["sl"], s["tgt"])
        cc[cls] += 1
        mark = ""
        if cls == "KNIFE": knives.append((i, ds(s["etime"]), depth)); mark = f"  faca −{depth:.1f}R abaixo do SL"
        elif cls == "GRAB": mark = f"  grab (SL varrido, chegou a 3R; faca −{depth:.1f}R)"
        print(f"  #{i:2d} {ds(s['etime'])} {cls:5}{mark}")
    print(f"\nRESUMO: {dict(cc)}")
    print(f"FACAS VERDADEIRAS (nunca 3R, continuam a cair): {len(knives)} de {len(tr)}")
    for i, d, dep in knives:
        print(f"   #{i} {d}  fura SL em −{dep:.1f}R")
    # clusters de losses consecutivos (a assinatura da faca a cair em série)
    seq = [classify(s["etime"], s["ent"], s["sl"], s["tgt"])[0] for s in tr]
    run = 0; clusters = []
    for i, x in enumerate(seq):
        if x in ("KNIFE", "GRAB", "OPEN") and x != "WIN":  # perdedores
            run += 1
        else:
            if run >= 3: clusters.append((i - run, run))
            run = 0
    if run >= 3: clusters.append((len(seq) - run, run))
    print(f"\nCLUSTERS de ≥3 perdedores seguidos: {[(ds(tr[a]['etime'])[:10], n) for a, n in clusters]}")


if __name__ == "__main__":
    main()
