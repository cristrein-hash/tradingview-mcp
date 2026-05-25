#!/usr/bin/env bash
#
# safe_backtest_window.sh — controlled maintenance window for TradingView/MCP backtests.
#
# Pauses live recheck + the XAU 4H daemon, hard-restarts TradingView (clearing any
# wedged CDP), validates the CDP command channel, runs a SHORT smoke, then ALWAYS
# restores production: removes the pause flag, brings the daemon back, and confirms
# /health + zero orphan MCP servers.
#
# SAFETY:
#   - Does NOT touch the webhook receiver, its LaunchAgent, alerts, or secrets.
#   - Never prints secret values (only reads booleans from /health).
#   - Does NOT run a full backtest. Only --smoke (1 month, dry-run) is wired up here.
#   - Production restore runs on EVERY exit path (trap EXIT), including errors/Ctrl-C.
#
# Usage:
#   ./safe_backtest_window.sh --smoke     # restart TV + 1-month dry-run smoke + restore
#   ./safe_backtest_window.sh --help
#
set -uo pipefail

# ---------------------------------------------------------------- config
REPO_DIR="/Users/cristrein/tradingview-mcp"
ALERT_DIR="$REPO_DIR/alert-bridge"
NODE_BIN="/opt/homebrew/bin/node"
PAUSE_FLAG="/tmp/claude_recheck.paused"
CDP_PORT="9222"

DAEMON_LABEL="com.cristrein.xau-4h-monitor-daemon"
CRON_LABEL="com.cristrein.xau-4h-monitor-cron"
DAEMON_PLIST="$HOME/Library/LaunchAgents/${DAEMON_LABEL}.plist"
CRON_PLIST="$HOME/Library/LaunchAgents/${CRON_LABEL}.plist"
GUI_DOMAIN="gui/$(id -u)"

RECEIVER_HOST="127.0.0.1"
RECEIVER_PORT="8787"   # not a secret; default TV_WEBHOOK_PORT

SERVER_JS="$REPO_DIR/src/server.js"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

usage() {
  cat <<EOF
safe_backtest_window.sh — controlled TradingView/MCP backtest maintenance window

  --smoke              Pause production, hard-restart TradingView, validate CDP, run a SHORT
                       smoke (run_xau_15m_pullback_ohlcv.py --months 1 --dry-run), then restore.
  --collect [--months N]  Same maintenance window, but run a REAL OHLCV collection
                       (run_xau_15m_pullback_ohlcv.py --months N; default N=3, no dry-run).
  --help               Show this help.

A bare invocation (no args) prints this usage and runs nothing.
--full is intentionally rejected. The receiver, its LaunchAgent, alerts, and secrets are never touched.
Production is always restored via the EXIT trap.
EOF
}

# ---------------------------------------------------------------- args
MODE=""
MONTHS=3
while [ $# -gt 0 ]; do
  case "$1" in
    --smoke)   MODE="smoke" ;;
    --collect) MODE="collect" ;;
    --months)  shift; MONTHS="${1:-}" ;;
    --full)    echo "ERRO: --full não autorizado neste script. Use --smoke ou --collect." >&2; exit 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERRO: argumento desconhecido: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done
if [ -z "$MODE" ]; then usage >&2; exit 2; fi
if [ "$MODE" = "collect" ]; then
  if ! printf '%s' "$MONTHS" | grep -qE '^[0-9]+$' || [ "$MONTHS" -lt 1 ]; then
    echo "ERRO: --months precisa ser inteiro >= 1 (recebido: '${MONTHS}')" >&2; exit 2
  fi
fi

# ---------------------------------------------------------------- state (for restore)
DAEMON_STOPPED=0
CRON_STOPPED=0
RUN_RC=1
RESTORED=0

is_loaded() { launchctl list 2>/dev/null | grep -q "$1"; }

