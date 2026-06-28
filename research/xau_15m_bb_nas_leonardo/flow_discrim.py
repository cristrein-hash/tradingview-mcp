#!/usr/bin/env python3
"""Discrimination probe: for each flow feature, compare distribution among LOSERS (R<=0)
vs RUNNERS (R>=3) on substrate4. Helps find axes where losers and runners separate,
which is the only way to pass runners_cut <= 0.15*losers_cut. Reproducible, saved."""
import json, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
RECS = [json.loads(l) for l in (HERE/"substrate4_flow.jsonl").read_text().splitlines()]
FEATS = sorted(RECS[0]["flow"].keys())
losers = [r for r in RECS if r["R"] <= 0]
runners = [r for r in RECS if r["R"] >= 3]
print(f"losers={len(losers)} runners={len(runners)}")
rows = []
for f in FEATS:
    lv = [r["flow"][f] for r in losers if r["flow"].get(f) is not None]
    rv = [r["flow"][f] for r in runners if r["flow"].get(f) is not None]
    if not lv or not rv: continue
    lm = st.mean(lv); rm = st.mean(rv)
    # fraction ==1 / ==0 for binary
    uniq = set(lv) | set(rv)
    binary = uniq <= {0, 1}
    rows.append((abs(rm - lm), f, lm, rm, binary))
rows.sort(reverse=True)
for d, f, lm, rm, b in rows:
    tag = "BIN" if b else "   "
    arrow = "RUN>LOS" if rm > lm else "LOS>RUN"
    print(f"{f:26s} {tag} loserMean{lm:+8.3f} runnerMean{rm:+8.3f} sep{d:7.3f} {arrow}")
