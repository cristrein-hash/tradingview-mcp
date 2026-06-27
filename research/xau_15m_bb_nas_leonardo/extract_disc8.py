#!/usr/bin/env python3
"""Extrai allRules + survivors + verdict do Workflow 8ATR-discriminator p/ disc8_report.txt."""
import json
from pathlib import Path
OUT=Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/b3051da4-3014-4915-9b74-e74977852ecf/tasks/wurlv3wb8.output")
d=json.load(open(OUT)); r=d["result"]
if isinstance(r,str): r=json.loads(r)
rep=Path(__file__).parent/"disc8_report.txt"
def pct(x):
    try: return f"{float(x)*100:.1f}" if float(x)<=1.5 else f"{float(x):.1f}"
    except: return str(x)
with open(rep,"w") as f:
    f.write(f"SURVIVORS (pós-verify): {len(r.get('survivors',[]))}\n")
    for s in r.get("survivors",[]):
        f.write(f"  • {s.get('desc')}\n    WR_keep={pct(s.get('wr_keep'))} streak_keep={s.get('streak_keep')} winners_kept={pct(s.get('winners_kept_pct'))}%\n    {s.get('reason','')}\n\n")
    f.write("\n===== TODAS REGRAS (allRules) =====\n")
    for x in r.get("allRules",[]):
        f.write(f"\n[{'ROBUST' if x.get('robust') else 'teaching'}] {x.get('desc')}\n")
        f.write(f"   n_keep={x.get('n_keep')} WR={pct(x.get('wr_keep'))} streak={x.get('streak_keep')} winners_kept={pct(x.get('winners_kept_pct'))}% losers_cut={pct(x.get('losers_cut_pct'))}% | ano {pct(x.get('y24'))}/{pct(x.get('y25'))}/{pct(x.get('y26'))}\n")
    f.write("\n\n===== VERDICT =====\n"+r.get("verdict",""))
print("disc8_report.txt:", rep.stat().st_size, "bytes |", len(r.get("survivors",[])), "survivors,", len(r.get("allRules",[])), "rules")
