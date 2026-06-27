#!/usr/bin/env python3
"""Extrai survivors + verdict do output do Workflow xau15m-causal-entry-engine p/ engine_report.txt (reprodutível)."""
import json
from pathlib import Path
OUT=Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/b3051da4-3014-4915-9b74-e74977852ecf/tasks/whkqd8w1y.output")
d=json.load(open(OUT)); r=d["result"]
if isinstance(r,str): r=json.loads(r)
rep=Path(__file__).parent/"engine_report.txt"
with open(rep,"w") as f:
    f.write(f"SURVIVORS (pós-verify adversarial): {len(r['survivors'])}\n\n")
    for s in r["survivors"]:
        f.write("• "+s.get("desc","")+"\n")
        f.write(f"    LOBO_pior={s.get('leaveblock_avgr')} peryear_ok={s.get('peryear_ok')}\n")
        f.write("    reason: "+s.get("reason","")+"\n\n")
    f.write("\n===== VERDICT (synth completo) =====\n")
    f.write(r.get("verdict",""))
print("engine_report.txt escrito:", rep.stat().st_size, "bytes |", len(r["survivors"]), "survivors")
