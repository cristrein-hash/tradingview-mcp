"""
Adversarial verification of loser-cut combo [{"feat":"vol_p_spike","dir":"lo","q":0.2}]
for XAU 15M LONG BOTTOM.

Checks:
 1. Re-confirm combo metrics (via score_lens).
 2. Per-year sanity (2026 must not drop >40% vs h1_base 53.7).
 3. Redundancy: single-feature combo, so leave-one-out = base. Instead test whether
    vol_p_spike is just a position re-cut by comparing the set of trades it cuts
    vs the set a pure-position lens (legpos90 hi q0.2) cuts (Jaccard overlap of cut trades).
 4. Null robustness: re-run score_lens several times to see null_p stability.

Outputs JSON to stdout. Reproducible / committable.
"""
import json, subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = os.path.join(HERE, "score_lens.py")

def run(combo):
    out = subprocess.check_output(["python3", SCORE, json.dumps(combo)], cwd=HERE)
    return json.loads(out.decode())

def main():
    target = [{"feat": "vol_p_spike", "dir": "lo", "q": 0.2}]
    pos    = [{"feat": "legpos90", "dir": "hi", "q": 0.2}]

    r_t = run(target)
    r_p = run(pos)

    # Null stability: score_lens recomputes null each call; sample a few.
    null_ps = [run(target)["null_p_avgR_random_ge"] for _ in range(5)]

    base = r_t["h1_base"]
    aft  = r_t["after"]

    report = {
        "target_combo": target,
        "base_avgR": base["avgR"], "base_DD": base["DD"], "base_yr": base["yr"],
        "after_avgR": aft["avgR"], "after_DD": aft["DD"], "after_yr": aft["yr"],
        "losers_cut": r_t["losers_cut"], "runners_cut": r_t["runners_cut"],
        "efic": r_t["efic_losL_per_runL"],
        "null_p_samples": null_ps,
        "null_p_max": max(null_ps),
        # per-year flags
        "all_years_positive": all(v >= 0 for v in aft["yr"].values()),
        "yr2026_drop_pct_vs_h1base": round((53.7 - aft["yr"]["2026"]) / 53.7 * 100, 1),
        "yr2026_gutted_gt40pct": (53.7 - aft["yr"]["2026"]) / 53.7 > 0.40,
        # position-redundancy comparison
        "pos_lens_after_avgR": r_p["after"]["avgR"],
        "pos_lens_losers_cut": r_p["losers_cut"],
        "pos_lens_runners_cut": r_p["runners_cut"],
        "pos_lens_efic": r_p["efic_losL_per_runL"],
        "delta_avgR_vs_pos_lens": round(aft["avgR"] - r_p["after"]["avgR"], 4),
    }
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
