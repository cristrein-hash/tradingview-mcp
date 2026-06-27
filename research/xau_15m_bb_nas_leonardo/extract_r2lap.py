#!/usr/bin/env python3
"""Extrai survivors + verdict do Workflow R2-lapidacao p/ r2lap_report.txt."""
import json
from pathlib import Path
OUT=Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/b3051da4-3014-4915-9b74-e74977852ecf/tasks/wak9d0c11.output")
d=json.load(open(OUT)); r=d["result"]
if isinstance(r,str): r=json.loads(r)
rep=Path(__file__).parent/"r2lap_report.txt"
with open(rep,"w") as f:
    f.write(f"SURVIVORS (pós-verify): {len(r.get('survivors',[]))}\n")
    for s in r.get("survivors",[]):
        f.write(f"  • {s.get('desc')}\n    WR_keep={s.get('wr_keep')} streak_keep={s.get('streak_keep')} winners_kept={s.get('winners_kept_pct')}%\n    {s.get('reason','')}\n\n")
    f.write("\n===== REGRAS robust=true (finders) =====\n")
    for x in r.get("allRules",[]):
        if x.get("robust"):
            f.write(f"  [{x.get('family','')[:30]}] {x.get('desc')}\n    n={x.get('n_keep')} WR={x.get('wr_keep')} streak={x.get('streak_keep')} winners_kept={x.get('winners_kept_pct')}% | ano {x.get('y24')}/{x.get('y25')}/{x.get('y26')}\n")
    f.write("\n===== VERDICT =====\n"+r.get("verdict",""))
print("r2lap_report.txt:", rep.stat().st_size, "|", len(r.get("survivors",[])), "survivors")
