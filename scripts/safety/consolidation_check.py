#!/usr/bin/env python3
"""BUSCA-PRIMEIRO (Cris 2026-07-23) — o passo OBRIGATÓRIO antes de construir qualquer leitura de
contexto/regime/mtf/trajetória/macro/sinal. Inspeciona o que JÁ EXISTE (dossiê E0 + memória + código vivo)
para a capacidade pedida, e escreve o token que o `consolidation_guard` hook exige. Sem correr isto, o guard
BLOQUEIA a escrita de readers novos (anti auto-boicote: construir paralelo em vez de consumir o aprovado).

Uso: python3 scripts/safety/consolidation_check.py "<capacidade>"   (ex.: "trajetória multi-tf", "yields", "regime")
"""
import sys, json, subprocess, datetime as dt
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
E0_F = REPO / "external_factors_v2/snapshots/market_context.json"
TOKEN = REPO / "my-strategy/core/.consolidation_token.json"
MEM = Path.home() / ".claude/projects/-Users-cristrein-tradingview-mcp/memory"

cap = " ".join(sys.argv[1:]).strip() or "(sem capacidade)"
print(f"═══ BUSCA-PRIMEIRO · capacidade: {cap} ═══\n")

print("[1] DOSSIÊ E0 (market_context.json) — cérebro de contexto ÚNICO. JÁ dá:")
try:
    ax = json.loads(E0_F.read_text()).get("axes") or {}
    for k in ax:
        v = ax[k]
        sample = json.dumps(v, ensure_ascii=False)[:90] if isinstance(v, dict) else str(v)[:90]
        print(f"    • axes.{k}: {sample}")
except Exception as e:
    print(f"    (E0 ilegível: {e})")

print("\n[2] MEMÓRIA — ficheiros que mencionam a capacidade:")
try:
    r = subprocess.run(["grep", "-rilE", cap.replace(" ", ".*"), str(MEM)],
                       capture_output=True, text=True, timeout=15)
    hits = [x.split("/")[-1] for x in r.stdout.splitlines()][:8]
    print("   ", hits or "(nenhum)")
except Exception:
    print("    (grep memória falhou)")

print("\n[3] CÓDIGO VIVO — módulos que já implementam algo da capacidade:")
try:
    r = subprocess.run(["grep", "-rilE", cap.replace(" ", ".*"),
                        str(REPO / "my-strategy"), str(REPO / "alert-bridge")],
                       capture_output=True, text=True, timeout=15)
    hits = [x.replace(str(REPO) + "/", "") for x in r.stdout.splitlines() if "__pycache__" not in x][:8]
    print("   ", hits or "(nenhum)")
except Exception:
    print("    (grep código falhou)")

TOKEN.write_text(json.dumps({"ts": int(dt.datetime.now(dt.timezone.utc).timestamp()), "capability": cap}))
print(f"\n✅ token escrito ({TOKEN.name}). REGRA: se o E0/memória/código já dá isto → CONSUMIR, não reconstruir.")
print("   Só construir NOVO se genuinamente não existir — e anunciá-lo.")