restore_production() {
  [ "$RESTORED" = "1" ] && return
  RESTORED=1
  log "=========== RESTORE PRODUÇÃO ==========="

  # 1) remove pause flag (ALWAYS)
  rm -f "$PAUSE_FLAG"
  if [ -e "$PAUSE_FLAG" ]; then log "!! ATENÇÃO: pause flag ainda presente: $PAUSE_FLAG"; else log "pause flag removida"; fi

  # 2) bring the daemon back
  if [ "$DAEMON_STOPPED" = "1" ]; then
    if [ -f "$DAEMON_PLIST" ]; then
      launchctl bootstrap "$GUI_DOMAIN" "$DAEMON_PLIST" 2>/dev/null \
        || launchctl kickstart -k "$GUI_DOMAIN/$DAEMON_LABEL" 2>/dev/null \
        || true
    fi
    sleep 2
    if is_loaded "$DAEMON_LABEL"; then
      log "daemon reativado OK ($DAEMON_LABEL)"
    else
      log "!! ATENÇÃO: daemon NÃO ativo. Reative manual: launchctl bootstrap $GUI_DOMAIN $DAEMON_PLIST"
    fi
  fi

  # 3) bring cron back if we stopped it
  if [ "$CRON_STOPPED" = "1" ] && [ -f "$CRON_PLIST" ]; then
    launchctl bootstrap "$GUI_DOMAIN" "$CRON_PLIST" 2>/dev/null || true
    is_loaded "$CRON_LABEL" && log "cron reativado OK" || log "!! cron NÃO ativo (reative manual se necessário)"
  fi

  # 4) confirm receiver /health (read-only; never touched)
  local H
  H=$(curl -s -m 5 "http://$RECEIVER_HOST:$RECEIVER_PORT/health" 2>/dev/null)
  if echo "$H" | python3 -c "import sys,json;d=json.load(sys.stdin);print('ok='+str(d.get('ok'))+' claude_recheck='+str(d.get('claude_recheck'))+' pause_flag_present='+str(d.get('runtime',{}).get('pause_flag_present')))" 2>/dev/null; then
    :
  else
    log "!! receiver /health não respondeu ou inválido"
  fi

  # 5) confirm zero orphan MCP server.js
  local orph
  orph=$(pgrep -f "$SERVER_JS" 2>/dev/null | wc -l | tr -d ' ')
  log "server.js vivos agora: $orph"

  log "=========== FIM RESTORE ==========="
}
trap restore_production EXIT INT TERM

# ---------------------------------------------------------------- preflight
cd "$REPO_DIR" || { echo "ERRO: repo não encontrado: $REPO_DIR" >&2; exit 1; }
[ -x "$NODE_BIN" ] || { echo "ERRO: node não encontrado: $NODE_BIN" >&2; exit 1; }
log "=========== MAINTENANCE WINDOW START (mode=$MODE) ==========="

# 1) enter maintenance: pause flag (interlock required by the smoke script)
touch "$PAUSE_FLAG"
log "pause flag criada ($PAUSE_FLAG) — claude_recheck pausado"

# 2) stop the XAU daemon (bootout: KeepAlive would restart a simple stop)
if is_loaded "$DAEMON_LABEL"; then
  launchctl bootout "$GUI_DOMAIN/$DAEMON_LABEL" 2>/dev/null || true
  DAEMON_STOPPED=1
  sleep 1
  is_loaded "$DAEMON_LABEL" && log "!! daemon ainda carregado após bootout" || log "daemon parado ($DAEMON_LABEL)"
else
  log "daemon já não estava carregado"
fi

# 3) stop the cron variant if loaded
if is_loaded "$CRON_LABEL"; then
  launchctl bootout "$GUI_DOMAIN/$CRON_LABEL" 2>/dev/null || true
  CRON_STOPPED=1
  log "cron parado ($CRON_LABEL)"
fi

# 4) kill any MCP server.js (clears orphans before the window)
if pgrep -f "$SERVER_JS" >/dev/null 2>&1; then
  pkill -f "$SERVER_JS" 2>/dev/null || true
  sleep 1
