#!/usr/bin/env python3
"""Extrai map + ideias do Workflow orthogonal-scout p/ scout_map.txt."""
import json
from pathlib import Path
OUT=Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/b3051da4-3014-4915-9b74-e74977852ecf/tasks/wv8b82kvm.output")
d=json.load(open(OUT)); r=d["result"]
if isinstance(r,str): r=json.loads(r)
rep=Path(__file__).parent/"scout_map.txt"
with open(rep,"w") as f:
    f.write(f"IDEIAS BRUTAS: {len(r.get('ideas',[]))}\n\n===== MAPA RANQUEADO (synth) =====\n")
    f.write(r.get("map",""))
print("scout_map.txt:", rep.stat().st_size, "bytes |", len(r.get('ideas',[])), "ideias")
