#!/usr/bin/env python3
"""Gate v5-4H sobre o censo A1/A2 (pergunta Cris 28/08: ligar SÓ o v5-4H?). Usa o motor REAL
engine_4h_regime_gate_RAW (regime_at causal, hour-level) sobre os 863 episódios já materializados
(episodes.jsonl do run_audit). Painel por rótulo + gate !=BEAR + gate BULL-only. py3 stdlib."""
import json
import sys
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
# o motor v5 é um script (executa análise no import) — corrê-lo capturando o namespace:
ns = runpy.run_path(str(HERE.parent / "engine_4h_regime_gate_RAW.py"))
regime_at = ns["regime_at"]

eps = [json.loads(l) for l in open(HERE / "episodes.jsonl") if l.strip()]


def panel(rl, cost=0.2):
    n = len(rl); w = sum(1 for r in rl if r > 0)
    s = sum(r - cost for r in rl)
    cum = peak = dd = 0.0; stk = mx = 0
    for r in rl:
        cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
        stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
    return dict(N=n, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)


for e in eps:
    e["v5"] = regime_at(e["t"])

print("=== v5-4H (motor real, causal) sobre o censo · custo 0.2 ===")
for lab in ("BULL", "RANGE", "BEAR"):
    print(f"  v5 {lab:<6}", panel([e["R"] for e in eps if e["v5"] == lab]))
print(f"  gate !=BEAR ", panel([e["R"] for e in eps if e["v5"] != "BEAR"]))
print(f"  gate BULL-only", panel([e["R"] for e in eps if e["v5"] == "BULL"]))
h = {}
for e in eps:
    if e["v5"] != "BEAR":
        h[e["half"]] = round(h.get(e["half"], 0) + e["R"] - 0.2, 1)
print("  !=BEAR por semestre:", dict(sorted(h.items())))
# cruzamento com Layer1 causal do audit (concordância)
agree = sum(1 for e in eps if (e["v5"] == "BEAR") == (e["reg"] == "BEAR"))
print(f"  concordância BEAR v5×Layer1: {agree}/{len(eps)} ({100*agree//len(eps)}%)")
json.dump({lab: panel([e["R"] for e in eps if e["v5"] == lab]) for lab in ("BULL", "RANGE", "BEAR")} |
          {"gate_neq_bear": panel([e["R"] for e in eps if e["v5"] != "BEAR"]),
           "halves_neq_bear": h},
          open(HERE / "v5_gate_results.json", "w"), indent=1)
print("gravado v5_gate_results.json")
