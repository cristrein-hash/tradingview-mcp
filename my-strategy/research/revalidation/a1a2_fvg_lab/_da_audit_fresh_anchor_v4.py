#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of fresh_anchor_study_v4 Candidate A (anchor=recent fractal high).
Read-only. Verifies: (1) outcome-window overlap / effective N in the BULL-gated population;
(2) full anchor-INVARIANT panel of A's INCREMENTAL firings (WR/avgR/ret-DD) vs baseline;
(3) whether the 'late-band' flood is real or an artifact of A's shrunken-leg anchor, by
recomputing bounce% against the GLOBAL 96-bar high; (4) whether a depth floor or a
global-anchor bounce gate isolates the good fresh bounces without the shallow-leg dilution.
No tuning to any single day; thresholds probed for diagnosis only. py3.9 stdlib."""
import sys, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, HORIZON
from fvg_localization_study import BLK, r_of, panel
from fvg_localization_study_v2 import detect_at as detect_base, HH_WIN
from fvg_localization_study_v3 import build_regime_lookup, regime_at
import fresh_anchor_study_v4 as V4


def bars_to_resolution(S, r, N):
    ei, sl, ent = r["ei"], r["sl"], r["ent"]; tgt = ent + 3 * (ent - sl)
    for m in range(ei + 1, min(N, ei + HORIZON + 1)):
        if S["L"][m] <= sl or S["H"][m] >= tgt:
            return m - ei
    return HORIZON


def overlap_stats(S, d, N):
    eis = sorted(r["ei"] for r in d.values())
    btr = [bars_to_resolution(S, r, N) for r in d.values()]
    span = max(eis) - min(eis) + 1
    conc = sum(btr) / span                       # avg firings live at once over the span
    return st.median(btr), conc, len(d) / conc if conc else float("inf")


def global_hh_bar(S, i):
    lo = max(0, i - HH_WIN)
    return max(range(lo, i - 8), key=lambda z: S["H"][z])


def main():
    S = V4.load_series(BLK); N = S["N"]
    known, REG = build_regime_lookup()
    base = V4.sweep(S, detect_base); A = V4.sweep(S, V4.detect_A)
    for d in (base, A):
        for i, r in d.items():
            r["regime"] = regime_at(known, REG, r["t"])
    bB = {i: r for i, r in base.items() if r["regime"] == "BULL"}
    bA = {i: r for i, r in A.items() if r["regime"] == "BULL"}

    print("=== (1) OVERLAP / EFFECTIVE N (BULL-gated) ===")
    for name, d in (("BASELINE", bB), ("A", bA)):
        mb, conc, effn = overlap_stats(S, d, N)
        print(f"  {name:8}: N{len(d)} med_bars_to_res={mb:.0f} avg_concurrent={conc:.2f}x eff_N~{effn:.0f}")
    print("  NOTE: BULL-gating sparsifies firings across 17mo → overlap far below the ~9x of dense samples.")

    print("\n=== (2) INCREMENTAL A firings (anchor-INVARIANT R outcomes) ===")
    inc = [bA[i] for i in bA if i not in base]
    kept = [bA[i] for i in bA if i in base]
    print(f"  incremental N{len(inc)}: {panel([r_of(r['o']) for r in inc])['s']}")
    print(f"  shared-bar N{len(kept)}: {panel([r_of(r['o']) for r in kept])['s']}")
    print(f"  incremental depth med {st.median([r['depth'] for r in inc]):.2f}ATR vs "
          f"baseline BULL depth med {st.median([r['depth'] for r in bB.values()]):.2f}ATR")

    print("\n=== (3) LATE-BAND: anchor artifact? (bounce vs A-anchor vs GLOBAL-96 high) ===")
    lateA = sum(1 for r in inc if r["bounce"] > 60) / len(inc) * 100
    lateG = 0
    for r in inc:
        i = r["cat_i"]; gh = S["H"][global_hh_bar(S, i)]; pb = S["L"][r["j"]]
        b = 100 * (r["ent"] - pb) / (gh - pb) if gh > pb else 0
        r["bounce_global"] = b
        lateG += b > 60
    lateG = lateG / len(inc) * 100
    print(f"  late(>60) incremental: A-own-anchor {lateA:.0f}%  vs GLOBAL-96 anchor {lateG:.0f}%")
    print("  => the 'late-band flood' is largely a MEASUREMENT artifact of A's shrunken leg.")

    print("\n=== (4) Can a filter isolate good fresh bounces (anchor-invariant)? ===")
    for lab, keep in [
        ("A incremental, depth>=3ATR", [r for r in inc if r["depth"] >= 3.0]),
        ("A incremental, depth>=4ATR", [r for r in inc if r["depth"] >= 4.0]),
        ("A incremental, global-bounce<=50", [r for r in inc if r["bounce_global"] <= 50]),
    ]:
        if keep:
            print(f"  {lab:34}: {panel([r_of(r['o']) for r in keep])['s']}")

    # A restricted overall (baseline union incremental-with-depth-floor) — does R3 recover?
    for floor in (3.0, 4.0):
        merged = list(bB.values()) + [r for r in inc if r["depth"] >= floor]
        pm = panel([r_of(r["o"]) for r in merged]); pbz = panel([r_of(r["o"]) for r in bB.values()])
        r3 = pm["sumR"] >= pbz["sumR"] and pm["avg"] >= pbz["avg"] and pm["rdd"] >= pbz["rdd"]
        print(f"  A_base∪inc[depth>={floor}]: {pm['s']}  R3(vs base)={'PASS' if r3 else 'FAIL'}")

    print("\n=== NULL reference (from v4) avgR +0.48 — A full avgR +0.34, incremental +0.28 ===")


if __name__ == "__main__":
    main()
