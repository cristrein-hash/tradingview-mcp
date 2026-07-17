#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · detalhe factual das 7 entradas do detetor (fundo fractal -> entrada MB3).
Mostra: low do fractal, barra/preço da entrada MB3 (após confirmação p+3), SL, alvo, RATR, outcome, lag.
Diagnóstico: quão longe do fundo a entrada MB3 dispara. RAW-first, causal. py3.9 stdlib.
"""
import sys, csv, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from a1_causal_entry import load_series, _is_swinglow, M_FRAC, causal_entry
from s2b_seq_features import feats, blocks, BUCKET
from s3b_zigzag_region import zzleg_region

ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
WIN = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())


def main():
    S = load_series(blocks()); T, L, N = S["T"], S["L"], S["N"]
    tab = {}
    for r in csv.DictReader(open(HERE / "results" / "a1a2_bucket_table.csv")):
        tab[int(r["t"])] = (r["kind"], r["family_label"])
    gr = []; gd = []
    for p in range(M_FRAC, N - M_FRAC):
        if _is_swinglow(L, p, M_FRAC) and tab.get(T[p], ("", ""))[0] in ("GT_A1", "GT_A2"):
            fv = feats(S, {}, p, "fix48")
            if fv: gr.append(fv["reclaim"]); gd.append(fv["depth"])
    mrc, mdp = st.median(gr), st.median(gd)
    print("# fundo(p) low -> entrada MB3(ei) | dist entry-low | RATR | out | lag")
    k = 0
    for p in range(M_FRAC, N - M_FRAC):
        if T[p] < WIN or not _is_swinglow(L, p, M_FRAC):
            continue
        info = tab.get(T[p])
        if not info or info[1] not in BUCKET:
            continue
        fv = feats(S, {}, p, "fix48")
        if not fv or fv["reclaim"] < mrc or fv["depth"] < mdp:
            continue
        reg, _ = zzleg_region(int(T[p]), L[p])
        if reg not in ("BOTTOM", "MIDDLE"):
            continue
        e = causal_entry(S, p + M_FRAC, "MB3")
        if not e:
            continue
        k += 1
        print(f"{k} {ds(T[p])} low={L[p]:8.2f} -> {ds(T[e['ei']])} ent={e['ent']:8.2f} "
              f"| +{e['ent']-L[p]:5.1f}pts acima do low | SL={e['sl']:.2f} tgt={e['tgt']:.2f} "
              f"RATR={e['RATR']:.2f} {e['o']:4} | {e['ei']-p}b")


if __name__ == "__main__":
    main()
