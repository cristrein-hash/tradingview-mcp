#!/usr/bin/env python3
"""Inspeciona: (a) scripts que computam realized_letrun (régua a modificar p/ BE-após-1R), (b) fonte de entry/SL/path
por trade L2 (price_sequence_4h / supply_demand no episode_reading_input)."""
import json,subprocess
from pathlib import Path
BASE=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
print("=== .py com 'letrun' ===")
out=subprocess.run(["grep","-rl","letrun",str(BASE),"--include=*.py"],capture_output=True,text=True)
print(out.stdout or "(nenhum)")
print("=== .py com 'realized_letrun' (def da régua) ===")
out=subprocess.run(["grep","-rln","realized_letrun",str(BASE),"--include=*.py"],capture_output=True,text=True)
print(out.stdout or "(nenhum)")
f=BASE/"XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_episode_reading_input_276.jsonl"
d=json.loads(f.read_text().splitlines()[0])
print("\n=== episode_reading_input[0] estrutura ===")
print("bar_idx:",d.get("bar_idx"),"ts:",d.get("timestamp"))
ps=d.get("price_sequence_4h")
print("price_sequence_4h type:",type(ps).__name__, "len" , len(ps) if hasattr(ps,'__len__') else '-')
if isinstance(ps,(list,dict)): print("  sample:",json.dumps(ps)[:400])
sd=d.get("supply_demand")
print("supply_demand:",json.dumps(sd)[:400] if sd else None)
