#!/usr/bin/env python3
"""Round 2: explore neighborhood of the winning combo rsi_cj+micro_bos_up.
micro_bos_up (structure) appears to carry signal orthogonal to position.
Test it paired with other momentum/candle axes and vary q. Reproducible."""
import json, subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
LENS = os.path.join(HERE, "score_lens.py")

COMBOS = [
    '[{"feat":"rsi_cj","dir":"hi","q":0.25},{"feat":"micro_bos_up","dir":"hi","q":0.25}]',
    '[{"feat":"rsi_cj","dir":"hi","q":0.2},{"feat":"micro_bos_up","dir":"hi","q":0.2}]',
    '[{"feat":"rsi_slope3","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33}]',
    '[{"feat":"rsi_min8","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33}]',
    '[{"feat":"body_cj","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33}]',
    '[{"feat":"close_pos_cj","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33}]',
    '[{"feat":"up_velocity","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33}]',
    '[{"feat":"ema21_slope","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33}]',
    # 3-axis: momentum + candle + structure around winner
    '[{"feat":"rsi_cj","dir":"hi","q":0.33},{"feat":"micro_bos_up","dir":"hi","q":0.33},{"feat":"body_cj","dir":"hi","q":0.33}]',
    '[{"feat":"rsi_cj","dir":"hi","q":0.25},{"feat":"micro_bos_up","dir":"hi","q":0.33},{"feat":"close_pos_cj","dir":"hi","q":0.33}]',
]

def run(spec):
    out = subprocess.run([sys.executable, LENS, spec], capture_output=True, text=True)
    if out.returncode != 0:
        return {"spec": spec, "error": out.stderr.strip()[:200]}
    d = json.loads(out.stdout); a = d["after"]
    return {"spec": spec, "N": a["N"], "avgR": a["avgR"], "DD": a["DD"], "yr": a["yr"],
            "losers_cut": d["losers_cut"], "runners_cut": d["runners_cut"],
            "efic": d["efic_losL_per_runL"], "null_p": d["null_p_avgR_random_ge"],
            "hint": d["verdict_hint"]}

def passes(r):
    if "error" in r: return False
    return (r["null_p"] < 0.05 and r["runners_cut"] <= 0.15*r["losers_cut"]
            and r["avgR"] > 0.446 and all(v >= 0 for v in r["yr"].values()))

if __name__ == "__main__":
    for spec in COMBOS:
        r = run(spec); r["PASS"] = passes(r); print(json.dumps(r))
