#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit helper — extrai a distribuição de bounce% dos 32 fundos A1/A2
e computa CI de Wilson do WR. Read-only, não toca nada. Reproduz a auditoria do painel FVG."""
import sys, bisect, json, math
sys.path.insert(0, '/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation')
from a1_causal_entry import load_series, causal_entry
from fvg_localization_study import BLK, LEG_LB

S = load_series(BLK); T, H = S["T"], S["H"]
GT = json.load(open('/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/results/REGIME_GT_FUNDOS_UNIFIED_20260714.json'))
F = sorted([f for f in GT["fundos"] if f.get("subclasse") in ("A1_pullback_fundo", "A2_pullback_raso")], key=lambda x: x["t"])
bounces = []
for f in F:
    jf = bisect.bisect_right(T, int(f["t"])) - 1
    if jf < LEG_LB + 3 or jf >= S["N"]:
        continue
    e = causal_entry(S, jf, "MB3")
    if not e:
        continue
    ent, pb_low = e["ent"], min(S["L"][max(0, jf - 16):jf + 1])
    hh = max(H[jf - LEG_LB:jf])
    bounce = 100 * (ent - pb_low) / (hh - pb_low) if hh > pb_low else 0.0
    bounces.append((round(bounce, 1), e["o"], f["subclasse"][:2]))
bounces.sort()
print("sorted bounce%:", [b[0] for b in bounces])
print("n>40:", sum(1 for b in bounces if b[0] > 40), "n>50:", sum(1 for b in bounces if b[0] > 50), "n>60:", sum(1 for b in bounces if b[0] > 60))
print("losses:", [b for b in bounces if b[1] == "LOSS"])
n, p, z = len(bounces), sum(1 for b in bounces if b[1] == "WIN") / len(bounces), 1.96
den = 1 + z * z / n; c = p + z * z / (2 * n); half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
print("WR %.1f%% Wilson95 CI [%.1f, %.1f]" % (100 * p, 100 * (c - half) / den, 100 * (c + half) / den))
