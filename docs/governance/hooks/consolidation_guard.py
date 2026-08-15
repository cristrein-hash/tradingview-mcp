#!/usr/bin/env python3
"""Consolidation guard (PreToolUse Write|Edit) — Cris 2026-07-23.
BLOQUEIA (exit 2) a criação/edição de um reader de contexto/regime/mtf/trajetória/macro/sinal que re-lê
bars/store, A NÃO SER QUE: (a) o conteúdo CONSOME o dossiê E0 (market_context/_e0/axes), OU (b) o token de
busca-primeiro está fresco (correu `scripts/safety/consolidation_check.py` nos últimos 20 min).
Anti auto-boicote: construir paralelo em vez de consumir o E0 aprovado (feedback_consume_existing_never_rebuild).
"""
import sys, json, re, time
from pathlib import Path

TOKEN = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/.consolidation_token.json")
FRESH_S = 20 * 60

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name") or ""
if tool not in ("Write", "Edit"):
    sys.exit(0)
ti = data.get("tool_input") or {}
content = (ti.get("content") or "") + (ti.get("new_string") or "")
fpath = (ti.get("file_path") or "").lower()
low = (content + " " + fpath).lower()

# EXEMPT: o próprio pipeline E0, a ferramenta de busca, hooks, testes, research, memória, docs
EXEMPT = ("/hooks/", "consolidation_check", "external_factors", "market_context", "/research/", "test_",
          "/memory/", ".md", "/docs/", "watchdog", "telegram", "journal")
if any(x in low for x in EXEMPT):
    sys.exit(0)

# padrão de "construir reader de contexto/regime/trajetória que re-lê bars/store"
build = re.search(r"(_leg_read|def _leg|def .*regime|def .*trend|lower[\s-]?high|higher[\s-]?low|"
                  r"bars_15m|bars_1h|bars_4h|store/bars|read.*bars_|trajector|multi[\s-]?tf|swing)", low)
purpose = re.search(r"(sinal|signal|classify|fraco|forte|contexto|context|direç|direction|regime|viés|vies|bias|decis)", low)
if not (build and purpose):
    sys.exit(0)

# consome E0 explicitamente? então ok
if re.search(r"(market_context|_e0\(|axes\[|e0\.get|external_factors|dossi)", low):
    sys.exit(0)

# senão, exige token de busca fresco
fresh = False
try:
    t = json.loads(TOKEN.read_text())
    fresh = (time.time() - (t.get("ts") or 0)) < FRESH_S
except Exception:
    fresh = False

if fresh:
    sys.exit(0)

sys.stderr.write(
    "🛑🛑 CONSOLIDATION GUARD — BLOQUEADO (Cris 2026-07-23, anti auto-boicote)\n"
    "  Estás a construir um reader de contexto/regime/trajetória/sinal que re-lê bars/store — SEM consumir o\n"
    "  dossiê E0 e SEM ter corrido a busca-primeiro. Isto é o padrão recorrente: construir PARALELO em vez de\n"
    "  consumir o aprovado (o E0 market_context.json já dá mtf multi-TF + macro yields/DXY + confluence + regime).\n"
    "  → CORRE PRIMEIRO: python3 scripts/safety/consolidation_check.py \"<capacidade>\"\n"
    "     (mostra o que E0/memória/código já dá; se já existe, CONSOME em vez de reconstruir)\n"
    "  → ou faz o teu módulo CONSUMIR o E0 (market_context.json / _e0()).\n"
    "  Ver feedback_consume_existing_never_rebuild.\n")
try:
    import _guard_log; _guard_log.fire("consolidation", "block", "reconstrói reader paralelo sem consumir E0")
except Exception:
    pass
sys.exit(2)
