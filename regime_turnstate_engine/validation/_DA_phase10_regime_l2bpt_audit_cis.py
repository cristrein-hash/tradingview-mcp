#!/usr/bin/env python3
"""
Devil's-Advocate audit support — rough CIs for the phase10-regime x L2/BPT
diagnostic evaluation (276 episodes; regime BULL/RANGE/BEAR at entry bar).

This script ONLY recomputes the back-of-envelope confidence intervals used
to weigh the proposed reflection takeaways (A/B/C). All inputs are the
reported cell summaries; per-trade R series were NOT available to the audit,
so avgR SEs assume a plausible capped-R sd (sd~1.5R) and are explicitly
ROUGH / illustrative, not inferential claims. WR CIs (Wilson) are exact
given the reported N and WR.
"""
import math


def wilson(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    den = 1 + z * z / n
    center = p + z * z / (2 * n)
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((center - half) / den, (center + half) / den)


def avgr_ci(avg, n, sd=1.5, z=1.96):
    se = sd / math.sqrt(n)
    return se, (avg - z * se, avg + z * se)


def main():
    print("=== Base-rate WR Wilson 95% (exact given N, WR) ===")
    for name, wr, n in [("BULL", .60, 73), ("RANGE", .46, 164), ("BEAR", .41, 39)]:
        lo, hi = wilson(wr, n)
        print(f"{name:6} N{n:3} WR{wr:.0%}  Wilson[{lo:.0%},{hi:.0%}]")

    print("\n=== avgR ~95% (ROUGH, assumed sd=1.5R capped) ===")
    for name, avg, n in [("BULL_base", .66, 73), ("RANGE_base", .23, 164),
                         ("BEAR_base", -.06, 39)]:
        se, (lo, hi) = avgr_ci(avg, n)
        print(f"{name:12} avgR{avg:+.2f} N{n:3} SE~{se:.2f} ~95%[{lo:+.2f},{hi:+.2f}]")

    print("\n=== BULL vs BEAR base-rate avgR diff (ROUGH) ===")
    diff = .66 - (-.06)
    se = 1.5 * math.sqrt(1 / 73 + 1 / 39)
    print(f"diff +{diff:.2f}, SE~{se:.2f}, z~{diff / se:.2f}")

    print("\n=== TAKE tiny cells (ROUGH) ===")
    for name, avg, n in [("TAKE_BULL", 1.50, 6), ("TAKE_BEAR", 1.28, 5),
                         ("TAKE_RANGE", .66, 21)]:
        se, (lo, hi) = avgr_ci(avg, n)
        print(f"{name:11} avgR{avg:+.2f} N{n:2} SE~{se:.2f} ~95%[{lo:+.2f},{hi:+.2f}]")

    print("\n=== REVIEW-BULL untaken cell (ROUGH) ===")
    se, (lo, hi) = avgr_ci(1.34, 18)
    print(f"REVIEW_BULL avgR1.34 N18 SE~{se:.2f} ~95%[{lo:+.2f},{hi:+.2f}]")


if __name__ == "__main__":
    main()
