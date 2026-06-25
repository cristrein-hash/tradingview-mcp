#!/usr/bin/env python3
"""SANITY_PROBE — margem da regra dist_poc<=0.354 nos 34: lista winners por dist_poc crescente (quão perto do limite),
maior loser cortado, e a que threshold a regra começa a cortar winner. Resposta à pergunta 'corta algum winner?'."""
import json
from pathlib import Path
T = json.load(open(Path(__file__).parent / "l1_contrastive_features.json"))
for t in T:
    t["dp"] = float(t["dist_poc"]) if t["dist_poc"] not in (None, "None", "") else None
    t["win"] = t["win"] in (True, "True"); t["runner"] = t["runner"] in (True, "True")
THR = 0.354
los_cut = sorted([t for t in T if not t["win"] and t["dp"] is not None and t["dp"] <= THR], key=lambda t: -t["dp"])
wins = sorted([t for t in T if t["win"] and t["dp"] is not None], key=lambda t: t["dp"])
print(f"regra dist_poc <= {THR}")
print(f"  losers cortados = {len(los_cut)}  |  winners cortados = {sum(1 for t in wins if t['dp'] <= THR)}")
print(f"  MAIOR loser cortado: dist_poc={los_cut[0]['dp']:.3f} ({los_cut[0]['ts'][:10]})")
print(f"\n  winners MAIS PRÓXIMOS do limite (todos ACIMA de {THR} = preservados):")
for t in wins[:5]:
    marg = t["dp"] - THR
    print(f"    {t['ts'][:10]}  dist_poc={t['dp']:.3f}  margem=+{marg:.3f} ATR  {'[RUNNER +'+str(t['mfe'])+'R mfe]' if t['runner'] else ''}")
# a que threshold começa a cortar o 1o winner
w1 = wins[0]["dp"]
print(f"\n  → 1o winner cortado em threshold >= {w1:.3f} (winner {wins[0]['ts'][:10]}, mfe={wins[0]['mfe']})")
print(f"  → folga do limite atual até esse winner: {w1-THR:+.3f} ATR  (={100*(w1-THR)/THR:+.0f}% no threshold)")
print(f"  → gap entre maior-loser-cortado e menor-winner: {w1-los_cut[0]['dp']:.3f} ATR")
