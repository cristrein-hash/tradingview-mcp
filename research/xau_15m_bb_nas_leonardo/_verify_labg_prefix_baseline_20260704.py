#!/usr/bin/env python3
"""R8/R9 — (1) prefixo do universo Lab G: 4499 linhas antigas byte-idênticas pós-extensão
(letrun é confinado ao bloco → g_R antigo não muda; engine setdefault → barras antigas autoritativas);
(2) baseline N435 do engine reproduz sobre a base estendida (+291,5 bruto)."""
import json, sys
from pathlib import Path
SB = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/derivados_sandbox/backup_candidates")
HERE = Path(__file__).parent

old = {}
for l in open(SB / "lab_g_candidates.jsonl", "rb"):
    r = json.loads(l); old[(r["block"], r["t"])] = l
new = {}
for l in open(HERE / "results" / "lab_g_candidates.jsonl", "rb"):
    r = json.loads(l); new[(r["block"], r["t"])] = l
missing = [k for k in old if k not in new]
changed = [k for k in old if k in new and old[k] != new[k]]
added = [k for k in new if k not in old]
print(f"lab_g_candidates: antigos {len(old)} · faltando {len(missing)} · MUDARAM {len(changed)} · novos {len(added)}")
if changed[:3]:
    for k in changed[:3]:
        a, b = json.loads(old[k]), json.loads(new[k])
        print("  ex:", k, sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))[:8])
if missing or changed: print("LAB_G PREFIX FAIL"); sys.exit(1)
print("LAB_G PREFIX PASS")

ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
base = [c for c in ns["cand"] if c["v5h"] != "BEAR"]
s = sum(c["R"] for c in base)
print(f"engine estendido: base #4 N{len(base)} sumR {s:.1f} (esperado N435 +291,5)")
assert len(base) == 435 and abs(s - 291.5) < 0.5, "baseline não reproduz na base estendida"
print("BASELINE PASS")
