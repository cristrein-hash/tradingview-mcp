#!/usr/bin/env python3
"""Pre-analysis myopia guard hook (PreToolUse on Bash).

PROBLEM IT SOLVES: passive recalled memory ("use convergent contextual, not single-axis aggregate")
does NOT change the default at action time — Claude repeatedly defaults to static single-axis lift
tests. The post_backtest_devils_advocate hook catches errors AFTER the wrong analysis runs (expensive
redo cycle). This hook fires BEFORE running a separation/reading/filter analysis and forces a design
self-check, preventing the myopic analysis instead of cleaning it up.

Triggers when a Bash command runs a python analysis script in the strategy research dir whose command
text references separation/lift/runner/loser/filter/reading. Injects the anti-myopia checklist.

Dedup per (session, script) via /tmp/.claude_myopia_acknowledged so it asks once per script.

Exit codes: 0 = pass through; 2 = inject checklist via stderr (Claude sees it as system feedback).
"""
import json, sys, re, hashlib, time
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

cmd = (data.get("tool_input") or {}).get("command", "") or ""
if "python" not in cmd:
    sys.exit(0)
# Skip self-tests of the guards themselves + trivial -c probes
if "/hooks/" in cmd or ".claude/hooks" in cmd:
    sys.exit(0)
if re.search(r"python3?\s+-c\s+", cmd):
    sys.exit(0)
# Only fire on ACTUAL analysis execution: running a .py script or a python heredoc (not echoes/greps)
if not (re.search(r"python3?\s+\S+\.py\b", cmd) or re.search(r"python3?\s+-\s*<<|python3?\s+<<", cmd)):
    sys.exit(0)

# Signature of a separation/reading/filter analysis
sep = [r"separa", r"\blift\b", r"runner", r"\bloser\b", r"\bskip", r"\bfilter\b|filtro",
       r"convex", r"bottleneck|gargalo", r"attribution|atribu", r"discrimin", r"markup|reject",
       r"reading|leitura", r"winner",
       # G7 alargado (Cris 2026-08-14): interpretação de ESTRUTURA também dispara (nunca decidir por 1 campo)
       r"\bchoch\b", r"\btrend\b", r"higher[\s-]?low|lower[\s-]?high", r"\bswing\b",
       r"estrutura|structure", r"pivot|pivô", r"_leg\b|leg_read"]
# G7 alargado (Cris 2026-08-14): inspeciona também o CONTEÚDO do script .py referenciado — não só o comando.
# (O meu erro 13/08 correu em 'guard_backtest_...py', sem palavra-chave no NOME → o gatilho só-comando
#  nunca dispararia; mas o CONTEÚDO tem choch/trend/structure. Ler o ficheiro fecha esse buraco.)
blob = cmd
_mpy = re.search(r"python3?\s+(\S+\.py)", cmd)
if _mpy:
    try:
        blob += "\n" + Path(_mpy.group(1)).read_text(errors="ignore")[:20000]
    except Exception:
        pass
if sum(1 for p in sep if re.search(p, blob, re.IGNORECASE)) < 1:
    sys.exit(0)

# G7 (Cris 2026-08-11) — bypass EXPLÍCITO e AUDITÁVEL: exige `SANITY_PROBE: <razão>` (colon+texto), não o
# antigo dedup silencioso (que deixava re-correr a mesma análise míope sem endereçar o checklist).
if re.search(r"SANITY_PROBE\s*:\s*\S", cmd):
    sys.exit(0)

# dedup per session+script
m = re.search(r"python3?\s+(\S+\.py)", cmd)
script = m.group(1) if m else cmd[:80]
sig = hashlib.sha256(script.encode()).hexdigest()[:16]
ack_dir = Path("/tmp/.claude_myopia_acknowledged"); ack_dir.mkdir(exist_ok=True)
sid = data.get("session_id") or "unknown"
ack = ack_dir / f"{sid}_{sig}"
now = time.time()
for f in ack_dir.glob("*"):
    try:
        if now - f.stat().st_mtime > 1*3600: f.unlink()   # G7: 12h→1h (dedup re-arma mais cedo)
    except Exception: pass
if ack.exists():
    sys.exit(0)
ack.touch()

msg = (
    "🧭 ANÁLISE DE LEITURA/SEPARAÇÃO DETECTADA — checklist anti-miopia ANTES de rodar.\n\n"
    "O default errado (repetido o dia inteiro) = teste de EIXO ÚNICO ESTÁTICO na barra i. Confirme:\n"
    "  1. MULTI-FATORIAL? (convergência de ≥2-3 sub-estados ortogonais — NÃO um fator isolado)\n"
    "  2. TRAJETÓRIA? (estado derivado de lookback de barras passadas — NÃO snapshot na barra i;\n"
    "     markup/rejeição/momentum/aceitação são DINÂMICOS)\n"
    "  3. DOIS OBJETIVOS? (capturar convexidade/runner E evitar topo/loser — NÃO um só)\n"
    "  4. FEATURE SET COMPLETO? (84-feat + SVP + bubbles + NAS + sequências — NÃO fatia fina)\n"
    "  5. VALIDAÇÃO? (null/sub-janela dentro dos 276 — NÃO calibração-como-validação; capado nunca árbitro)\n"
    "  6. PRIOR LAYERS vivas como evidência condicional? bater baselines (supply_reject 1.08, bear_leg 1.63)?\n"
    "  7. ESTRUTURA MULTI-CAMPO (Cris 2026-08-14): os campos do dossiE E0/market_context (consumir, nunca\n"
    "     reconstruir) trazem trend E choch por TF — NUNCA decidas por UM SO campo. O rotulo de swing (HH/HL)\n"
    "     ATRASA; a quebra (choch) e a VELA real dao o sinal em tempo real. ERRO 13/08: li so o rotulo lento\n"
    "     e chamei 4H up, ignorando a quebra impressa — nao vi a faca e custou dinheiro. Usa os 3 sempre.\n\n"
    "Se a análise viola 1-2, é MIOPIA — re-desenhe como leitura dinâmica multi-fatorial ANTES de rodar.\n"
    "Se é sonda de sanidade deliberada, declare 'SANITY_PROBE: <razão>' no comando (razão OBRIGATÓRIA, auditável) e prossiga.\n"
    "(Este hook registra ack por script; roda 1× por análise.)"
)
print(msg, file=sys.stderr)
sys.exit(2)
