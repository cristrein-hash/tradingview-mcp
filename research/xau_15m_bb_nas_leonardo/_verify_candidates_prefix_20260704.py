#!/usr/bin/env python3
"""R8/R9 — Validação do prefixo: os 4502 candidatos antigos devem reproduzir BYTE-IDÊNTICOS
(por linha, chaveado por (block,t)) após o rebuild com o 9º bloco. Falha = rollback dos candidates."""
import json, sys
from pathlib import Path
SB = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/derivados_sandbox/backup_candidates")
HERE = Path(__file__).parent
for fname in ("entry_candidates.jsonl", "entry_candidates_htf.jsonl"):
    old = {}
    for l in open(SB / fname, "rb"):
        r = json.loads(l); old[(r["block"], r["t"])] = l
    new = {}
    for l in open(HERE / fname, "rb"):
        r = json.loads(l); new[(r["block"], r["t"])] = l
    missing = [k for k in old if k not in new]
    changed = [k for k in old if k in new and old[k] != new[k]]
    added = [k for k in new if k not in old]
    print(f"{fname}: antigos {len(old)} · faltando {len(missing)} · MUDARAM {len(changed)} · novos {len(added)}")
    if changed[:3]:
        for k in changed[:3]:
            a, b = json.loads(old[k]), json.loads(new[k])
            diff = {f for f in set(a) | set(b) if a.get(f) != b.get(f)}
            print(f"   ex {k}: campos que mudaram: {sorted(diff)[:10]}")
    if missing or changed:
        print("PREFIX FAIL"); sys.exit(1)
print("PREFIX PASS — antigos byte-idênticos; novos são aditivos")
