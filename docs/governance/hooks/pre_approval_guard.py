#!/usr/bin/env python3
"""Pre-approval guard hook (PreToolUse on Write|Edit).

Block any Write/Edit on memory file that promotes a strategy as OFICIAL/APROVADA
unless the content has a 'lookahead-audited: YYYY-MM-DD' marker.

Triggered only for files under tradingview-mcp memory directory.

Exit codes:
  0 = allow
  2 = block with stderr message (Claude must rerun after fixing)
"""
import json, sys, re, os

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input") or {}
file_path = tool_input.get("file_path", "") or ""

# Scope filter: only act on tradingview-mcp memory files
in_scope = (
    "tradingview-mcp/memory" in file_path
    or "/.claude/projects/-Users-cristrein-tradingview-mcp/memory/" in file_path
)
if not in_scope:
    sys.exit(0)

# What content is being written
new_string = (
    tool_input.get("new_string")
    or tool_input.get("content")
    or ""
)
if not new_string:
    sys.exit(0)

# Detect promotion patterns (active markers, not historical mentions)
promotion_patterns = [
    r"(?im)promovid[oa]\s+(a\s+)?OFICIAL",
    r"(?im)nov[oa]\s+OFICIAL",
    r"(?im)aprovad[oa]\s+(como\s+)?OFICIAL",
    r"(?im)OFICIAL\s*[-—:]\s*(promovid|aprovad|adotad)",
    r"(?im)passa\s+a\s+OFICIAL",
    r"(?im)candidato\s+OFICIAL",
    r"(?im)\*\*OFICIAL\*\*",
    r"(?im)status[:\s]+OFICIAL",
    r"(?im)marcado\s+como\s+OFICIAL",
]
is_promotion = any(re.search(p, new_string) for p in promotion_patterns)
if not is_promotion:
    sys.exit(0)

# Allow if lookahead audit marker exists
if re.search(r"lookahead-audited:\s*\d{4}-\d{2}-\d{2}", new_string):
    sys.exit(0)

# Block
reason = (
    "PRE-APPROVAL GUARD — bloqueado.\n\n"
    f"Arquivo: {file_path}\n"
    "Conteúdo promove estratégia como OFICIAL/APROVADA SEM marcação 'lookahead-audited: YYYY-MM-DD'.\n\n"
    "ANTES de prosseguir:\n"
    "1. Rodar auditoria look-ahead em TODAS features daily/weekly aplicadas a bars intraday.\n"
    "2. Comparar versão SHIFT1 (sem look-ahead) vs ORIG.\n"
    "3. Critério ROBUSTO: Δ sumR < 25% E Δ WR < 10pp E Δ n < 10%.\n"
    "4. Se passou: adicionar linha 'lookahead-audited: 2026-MM-DD' no frontmatter ou descrição.\n"
    "5. Se falhou: INVALIDAR, NÃO promover.\n\n"
    "Histórico: A1' SUPERTREND v1 promovida 2026-06-05 com WR 88%/+75R, invalidada 2026-06-06 "
    "ao descobrir look-ahead — versão limpa WR 46%/+20R. Esse hook existe pra prevenir repetição."
)
try:
    import _guard_log; _guard_log.fire("pre_approval", "block", "promoção sem auditoria lookahead")
except Exception:
    pass
print(reason, file=sys.stderr)
sys.exit(2)
