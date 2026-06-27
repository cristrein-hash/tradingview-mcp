#!/usr/bin/env python3
"""Extrai proposals + survivors + verdict do Workflow loser-cut p/ losercut_report.txt (reprodutível)."""
import json
from pathlib import Path
OUT=Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/b3051da4-3014-4915-9b74-e74977852ecf/tasks/wrywptvhk.output")
d=json.load(open(OUT)); r=d["result"]
if isinstance(r,str): r=json.loads(r)
rep=Path(__file__).parent/"losercut_report.txt"
with open(rep,"w") as f:
    f.write(f"SURVIVORS (filtros que passaram verify): {len(r.get('survivors',[]))}\n")
    for s in r.get("survivors",[]):
        f.write(f"  • {s.get('target')}: WR_after={s.get('wr_after')} streak_after={s.get('maxstreak_after')} winners_kept={s.get('winners_kept_pct')}%\n    {s.get('reason','')}\n\n")
    f.write("\n===== PROPOSALS (antes/depois por alvo) =====\n")
    for p in r.get("proposals",[]):
        b=p.get("before",{}); fl=p.get("filter",{})
        f.write(f"\n[{p.get('target')}] ANTES n={b.get('n')} WR={b.get('wr')} streak={b.get('maxstreak')}\n")
        f.write(f"  FILTRO: {fl.get('desc')}\n")
        f.write(f"  DEPOIS n={fl.get('n_after')} WR={fl.get('wr_after')} streak={fl.get('maxstreak_after')} winners_kept={fl.get('winners_kept_pct')}% losers_cut={fl.get('losers_cut_pct')}% | ano {fl.get('y24')}/{fl.get('y25')}/{fl.get('y26')}\n")
    f.write("\n\n===== VERDICT =====\n"+r.get("verdict",""))
print("losercut_report.txt:", rep.stat().st_size, "bytes |", len(r.get("survivors",[])), "survivors,", len(r.get("proposals",[])), "proposals")
