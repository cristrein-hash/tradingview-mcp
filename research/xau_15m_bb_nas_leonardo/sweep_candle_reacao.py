#!/usr/bin/env python3
"""Sweep candle-reacao family lenses for XAU 15M LONG BOTTOM.
Gates: null_p < 0.05 AND runners_cut <= 0.15*losers_cut AND avgR_after > 0.446
       AND all yr >= 0.
Calls score_lens.py as a subprocess; reads JSON. Reproducible/committable.
"""
import json
import subprocess
import itertools
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCORER = os.path.join(HERE, "score_lens.py")
BASE_AVGR = 0.446

# candle-reacao family + a few orthogonal axes to attempt to add a different axis
CANDLE = ["body_cj", "close_pos_cj", "reclaim_speed", "reclaim_atr",
          "up_closes5", "up_closes_pc", "low_wick_cj", "low_wick_p", "vol_cj"]
ORTHO = ["rsi_slope3", "rsi_min8", "ema21_slope", "up_velocity",
         "higher_lows8", "micro_bos_up", "vol_p_spike"]
QS = [0.2, 0.25, 0.33]
# direction: candle reaction features favor WIN when HIGH (per scan); low_wick = lo means small lower wick
DIRHI = {f: "hi" for f in CANDLE + ORTHO}
DIRHI["low_wick_cj"] = "lo"
DIRHI["low_wick_p"] = "lo"


def score(combo):
    spec = json.dumps(combo)
    out = subprocess.run(["python3", SCORER, spec], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


def gates(d):
    a = d["after"]
    lc = d["losers_cut"]
    rc = d["runners_cut"]
    yr_ok = all(v >= 0 for v in a["yr"].values())
    return (d["null_p_avgR_random_ge"] < 0.05
            and rc <= 0.15 * lc
            and a["avgR"] > BASE_AVGR
            and yr_ok)


def main():
    results = []
    combos = []
    # singles
    for f in CANDLE:
        for q in QS:
            combos.append([{"feat": f, "dir": DIRHI[f], "q": q}])
    # candle pairs
    for f1, f2 in itertools.combinations(CANDLE, 2):
        for q in QS:
            combos.append([{"feat": f1, "dir": DIRHI[f1], "q": q},
                           {"feat": f2, "dir": DIRHI[f2], "q": q}])
    # candle + orthogonal axis
    for f1 in CANDLE:
        for f2 in ORTHO:
            for q in QS:
                combos.append([{"feat": f1, "dir": DIRHI[f1], "q": q},
                               {"feat": f2, "dir": DIRHI[f2], "q": q}])

    passed = []
    for c in combos:
        d = score(c)
        if d is None:
            continue
        a = d["after"]
        rec = {
            "combo": c,
            "avgR": a["avgR"], "DD": a["DD"], "yr": a["yr"],
            "losC": d["losers_cut"], "runC": d["runners_cut"],
            "efic": d["efic_losL_per_runL"],
            "p": d["null_p_avgR_random_ge"],
        }
        results.append(rec)
        if gates(d):
            passed.append(rec)

    results.sort(key=lambda r: r["p"])
    print("=== TOP 12 by null_p (lowest) ===")
    for r in results[:12]:
        print(f"p={r['p']:.3f} avgR={r['avgR']:.3f} DD={r['DD']} "
              f"losC={r['losC']} runC={r['runC']} efic={r['efic']} "
              f"yr={r['yr']} :: {[ (x['feat'],x['dir'],x['q']) for x in r['combo'] ]}")
    print(f"\n=== PASSED ALL GATES: {len(passed)} ===")
    for r in passed:
        print(json.dumps(r))


if __name__ == "__main__":
    main()
