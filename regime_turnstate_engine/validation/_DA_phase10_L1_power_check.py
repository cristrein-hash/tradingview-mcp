#!/usr/bin/env python3
"""Devil's-Advocate power/selection check for phase10 regime applied to L1 EMA21 LONG.
One-shot stats backing the audit verdict: Wilson 95% CIs, two-proportion z, and
multiple-looks selection probability for the highlighted POC26 BULL N9 WR89% cell.
Not a pipeline; reproducibility aid for the audit memo. Inputs are the reported cells."""
import math
from math import comb, sqrt


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def twoprop_z(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return (p1 - p2) / se if se else 0.0


CELLS = [
    ("BULL all", 8, 15),
    ("RANGE all", 10, 17),
    ("POC26 BULL", 8, 9),
    ("POC26 BULL+RNG", 18, 25),
    ("BASE34", 18, 34),
    ("POC26", 18, 26),
]

if __name__ == "__main__":
    for label, k, n in CELLS:
        lo, hi = wilson(k, n)
        print(f"{label:16} {k}/{n} WR={100*k/n:4.0f}%  Wilson95=[{100*lo:3.0f},{100*hi:3.0f}]")
    print("z BULL(8/15) vs POC26BULL(8/9):", round(twoprop_z(8, 15, 8, 9), 2))
    print("z BASE34(18/34) vs POC26BULL(8/9):", round(twoprop_z(18, 34, 8, 9), 2))
    # Selection: prob of >=8/9 wins under base rate p=0.53, over ~8 inspected subsets
    p, n = 0.53, 9
    pge8 = sum(comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(8, 10))
    print("P(>=8/9 wins | p=0.53):", round(pge8, 3),
          " over ~8 looks ->", round(1 - (1 - pge8) ** 8, 3))
