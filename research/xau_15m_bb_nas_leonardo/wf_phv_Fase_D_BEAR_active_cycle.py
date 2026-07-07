#!/usr/bin/env python3
"""STRICT-CAUSAL adversarial re-implementation of the Fase-D BEAR-active cycle-phase
classifier. No reference to n-targets. No e['out']. No zone.last_t. No window > j.

Adversarial hardening vs the candidate:
  * The candidate derives causal swings by computing the FULL-series zigzag once and
    filtering conf_bar<=j. To rule out a hidden repaint leak, here I recompute the
    zigzag confirmation ONLINE: for a given decision bar j I run the zigzag walk using
    ONLY bars 0..j and take whatever pivots are confirmed within that truncated walk.
    If the ci<=j filter were leaking, the online truncated walk would disagree.
  * Fixed config = candidate's selected best (W=72, pos_thr=0.45). No sweep, no
    selection over labels here — just re-measure the reported cell.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import HI, LO, CL, ATR, ENTRIES, score, causal_swings_upto

W = 72
POS_THR = 0.45
R = 6

def zz_online(j, r=R):
    """Zigzag pivots confirmed using ONLY bars 0..j (independent truncated walk)."""
    piv = []; d = 0; ehi = elo = 0
    for i in range(1, j + 1):
        a = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d <= 0 and HI[i] - LO[elo] >= r * a and elo < i:
            piv.append(("L", elo, LO[elo], i)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
        elif d >= 0 and HI[ehi] - LO[i] >= r * a and ehi < i:
            piv.append(("H", ehi, HI[ehi], i)); d = -1
            elo = min(range(ehi, i + 1), key=lambda k: LO[k])
    return piv

def lower_low_online(j):
    Ls = [(idx, pr) for tp, idx, pr, ci in zz_online(j) if tp == "L"]
    return 1 if (len(Ls) >= 2 and Ls[-1][1] < Ls[-2][1]) else 0

def pos_causal(j, w=W):
    lo_i = max(0, j - w + 1)
    win = range(lo_i, j + 1)          # all indices <= j
    hh = max(HI[k] for k in win)
    ll = min(LO[k] for k in win)
    rng = max(hh - ll, 1e-9)
    return (CL[j] - ll) / rng

def cut(e):
    j = e["j"]
    return lower_low_online(j) == 1 and pos_causal(j) < POS_THR

if __name__ == "__main__":
    # cross-check: online truncated walk vs candidate's filter-the-full-array approach
    disagree = 0
    for e in ENTRIES:
        j = e["j"]
        a = lower_low_online(j)
        Ls = [(idx, pr) for tp, idx, pr, ci in causal_swings_upto(j) if tp == "L"]
        b = 1 if (len(Ls) >= 2 and Ls[-1][1] < Ls[-2][1]) else 0
        if a != b: disagree += 1
    print("lower_low online-vs-filter disagreements:", disagree, "/", len(ENTRIES))

    keep = [e["n"] for e in ENTRIES if not cut(e)]
    sc = score(keep)
    print("STRICT config: W=%d pos_thr=%.2f" % (W, POS_THR))
    print(sc)
    print("KEEP_NS =", sorted(keep))

    # post-hoc sanity ONLY (never used in logic)
    loser_targets = [21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
    winner_keys   = [1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]
    ks = set(keep)
    print("SANITY loser-cut  %d/%d" % (len([n for n in loser_targets if n not in ks]), len(loser_targets)))
    print("SANITY winner-keep %d/%d" % (len([n for n in winner_keys if n in ks]), len(winner_keys)))
