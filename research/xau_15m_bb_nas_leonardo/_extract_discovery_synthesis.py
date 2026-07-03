#!/usr/bin/env python3
"""Materializa a síntese do discovery multi-agente (Lab A rodada 2) do journal do workflow
para artefato versionável. Fonte: wf_fe1ae2d6-cfe (6 agentes: 5 perspectivas + síntese)."""
import json
from pathlib import Path

J = Path("/Users/cristrein/.claude/projects/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/subagents/workflows/wf_fe1ae2d6-cfe/journal.jsonl")
OUT = Path(__file__).parent / "results" / "lab_a2_discovery_synthesis.json"
syn = None; persp = []
for line in open(J):
    d = json.loads(line)
    if d.get("type") != "result": continue
    r = d.get("value") or d.get("result") or {}
    if isinstance(r, str):
        try: r = json.loads(r)
        except Exception: continue
    if "preregister_now" in r: syn = r
    elif "hypotheses" in r: persp.append(r)
json.dump({"synthesis": syn, "perspectives": persp}, open(OUT, "w"), indent=1, ensure_ascii=False)
print(f"OK: síntese + {len(persp)} perspectivas → {OUT}")
