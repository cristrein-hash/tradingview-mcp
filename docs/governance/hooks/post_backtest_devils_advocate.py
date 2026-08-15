#!/usr/bin/env python3
"""Post-backtest Devil's Advocate guard hook (PostToolUse on Bash).

After any Bash that produces backtest output (sumR/WR/trades patterns),
inject a system reminder forcing spawn of Devil's Advocate agent BEFORE
reporting the result to the user.

Tracks per-session backtest hashes in /tmp/.claude_devil_acknowledged to
avoid spamming the same backtest multiple times.

Exit codes:
  0 = pass through (no injection needed)
  2 = inject reminder via stderr (Claude sees it as system feedback)
"""
import json, sys, re, hashlib, os, time
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input") or {}
command = tool_input.get("command", "") or ""
tool_response = data.get("tool_response") or {}

# Tolerate either string or dict
output = ""
if isinstance(tool_response, dict):
    output = tool_response.get("output") or tool_response.get("stdout") or tool_response.get("content") or ""
    if isinstance(output, list):
        output = " ".join(str(x) for x in output)
elif isinstance(tool_response, str):
    output = tool_response

if not output:
    sys.exit(0)

# Only consider python script executions (typical for backtests)
if "python" not in command:
    sys.exit(0)

# Filter out trivial python -c smoke tests / version checks
if re.search(r"python3?\s+-c\s+", command) and len(output) < 200:
    sys.exit(0)

# Detect backtest signature in output
backtest_indicators = [
    r"\bsumR\b",
    r"\bavgR\b",
    r"WR[\s=:\|]+\d+",
    r"\bwinners?\b[^.]*\blosers?\b",
    r"win[_\s]rate",
    r"\bn\s*=\s*\d+[^.]*\bW\s*=\s*\d+",
    r"baseline:\s*n=",
    r"trades?\s*=\s*\d+",
    r"streak\s*L",
    r"Robust(ness|a)",
]
hits = sum(1 for p in backtest_indicators if re.search(p, output, re.IGNORECASE))
if hits < 2:
    sys.exit(0)

# Dedup per-session via hash of command + first 500 chars of output
sig = hashlib.sha256((command[:200] + "|" + output[:500]).encode()).hexdigest()[:16]
ack_dir = Path("/tmp/.claude_devil_acknowledged")
ack_dir.mkdir(exist_ok=True)
session_id = data.get("session_id") or "unknown"
ack_file = ack_dir / f"{session_id}_{sig}"

# Garbage collect old files (> 12h)
now = time.time()
for f in ack_dir.glob("*"):
    try:
        if now - f.stat().st_mtime > 12*3600:
            f.unlink()
    except Exception:
        pass

if ack_file.exists():
    sys.exit(0)
ack_file.touch()

msg = (
    "🚨 BACKTEST DETECTADO — Devil's Advocate obrigatório.\n\n"
    "ANTES de reportar este resultado ao Cris, spawn agente Devil's Advocate "
    "(Agent subagent_type=general-purpose) questionando:\n"
    "  1. Look-ahead bias — alguma feature daily/weekly usa close do mesmo dia?\n"
    "  2. In-sample contamination — parâmetros tunados sobre estes mesmos dados?\n"
    "  3. Selection bias — quantas variações foram testadas? Bonferroni?\n"
    "  4. Statistical power — n suficiente para detectar uma queda de 20% WR?\n"
    "  5. Hidden execution risks — slippage, gap, latência de regime gate.\n"
    "  6. Reconciliação visual — cross-check com chart real, não só classifier.\n\n"
    "Reportar feedback do Devil's Advocate ANTES da conclusão.\n"
    "Pular este passo = repetir A1' SUPERTREND (WR 88%→46% pós-audit).\n\n"
    "Se Devil's Advocate JÁ foi executado para este backtest específico nesta sessão, "
    "prossiga normalmente (este hook já registrou ack)."
)
try:
    import _guard_log; _guard_log.fire("post_backtest_da", "block", "backtest sem devil's advocate")
except Exception:
    pass
print(msg, file=sys.stderr)
sys.exit(2)
