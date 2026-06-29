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
# 2) calendário ForexFactory (keyless): datas/consenso/actual reais (substitui gerador+consenso+captura manual)
/usr/bin/python3 collectors/forexfactory_collect.py >> "$LOG" 2>&1 || echo "[warn] forexfactory_collect falhou" >> "$LOG"
# 3) ciclo do monitor (overlay consenso + freeze latest.json)
/usr/bin/python3 runtime/monitor_external_factors.py >> "$LOG" 2>&1
# 4) frota Tier-2 LLM via `claude -p` (DENTRO do plano Max — Opção B; sem billing de API).
#    Sem ANTHROPIC_API_KEY no ambiente -> claude usa auth da assinatura. Fallback keyless interno se CLI ausente.
if command -v claude >/dev/null 2>&1 || [ -x "$HOME/.local/bin/claude" ]; then
  PATH="$HOME/.local/bin:$PATH" /usr/bin/python3 agents/fleet.py >> "$LOG" 2>&1 || echo "[warn] fleet falhou" >> "$LOG"
else
  echo "[info] claude CLI ausente -> Tier-2 pulado (Camada A keyless segue)" >> "$LOG"
fi
# poda: manter só os 200 snapshots state_*.json mais recentes + cap do daemon.log em 5000 linhas
ls -1t "$DIR"/snapshots/state_*.json 2>/dev/null | tail -n +201 | xargs rm -f 2>/dev/null || true
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 5000 ]; then tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"; fi
echo "ciclo ok $(date -u +%FT%TZ)" >> "$LOG"
