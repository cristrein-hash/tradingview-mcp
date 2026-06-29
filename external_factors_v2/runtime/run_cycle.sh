#!/bin/zsh
# Um ciclo de monitoração External Factors v2 (Tier-1 + Camada A consenso/direção + freeze).
# Keyless por padrão; se .env tiver ANTHROPIC_API_KEY, a frota Tier-2 também roda.
set -e
DIR="/Users/cristrein/tradingview-mcp/external_factors_v2"
cd "$DIR"
LOG="$DIR/snapshots/daemon.log"
echo "=== $(date -u +%FT%TZ) ===" >> "$LOG"
# 1) refresh Tier-1 (keyless) — só se coletor existir; tolera falha de rede
/usr/bin/python3 collectors/fred_collect.py >> "$LOG" 2>&1 || echo "[warn] fred_collect falhou" >> "$LOG"
# 2) captura actual de NFP se já liberado (atualiza direção)
/usr/bin/python3 runtime/capture_nfp_actual.py >> "$LOG" 2>&1 || true
# 3) ciclo do monitor (overlay consenso + freeze latest.json)
/usr/bin/python3 runtime/monitor_external_factors.py >> "$LOG" 2>&1
# 4) frota Tier-2 LLM (só se key presente; senão fallback keyless interno)
if [ -f "$DIR/.env" ] && grep -q "^ANTHROPIC_API_KEY=." "$DIR/.env"; then
  "$DIR/.venv-agents/bin/python" agents/fleet.py >> "$LOG" 2>&1 || echo "[warn] fleet falhou" >> "$LOG"
fi
echo "ciclo ok $(date -u +%FT%TZ)" >> "$LOG"
