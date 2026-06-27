#!/usr/bin/env python3
"""XAU 15M — FEASIBILITY PROBE for the VOLATILITY-TRANSITION-TIMING lens (proposal-stage, NOT a verdict).
Confirms only that compression/expansion-onset mechanics are (a) computable causally from RAW primitives
(OHLC/ATR/EMA per bar) and (b) selective enough to gate to 1-5/week. Verified 2026-06-26.

KEY DESIGN FINDING (negative, informs the proposals): entering ON the expansion-thrust bar chases MAE
(medMAE 3.96 ATR > baseline 3.08) and does NOT lift WR — you buy the spike, get whipped. The fix that the
proposed features encode is: enter on the RETEST / first-pullback of the freshly-broken compression box
(displacement → return-to-origin), with SL beyond the squeeze range. This probe is a sanity gate on
computability + base rates, NOT an edge claim. Edge must be validated in the Stage-B build across 8 blocks.
"""
import json, statistics
from pathlib import Path

PRIM = Path(__file__).parent / "primitives"


def mean(a):
    return sum(a) / len(a) if a else 0.0


def load_series(p):
    d = json.load(open(p))
    return [x for x in d["series"] if x.get("atr")]


def probe(s):
    rngs = [x["h"] - x["l"] for x in s]
    atrs = [x["atr"] for x in s]
    n = len(s)
    # 1) compression ratio fast(6)/slow(48) — squeeze state distribution
    comp = [mean(rngs[i - 6:i]) / mean(rngs[i - 48:i]) for i in range(60, n) if mean(rngs[i - 48:i])]
    # 2) NR7 inside-compression frequency
    nr7 = sum(1 for i in range(7, n) if rngs[i] == min(rngs[i - 6:i + 1]))
    # 3) k-bar sub-0.7ATR squeeze plateau
    sq = sum(1 for i in range(20, n) if all(rngs[j] < 0.7 * atrs[j] for j in range(i - 3, i)))
    # 4) expansion-thrust bar (release) base rate
    rel = 0
    for i in range(20, n):
        r = rngs[i]
        if atrs[i - 1] and r > 1.8 * atrs[i - 1]:
            clp = (s[i]["c"] - s[i]["l"]) / r if r else 0.5
            if clp > 0.75 or clp < 0.25:
                rel += 1
    return {
        "n_bars": n,
        "comp_p10_p50_p90": [round(x, 2) for x in (statistics.quantiles(comp, n=10)[0],
                                                    statistics.median(comp),
                                                    statistics.quantiles(comp, n=10)[-1])],
        "nr7_freq": round(nr7 / n, 4),
        "squeeze3_freq": round(sq / n, 4),
        "thrust_freq": round(rel / n, 4),
    }


if __name__ == "__main__":
    for p in sorted(PRIM.glob("*.primitives.json")):
        s = load_series(p)
        print(p.name, probe(s))