fi
log "server.js mortos (restantes: $(pgrep -f "$SERVER_JS" 2>/dev/null | wc -l | tr -d ' '))"

# Reusable CDP/API health poll (node-side). $1 = deadline ms. Exit 0 if cdp&&api, else 4.
cdp_poll() {
  "$NODE_BIN" -e "import('$REPO_DIR/src/core/health.js').then(async h=>{const deadline=Date.now()+$1;let last={};let n=0;while(Date.now()<deadline){n++;try{const r=await h.healthCheck();last={try:n,cdp:r.cdp_connected,api:r.api_available,sym:r.chart_symbol,tf:r.chart_resolution};if(r.cdp_connected&&r.api_available){console.log(JSON.stringify(last));process.exit(0);}}catch(e){last={try:n,error:e.message};}await new Promise(rs=>setTimeout(rs,3000));}console.log(JSON.stringify(last));process.exit(4);})"
}

# 5) check CDP/API health; hard-restart TradingView ONLY if it is NOT healthy.
# A hard restart leaves the chart freshly-loaded, where chart_set_symbol races
# (observed: tf applies, symbol stays). If CDP/API is already healthy we keep the
# stable instance — the restart only exists to clear a wedged CDP.
log "checando CDP/API (poll curto, até ~12s)..."
HEALTH=$(cdp_poll 12000); HRC=$?
echo "  health -> $HEALTH"
if [ $HRC -eq 0 ]; then
  log "CDP/API saudável — PULANDO hard restart (instância estável)"
else
  log "CDP/API unhealthy — hard restart do TradingView (port $CDP_PORT)..."
  LAUNCH=$("$NODE_BIN" -e "import('$REPO_DIR/src/core/health.js').then(async h=>{try{const r=await h.launch({port:$CDP_PORT,kill_existing:true});console.log(JSON.stringify(r));process.exit(r.success?0:3);}catch(e){console.log(JSON.stringify({success:false,error:e.message}));process.exit(3);}})")
  LRC=$?
  echo "  launch -> $LAUNCH"
  if [ $LRC -ne 0 ]; then log "!! FALHA no restart do TradingView — abortando (restore via trap)"; exit 3; fi
  log "revalidando CDP (poll, até ~36s)..."
  HEALTH=$(cdp_poll 36000); HRC=$?
  echo "  health -> $HEALTH"
  if [ $HRC -ne 0 ]; then log "!! CDP não saudável após restart — abortando (restore via trap)"; exit 4; fi
fi
log "CDP OK"

# 7) run the requested operation (inside the maintenance window; trap restores either way)
if [ "$MODE" = "smoke" ]; then
  log "=========== SMOKE (1 mês, dry-run) ==========="
  ( cd "$ALERT_DIR" && python3 -u run_xau_15m_pullback_ohlcv.py --months 1 --dry-run )
  RUN_RC=$?
  if [ $RUN_RC -eq 0 ]; then log "SMOKE PASS (exit_code=0)"; else log "SMOKE FAIL (exit_code=$RUN_RC)"; fi
elif [ "$MODE" = "collect" ]; then
  log "=========== COLLECT (real, ${MONTHS} mês/meses, no dry-run) ==========="
  # No --resume: each window does a TradingView hard restart (chart resets to the saved
  # layout), so the chart symbol/timeframe setup MUST run every time. --resume skips that
  # setup (run_xau_15m_pullback_ohlcv.py:391) and would abort at the chunk-0 guard.
  ( cd "$ALERT_DIR" && python3 -u run_xau_15m_pullback_ohlcv.py --months "$MONTHS" )
  RUN_RC=$?
  if [ $RUN_RC -eq 0 ]; then log "COLLECT PASS (exit_code=0)"; else log "COLLECT FAIL (exit_code=$RUN_RC)"; fi
fi

# restore_production runs here via trap EXIT
exit $RUN_RC
